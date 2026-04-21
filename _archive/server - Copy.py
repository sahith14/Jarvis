# server.py — JARVIS Unified (Windows + Groq + All Features)
import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq

# -------------------- Load environment --------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in .env file")

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("jarvis")

# -------------------- FastAPI --------------------
app = FastAPI(title="JARVIS Unified")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Groq Client --------------------
groq_client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

# -------------------- Windows Controller Imports --------------------
try:
    from controller import (
        focus_app, minimize_app, maximize_app, close_app, list_windows,
        get_active_window_title, copy_text, get_clipboard, type_text,
        press_key, hotkey, get_system_stats, get_running_processes,
        is_cpu_high, is_ram_high,
    )
except ImportError:
    log.warning("controller.py not found – window control disabled")
    # Provide stubs
    def focus_app(n): return "Controller missing"
    def minimize_app(n): return "Controller missing"
    def maximize_app(n): return "Controller missing"
    def close_app(n): return "Controller missing"
    def list_windows(): return "Controller missing"
    def get_active_window_title(): return "unknown"
    def copy_text(t): return "Controller missing"
    def get_clipboard(): return "Controller missing"
    def type_text(t): return "Controller missing"
    def press_key(k): return "Controller missing"
    def hotkey(*k): return "Controller missing"
    def get_system_stats(): return "Controller missing"
    def get_running_processes(): return "Controller missing"
    def is_cpu_high(): return False
    def is_ram_high(): return False

# -------------------- Awareness & Intelligence --------------------
try:
    from awareness import awareness
    from intelligence import intelligence
    from learning import UsageLearner
    usage_learner = UsageLearner()
except ImportError:
    log.warning("Awareness modules missing – running in reduced mode")
    class DummyAwareness:
        def start(self, *a, **k): return "Awareness unavailable"
        def stop(self): pass
    awareness = DummyAwareness()
    class DummyIntelligence:
        def detect_user_state(self): return "idle"
        def should_suppress(self, p): return False
    intelligence = DummyIntelligence()
    class DummyLearner:
        def track_behavior(self, a): pass
        def get_usual_apps(self, h=None): return []
    usage_learner = DummyLearner()

# -------------------- Agent Manager & Code Monitor --------------------
try:
    from agent_manager import agent_manager
except ImportError:
    class DummyAgentManager:
        def start_agent(self, n): return "Agent manager missing"
        def stop_agent(self, n): return "Agent manager missing"
        def list_agents(self): return "No agents"
    agent_manager = DummyAgentManager()

try:
    from code_monitor import start_monitoring
except ImportError:
    def start_monitoring(cb): return None

# -------------------- Permission System --------------------
try:
    from permission_system import permissions
except ImportError:
    class DummyPermissions:
        def classify_command(self, t): return "safe"
        def has_pending(self): return False
        def create_pending_action(self, *a, **k): return None
    permissions = DummyPermissions()

# -------------------- User Profile & Context --------------------
try:
    from user_profile import profile, context, personality
except ImportError:
    class DummyProfile:
        name = ""
        def get_greeting(self): return "Hello."
        def get_profile_summary(self): return ""
    profile = DummyProfile()
    class DummyContext:
        def record_exchange(self, u, r, t="ai"): pass
        def get_history_for_prompt(self): return ""
        def get_context_summary(self): return ""
    context = DummyContext()
    class DummyPersonality:
        def get_personality_prompt(self): return "Be concise."
    personality = DummyPersonality()

# -------------------- Memory (JSON) --------------------
MEMORY_FILE = Path("memory.json")
def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"name": "", "facts": [], "notes": []}

def save_memory(mem):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, indent=2)

memory = load_memory()

# -------------------- Screen & Camera Monitoring --------------------
SCREEN_DIR = Path("screen_captures")
SCREEN_DIR.mkdir(exist_ok=True)
screen_watch_active = True
camera_active = False
latest_screenshot = None
latest_camera_frame = None

