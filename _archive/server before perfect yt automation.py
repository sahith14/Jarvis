# server.py – JARVIS with CDP Chrome control, Apple Music, Spotify, and file navigation
import asyncio
import json
import logging
import os
import webbrowser
import subprocess
import requests
import time
import urllib.parse
from pathlib import Path

# CDP / Windows imports
import win32com.client
import websocket

from fastapi import FastAPI, WebSocket
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
# Chrome DevTools Protocol (CDP) helpers – invisible, reliable tab control
# -------------------------------------------------------------------
CHROME_DEBUG_PORT = 9222
CHROME_USER_DATA_DIR = os.path.expanduser("~/.jarvis_chrome_profile")

def _launch_chrome_with_debug():
    """Launch a dedicated Chrome instance with remote debugging enabled."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    chrome_exe = None
    for p in chrome_paths:
        if os.path.exists(p):
            chrome_exe = p
            break
    if not chrome_exe:
        raise RuntimeError("Chrome not found")
    cmd = [
        chrome_exe,
        f"--remote-debugging-port={CHROME_DEBUG_PORT}",
        f"--user-data-dir={CHROME_USER_DATA_DIR}",
        "--new-window", "about:blank",
        "--start-minimized",
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)  # give Chrome time to start

def _get_cdp_tabs():
    """Return list of open tabs from Chrome debug endpoint."""
    try:
        resp = requests.get(f"http://localhost:{CHROME_DEBUG_PORT}/json", timeout=2)
        return resp.json()
    except Exception:
        return []

def _find_tab_by_url(url_pattern: str):
    tabs = _get_cdp_tabs()
    for tab in tabs:
        if tab.get("url") and url_pattern in tab["url"]:
            return tab
    return None

def _create_new_tab(url: str):
    """Create a new tab via CDP and navigate to URL."""
    try:
        # Get the first available page (any tab) to send the command
        tabs = _get_cdp_tabs()
        if not tabs:
            return None
        # Use the first tab's WebSocket to create a new target
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url, timeout=5)
        ws.send(json.dumps({
            "id": 1,
            "method": "Target.createTarget",
            "params": {"url": url}
        }))
        ws.close()
        return True
    except Exception as e:
        log.warning(f"CDP create tab failed: {e}")
        return False

def _navigate_tab(tab, url: str):
    """Navigate an existing tab to a new URL via CDP."""
    try:
        ws_url = tab["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url, timeout=5)
        ws.send(json.dumps({
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": url}
        }))
        ws.close()
        return True
    except Exception as e:
        log.warning(f"CDP navigate failed: {e}")
        return False

def _ensure_chrome_with_debug():
    """Ensure Chrome with debug port is running. Launch if not."""
    try:
        requests.get(f"http://localhost:{CHROME_DEBUG_PORT}/json", timeout=2)
    except Exception:
        _launch_chrome_with_debug()
        # Wait and retry
        for _ in range(5):
            time.sleep(1)
            try:
                requests.get(f"http://localhost:{CHROME_DEBUG_PORT}/json", timeout=2)
                break
            except:
                pass

# -------------------------------------------------------------------
# ACTION FUNCTIONS
# -------------------------------------------------------------------
def open_app(app_name: str) -> str:
    app_name = app_name.lower()
    if os.name == 'nt':
        cmd_map = {
            "chrome": "start chrome",
            "notepad": "notepad",
            "calculator": "calc",
            "explorer": "explorer",
            "cmd": "start cmd",
            "powershell": "start powershell",
            "vscode": "code",
            "spotify": "start spotify",
            "edge": "start msedge",
        }
        cmd = cmd_map.get(app_name, f"start {app_name}")
        os.system(cmd)
    else:
        subprocess.Popen([app_name])
    return f"Opened {app_name}"

def open_youtube(query: str) -> str:
    """Open YouTube and play the first video using CDP."""
    # Build video URL (use Invidious API to get first video)
    video_url = None
    try:
        resp = requests.get(
            "https://invidious.fdn.fr/api/v1/search",
            params={"q": query, "type": "video", "sort": "relevance"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                video_url = f"https://www.youtube.com/watch?v={data[0]['videoId']}"
    except Exception:
        pass
    if not video_url:
        video_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    # CDP magic
    try:
        _ensure_chrome_with_debug()
        yt_tab = _find_tab_by_url("youtube.com")
        if yt_tab:
            _navigate_tab(yt_tab, video_url)
            return f"Playing '{query}' on YouTube"
        else:
            _create_new_tab(video_url)
            return f"Opened YouTube with '{query}'"
    except Exception as e:
        log.error(f"CDP failed: {e}")
        # fallback
        webbrowser.open_new_tab(video_url)
        return f"YouTube opened (fallback): {query}"

def play_music(song: str, service: str = "youtube") -> str:
    """Play a song on the specified service."""
    service = service.lower()
    if service == "apple_music" or service == "apple music":
        # Apple Music URI scheme
        encoded = urllib.parse.quote(song)
        webbrowser.open(f"music://music.apple.com/search?term={encoded}")
        # Alternative: open Windows app via start
        os.system(f'start music:')
        time.sleep(1)
        # Use pyautogui to type search? For simplicity, we rely on URI
        return f"Searching Apple Music for '{song}'"
    elif service == "spotify":
        webbrowser.open(f"spotify:search:{urllib.parse.quote(song)}")
        return f"Searching Spotify for '{song}'"
    else:
        # Default to YouTube
        return open_youtube(song)

def open_website(url: str) -> str:
    """Open a website in the controlled Chrome window."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        _ensure_chrome_with_debug()
        _create_new_tab(url)
        return f"Opened {url}"
    except Exception:
        webbrowser.open_new_tab(url)
        return f"Opened {url} (fallback)"

