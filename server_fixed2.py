import asyncio
import json
import logging
import os
import shutil
import re
from datetime import datetime
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

# ---------- HELPERS ----------
def expand_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))

def open_file_explorer(path: str = None) -> bool:
    try:
        os.startfile(expand_path(path or "~"))
        return True
    except Exception as e:
        log.error(f"Explorer error: {e}")
        return False

def create_folder(path: str) -> str:
    try:
        os.makedirs(expand_path(path), exist_ok=True)
        return f"Created folder '{path}' sir."
    except Exception as e:
        return f"Failed: {e}"

def delete_folder(path: str) -> str:
    try:
        full = expand_path(path)
        if os.path.exists(full):
            shutil.rmtree(full)
            return f"Deleted folder '{path}' sir."
        return f"Folder '{path}' not found sir."
    except Exception as e:
        return f"Failed: {e}"

def create_file(path: str) -> str:
    try:
        with open(expand_path(path), "w") as f:
            f.write("")
        return f"Created file '{path}' sir."
    except Exception as e:
        return f"Failed: {e}"

def read_file(path: str) -> str:
    try:
        with open(expand_path(path), "r", encoding="utf-8") as f:
            content = f.read()
        return content[:500]
    except Exception as e:
        return f"Error: {e}"

def delete_file(path: str) -> str:
    try:
        full = expand_path(path)
        if os.path.exists(full):
            os.remove(full)
            return f"Deleted file '{path}' sir."
        return f"File not found sir."
    except Exception as e:
        return f"Failed: {e}"

def search_files(keyword: str, root: str = ".") -> str:
    try:
        matches = []
        for r, _, files in os.walk(expand_path(root)):
            for f in files:
                if keyword.lower() in f.lower():
                    matches.append(os.path.join(r, f))
                    if len(matches) >= 5:
                        break
        return "\n".join(matches) if matches else "Nothing found sir."
    except Exception as e:
        return f"Error: {e}"

# ---------- COMMAND ENGINE (simple keyword matching) ----------
async def execute_command(user_text: str) -> str:
    # Remove "hey jarvis", "jarvis" prefix
    text = re.sub(r"^(hey\s+)?jarvis[, ]*", "", user_text.lower().strip())

    if not text:
        return "Yes sir?"

    # --- FILE EXPLORER ---
    if "open" in text and "downloads" in text:
        open_file_explorer("~/Downloads")
        return "Opening Downloads, sir."

    if "open" in text and "desktop" in text:
        open_file_explorer("~/Desktop")
        return "Opening Desktop, sir."

    if "open" in text and "documents" in text:
        open_file_explorer("~/Documents")
        return "Opening Documents, sir."

    if "open" in text and "file explorer" in text:
        open_file_explorer()
        return "Opening File Explorer, sir."

    if "open" in text and "folder" in text:
        folder = text.split("folder")[-1].strip()
        full = expand_path(folder)
        if os.path.exists(full):
            open_file_explorer(full)
            return f"Opening {folder}, sir."
        return "Folder not found, sir."

    # --- FOLDER OPERATIONS ---
    if "create folder" in text:
        folder = text.split("folder")[-1].strip()
        return create_folder(folder)

    if "delete folder" in text:
        folder = text.split("folder")[-1].strip()
        return delete_folder(folder)

    # --- FILE OPERATIONS ---
    if "create file" in text:
        filename = text.split("file")[-1].strip()
        return create_file(filename)

    if "read file" in text:
        filename = text.split("file")[-1].strip()
        return read_file(filename)

    if "delete file" in text:
        filename = text.split("file")[-1].strip()
        return delete_file(filename)

    if "search for" in text:
        keyword = text.split("search for")[-1].strip()
        return search_files(keyword)

    # --- SIMPLE UTILITIES ---
    if "time" in text:
        return datetime.now().strftime("%I:%M %p")

    if "hello" in text or "hi" in text:
        return "Hello sir, how may I help you?"

    # --- AI FALLBACK (only for conversation) ---
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are JARVIS. Be brief (1-2 sentences). Address user as 'sir' (lowercase). Never pretend to do actions you didn't actually do."},
                {"role": "user", "content": user_text}
            ],
            max_tokens=100
        )
        return res.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "System error, sir."

# ---------- API ENDPOINTS ----------
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
                user_text = msg.get("text", "")
                log.info(f"User: {user_text}")
                response = await execute_command(user_text)
                log.info(f"JARVIS: {response}")
                await websocket.send_json({"type": "audio", "text": response})
    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
