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

# ========== HELPER ==========
def expand_path(path: str) -> str:
    """Convert relative or ~ paths to absolute"""
    return os.path.abspath(os.path.expanduser(path))

# ========== ACTUAL FILE/FOLDER ACTIONS ==========
def open_file_explorer(path: str = None) -> bool:
    try:
        if path:
            os.startfile(expand_path(path))
        else:
            os.startfile(expand_path("~"))
        return True
    except Exception as e:
        log.error(f"Explorer error: {e}")
        return False

def create_folder(path: str) -> str:
    try:
        full = expand_path(path)
        os.makedirs(full, exist_ok=True)
        return f"Created folder '{path}' sir."
    except Exception as e:
        return f"Failed: {str(e)}"

def delete_folder(path: str) -> str:
    try:
        full = expand_path(path)
        if os.path.exists(full):
            shutil.rmtree(full)
            return f"Deleted folder '{path}' sir."
        else:
            return f"Folder '{path}' not found sir."
    except Exception as e:
        return f"Failed: {str(e)}"

def rename_folder(old_path: str, new_path: str) -> str:
    try:
        old_full = expand_path(old_path)
        new_full = expand_path(new_path)
        os.rename(old_full, new_full)
        return f"Renamed '{old_path}' to '{new_path}' sir."
    except Exception as e:
        return f"Failed: {str(e)}"

def list_folder(path: str = ".") -> str:
    try:
        full = expand_path(path)
        items = os.listdir(full)
        folders = [i for i in items if os.path.isdir(os.path.join(full, i))]
        files = [i for i in items if os.path.isfile(os.path.join(full, i))]
        result = f"?? Folders ({len(folders)}): {', '.join(folders[:10])}"
        if len(folders) > 10:
            result += f" and {len(folders)-10} more"
        result += f"\n?? Files ({len(files)}): {', '.join(files[:10])}"
        if len(files) > 10:
            result += f" and {len(files)-10} more"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def create_file(path: str, content: str = "") -> str:
    try:
        full = expand_path(path)
        with open(full, 'w') as f:
            f.write(content)
        return f"Created file '{path}' sir."
    except Exception as e:
        return f"Failed: {str(e)}"

def read_file(path: str) -> str:
    try:
        full = expand_path(path)
        with open(full, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content) > 500:
            content = content[:500] + "... (truncated)"
        return f"?? {path}:\n{content}"
    except Exception as e:
        return f"Error: {str(e)}"

def delete_file(path: str) -> str:
    try:
        full = expand_path(path)
        if os.path.exists(full):
            os.remove(full)
            return f"Deleted file '{path}' sir."
        else:
            return f"File '{path}' not found sir."
    except Exception as e:
        return f"Failed: {str(e)}"

def search_files(keyword: str, root: str = ".") -> str:
    try:
        full_root = expand_path(root)
        matches = []
        for r, dirs, files in os.walk(full_root):
            for f in files:
                if keyword.lower() in f.lower():
                    matches.append(os.path.join(r, f))
                    if len(matches) >= 10:
                        break
            if len(matches) >= 10:
                break
        if matches:
            return "Found:\n" + "\n".join(matches)
        else:
            return f"No files found containing '{keyword}' sir."
    except Exception as e:
        return f"Search error: {str(e)}"

# ========== COMMAND PARSER (CATCHES EVERYTHING BEFORE AI) ==========
async def execute_command(user_text: str) -> str:
    text = user_text.lower().strip()
    # Remove leading "jarvis"
    if text.startswith("jarvis"):
        text = text[6:].strip()
    if not text:
        return "Yes sir?"

    # ----- EXPLORER -----
    if re.search(r'open\s+(?:my\s+)?files?|open\s+file\s+explorer', text):
        open_file_explorer()
        return "Opening File Explorer, sir."

    if re.search(r'open\s+downloads\s*folder?', text):
        open_file_explorer(expand_path("~/Downloads"))
        return "Opening Downloads folder, sir."

    if re.search(r'open\s+desktop\s*folder?', text):
        open_file_explorer(expand_path("~/Desktop"))
        return "Opening Desktop folder, sir."

    if re.search(r'open\s+documents\s*folder?', text):
        open_file_explorer(expand_path("~/Documents"))
        return "Opening Documents folder, sir."

    # open folder <name>
    m = re.search(r'open\s+(?:the\s+)?folder\s+([^\s]+(?:\s+[^\s]+)*)', text)
    if m:
        folder = m.group(1).strip()
        open_file_explorer(expand_path(folder))
        return f"Opening folder '{folder}', sir."

    # ----- CREATE FOLDER -----
    m = re.search(r'(?:create|make|new)\s+folder\s+(?:called\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return create_folder(m.group(1))

    # ----- DELETE FOLDER -----
    m = re.search(r'(?:delete|remove)\s+folder\s+(?:called\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return delete_folder(m.group(1))

    # ----- RENAME FOLDER -----
    m = re.search(r'rename\s+folder\s+(?:called\s+)?["\']?([^"\']+)["\']?\s+to\s+["\']?([^"\']+)["\']?', text)
    if m:
        return rename_folder(m.group(1), m.group(2))

    # ----- LIST CONTENTS -----
    m = re.search(r'(?:list|show)\s+(?:contents of|files in)\s+(?:folder\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return list_folder(m.group(1))
    if re.search(r'what\'s\s+in\s+(?:the\s+)?folder', text):
        m = re.search(r'what\'s\s+in\s+(?:the\s+)?folder\s+["\']?([^"\']+)["\']?', text)
        if m:
            return list_folder(m.group(1))
        else:
            return list_folder(".")

    # ----- CREATE FILE -----
    m = re.search(r'(?:create|make|new)\s+file\s+(?:called\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return create_file(m.group(1))

    # ----- READ FILE -----
    m = re.search(r'read\s+file\s+(?:called\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return read_file(m.group(1))

    # ----- DELETE FILE -----
    m = re.search(r'(?:delete|remove)\s+file\s+(?:called\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return delete_file(m.group(1))

    # ----- SEARCH FILES -----
    m = re.search(r'search\s+(?:for\s+)?["\']?([^"\']+)["\']?', text)
    if m:
        return search_files(m.group(1))

    # ----- SIMPLE COMMANDS -----
    if re.search(r'\b(?:hello|hi|hey)\b', text):
        return "Hello sir, how may I help you?"
    if re.search(r'\btime\b', text):
        return f"The time is {datetime.now().strftime('%I:%M %p')}, sir."

    # ----- DEFAULT: AI CONVERSATION (only if no file command matched) -----
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are JARVIS. Be brief (1-2 sentences). Address user as 'sir' (lowercase)."},
                {"role": "user", "content": user_text}
            ],
            max_tokens=100
        )
        return completion.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "I'm having trouble, sir. Please try again."

# ========== API ENDPOINTS ==========
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
