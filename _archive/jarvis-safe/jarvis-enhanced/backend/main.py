import os, json, logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

from tools import *
from safe_edit import generate_diff, apply_patch, rollback_file, assess_danger
from memory import (
    set_preference, get_preference, log_command, build_memory_context, add_fact
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are JARVIS, an AI assistant. Respond with JSON only.
Available actions:
- open_app: { "action": "open_app", "target": "app name" }
- open_youtube: { "action": "open_youtube", "query": "search" }
- play_music: { "action": "play_music", "target": "play|pause|next|previous" }
- navigate_folder: { "action": "navigate_folder", "path": "path" }
- create_file: { "action": "create_file", "path": "path" }
- delete_file: { "action": "delete_file", "path": "path" }
- read_file: { "action": "read_file", "path": "path" }
- rename_file: { "action": "rename_file", "old": "old", "new": "new" }
- run_terminal: { "action": "run_terminal", "command": "safe command", "working_dir": "optional" }
- propose_edit: { "action": "propose_edit", "path": "path", "content": "full new content" }
- remember: { "action": "remember", "fact": "fact to store" }
- set_preference: { "action": "set_preference", "key": "key", "value": "value" }
For conversation: { "action": "chat", "message": "response" }"""

class ActionRequest(BaseModel):
    action: str
    params: dict

@app.get("/api/settings/status")
async def status():
    return {"status": "online", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}

@app.post("/api/apply-patch")
async def apply_patch_endpoint(path: str, content: str):
    success, message = apply_patch(path, content)
    if not success:
        raise HTTPException(400, detail=message)
    return {"status": "success", "message": message}

@app.post("/api/rollback")
async def rollback_endpoint(path: str):
    success = rollback_file(path)
    if not success:
        raise HTTPException(404, detail="No backup found")
    return {"status": "success", "message": f"Rolled back {path}"}

@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    log.info("Voice WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") != "transcript":
                continue
            user_text = msg.get("text", "").strip()
            if not user_text:
                continue
            log.info(f"User: {user_text}")

            # Build memory context
            memory_context = build_memory_context(user_text)
            system_with_memory = SYSTEM_PROMPT + "\n\nUSER CONTEXT:\n" + memory_context

            try:
                completion = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_with_memory},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.3, max_tokens=500, response_format={"type": "json_object"}
                )
                ai_response = json.loads(completion.choices[0].message.content)
            except Exception as e:
                log.error(f"Groq error: {e}")
                ai_response = {"action": "chat", "message": "I'm having trouble, sir."}

            result_message = ""
            if ai_response.get("action") != "chat":
                action = ai_response.get("action")
                params = {k: v for k, v in ai_response.items() if k != "action"}
                try:
                    if action == "open_app":
                        result_message = open_app(params.get("target", ""))
                    elif action == "open_youtube":
                        query = params.get("query", "")
                        video_url = get_best_youtube_video(query) if query else ""
                        result_message = open_youtube(video_url or query)
                    elif action == "play_music":
                        result_message = play_music(params.get("target", ""))
                    elif action == "navigate_folder":
                        result_message = navigate_folder(params.get("path", ""))
                    elif action == "create_file":
                        result_message = create_file(params.get("path", ""))
                    elif action == "delete_file":
                        result_message = delete_file(params.get("path", ""))
                    elif action == "read_file":
                        content = read_file(params.get("path", ""))
                        await websocket.send_json({"type": "file_content", "path": params.get("path"), "content": content})
                        result_message = f"Read file {params.get('path')}"
                    elif action == "rename_file":
                        result_message = rename_file(params.get("old", ""), params.get("new", ""))
                    elif action == "run_terminal":
                        result_message = run_terminal_command(params.get("command", ""), params.get("working_dir"))
                    elif action == "remember":
                        add_fact(params.get("fact", ""))
                        result_message = "I'll remember that, sir."
                    elif action == "set_preference":
                        set_preference(params.get("key", ""), params.get("value", ""))
                        result_message = f"Preference {params.get('key')} set."
                    elif action == "propose_edit":
                        path = params.get("path", "")
                        new_content = params.get("content", "")
                        old_content = read_file(path)
                        diff = generate_diff(old_content, new_content)
                        danger_level, warnings = assess_danger(old_content, new_content)
                        await websocket.send_json({
                            "type": "propose_edit",
                            "path": path, "old_content": old_content,
                            "new_content": new_content, "diff": diff,
                            "danger_level": danger_level, "warnings": warnings
                        })
                        result_message = f"Proposed edit for {path}. Awaiting approval."
                    else:
                        result_message = f"Unknown action: {action}"
                except Exception as e:
                    log.error(f"Action error: {e}")
                    result_message = f"Action failed: {str(e)}"
                ai_response["message"] = result_message

            log_command(user_text, ai_response.get("message", ""))
            await websocket.send_json({"type": "response", "data": ai_response})
    except WebSocketDisconnect:
        log.info("Voice WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
