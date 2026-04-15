import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq
from terminal_control import run_terminal_command, open_terminal_and_run, list_directory, create_file

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

GROQ_API_KEY = "os.getenv("GROQ_API_KEY")"
groq = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are JARVIS, a British AI assistant. You can control the computer terminal.
Available actions (output as [ACTION:type|command]):
- terminal: run any command
- open_terminal: open new terminal window  
- list_files: show directory contents
- create_file: create a new file

Be brief (1 sentence). Address user as sir (lowercase).
Example: [ACTION:terminal|dir] will list files.
"""

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

@app.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "transcript" and msg.get("isFinal"):
                user_text = msg.get("text", "")
                log.info(f"User: {user_text}")
                
                await websocket.send_json({"type": "status", "state": "thinking"})
                
                # Check for terminal commands
                response_text = ""
                lower_text = user_text.lower()
                
                if "list files" in lower_text or "show files" in lower_text:
                    result = await list_directory(".")
                    response_text = f"sir, here are the files: {result['output'][:200]}"
                elif "open terminal" in lower_text:
                    result = await open_terminal_and_run("echo JARVIS is ready")
                    response_text = "Terminal opened, sir."
                elif "run command" in lower_text or "execute" in lower_text:
                    cmd = user_text.replace("run command", "").replace("execute", "").strip()
                    result = await run_terminal_command(cmd)
                    if result["success"]:
                        response_text = f"Command executed, sir. Output: {result['output'][:200]}"
                    else:
                        response_text = f"Command failed, sir. Error: {result['error'][:100]}"
                else:
                    # Use Groq for general conversation
                    try:
                        completion = groq.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_text}
                            ],
                            max_tokens=150
                        )
                        response_text = completion.choices[0].message.content
                    except Exception as e:
                        response_text = "I'm having trouble, sir."
                
                log.info(f"JARVIS: {response_text}")
                
                await websocket.send_json({
                    "type": "audio",
                    "text": response_text
                })
                
                await websocket.send_json({"type": "status", "state": "idle"})
                
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
