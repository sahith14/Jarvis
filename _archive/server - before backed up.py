# server.py � JARVIS Full Mark III + Direct YouTube + Screen Monitoring
import asyncio, json, os, subprocess, sys, threading, time, traceback, urllib.parse, webbrowser, queue
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq

# -------------------- MODULE IMPORTS --------------------
from permission_system import permissions
from controller import (
    focus_app, minimize_app, maximize_app, close_app, list_windows,
    get_active_window_title, copy_text, get_clipboard, type_text,
    press_key, hotkey, get_system_stats, get_running_processes,
    is_cpu_high, is_ram_high,
)
from user_profile import profile, context, personality
from agent_manager import agent_manager
from awareness import awareness
from intelligence import intelligence
from learning import UsageLearner
from code_monitor import start_monitoring

usage_learner = UsageLearner()

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# -------------------- MEMORY --------------------
MEMORY_FILE = Path("memory.json")
def load_memory(): return json.load(open(MEMORY_FILE)) if MEMORY_FILE.exists() else {"name":"","facts":[],"notes":[]}
def save_memory(m): json.dump(m, open(MEMORY_FILE,"w"), indent=2)
memory = load_memory()

# -------------------- SCREEN & CAMERA --------------------
SCREEN_DIR = Path("screen_captures")
SCREEN_DIR.mkdir(exist_ok=True)
screen_watch_active = True
camera_active = False
latest_screenshot = None
_screen_thread_started = False

def capture_screen_silent():
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(SCREEN_DIR / f"screen_{ts}.png")
        ps = f"Add-Type -AssemblyName System.Windows.Forms;$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;$g=[System.Drawing.Graphics]::FromImage($bmp);$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);$bmp.Save('{path}');"
        subprocess.run(["powershell","-Command",ps], capture_output=True, timeout=5, creationflags=0x08000000)
        caps = sorted(SCREEN_DIR.glob("screen_*.png"))
        for old in caps[:-5]: old.unlink(missing_ok=True)
        return path
    except: return None

def _screen_watcher_loop():
    global latest_screenshot
    while True:
        if screen_watch_active:
            path = capture_screen_silent()
            if path: latest_screenshot = path
        time.sleep(10)

latest_camera_frame = None
def _camera_watcher_loop():
    global latest_camera_frame
    cap = None
    try: import cv2
    except: return
    while True:
        if camera_active:
            if cap is None: cap = cv2.VideoCapture(0)
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

awareness_queue = queue.Queue()
def awareness_speak(text): awareness_queue.put(text)

code_monitor = start_monitoring(awareness_speak)

class ErrorTrapper:
    def __init__(self, orig): self.orig = orig; self.is_reporting = False
    def write(self, data):
        try: self.orig.write(data)
        except: pass
        if not self.is_reporting:
            self.is_reporting = True
            try:
                if len(data.strip()) > 10 and any(x in data.lower() for x in ["error","traceback","exception","failed"]):
                    awareness_speak(f"System error: {data[:120]}")
            finally: self.is_reporting = False
    def flush(self): self.orig.flush()
sys.stderr = ErrorTrapper(sys.stderr)

def awareness_generate(prompt):
    try:
        resp = groq_client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=0.8, max_tokens=60)
        return resp.choices[0].message.content.strip()
    except: return ""

def analyze_image_sync():
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or (not camera_active and not screen_watch_active): return ""
    try:
        import google.generativeai as genai
        import PIL.Image
        img_path = latest_camera_frame if camera_active and latest_camera_frame else (latest_screenshot if screen_watch_active else None)
        if img_path and os.path.exists(img_path):
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-flash-latest")
            img = PIL.Image.open(img_path)
            resp = model.generate_content(["Describe this briefly (1-2 sentences).", img])
            return resp.text.strip()
    except: pass
    return ""

