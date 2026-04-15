import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import base64

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('jarvis')

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

from ai_groq import generate_response
from tts_elevenlabs import synthesize_speech

SYSTEM_PROMPT = """You are JARVIS, a British AI assistant. 
Be brief and helpful (1-2 sentences). Address the user as 'sir'."""

@app.websocket("/ws/voice")
async def voice_handler(websocket: WebSocket):
    await websocket.accept()
    log.info("JARVIS connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "transcript" and msg.get("isFinal"):
                user_text = msg.get("text", "")
                log.info(f"User: {user_text}")
                
                # Send thinking status
                await websocket.send_json({"type": "status", "state": "thinking"})
                
                # Generate AI response
                response_text = await generate_response(user_text, SYSTEM_PROMPT)
                log.info(f"JARVIS: {response_text}")
                
                # Generate speech
                audio_bytes = await synthesize_speech(response_text)
                
                if audio_bytes:
                    # Send audio response
                    b64_audio = base64.b64encode(audio_bytes).decode()
                    await websocket.send_json({
                        "type": "audio",
                        "data": b64_audio,
                        "text": response_text
                    })
                else:
                    # Fallback to text only
                    await websocket.send_json({"type": "text", "text": response_text})
                
                # Send idle status
                await websocket.send_json({"type": "status", "state": "idle"})
                
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8341)
