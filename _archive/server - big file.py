# server.py — JARVIS Mark III
# ══════════════════════════════════════════════════════════════════════════════
load_dotenv()
# ══════════════════════════════════════════════════════════════════════════════
# CRITICAL: Kill any existing Chrome with remote debugging on startup
# MARK IV MODULE IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
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
# ══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════════════════════
last_user_message = ""
last_response = ""
last_speech_time = 0.0
# ══════════════════════════════════════════════════════════════════════════════
# SCREEN & CAMERA AWARENESS
                print("[CAMERA] Stream closed")
            time.sleep(1)
# Awareness engine message queue (thread-safe)
import queue
awareness_queue = queue.Queue()
def awareness_speak(text: str):
    """Callback for awareness engine to push messages to WebSocket."""
    awareness_queue.put(text)
# ── CODE MONITOR ──
code_monitor = start_monitoring(awareness_speak)
# ── CONSOLE ERROR TRACKER ──
class ErrorTrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.is_reporting = False
    def write(self, data):
        try:
            self.original_stream.write(data)
        except UnicodeEncodeError:
            self.original_stream.write(data.encode('ascii', 'replace').decode('ascii'))
        # Prevent recursive reporting if awareness_speak itself fails
        if not self.is_reporting:
            self.is_reporting = True
            try:
                low_data = data.lower()
                if "error" in low_data or "traceback" in low_data or "exception" in low_data:
                    if len(data.strip()) > 15:
                        awareness_speak(f"Sir, I've detected a system error: {data.strip()[:120]}")
            except:
                pass
            finally:
                self.is_reporting = False
    def flush(self):
        self.original_stream.flush()
sys.stderr = ErrorTrapper(sys.stderr)
def awareness_generate(prompt: str) -> str:
    """Callback for awareness engine to generate AI comments via Groq."""
    try:
        resp = groq_client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=60,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""
def start_watchers():
    global _screen_thread_started, _camera_thread_started
    if not _screen_thread_started:
        _screen_thread_started = True
        threading.Thread(target=_screen_watcher_loop, daemon=True).start()
        print("[SCREEN] Background watcher started (every 10s)")
    if not _camera_thread_started:
        _camera_thread_started = True
        threading.Thread(target=_camera_watcher_loop, daemon=True).start()
        print("[CAMERA] Background watcher started")
        
    # Start WhatsApp auto-reply agent in the background
    try:
        subprocess.Popen(["python", "whatsapp_agent.py"], creationflags=0x08000000)
        print("[WHATSAPP] Background auto-reply agent started")
    except Exception as e:
        print(f"[WHATSAPP] Failed to start agent: {e}")
    # Start WhatsApp via agent manager
    agent_manager.start_agent("whatsapp")
    print("[BOOT] Agent manager initialized")
