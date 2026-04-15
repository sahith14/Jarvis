import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import AI and TTS
from ai_groq import generate_response
from tts_elevenlabs import synthesize_speech

SYSTEM_PROMPT = "You are JARVIS, a British AI assistant. Be brief (1-2 sentences). Address the user as 'sir'."

# API endpoint for settings/status
@app.get("/api/settings/status")
async def settings_status():
    return JSONResponse({
        "claude_code_installed": False,
        "calendar_accessible": False,
        "mail_accessible": False,
        "notes_accessible": False,
        "memory_count": 0,
        "task_count": 0,
        "server_port": 8000,
        "uptime_seconds": 0,
        "env_keys_set": {
            "anthropic": True,
            "fish_audio": True,
            "fish_voice_id": True,
            "user_name": "Sahith"
        }
    })

@app.get("/api/settings/preferences")
async def settings_preferences():
    return JSONResponse({
        "user_name": "Sahith",
        "honorific": "sir",
        "calendar_accounts": "auto"
    })

@app.post("/api/settings/keys")
async def settings_keys(request: dict):
    return JSONResponse({"success": True})

@app.post("/api/settings/test-anthropic")
async def test_anthropic():
    return JSONResponse({"valid": True})

@app.post("/api/settings/test-fish")
async def test_fish():
    return JSONResponse({"valid": True})

@app.post("/api/settings/preferences")
async def save_preferences(request: dict):
    return JSONResponse({"success": True})

@app.post("/api/restart")
async def restart():
    return JSONResponse({"status": "restarting"})

# Main WebSocket endpoint
@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
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
                
                response = await generate_response(user_text, SYSTEM_PROMPT)
                log.info(f"JARVIS: {response}")
                
                audio_bytes = await synthesize_speech(response)
                
                if audio_bytes:
                    b64_audio = base64.b64encode(audio_bytes).decode()
                    await websocket.send_json({
                        "type": "audio",
                        "data": b64_audio,
                        "text": response
                    })
                else:
                    await websocket.send_json({"type": "text", "text": response})
                
                await websocket.send_json({"type": "status", "state": "idle"})
                
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
