# -------------------- FIXED WATCHERS --------------------
def start_watchers():
    global _screen_thread_started
    if not _screen_thread_started:
        _screen_thread_started = True
        threading.Thread(target=_screen_watcher_loop, daemon=True).start()
        threading.Thread(target=_camera_watcher_loop, daemon=True).start()
    agent_manager.start_agent("whatsapp")
    awareness.start(awareness_speak, awareness_generate, analyze_image_sync)


# -------------------- FIXED FAST COMMANDS --------------------
def handle_fast_command(text):
    t = text.lower().strip()

    if t in ("what time is it","time"):
        return datetime.now().strftime("It's %I:%M %p")

    # ? YOUTUBE FIRST (CRITICAL FIX)
    if "youtube" in t:
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


# -------------------- FIXED YOUTUBE --------------------
def tool_play_youtube(query):
    if not query:
        url = "https://www.youtube.com"
    else:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    subprocess.Popen(["cmd", "/c", "start", "chrome", url])
    return f"Opening YouTube {('with ' + query) if query else ''}"