# -------------------- YOUTUBE DIRECT PLAY --------------------
def get_youtube_video_id_fast(query):
    for base in ["https://invidious.fdn.fr","https://inv.nadeko.net","https://invidious.privacydev.net"]:
        try:
            r = requests.get(f"{base}/api/v1/search", params={"q":query,"type":"video"}, timeout=3)
            if r.status_code==200:
                data = r.json()
                if data and isinstance(data,list) and len(data)>0:
                    vid = data[0].get("videoId")
                    if vid: return vid
        except: continue
    return None

# -------------------- TOOLS --------------------
APP_ALIASES = {"chrome":"chrome","notepad":"notepad","calculator":"calc","cmd":"cmd","explorer":"explorer","spotify":"spotify","vscode":"code","settings":"ms-settings:"}
def tool_open_app(name):
    cmd = APP_ALIASES.get(name.lower(), name)
    subprocess.Popen(["cmd", "/c", "start", "", cmd])
    return f"Opening {name}"

FOLDER_SHORTCUTS = {"downloads":"~/Downloads","desktop":"~/Desktop","documents":"~/Documents"}
def tool_open_folder(path):
    p = os.path.expanduser(FOLDER_SHORTCUTS.get(path.lower(), path))
    os.startfile(p)
    return f"Opened {p}"

def dispatch_tool(name, args):
    if name=="open_app":
        app_name = args.get("app_name","").lower().strip()

        # 🔥 HARD BLOCK ANY youtube-related call
        if "youtube" in app_name:
         # extract query if exists
            query = app_name.replace("youtube","").replace("play","").strip()
            return tool_play_youtube(query)

        return tool_open_app(app_name)

