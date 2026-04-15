import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

@app.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket connected - waiting for wake word")
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            log.info(f"Received: {msg}")
            
            if msg.get("type") == "transcript":
                user_text = msg.get("text", "").lower()
                log.info(f"User said: {user_text}")
                
                if "jarvis" in user_text:
                    log.info("WAKE WORD DETECTED!")
                    response = "Yes sir, I'm here. How can I help you?"
                elif "hello" in user_text:
                    response = "Hello sir, good to see you."
                elif "time" in user_text:
                    from datetime import datetime
                    response = f"The time is {datetime.now().strftime('%I:%M %p')}, sir."
                else:
                    response = f"I heard you say: {user_text[:50]}"
                
                log.info(f"JARVIS: {response}")
                await websocket.send_json({"type": "audio", "text": response})
                
    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