# ----- Persistent Explorer (same as before) -----
_explorer_window = None
def get_or_create_explorer():
    global _explorer_window
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        for w in shell.Windows():
            try:
                if w.Name == "File Explorer" and w.Visible:
                    _explorer_window = w
                    return w
            except:
                continue
        _explorer_window = shell.Explore(os.path.expanduser("~"))
        return _explorer_window
    except Exception as e:
        log.error(f"Explorer COM error: {e}")
        return None

def navigate_folder(path: str) -> str:
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return f"Path not found: {expanded}"
    try:
        win = get_or_create_explorer()
        if win:
            win.Navigate(expanded)
            win.Visible = True
            return f"Navigated to {path}"
        else:
            os.startfile(expanded)
            return f"Opened folder: {expanded}"
    except Exception:
        os.startfile(expanded)
        return f"Opened folder: {expanded}"

def create_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    Path(expanded).touch()
    return f"Created file: {expanded}"

def delete_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        os.remove(expanded)
        return f"Deleted file: {expanded}"
    return f"File not found: {expanded}"

def read_file(path: str) -> str:
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

# -------------------------------------------------------------------
# UPDATED SYSTEM PROMPT with music service routing
# -------------------------------------------------------------------
SYSTEM_PROMPT = """You are JARVIS. Respond ONLY with JSON.
Actions:
- open_app: {"action": "open_app", "target": "app name"}
- open_youtube: {"action": "open_youtube", "query": "search or video"}
- play_music: {"action": "play_music", "song": "song name", "service": "youtube|spotify|apple_music"}
- navigate_folder: {"action": "navigate_folder", "path": "folder"}
- create_file: {"action": "create_file", "path": "file"}
- delete_file: {"action": "delete_file", "path": "file"}
- read_file: {"action": "read_file", "path": "file"}
- open_website: {"action": "open_website", "url": "domain.com"}
- chat: {"action": "chat", "message": "response"}

Music routing:
- "play Despacito" -> {"action": "open_youtube", "query": "Despacito"}
- "play Despacito on Apple Music" -> {"action": "play_music", "song": "Despacito", "service": "apple_music"}
- "play Despacito on Spotify" -> {"action": "play_music", "song": "Despacito", "service": "spotify"}

Output ONLY the JSON object."""

# -------------------------------------------------------------------
# WEBSOCKET
# -------------------------------------------------------------------
@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
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
                    max_tokens=250,
                    response_format={"type": "json_object"}
                )
                ai_response = json.loads(completion.choices[0].message.content)
            except Exception as e:
                log.error(f"Groq error: {e}")
                ai_response = {"action": "chat", "message": "I'm having trouble, sir."}

            action = ai_response.get("action", "chat")
            response_text = ""
            try:
                if action == "open_app":
                    response_text = open_app(ai_response.get("target", ""))
                elif action == "open_youtube":
                    response_text = open_youtube(ai_response.get("query", ""))
                elif action == "play_music":
                    response_text = play_music(
                        ai_response.get("song", ""),
                        ai_response.get("service", "youtube")
                    )
                elif action == "navigate_folder":
                    response_text = navigate_folder(ai_response.get("path", ""))
                elif action == "create_file":
                    response_text = create_file(ai_response.get("path", ""))
                elif action == "delete_file":
                    response_text = delete_file(ai_response.get("path", ""))
                elif action == "read_file":
                    content = read_file(ai_response.get("path", ""))
                    await websocket.send_json({
                        "type": "file_content",
                        "path": ai_response.get("path"),
                        "content": content
                    })
                    response_text = f"Read file {ai_response.get('path')}"
                elif action == "open_website":
                    response_text = open_website(ai_response.get("url", ""))
                else:
                    response_text = ai_response.get("message", "Yes sir?")
            except Exception as e:
                log.error(f"Action error: {e}")
                response_text = f"Action failed: {str(e)}"

            log.info(f"JARVIS: {response_text}")
            await websocket.send_json({"type": "audio", "text": response_text})
            await websocket.send_json({"type": "status", "state": "idle"})

    except Exception as e:
        log.error(f"WebSocket error: {e}")

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)