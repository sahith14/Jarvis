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
import win32com.client

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

GROQ_API_KEY = "os.getenv("GROQ_API_KEY")"
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------- PERSISTENT EXPLORER WINDOW ----------
_explorer_window = None

def get_or_create_explorer():
    global _explorer_window
    shell = win32com.client.Dispatch("Shell.Application")
    for w in shell.Windows():
        if w.Name == "File Explorer" and w.Visible:
            _explorer_window = w
            return w
    _explorer_window = shell.Explore(os.path.expanduser("~"))
    return _explorer_window

def navigate_explorer(path):
    global _explorer_window
    win = get_or_create_explorer()
    full_path = os.path.abspath(os.path.expanduser(path))
    if os.path.exists(full_path):
        win.Navigate(full_path)
        win.Visible = True
        return True
    return False

def open_file_explorer(path: str = None):
    navigate_explorer(path or "~")

# ---------- LOCATION RESOLUTION ----------
def resolve_location(name: str, location_phrase: str) -> str:
    """Resolve full path given item name and location phrase like 'in the desktop'"""
    location_phrase = location_phrase.lower().strip()
    # Remove "in the" or "in"
    if location_phrase.startswith("in the"):
        loc = location_phrase[6:].strip()
    elif location_phrase.startswith("in"):
        loc = location_phrase[2:].strip()
    else:
        loc = location_phrase
    # Map common locations
    base_map = {
        "desktop": "~/Desktop",
        "downloads": "~/Downloads",
        "documents": "~/Documents",
        "pictures": "~/Pictures",
        "music": "~/Music",
        "videos": "~/Videos",
        "home": "~"
    }
    if loc in base_map:
        base = os.path.expanduser(base_map[loc])
    else:
        # treat loc as a relative path from current directory? but for simplicity, use as is
        base = expand_path(loc)
    return os.path.join(base, name)

def expand_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))

# ---------- FILE/FOLDER ACTIONS ----------
def create_folder(path: str) -> str:
    try:
        os.makedirs(expand_path(path), exist_ok=True)
        return f"Created folder '{os.path.basename(path)}' sir."
    except Exception as e:
        return f"Failed: {e}"

def delete_folder(path: str) -> str:
    try:
        full = expand_path(path)
        if os.path.exists(full):
            shutil.rmtree(full)
            return f"Deleted folder '{os.path.basename(path)}' sir."
        return f"Folder not found sir."
    except Exception as e:
        return f"Failed: {e}"

def create_file(path: str) -> str:
    try:
        with open(expand_path(path), "w") as f:
            f.write("")
        return f"Created file '{os.path.basename(path)}' sir."
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
            return f"Deleted file '{os.path.basename(path)}' sir."
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

# ---------- COMMAND PARSER WITH LOCATION PHRASES ----------
async def execute_command(user_text: str) -> str:
    original = user_text
    text = re.sub(r"^(hey\s+)?jarvis[, ]*", "", user_text.lower().strip())

    if not text:
        return "Yes sir?"

    # Detect location phrase at the end (e.g., "in the desktop", "in downloads")
    location_match = re.search(r"\s+(in\s+(?:the\s+)?\w+)$", text)
    location = None
    item_name = text
    if location_match:
        location = location_match.group(1).strip()
        item_name = text[:location_match.start()].strip()

    # --- OPEN (navigate) with location ---
    if item_name.startswith("open "):
        target = item_name[5:].strip()  # remove "open "
        if location:
            full_path = resolve_location(target, location)
        else:
            full_path = expand_path(target)
        if os.path.exists(full_path):
            open_file_explorer(full_path)
            return f"Navigated to {target}, sir."
        else:
            return f"Path not found, sir."

    # --- CREATE FOLDER with location ---
    if item_name.startswith("create folder "):
        folder = item_name[14:].strip()
        if location:
            full_path = resolve_location(folder, location)
        else:
            full_path = expand_path(folder)
        return create_folder(full_path)

    # --- DELETE FOLDER with location ---
    if item_name.startswith("delete folder "):
        folder = item_name[14:].strip()
        if location:
            full_path = resolve_location(folder, location)
        else:
            full_path = expand_path(folder)
        return delete_folder(full_path)

    # --- CREATE FILE with location ---
    if item_name.startswith("create file "):
        filename = item_name[12:].strip()
        if location:
            full_path = resolve_location(filename, location)
        else:
            full_path = expand_path(filename)
        return create_file(full_path)

    # --- READ FILE with location ---
    if item_name.startswith("read file "):
        filename = item_name[10:].strip()
        if location:
            full_path = resolve_location(filename, location)
        else:
            full_path = expand_path(filename)
        return read_file(full_path)

    # --- DELETE FILE with location ---
    if item_name.startswith("delete file "):
        filename = item_name[12:].strip()
        if location:
            full_path = resolve_location(filename, location)
        else:
            full_path = expand_path(filename)
        return delete_file(full_path)

    # --- SEARCH FILES ---
    if item_name.startswith("search for "):
        keyword = item_name[11:].strip()
        return search_files(keyword)

    # --- SIMPLE OPEN COMMANDS (without location) ---
    if "open downloads" in text:
        open_file_explorer("~/Downloads")
        return "Navigated to Downloads, sir."
    if "open desktop" in text:
        open_file_explorer("~/Desktop")
        return "Navigated to Desktop, sir."
    if "open documents" in text:
        open_file_explorer("~/Documents")
        return "Navigated to Documents, sir."
    if "open file explorer" in text:
        open_file_explorer()
        return "Opening File Explorer, sir."

    # --- TIME & GREETINGS ---
    if "time" in text:
        return datetime.now().strftime("%I:%M %p")
    if "hello" in text or "hi" in text:
        return "Hello sir, how may I help you?"
        # --- INTELLIGENT FALLBACK FOR FILE EXPLORER ---
        try:
            # Ask AI to classify intent
            intent_check = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "If the user wants to open file explorer or browse files, reply ONLY with YES. Otherwise reply NO."
                    },
                    {"role": "user", "content": original}
                ],
               max_tokens=5
            )

            decision = intent_check.choices[0].message.content.strip().upper()

            if "YES" in decision:
                open_file_explorer()
                return "Opening File Explorer, sir."

        except Exception as e:
            log.error(f"Intent check failed: {e}")

    # --- AI FALLBACK ---
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are JARVIS. Be brief (1-2 sentences). Address user as 'sir' (lowercase)."},
                {"role": "user", "content": original}
            ],
            max_tokens=100
        )
        return res.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "System error, sir."

# ---------- API ----------
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
