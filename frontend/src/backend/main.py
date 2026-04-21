import os
import json
import logging
import asyncio
import webbrowser
import subprocess
import requests
import time
import pyautogui
import pyperclip
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env file")
groq = Groq(api_key=GROQ_API_KEY)

# -------------------------------------------------------------------
# WINDOWS ACTION FUNCTIONS
# -------------------------------------------------------------------
def open_app(app_name: str) -> str:
    app_name = app_name.lower()
    if "chrome" in app_name:
        os.system("start chrome")
    elif "notepad" in app_name:
        os.system("notepad")
    elif "calculator" in app_name:
        os.system("calc")
    elif "explorer" in app_name or "file explorer" in app_name:
        os.system("explorer")
    elif "cmd" in app_name or "terminal" in app_name:
        os.system("start cmd")
    elif "powershell" in app_name:
        os.system("start powershell")
    elif "whatsapp" in app_name:
        # Try to open WhatsApp desktop or web
        whatsapp_path = os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe")
        if os.path.exists(whatsapp_path):
            os.startfile(whatsapp_path)
        else:
            webbrowser.open("https://web.whatsapp.com")
    elif "spotify" in app_name:
        os.system("start spotify")
    elif "apple music" in app_name or "music" in app_name:
        # Open Windows Media Player or Spotify as fallback
        os.system("start wmplayer")
    else:
        os.system(f"start {app_name}")
    return f"Opened {app_name}"

def navigate_folder(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        os.startfile(expanded)
        return f"Opened folder: {expanded}"
    return f"Path not found: {expanded}"

def open_youtube(query: str) -> str:
    """Open YouTube and play the best matching video."""
    if not query:
        webbrowser.open("https://youtube.com")
        return "Opened YouTube"
    # Try Invidious API to get first video
    try:
        resp = requests.get(
            "https://invidious.fdn.fr/api/v1/search",
            params={"q": query, "type": "video", "sort": "relevance"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                video_id = data[0]["videoId"]
                webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")
                return f"Playing '{query}' on YouTube"
    except Exception:
        pass
    # Fallback to search
    webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
    return f"Searching YouTube for '{query}'"

def send_whatsapp_message(contact: str, message: str) -> str:
    """Open WhatsApp Web and send a message using pyautogui."""
    webbrowser.open("https://web.whatsapp.com")
    time.sleep(8)  # Wait for page load
    # Search for contact
    pyautogui.click(200, 200)  # Click search box (adjust as needed)
    pyautogui.write(contact)
    time.sleep(2)
    pyautogui.press("enter")
    time.sleep(1)
    # Type message
    pyautogui.write(message)
    pyautogui.press("enter")
    return f"Sent WhatsApp message to {contact}"

def open_website(url: str, login: bool = False) -> str:
    """Open website in Chrome, optionally attempt login."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"

def play_music(song: str) -> str:
    """Play music via Spotify or Windows Media Player."""
    # Try Spotify
    try:
        os.system(f'start spotify:search:{song}')
        time.sleep(2)
        pyautogui.press("enter")  # Play first result
        return f"Playing '{song}' on Spotify"
    except:
        # Fallback: search on YouTube Music
        webbrowser.open(f"https://music.youtube.com/search?q={song.replace(' ', '+')}")
        return f"Searching for '{song}' on YouTube Music"

def read_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def create_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    Path(expanded).touch()
    return f"Created file: {expanded}"

def delete_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        os.remove(expanded)
        return f"Deleted file: {expanded}"
    return "File not found"

# -------------------------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------------------------
SYSTEM_PROMPT = """You are JARVIS, an AI assistant for Windows. Respond ONLY with JSON.
Available actions:
- open_app: {"action": "open_app", "target": "app name"} // chrome, notepad, whatsapp, explorer, etc.
- navigate_folder: {"action": "navigate_folder", "path": "folder path"}
- open_youtube: {"action": "open_youtube", "query": "search term"}
- send_whatsapp: {"action": "send_whatsapp", "contact": "contact name", "message": "text"}
- open_website: {"action": "open_website", "url": "website.com"}
- play_music: {"action": "play_music", "song": "song name"}
- read_file: {"action": "read_file", "path": "file path"}
- create_file: {"action": "create_file", "path": "file path"}
- delete_file: {"action": "delete_file", "path": "file path"}
- chat: {"action": "chat", "message": "response"}

Examples:
"open downloads" -> {"action": "navigate_folder", "path": "~/Downloads"}
"play despacito" -> {"action": "play_music", "song": "despacito"}
"send hello to mom on whatsapp" -> {"action": "send_whatsapp", "contact": "Mom", "message": "hello"}
Output ONLY the JSON object."""

# -------------------------------------------------------------------
# WEBSOCKET
# -------------------------------------------------------------------
@app.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") != "transcript" or not msg.get("isFinal"):
                continue
            user_text = msg.get("text", "").strip()
            if not user_text:
                continue
            log.info(f"User: {user_text}")

            await websocket.send_json({"type": "status", "state": "thinking"})

            # Call Groq
            try:
                completion = groq.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ],
                    temperature=0.3,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                ai_response = json.loads(completion.choices[0].message.content)
            except Exception as e:
                log.error(f"Groq error: {e}")
                ai_response = {"action": "chat", "message": "I'm having trouble, sir."}

            # Execute action
            action = ai_response.get("action", "chat")
            response_text = ""
            try:
                if action == "open_app":
                    response_text = open_app(ai_response.get("target", ""))
                elif action == "navigate_folder":
                    response_text = navigate_folder(ai_response.get("path", ""))
                elif action == "open_youtube":
                    response_text = open_youtube(ai_response.get("query", ""))
                elif action == "send_whatsapp":
                    response_text = send_whatsapp_message(
                        ai_response.get("contact", ""),
                        ai_response.get("message", "")
                    )
                elif action == "open_website":
                    response_text = open_website(ai_response.get("url", ""))
                elif action == "play_music":
                    response_text = play_music(ai_response.get("song", ""))
                elif action == "read_file":
                    content = read_file(ai_response.get("path", ""))
                    await websocket.send_json({"type": "file_content", "path": ai_response.get("path"), "content": content})
                    response_text = f"Read file {ai_response.get('path')}"
                elif action == "create_file":
                    response_text = create_file(ai_response.get("path", ""))
                elif action == "delete_file":
                    response_text = delete_file(ai_response.get("path", ""))
                else:
                    response_text = ai_response.get("message", "Yes sir?")
            except Exception as e:
                log.error(f"Action error: {e}")
                response_text = f"Action failed: {str(e)}"

            log.info(f"JARVIS: {response_text}")
            await websocket.send_json({"type": "audio", "text": response_text})
            await websocket.send_json({"type": "status", "state": "idle"})
    except WebSocketDisconnect:
        log.info("WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