# ══════════════════════════════════════════════════════════════════════════════
# TASK-BASED COMMANDS (multi-action)
# ══════════════════════════════════════════════════════════════════════════════
TASK_COMMANDS = {
    "start my setup": ["chrome", "notepad", "explorer"],
    "start work": ["chrome", "vscode", "spotify"],
    "start coding": ["vscode", "cmd"],
    "start gaming": ["steam", "discord"],
    "start editing": ["premiere", "spotify"],
    "prepare my workspace": ["vscode", "chrome", "cmd"],
    "start streaming": ["obs64", "discord", "chrome"],
    "wind down": ["spotify"],
    "close everything": [],  # special
}
    Play YouTube video with:
    - Native browser tab replacement (no IFrames, preventing Vevo blocks)
    - Autoplay enabled
    - Prevents opening multiple YouTube tabs
    """
    if not query:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube homepage."
        url = "https://www.youtube.com"
        msg = "Opening YouTube homepage."
    elif query.startswith("http") and "youtube.com" in query:
        url = query
        if "autoplay=1" not in url:
            connector = "&" if "?" in url else "?"
            url += f"{connector}autoplay=1"
        msg = "Playing the requested video."
    else:
        print(f"[YOUTUBE] 🔍 Searching for: {query}")
        video_id = get_youtube_video_id_fast(query)
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
            msg = f"Playing '{query}'."
        else:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            msg = f"Showing YouTube results for '{query}'."
    
    print(f"[YOUTUBE] 🔍 Searching for: {query}")
    video_id = get_youtube_video_id_fast(query)
    # Smart Upgrade: Detect if user explicitly wants a new tab
    is_new_tab_requested = new_tab or (query and "new tab" in query.lower())
    
    if not video_id:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        print(f"[YOUTUBE] ⚠️ Fallback to search: {url}")
        webbrowser.open(url)
        return f"Showing YouTube results for '{query}'."
    url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
    
    def execute_youtube_automation():
    def execute_youtube_automation(target_url):
        import time
        import pyautogui
        import pygetwindow as gw
        import pyperclip
        
        try:
            if new_tab:
                raise Exception("Force new tab")
                
            # Find an existing YouTube tab by checking window titles
            yt_windows = [w for w in gw.getAllWindows() if "YouTube" in w.title]
            # STEP 1: Find ANY browser window and specifically look for YouTube
            all_windows = gw.getAllWindows()
            yt_window = next((w for w in all_windows if "YouTube" in w.title), None)
            
            if not yt_windows:
                raise Exception("No YouTube window found")
                
            win = yt_windows[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.4)
            browsers = ["Google Chrome", "Chrome", "Microsoft Edge", "Firefox", "Brave"]
            browser_window = None
            for b in browsers:
                wins = [w for w in all_windows if b.lower() in w.title.lower()]
                if wins:
                    browser_window = wins[0]
                    break
            if yt_window:
                # Perfect match: YouTube is the active tab in some window
                if yt_window.isMinimized:
                    yt_window.restore()
                yt_window.activate()
                time.sleep(0.5)
            elif browser_window:
                # Browser is open but YouTube isn't the active tab
                if browser_window.isMinimized:
                    browser_window.restore()
                browser_window.activate()
                time.sleep(0.5)
                if not is_new_tab_requested:
                    # TRY TO FIND THE BACKGROUND YOUTUBE TAB (Chrome Specific)
                    if "chrome" in browser_window.title.lower():
                        # Use Chrome's 'Search Tabs' feature to find and jump to YouTube
                        pyautogui.hotkey('ctrl', 'shift', 'a')
                        time.sleep(0.4)
                        pyautogui.write("YouTube")
                        time.sleep(0.4)
                        pyautogui.press('enter')
                        time.sleep(0.6) # Give it time to switch
            
            # Select address bar
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.2)
            
            # Paste the new URL
            pyperclip.copy(url)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.1)
            pyautogui.press('enter')
            print(f"[YOUTUBE] ✅ Replaced current video tab with: {url}")
            
            # Wait for it to load and try to force play
            # Now we decide: open new tab or replace current
            active_win = gw.getActiveWindow()
            if not active_win or not any(b.lower() in active_win.title.lower() for b in browsers):
                # If we still aren't in a browser, open a new one
                import webbrowser
                webbrowser.open(target_url)
                print(f"[YOUTUBE] 🌐 Opened new browser: {target_url}")
            else:
                # We are in a browser!
                if is_new_tab_requested:
                    pyautogui.hotkey('ctrl', 't')
                    time.sleep(0.4)
                
                # Replace the URL
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.3)
                pyperclip.copy(target_url)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.2)
                pyautogui.press('enter')
                print(f"[YOUTUBE] 🔁 Reused/Found tab: {target_url}")
            # Force play
            time.sleep(3.5)
            pyautogui.press('k')
            
        except Exception as e:
            # Fallback to standard new tab behavior
            print(f"[YOUTUBE] ✅ Opening new tab: {url}")
            webbrowser.open(url)
            time.sleep(3.5)
            pyautogui.press('k')
            print(f"[YOUTUBE ERROR] {e}")
    import threading
    threading.Thread(target=execute_youtube_automation, daemon=True).start()
    return f"Playing '{query}'."
    threading.Thread(target=execute_youtube_automation, args=(url,), daemon=True).start()
    return msg
# ══════════════════════════════════════════════════════════════════════════════
# OTHER TOOLS
# ══════════════════════════════════════════════════════════════════════════════
def tool_open_website(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    
    # If it's a YouTube URL, use the tab-replacement logic
    if "youtube.com" in url.lower():
        return tool_play_youtube(url)
        
    webbrowser.open(url)
    return f"Opened {url}."
    "calculator": "calc",
}
from controller import is_app_running
def tool_open_app(app_name: str) -> str:
    key = app_name.lower().strip()
    cmd = APP_ALIASES.get(key, key)
    # Self-Healing: Check if already running first
    if is_app_running(key) or is_app_running(cmd):
        focus_result = focus_app(app_name)
        if "Switched to" in focus_result:
            return f"{app_name} was already running. I've brought it to the front. Consider asking the user what they want to do next."
    try:
        # URLs → open in default browser
        if cmd.startswith("http://") or cmd.startswith("https://"):
            webbrowser.open(cmd)
            return f"Opening {app_name}."
            return f"Opening {app_name}. Ready to search or browse?"
        # ms-settings and UWP URIs (e.g. "ms-settings:bluetooth", "microsoft.windows.camera:")
        # ms-settings and UWP URIs
        if cmd.startswith("ms-settings") or cmd.endswith(":"):
            subprocess.Popen(["cmd", "/c", "start", cmd], creationflags=0x08000000)
            return f"Opening {app_name}."
            return f"Opening {app_name}. Anything specific you'd like to do in settings?"
        # Regular apps
        subprocess.Popen(["cmd", "/c", "start", "", cmd], creationflags=0x08000000)
        return f"Opening {app_name}."
        return f"Opening {app_name}. What's the plan, sir?"
    except Exception as e:
        return f"Failed to open {app_name}: {e}"
        # Fallback error recovery
        return f"Failed to open {app_name}: {e}. Should I try searching for this app on the web or in your files?"
    
FOLDER_SHORTCUTS = {
    "downloads": "~/Downloads", "documents": "~/Documents",
    subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
    return f"Screenshot saved to Desktop."
def analyze_image_sync() -> str:
    """Synchronous Deep Vision analysis for the Awareness Engine thread."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or (not camera_active and not screen_watch_active):
        return ""
        
    try:
        import google.generativeai as genai
        import PIL.Image
        img_path = None
        if camera_active and latest_camera_frame and os.path.exists(latest_camera_frame):
            img_path = latest_camera_frame
        elif screen_watch_active and latest_screenshot and os.path.exists(latest_screenshot):
            img_path = latest_screenshot
            
        if img_path and os.path.exists(img_path):
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-flash-latest")
            img = PIL.Image.open(img_path)
            prompt = "Analyze this screen or camera view. Point out anything interesting, cluttered, or potentially erroneous (like a syntax error or cluttered timeline). Be concise (1-2 sentences). Do not narrate obvious things."
            response = model.generate_content([prompt, img])
            return response.text.strip()
    except Exception as e:
        print(f"[DEEP VISION ERROR] {e}")
    return ""
