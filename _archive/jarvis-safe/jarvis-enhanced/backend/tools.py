import os
import subprocess
import webbrowser
import requests
import shlex
from pathlib import Path

def open_app(app_name: str) -> str:
    app_name = app_name.lower()
    if os.name == 'nt':
        cmd_map = {
            "chrome": "start chrome", "notepad": "notepad", "calculator": "calc",
            "explorer": "explorer", "cmd": "start cmd", "powershell": "start powershell",
            "vscode": "code", "spotify": "start spotify"
        }
        cmd = cmd_map.get(app_name, f"start {app_name}")
        os.system(cmd)
    else:
        subprocess.Popen([app_name])
    return f"Opened {app_name}"

def open_youtube(url_or_query: str) -> str:
    if not url_or_query.startswith("http"):
        url = f"https://www.youtube.com/results?search_query={url_or_query.replace(' ', '+')}"
    else:
        url = url_or_query
    webbrowser.open(url)
    return f"YouTube opened: {url}"

def get_best_youtube_video(query: str) -> str:
    try:
        resp = requests.get(
            "https://invidious.fdn.fr/api/v1/search",
            params={"q": query, "type": "video", "sort": "relevance"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return f"https://www.youtube.com/watch?v={data[0]['videoId']}"
    except Exception:
        pass
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

def play_music(target: str) -> str:
    """Control music via system media keys (Windows only)."""
    target = target.lower()
    if os.name == 'nt':
        import ctypes
        VK_MEDIA_PLAY_PAUSE = 0xB3
        VK_MEDIA_NEXT_TRACK = 0xB0
        VK_MEDIA_PREV_TRACK = 0xB1
        if target in ["play", "pause", "play/pause"]:
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
            return "Toggled play/pause"
        elif target == "next":
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
            return "Next track"
        elif target == "previous":
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return "Previous track"
    return f"Music control: {target} (not fully supported on this OS)"

def navigate_folder(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        if os.name == 'nt':
            os.startfile(expanded)
        else:
            subprocess.Popen(['open', expanded])
        return f"Opened folder: {expanded}"
    return f"Path not found: {expanded}"

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

def rename_file(old: str, new: str) -> str:
    old_exp = os.path.expanduser(old)
    new_exp = os.path.expanduser(new)
    if os.path.exists(old_exp):
        os.rename(old_exp, new_exp)
        return f"Renamed {old} to {new}"
    return f"File not found: {old}"

def run_terminal_command(command: str, working_dir: str = None) -> str:
    """Safely execute a terminal command with timeout."""
    import shlex
    try:
        # Block dangerous commands
        dangerous = ["rm -rf /", "format", "del /f", "rd /s", "shutdown", "restart"]
        cmd_lower = command.lower()
        if any(d in cmd_lower for d in dangerous):
            return "Command blocked for safety."
        cwd = os.path.expanduser(working_dir) if working_dir else None
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd
        )
        output = result.stdout[:500] if result.stdout else result.stderr[:500]
        return output if output else "Command executed (no output)."
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error: {str(e)}"
