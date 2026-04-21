import win32com.client
import pygetwindow as gw
import pyautogui
import time
import asyncio
import json
import logging
import os
import webbrowser
import subprocess
import requests
from pathlib import Path
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

# ------------------------------------------------------------
# ACTION FUNCTIONS (Windows‑compatible)
# ------------------------------------------------------------
def open_app(app_name: str) -> str:
    """Open an application by name."""
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
    # Build the URL
    if query.startswith("http"):
        url = query
    else:
        try:
            resp = requests.get(
                "https://invidious.fdn.fr/api/v1/search",
                params={"q": query, "type": "video", "sort": "relevance"},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    url = f"https://www.youtube.com/watch?v={data[0]['videoId']}"
                else:
                    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            else:
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        except:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    # Try to find an existing Chrome window that is on YouTube
    try:
        chrome_windows = gw.getWindowsWithTitle("Chrome")
        yt_window = None
        for w in chrome_windows:
            if "YouTube" in w.title:
                yt_window = w
                break

        if yt_window:
            # Focus the existing YouTube tab
            if yt_window.isMinimized:
                yt_window.restore()
            yt_window.activate()
            time.sleep(0.2)

            # Select address bar and type new URL
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.1)
            pyautogui.write(url)
            pyautogui.press('enter')
            return f"Updated YouTube tab with: {query}"
        else:
            # No YouTube tab found – open a new one (won't replace JARVIS)
            webbrowser.open_new_tab(url)
            return f"Opened new YouTube tab: {query}"
    except Exception as e:
        log.warning(f"Failed to reuse YouTube tab: {e}")
        webbrowser.open_new_tab(url)
        return f"Opened YouTube in new tab: {query}"    
_explorer_window = None

def get_or_create_explorer():
    global _explorer_window
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        # Try to find an existing File Explorer window
        for w in shell.Windows():
            try:
                if w.Name == "File Explorer" and w.Visible:
                    _explorer_window = w
                    return w
            except:
                continue
        # If none exists, create a new one
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
            # Fallback to os.startfile (opens new window)
            os.startfile(expanded)
            return f"Opened folder: {expanded} (new window)"
    except Exception as e:
        # Fallback
        os.startfile(expanded)
        return f"Opened folder: {expanded}"


def create_file(path: str) -> str:
    """Create an empty file."""
    expanded = os.path.expanduser(path)
    Path(expanded).touch()
    return f"Created file: {expanded}"

def delete_file(path: str) -> str:
    """Delete a file."""
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        os.remove(expanded)
        return f"Deleted file: {expanded}"
    return f"File not found: {expanded}"

def read_file(path: str) -> str:
    """Read and return file content."""
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

# ------------------------------------------------------------
# SYSTEM PROMPT – Forces JSON with action
# ------------------------------------------------------------
SYSTEM_PROMPT = """You are JARVIS, a helpful AI assistant. You must respond ONLY with a valid JSON object containing an action.
Available actions:
- {"action": "open_app", "target": "app name"}  // e.g., "chrome", "notepad", "calculator"
- {"action": "open_youtube", "query": "search term or URL"}
- {"action": "navigate_folder", "path": "folder path"}  // e.g., "~/Downloads", "C:/Projects"
- {"action": "create_file", "path": "file path"}
- {"action": "delete_file", "path": "file path"}
- {"action": "read_file", "path": "file path"}
- {"action": "chat", "message": "your response text"}

Examples:
User: "Open Chrome" → {"action": "open_app", "target": "chrome"}
User: "Play Never Gonna Give You Up on YouTube" → {"action": "open_youtube", "query": "Never Gonna Give You Up"}
User: "Open Downloads" → {"action": "navigate_folder", "path": "~/Downloads"}
User: "Create a file called test.txt on Desktop" → {"action": "create_file", "path": "~/Desktop/test.txt"}
User: "What time is it?" → {"action": "chat", "message": "It's 3:45 PM, sir."}

Output only the JSON object, no extra text."""

# ------------------------------------------------------------
# WEBSOCKET ENDPOINT
# ------------------------------------------------------------
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

            # Execute the action
            action = ai_response.get("action", "chat")
            response_text = ""
            try:
                if action == "open_app":
                    response_text = open_app(ai_response.get("target", ""))
                elif action == "open_youtube":
                    response_text = open_youtube(ai_response.get("query", ""))
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
                else:  # chat
                    response_text = ai_response.get("message", "Yes sir?")
            except Exception as e:
                log.error(f"Action execution error: {e}")
                response_text = f"Action failed: {str(e)}"

            log.info(f"JARVIS: {response_text}")
            await websocket.send_json({
                "type": "audio",
                "text": response_text
            })
            await websocket.send_json({"type": "status", "state": "idle"})

    except Exception as e:
        log.error(f"WebSocket error: {e}")

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
