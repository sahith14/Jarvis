# -------------------- FIXED FAST COMMANDS --------------------
def handle_fast_command(text):
    t = text.lower().strip()

    if t in ("what time is it","time"):
        return datetime.now().strftime("It's %I:%M %p")

    # ? HANDLE YOUTUBE FIRST (CRITICAL FIX)
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


# -------------------- FIXED YOUTUBE TOOL --------------------
def tool_play_youtube(query):
    if not query:
        url = "https://www.youtube.com"
    else:
        import urllib.parse
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    import subprocess
    subprocess.Popen(["cmd", "/c", "start", "chrome", url])

    return f"Opening YouTube {('with ' + query) if query else ''}"
