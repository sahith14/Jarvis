import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from terminal_control import open_file_explorer, open_downloads, open_desktop, open_documents, run_terminal_command

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
    log.info("WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "transcript":
                user_text = msg.get("text", "").lower()
                log.info(f"User: {user_text}")
                
                # File explorer commands
                if "open file explorer" in user_text or "open my files" in user_text:
                    result = await open_file_explorer()
                    response = "Opening File Explorer, sir."
                    
                elif "open downloads" in user_text:
                    result = await open_downloads()
                    response = "Opening Downloads folder, sir."
                    
                elif "open desktop" in user_text:
                    result = await open_desktop()
                    response = "Opening Desktop folder, sir."
                    
                elif "open documents" in user_text:
                    result = await open_documents()
                    response = "Opening Documents folder, sir."
                    
                elif "jarvis" in user_text:
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