def capture_screen_silent():
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(SCREEN_DIR / f"screen_{ts}.png")
        ps = (
            f"Add-Type -AssemblyName System.Windows.Forms;"
            f"$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
            f"$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;"
            f"$g=[System.Drawing.Graphics]::FromImage($bmp);"
            f"$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);"
            f"$bmp.Save('{path}');"
        )
        subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=5, creationflags=0x08000000)
        # keep only last 5
        caps = sorted(SCREEN_DIR.glob("screen_*.png"))
        for old in caps[:-5]:
            old.unlink(missing_ok=True)
        return path
    except:
        return None

def _screen_watcher_loop():
    global latest_screenshot
    while True:
        if screen_watch_active:
            path = capture_screen_silent()
            if path:
                latest_screenshot = path
        time.sleep(10)

def _camera_watcher_loop():
    global latest_camera_frame
    cap = None
    try:
        import cv2
    except ImportError:
        return
    while True:
        if camera_active:
            if cap is None:
                cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                path = str(SCREEN_DIR / "camera_latest.png")
                cv2.imwrite(path, frame)
                latest_camera_frame = path
            time.sleep(0.5)
        else:
            if cap is not None:
                cap.release()
                cap = None
            time.sleep(1)

threading.Thread(target=_screen_watcher_loop, daemon=True).start()
threading.Thread(target=_camera_watcher_loop, daemon=True).start()

# -------------------- Awareness Queue --------------------
import queue
awareness_queue = queue.Queue()
def awareness_speak(text):
    awareness_queue.put(text)

# Start code monitor (reports errors via awareness_speak)
code_monitor = start_monitoring(awareness_speak)

# -------------------- YouTube Direct Play --------------------
def get_youtube_video_id_fast(query):
    for base in ["https://invidious.fdn.fr", "https://inv.nadeko.net", "https://invidious.privacydev.net"]:
        try:
            r = requests.get(f"{base}/api/v1/search", params={"q": query, "type": "video"}, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if data and isinstance(data, list) and len(data) > 0:
                    vid = data[0].get("videoId")
                    if vid:
                        return vid
        except:
            continue
    return None

def tool_play_youtube(query):
    if not query:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
    vid = get_youtube_video_id_fast(query)
    url = f"https://www.youtube.com/watch?v={vid}&autoplay=1" if vid else f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Playing '{query}'" if vid else f"Showing YouTube results for '{query}'"

# -------------------- App & Folder Tools --------------------
APP_ALIASES = {
    "chrome": "chrome", "notepad": "notepad", "calculator": "calc", "cmd": "cmd",
    "explorer": "explorer", "spotify": "spotify", "vscode": "code", "settings": "ms-settings:"
}
FOLDER_SHORTCUTS = {"downloads": "~/Downloads", "desktop": "~/Desktop", "documents": "~/Documents"}

def tool_open_app(name):
    cmd = APP_ALIASES.get(name.lower(), name)
    os.system(f'start "" "{cmd}"')
    return f"Opening {name}"

def tool_open_folder(path):
    p = os.path.expanduser(FOLDER_SHORTCUTS.get(path.lower(), path))
    os.startfile(p)
    return f"Opened {p}"

# -------------------- Fast Command Router --------------------
def handle_fast_command(text):
    t = text.lower().strip()
    if t in ("what time is it", "time"):
        return datetime.now().strftime("It's %I:%M %p")
    if t.startswith("play "):
        return tool_play_youtube(text[5:])
    if t.startswith("open ") and not t.startswith("open folder"):
        return tool_open_app(text[5:])
    if "downloads" in t and "open" in t:
        return tool_open_folder("downloads")
    # Memory
    if t.startswith("my name is "):
        name = text[11:].strip()
        memory["name"] = name
        save_memory(memory)
        return f"Got it, {name}."
    if t.startswith("remember "):
        note = text[9:].strip()
        memory.setdefault("notes", []).append(note)
        save_memory(memory)
        return "Saved."
    if t in ("what do you remember", "recall", "memory"):
        if not memory.get("name") and not memory.get("notes"):
            return "Nothing yet."
        parts = []
        if memory.get("name"):
            parts.append(f"Name: {memory['name']}")
        if memory.get("notes"):
            parts.append("Notes: " + ", ".join(memory["notes"][:5]))
        return " ".join(parts)
    return None

# -------------------- Tool Dispatch --------------------
def dispatch_tool(name, args):
    if name == "play_youtube":
        return tool_play_youtube(args.get("query", ""))
    if name == "open_app":
        return tool_open_app(args.get("app_name", ""))
    if name == "open_folder":
        return tool_open_folder(args.get("path", ""))
    if name == "focus_app":
        return focus_app(args.get("app_name", ""))
    if name == "get_system_stats":
        return get_system_stats()
    if name == "list_windows":
        return list_windows()
    return f"Unknown tool: {name}"

# -------------------- Groq Tool Definitions --------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "play_youtube",
            "description": "Play a YouTube video",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application",
            "parameters": {
                "type": "object",
                "properties": {"app_name": {"type": "string"}},
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_folder",
            "description": "Open a folder",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    },
]

