import asyncio
import json
import logging
import os
import webbrowser
from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

awaiting_youtube = False

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok", "message": "JARVIS backend running"})

@app.websocket("/ws/voice")
async def ws(websocket: WebSocket):
    global awaiting_youtube
    await websocket.accept()
    log.info("WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "transcript":
                text = msg.get("text", "").lower().strip()
                log.info(f"User: {text}")

                # Remove wake word
                if text.startswith("jarvis"):
                    text = text[6:].strip()
                if text.startswith("hey jarvis"):
                    text = text[10:].strip()

                # YouTube flow
                if awaiting_youtube:
                    awaiting_youtube = False
                    webbrowser.open(f"https://www.youtube.com/results?search_query={text.replace(' ', '+')}")
                    response = f"Searching YouTube for '{text}', sir."
                elif "open youtube" in text:
                    webbrowser.open("https://www.youtube.com")
                    awaiting_youtube = True
                    response = "Opening YouTube, sir. What would you like me to search for?"
                elif "hello" in text:
                    response = "Hello sir, how may I help you?"
                elif "time" in text:
                    response = datetime.now().strftime("%I:%M %p")
                else:
                    response = f"You said: {msg.get('text', '')}"

                await websocket.send_json({"type": "audio", "text": response})
    except Exception as e:
        log.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
