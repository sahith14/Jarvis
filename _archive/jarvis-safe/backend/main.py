import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

from tools import (
    open_app, open_youtube, play_music, navigate_folder,
    create_file, delete_file, read_file, rename_file,
    get_best_youtube_video
)
from safe_edit import generate_diff, apply_patch, rollback_file, validate_code

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are JARVIS, an AI assistant. Respond with JSON only.
Available actions:
- open_app: { "action": "open_app", "target": "chrome|notepad|calculator|..." }
- open_youtube: { "action": "open_youtube", "query": "search term" }
- play_music: { "action": "play_music", "target": "play|pause|next|previous|song name" }
- navigate_folder: { "action": "navigate_folder", "path": "absolute or relative path" }
- create_file: { "action": "create_file", "path": "file path" }
- delete_file: { "action": "delete_file", "path": "file path" }
- read_file: { "action": "read_file", "path": "file path" }
- rename_file: { "action": "rename_file", "old": "old path", "new": "new path" }
- propose_edit: { "action": "propose_edit", "path": "file path", "content": "new file content" }

For code editing, AI should return "propose_edit" with full new content.
For conversation, return { "action": "chat", "message": "response text" }.
Always output valid JSON only."""

class ActionRequest(BaseModel):
    action: str
    params: dict

@app.get("/api/settings/status")
async def status():
    return {"status": "online", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}

@app.post("/api/apply-patch")
async def apply_patch_endpoint(path: str, content: str):
    """Apply a code patch after user approval."""
    success, message = apply_patch(path, content)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message}

@app.post("/api/rollback")
async def rollback_endpoint(path: str):
    """Rollback a file to its backup."""
    success = rollback_file(path)
    if not success:
        raise HTTPException(status_code=404, detail="No backup found")
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

            # Call Groq
            try:
                completion = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )
                ai_response = json.loads(completion.choices[0].message.content)
            except Exception as e:
                log.error(f"Groq error: {e}")
                ai_response = {"action": "chat", "message": "I'm having trouble, sir."}

            # Execute action if not chat
            result_message = ""
            if ai_response.get("action") != "chat":
                action = ai_response.get("action")
                params = {k: v for k, v in ai_response.items() if k != "action"}
                try:
                    if action == "open_app":
                        result_message = open_app(params.get("target", ""))
                    elif action == "open_youtube":
                        query = params.get("query", "")
                        if query:
                            video_url = get_best_youtube_video(query)
                            result_message = open_youtube(video_url)
                        else:
                            result_message = "No search query provided."
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
                    elif action == "propose_edit":
                        path = params.get("path", "")
                        new_content = params.get("content", "")
                        old_content = read_file(path)
                        diff = generate_diff(old_content, new_content)
                        await websocket.send_json({
                            "type": "propose_edit",
                            "path": path,
                            "old_content": old_content,
                            "new_content": new_content,
                            "diff": diff
                        })
                        result_message = f"Proposed edit for {path}. Awaiting approval."
                    else:
                        result_message = f"Unknown action: {action}"
                except Exception as e:
                    log.error(f"Action execution error: {e}")
                    result_message = f"Action failed: {str(e)}"
                ai_response["message"] = result_message

            await websocket.send_json({
                "type": "response",
                "data": ai_response
            })
    except WebSocketDisconnect:
        log.info("Voice WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