# ══════════════════════════════════════════════════════════════════════════════
# PRIORITY COMMAND ROUTER — executes BEFORE AI, feels instant
# ══════════════════════════════════════════════════════════════════════════════
def handle_fast_command(text: str, bypass_permissions: bool = False) -> str | None:
    """
    Pattern-match user text against known commands.
    Returns response string if handled, None if AI should take over.
    Uses strict startswith/regex — never loose substring matching.
    """
    global memory
    t = text.lower().strip()
    # --- PERMISSION SYSTEM GATE ---
    if not bypass_permissions:
        classification = permissions.classify_command(text)
        if classification in ("restricted", "dangerous"):
            # Create a pending action to confirm this exact text
            action = permissions.create_pending_action(
                command_text=text,
                execute_fn=None,  # Handled in WS loop by calling this again with bypass=True
            )
            return action.confirmation_message
    # Record for context engine
    context.record_exchange(text, "", "fast")
    # --- TIME & DATE ---
    if t in ("what time is it", "what's the time", "time please", "tell me the time"):
        now = datetime.now().strftime("%I:%M %p")
        screen_watch_active = True
        return "Screen monitoring active. I'll keep an eye on things."
    # --- DESKTOP CONTROL (New) ---
    if t.startswith("switch to ") or t.startswith("focus "):
        app = t.replace("switch to ", "").replace("focus ", "").strip()
        context.record_app(app)
        usage_learner.track_behavior(app) # Track behavioral usage
        return focus_app(app)
    if t.startswith("minimize "):
        return minimize_app(t.replace("minimize ", "").strip())
    if t.startswith("maximize "):
        return maximize_app(t.replace("maximize ", "").strip())
    if t.startswith("close "):
        return close_app(t.replace("close ", "").strip())
    if t in ("list windows", "what's open"):
        return list_windows()
        
    if t.startswith("type "):
        return type_text(text[5:])
    if t.startswith("copy "):
        return copy_text(text[5:])
    if t in ("clipboard", "what's in clipboard"):
        return get_clipboard()
        
    if t in ("system stats", "cpu", "ram", "battery", "system health", "how's my system"):
        return get_system_stats()
    if t in ("what's running", "top processes", "process list"):
        return get_running_processes()
    # --- AGENT MANAGER (New) ---
    if t in ("start whatsapp agent", "start whatsapp"):
        return agent_manager.start_agent("whatsapp")
    if t in ("stop whatsapp agent", "stop whatsapp", "stop agent"):
        return agent_manager.stop_agent("whatsapp")
    if t in ("agent status", "status of agents", "are agents running"):
        return agent_manager.list_agents()
    # --- AWARENESS ENGINE (New) ---
    if t in ("awareness on", "start observing", "observe me", "start awareness"):
        return awareness.start(speak_fn=awareness_speak, generate_fn=awareness_generate, analyze_image_fn=analyze_image_sync)
    if t in ("awareness off", "stop observing", "stop awareness"):
        return awareness.stop()
    # --- CONTEXT CONTINUATION ---
    if context.is_continuation(t):
        info = context.get_continuation_info()
        if not info:
            return "I'm not sure what you want me to continue."
        if info["type"] == "fast":
            return handle_fast_command(info["command"], bypass_permissions=True)
        elif info["tool"]:
            return dispatch_tool(info["tool"], info["args"])
    # Not a fast command -- let AI handle it
    return None
        return f"Search error: {e}"