# -------------------- AI Response Generator --------------------
def build_system_prompt():
    now = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")
    mem_str = json.dumps(memory)
    return f"""You are JARVIS. Date: {now}. Memory: {mem_str}. Be concise. Use tools when appropriate."""

async def run_agent(user_text):
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_text},
    ]
    for _ in range(2):
        resp = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.6,
            max_tokens=512,
        )
        msg = resp.choices[0].message
        if resp.choices[0].finish_reason != "tool_calls" or not msg.tool_calls:
            return msg.content or "Done."
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in msg.tool_calls
            ]
        })
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = dispatch_tool(tc.function.name, args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return "Done."

# -------------------- WebSocket Handler --------------------
@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket connected")

    # Awareness worker
    async def awareness_worker():
        while True:
            try:
                if not awareness_queue.empty():
                    msg = awareness_queue.get_nowait()
                    await websocket.send_json({"type": "audio", "text": msg})
                    await websocket.send_json({"type": "status", "state": "idle"})
                await asyncio.sleep(0.5)
            except:
                break
    awareness_task = asyncio.create_task(awareness_worker())

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

            # Permission confirmation flow
            if permissions.has_pending():
                tl = user_text.lower()
                if tl in ("yes", "yeah", "yep", "do it", "proceed"):
                    action = permissions.confirm_action()
                    if action and action.execute_fn:
                        resp = action.execute_fn(**action.execute_args)
                    else:
                        resp = handle_fast_command(action.command_text) or await run_agent(action.command_text)
                    await websocket.send_json({"type": "audio", "text": resp})
                    await websocket.send_json({"type": "status", "state": "idle"})
                    continue
                elif tl in ("no", "nope", "cancel"):
                    permissions.deny_action()
                    await websocket.send_json({"type": "audio", "text": "Cancelled."})
                    await websocket.send_json({"type": "status", "state": "idle"})
                    continue

            # Fast command first
            resp = handle_fast_command(user_text)
            if not resp:
                await websocket.send_json({"type": "status", "state": "thinking"})
                resp = await run_agent(user_text)
            await websocket.send_json({"type": "audio", "text": resp})
            await websocket.send_json({"type": "status", "state": "idle"})

    except WebSocketDisconnect:
        log.info("WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
    finally:
        awareness_task.cancel()

# -------------------- REST API --------------------
@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok", "model": MODEL})

# -------------------- Startup --------------------
def start_watchers():
    # Already started threads for screen/camera
    agent_manager.start_agent("whatsapp")
    awareness.start(speak_fn=awareness_speak, generate_fn=lambda p: groq_client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": p}], max_tokens=60
    ).choices[0].message.content)

if __name__ == "__main__":
    import uvicorn
    print("🚀 JARVIS Unified Server Starting...")
    start_watchers()
    uvicorn.run(app, host="127.0.0.1", port=8340)