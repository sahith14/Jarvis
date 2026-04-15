import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

GROQ_API_KEY = "os.getenv("GROQ_API_KEY")"
groq_client = Groq(api_key=GROQ_API_KEY)

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

@app.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    log.info("Connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "transcript" and msg.get("isFinal"):
                user_text = msg.get("text", "")
                log.info(f"User: {user_text}")
                
                await websocket.send_json({"type": "status", "state": "thinking"})
                
                # Get AI response
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are JARVIS. Be very brief (1 sentence). Address user as sir."},
                        {"role": "user", "content": user_text}
                    ],
                    max_tokens=100
                )
                reply = response.choices[0].message.content
                log.info(f"JARVIS: {reply}")
                
                # Send as text - browser will speak it
                await websocket.send_json({
                    "type": "audio",
                    "text": reply
                })
                
                await websocket.send_json({"type": "status", "state": "idle"})
                
    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
