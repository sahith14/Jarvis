import os
import subprocess
import webbrowser
import requests
from pathlib import Path

def open_app(app_name: str) -> str:
    """Open an application by name (cross-platform)."""
    app_name = app_name.lower()
    if os.name == 'nt':  # Windows
        cmd_map = {
            "chrome": "start chrome",
            "notepad": "notepad",
            "calculator": "calc",
            "explorer": "explorer"
        }
        cmd = cmd_map.get(app_name, app_name)
        os.system(cmd)
    else:  # macOS/Linux
        subprocess.Popen([app_name])
    return f"Opened {app_name}"

def open_youtube(url_or_query: str) -> str:
    """Open YouTube in browser."""
    if not url_or_query.startswith("http"):
        url = f"https://www.youtube.com/results?search_query={url_or_query.replace(' ', '+')}"
    else:
        url = url_or_query
    webbrowser.open(url)
    return f"Opened YouTube: {url}"

def get_best_youtube_video(query: str) -> str:
    """Use Invidious API to get first video URL."""
    try:
        resp = requests.get(
            "https://invidious.fdn.fr/api/v1/search",
            params={"q": query, "type": "video", "sort": "relevance"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                video_id = data[0]['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        pass
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

def play_music(target: str) -> str:
    """Control music playback (placeholder)."""
    return f"Music control: {target} (not fully implemented)"

def navigate_folder(path: str) -> str:
    """Open file explorer at given path."""
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        if os.name == 'nt':
            os.startfile(expanded)
        else:
            subprocess.Popen(['open', expanded])
        return f"Opened folder: {expanded}"
    else:
        return f"Path not found: {expanded}"

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
    else:
        return f"File not found: {expanded}"

def read_file(path: str) -> str:
    """Read file content."""
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def rename_file(old: str, new: str) -> str:
    """Rename/move a file."""
    old_exp = os.path.expanduser(old)
    new_exp = os.path.expanduser(new)
    if os.path.exists(old_exp):
        os.rename(old_exp, new_exp)
        return f"Renamed {old} to {new}"
    else:
        return f"File not found: {old}"