def tool_save_memory(key: str, value: str) -> str:
    # Support profile updates via special keys
    if key.startswith("profile."):
        return profile.update(key.replace("profile.", ""), value)
        
    memory.setdefault("facts", [])
    for fact in memory["facts"]:
        if fact.get("key") == key:
# TOOL DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════
def dispatch_tool(name: str, args: dict, bypass_permissions: bool = False) -> str:
    try:
        # --- PERMISSION SYSTEM (Tool Gate) ---
        if not bypass_permissions:
            # Check for restricted tool-specific actions
            is_restricted = False
            command_desc = f"tool call: {name}"
            
            if name == "run_command":
                is_restricted = True
                command_desc = f"run command: {args.get('command')}"
            elif name == "computer_control" and args.get("action") in ("shutdown", "restart", "reboot", "format"):
                is_restricted = True
                command_desc = args.get("action")
            
            if is_restricted:
                action = permissions.create_pending_action(
                    command_text=command_desc,
                    execute_fn=lambda: dispatch_tool(name, args, bypass_permissions=True)
                )
                return f"CONFIRM_REQUIRED: {action.confirmation_message}"
        if name == "play_youtube":
            return tool_play_youtube(args.get("query", ""), args.get("new_tab", False))
            if name == "open_website":
        return tool_open_website(args.get("url","")), args.get("value", ""))
        if name == "get_memory":
            return tool_get_memory()
            
        # New Desktop Control Tools
        if name == "focus_app": return focus_app(args.get("app_name", ""))
        if name == "type_text": return type_text(args.get("text", ""))
        if name == "get_system_stats": return get_system_stats()
        if name == "list_windows": return list_windows()
        
        return f"Unknown tool: {name}"
    except Exception as e:
        traceback.print_exc()