TOOLS = [
    {"type":"function","function":{"name":"play_youtube","description":"Play YouTube video","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
    {"type":"function","function":{"name":"open_app","description":"Open app","parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}},
    {"type":"function","function":{"name":"open_folder","description":"Open folder","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
]

def build_system_prompt():
    now = datetime.now().strftime("%A, %B %d, %Y � %I:%M %p")
    return f"You are JARVIS. Date: {now}. Be concise. Use tools."

async def run_agent(text):
    msgs = [{"role":"system","content":build_system_prompt()},{"role":"user","content":text}]
    for _ in range(2):
        resp = groq_client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS, tool_choice="auto", temperature=0.6, max_tokens=512)
        msg = resp.choices[0].message
        if resp.choices[0].finish_reason != "tool_calls" or not msg.tool_calls:
            return msg.content or "Done."
        msgs.append({"role":"assistant","content":msg.content,"tool_calls":[{"id":tc.id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}} for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = safe_dispatch(tc.function.name, args)
            msgs.append({"role":"tool","tool_call_id":tc.id,"content":result})
    return "Done."

# -------------------- FIXED FAST COMMANDS --------------------
def handle_fast_command(text):
    t = text.lower().strip()

    if t in ("what time is it","time"):
        return datetime.now().strftime("It's %I:%M %p")

    # ? YOUTUBE FIRST (prevents fake app launch)
    if "youtube" in t:
        # 🔥 HARD STOP: NEVER let it go to open_app
        query = ""

        if "play" in t:
            query = text.lower().split("play",1)[-1].strip()
        else:
            # remove noise words
            query = text.lower().replace("open","").replace("youtube","").strip()

        return tool_play_youtube(query)
        query = ""
        if "play" in t:
            query = text.lower().split("play",1)[-1].strip()
        return dispatch_tool("play_youtube", {"query": query})

    if "play" in t:
        return dispatch_tool("play_youtube", {"query": text.replace("play","").strip()})

    if "open folder" in t:
        return dispatch_tool("open_folder", {"path": text.replace("open folder","").strip()})

    if "open" in t:
        return dispatch_tool("open_app", {"app_name": text.replace("open","").strip()})

    if "downloads" in t and "open" in t:
        return dispatch_tool("open_folder", {"path":"downloads"})

    return None

# -------------------- WEBSOCKET --------------------
@app.websocket("/ws/voice")
async def ws(websocket: WebSocket):
    await websocket.accept()
    async def awareness_worker():
        while True:
            try:
                if not awareness_queue.empty():
                    msg = awareness_queue.get_nowait()
                    await websocket.send_json({"type":"audio","text":msg})
                    await websocket.send_json({"type":"status","state":"idle"})
                await asyncio.sleep(0.5)
            except: break
    awareness_task = asyncio.create_task(awareness_worker())
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            if data.get("type")!="transcript" or not data.get("isFinal"): continue
            text = data.get("text","").strip()
            cmd_type = permissions.classify_command(text)
            if cmd_type in ("restricted","dangerous"):
                action = permissions.create_pending_action(text)
                await websocket.send_json({"type":"audio","text":action.confirmation_message})
                continue
            if not text: continue

            # Permission check
            if permissions.has_pending():
                tl = text.lower()
                if tl in ("yes","yeah","yep","do it","proceed"):
                    action = permissions.confirm_action()

                    if action and action.execute_fn:
                        resp = action.execute_fn(**action.execute_args)
                    else:
                        resp = handle_fast_command(action.command_text) or await run_agent(action.command_text)

                    is_speaking = True; last_speech_time = time.time()

                    await websocket.send_json({"type":"audio","text":resp})
                    await websocket.send_json({"type":"status","state":"speaking"})

                    # ✅ IMPORTANT: tell frontend speech finished
                    await websocket.send_json({"type":"done_speaking"})

                    is_speaking = False

                    await websocket.send_json({"type":"status","state":"idle"})
                    continue
                elif tl in ("no","nope","cancel"):
                    permissions.deny_action()

                    is_speaking = True; last_speech_time = time.time()

                    await websocket.send_json({"type":"audio","text":"Cancelled."})
                    await websocket.send_json({"type":"status","state":"speaking"})
                    await websocket.send_json({"type":"done_speaking"})

                    is_speaking = False

                    await websocket.send_json({"type":"status","state":"idle"})
                    continue
                
            # Fast command
            resp = handle_fast_command(text)
            if not resp:
                # removed thinking delay
                resp = await run_agent(enhance_context(text))
            await websocket.send_json({"type":"audio","text":resp})
            await websocket.send_json({"type":"status","state":"idle"})
    except: pass
    finally:
        awareness_task.cancel()

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status":"ok","model":MODEL})

# -------------------- WATCHERS --------------------
def start_watchers():
    global _screen_thread_started
    if not _screen_thread_started:
        _screen_thread_started = True
        threading.Thread(target=_screen_watcher_loop, daemon=True).start()
        threading.Thread(target=_camera_watcher_loop, daemon=True).start()

    agent_manager.start_agent("whatsapp")
    awareness.start(awareness_speak, awareness_generate, analyze_image_sync)

if __name__=="__main__":
    import uvicorn
    print("JARVIS Full System Starting...")
    start_watchers()
    uvicorn.run(app, host="127.0.0.1", port=8340)


# -------------------- FIXED YOUTUBE TOOL --------------------
def tool_play_youtube(query):
    if not query:
        url = "https://www.youtube.com"
    else:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    subprocess.Popen(["cmd", "/c", "start", "chrome", url])
    return f"Opening YouTube {('with ' + query) if query else ''}"




# -------------------- TOOL SAFETY GUARD --------------------
def safe_dispatch(name, args):
    name = name.lower()

    # ?? Block nonsense app launches
    if name == "open_app":
        app = args.get("app_name","").lower()

        if any(x in app for x in ["youtube", "google", "website"]):
            return tool_play_youtube(app.replace("youtube","").strip())

    return dispatch_tool(name, args)



# -------------------- SPEECH STATE --------------------
is_speaking = False
last_speech_time = 0


last_user_command = ""

def enhance_context(text):
    global last_user_command
    combined = f"{last_user_command} -> {text}"
    last_user_command = text
    return combined