# ══════════════════════════════════════════════════════════════════════════════
def build_system_prompt() -> str:
    now = datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")
    now = datetime.now()
    now_str = now.strftime("%A, %B %d, %Y - %I:%M %p")
    mem_str = tool_get_memory()
    user_name = memory.get("name", "") or os.getenv("USER_NAME", "")
    greeting = f"User's name: {user_name}" if user_name else "User has not told me their name yet."
    
    # User Profile (Mark IV)
    user_name = profile.name or os.getenv("USER_NAME", "")
    greeting = profile.get_greeting()
    profile_summary = profile.get_profile_summary()
    
    # Context Engine (Mark IV)
    history = context.get_history_for_prompt()
    recent_context = context.get_context_summary()
    context_block = ""
    if last_user_message:
        context_block = f"\nPREVIOUS EXCHANGE:\nUser said: {last_user_message}\nYou replied: {last_response}\n"
    # Learning & Intelligence (Phase 2)
    current_state = intelligence.user_state
    usual_apps = usage_learner.get_usual_apps(hour=now.hour)
    learning_str = f"- User is currently: {current_state.upper()}\n"
    if usual_apps:
        learning_str += f"- User usually opens these apps around this time: {', '.join(usual_apps)}\n"
    return f"""You are JARVIS — an advanced AI assistant inspired by Tony Stark's JARVIS.
    # Personality Layer (Mark IV)
    personality_prompt = personality.get_personality_prompt()
PERSONALITY:
- Confident, efficient, slightly witty
- British butler with dry humor — never robotic
- Speak naturally, like a real assistant
- Keep responses to 1-2 sentences MAX
- Address the user by name when appropriate
DATE & TIME: {now}
    return f"""You are JARVIS. You act as an intelligent, contextual digital presence.
{greeting}
MEMORY:
Current Time: {now_str}
{personality_prompt}
USER PROFILE:
{profile_summary}
{mem_str}
{context_block}
RULES:
- Be concise — short punchy responses, never ramble
- ALWAYS use tools to perform actions — never pretend or describe what you would do
- For YouTube requests: use play_youtube tool
- Save user info (name, preferences, city) with save_memory
- If unsure, ask — don't guess
- Never say "I'm just an AI" or apologize excessively
BEHAVIORAL LEARNING:
{learning_str}
CURRENT CONTEXT:
{recent_context}
{history}
IMPORTANT RULES:
- Never break character.
- Keep responses short, punchy, and confident (1-2 sentences).
- Do not say "How can I help you?".
- If they ask for something to be played or opened, use your tools. Do not just say you will.
- If they say "start editing" or "prepare my workspace", know that these are multi-step workflows handled automatically.
- If I provide [VISION SYSTEM] text, it means I am feeding you exactly what you are looking at. DO NOT try to use tools to take a screenshot or open the camera. Just answer naturally based on the vision text provided.
"""
    await websocket.accept()
    print("[WS] Connected")
    # Worker to send awareness messages to the client asynchronously
    async def awareness_worker():
        while True:
            try:
                if not awareness_queue.empty():
                    msg = awareness_queue.get_nowait()
                    global last_speech_time
                    last_speech_time = time.time()
                    await websocket.send_json({"type": "audio", "text": msg})
                    await websocket.send_json({"type": "status", "state": "idle"})
                await asyncio.sleep(0.5)
            except Exception:
                break
                
    awareness_task = asyncio.create_task(awareness_worker())
    try:
        while True:
            try:
                raw = await websocket.receive_text()
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            except Exception:
                break
            if data.get("type") != "transcript" or not data.get("isFinal"):
            msg_type = data.get("type")
            
            if msg_type == "frontend_error":
                err_text = data.get("text", "Unknown frontend error")
                print(f"[FRONTEND ERROR] {err_text}")
                # We alert the user, but only for distinct errors to avoid spam
                awareness_speak(f"Sir, the frontend reported an error: {err_text[:100]}")
                continue
            if msg_type != "transcript" or not data.get("isFinal"):
                continue
            text = data.get("text", "").strip()
            if not text:
                continue
            # ── WAKE WORD: strip "jarvis" prefix for instant processing ──
            t_lower = text.lower().strip()
            if t_lower.startswith("jarvis "):
                text = text[7:].strip()
            elif t_lower == "jarvis":
                await websocket.send_json({"type": "audio", "text": "At your service."})
                await websocket.send_json({"type": "status", "state": "idle"})
            # Echo cancellation: Ignore transcripts if we just spoke
            if time.time() - last_speech_time < 2.0:
                print(f"[ECHO] Ignored: {text}")
                continue
            if not text:
                continue
            print(f"[USER] {text}")
            
            # Intelligence: Update user state and track behavior
            intelligence.detect_user_state()
            # Try to infer app name from current window for learning
            usage_learner.track_behavior(get_active_window_title().split("-")[-1].strip())
            # ── PERMISSION CONFIRMATION FLOW ──
            if permissions.has_pending():
                t_lower = text.lower().strip()
                if t_lower in ("yes", "yeah", "yep", "do it", "proceed", "go ahead"):
                    action = permissions.confirm_action()
                    if action:
                        if action.execute_fn:
                            response_text = action.execute_fn(**action.execute_args)
                        else:
                            # Re-run it bypassing permission check
                            response_text = handle_fast_command(action.command_text, bypass_permissions=True)
                            if not response_text:
                                response_text = await run_agent(action.command_text, vision_context="")
                        print(f"[FAST] Confirmed: {response_text}")
                        last_speech_time = time.time()
                        await websocket.send_json({"type": "audio", "text": str(response_text)})
                        await websocket.send_json({"type": "status", "state": "idle"})
                        continue
                elif t_lower in ("no", "nope", "cancel", "stop", "don't"):
                    permissions.deny_action()
                    response_text = "Action cancelled, sir."
                    await websocket.send_json({"type": "audio", "text": response_text})
                    await websocket.send_json({"type": "status", "state": "idle"})
                    continue
                else:
                    await websocket.send_json({"type": "audio", "text": "I need a yes or no to proceed, sir."})
                    await websocket.send_json({"type": "status", "state": "idle"})
                    continue
            # ── PRIORITY: try fast command router FIRST ──
            response_text = handle_fast_command(text)





