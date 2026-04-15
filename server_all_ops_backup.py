import asyncio
import json
import logging
import os
import shutil
import glob
import re
from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

GROQ_API_KEY = "os.getenv("GROQ_API_KEY")"
groq_client = Groq(api_key=GROQ_API_KEY)

# Helper: get safe path
def get_path(path: str, base: str = None) -> str:
    if base:
        full = os.path.join(base, path)
    else:
        full = os.path.expanduser(path)
    return os.path.abspath(full)

# ========== FILE EXPLORER ==========
async def open_file_explorer(path: str = None) -> bool:
    """Open Windows File Explorer"""
    try:
        if path:
            os.startfile(path)
        else:
            os.startfile(os.path.expanduser("~"))
        return True
    except Exception as e:
        log.error(f"Explorer error: {e}")
        return False

async def open_downloads():
    return await open_file_explorer(os.path.expanduser("~/Downloads"))

async def open_desktop():
    return await open_file_explorer(os.path.expanduser("~/Desktop"))

async def open_documents():
    return await open_file_explorer(os.path.expanduser("~/Documents"))

# ========== FOLDER OPERATIONS ==========
async def create_folder(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        os.makedirs(path, exist_ok=True)
        return f"Created folder '{name}' sir."
    except Exception as e:
        return f"Failed to create folder: {str(e)}"

async def delete_folder(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        if os.path.exists(path):
            shutil.rmtree(path)
            return f"Deleted folder '{name}' sir."
        else:
            return f"Folder '{name}' not found sir."
    except Exception as e:
        return f"Failed to delete: {str(e)}"

async def rename_folder(old: str, new: str, location: str = None) -> str:
    try:
        old_path = get_path(old, location)
        new_path = get_path(new, location)
        os.rename(old_path, new_path)
        return f"Renamed '{old}' to '{new}' sir."
    except Exception as e:
        return f"Failed to rename: {str(e)}"

async def move_folder(name: str, destination: str) -> str:
    try:
        src = get_path(name)
        dst = get_path(name, destination)
        shutil.move(src, dst)
        return f"Moved '{name}' to '{destination}' sir."
    except Exception as e:
        return f"Failed to move: {str(e)}"

async def copy_folder(name: str, destination: str) -> str:
    try:
        src = get_path(name)
        dst = get_path(name, destination)
        shutil.copytree(src, dst)
        return f"Copied '{name}' to '{destination}' sir."
    except Exception as e:
        return f"Failed to copy: {str(e)}"

async def list_folder_contents(path: str = ".") -> str:
    try:
        full = get_path(path)
        items = os.listdir(full)
        folders = [i for i in items if os.path.isdir(os.path.join(full, i))]
        files = [i for i in items if os.path.isfile(os.path.join(full, i))]
        result = f"?? Folders ({len(folders)}): {', '.join(folders[:10])}"
        if len(folders) > 10:
            result += f" and {len(folders)-10} more"
        result += f"\n?? Files ({len(files)}): {', '.join(files[:10])}"
        if len(files) > 10:
            result += f" and {len(files)-10} more"
        return result
    except Exception as e:
        return f"Error reading folder: {str(e)}"

async def folder_details(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        stat = os.stat(path)
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        item_count = len(os.listdir(path))
        return f"?? {name}\nSize: {size} bytes\nModified: {modified}\nContains: {item_count} items"
    except Exception as e:
        return f"Error: {str(e)}"

async def open_folder(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        await open_file_explorer(path)
        return f"Opening folder '{name}' sir."
    except Exception as e:
        return f"Failed to open folder: {str(e)}"

# ========== FILE OPERATIONS ==========
async def create_file(name: str, content: str = "", location: str = None) -> str:
    try:
        path = get_path(name, location)
        with open(path, 'w') as f:
            f.write(content)
        return f"Created file '{name}' sir."
    except Exception as e:
        return f"Failed to create file: {str(e)}"

async def delete_file(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        if os.path.exists(path):
            os.remove(path)
            return f"Deleted file '{name}' sir."
        else:
            return f"File '{name}' not found sir."
    except Exception as e:
        return f"Failed to delete: {str(e)}"

async def rename_file(old: str, new: str, location: str = None) -> str:
    try:
        old_path = get_path(old, location)
        new_path = get_path(new, location)
        os.rename(old_path, new_path)
        return f"Renamed '{old}' to '{new}' sir."
    except Exception as e:
        return f"Failed to rename: {str(e)}"

async def read_file(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content) > 500:
            content = content[:500] + "... (truncated)"
        return f"?? {name}:\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

async def write_to_file(name: str, content: str, location: str = None, append: bool = False) -> str:
    try:
        path = get_path(name, location)
        mode = 'a' if append else 'w'
        with open(path, mode) as f:
            f.write(content + '\n')
        action = "Appended to" if append else "Wrote to"
        return f"{action} file '{name}' sir."
    except Exception as e:
        return f"Failed to write: {str(e)}"

async def file_details(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        stat = os.stat(path)
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        ext = os.path.splitext(name)[1] or "No extension"
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024*1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size/(1024*1024):.1f} MB"
        return f"?? {name}\nType: {ext}\nSize: {size_str}\nModified: {modified}"
    except Exception as e:
        return f"Error: {str(e)}"

async def search_files(keyword: str, search_path: str = ".") -> str:
    try:
        path = get_path(search_path)
        matches = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if keyword.lower() in f.lower():
                    matches.append(os.path.join(root, f))
                    if len(matches) >= 10:
                        break
            if len(matches) >= 10:
                break
        if matches:
            return f"Found {len(matches)} files:\n" + "\n".join(matches)
        else:
            return f"No files found containing '{keyword}' sir."
    except Exception as e:
        return f"Search error: {str(e)}"

async def copy_file(name: str, destination: str, location: str = None) -> str:
    try:
        src = get_path(name, location)
        dst = get_path(name, destination)
        shutil.copy2(src, dst)
        return f"Copied '{name}' to '{destination}' sir."
    except Exception as e:
        return f"Failed to copy: {str(e)}"

# ========== ADVANCED ==========
async def folder_size(name: str, location: str = None) -> str:
    try:
        path = get_path(name, location)
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        if total < 1024:
            size_str = f"{total} bytes"
        elif total < 1024*1024:
            size_str = f"{total/1024:.1f} KB"
        else:
            size_str = f"{total/(1024*1024):.1f} MB"
        return f"Folder '{name}' total size: {size_str} sir."
    except Exception as e:
        return f"Error: {str(e)}"

async def find_large_files(threshold_mb: int = 100, search_path: str = ".") -> str:
    try:
        path = get_path(search_path)
        large = []
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                if size > threshold_mb * 1024 * 1024:
                    large.append(f"{fp} ({size/(1024*1024):.1f} MB)")
                    if len(large) >= 10:
                        break
            if len(large) >= 10:
                break
        if large:
            return f"Large files (> {threshold_mb} MB):\n" + "\n".join(large)
        else:
            return f"No files larger than {threshold_mb} MB found sir."
    except Exception as e:
        return f"Error: {str(e)}"

async def recent_files(days: int = 7, search_path: str = ".") -> str:
    try:
        path = get_path(search_path)
        cutoff = datetime.now().timestamp() - (days * 86400)
        recent = []
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                mtime = os.path.getmtime(fp)
                if mtime > cutoff:
                    recent.append(fp)
                    if len(recent) >= 10:
                        break
            if len(recent) >= 10:
                break
        if recent:
            return f"Recently modified files (last {days} days):\n" + "\n".join(recent)
        else:
            return f"No files modified in the last {days} days sir."
    except Exception as e:
        return f"Error: {str(e)}"

async def count_files(folder: str = ".") -> str:
    try:
        path = get_path(folder)
        total = 0
        for root, dirs, files in os.walk(path):
            total += len(files)
        return f"Folder '{folder}' contains {total} files sir."
    except Exception as e:
        return f"Error: {str(e)}"

async def tree_view(folder: str = ".", level: int = 0, max_level: int = 2) -> str:
    try:
        path = get_path(folder)
        lines = []
        def walk(p, lvl):
            if lvl > max_level:
                return
            indent = "  " * lvl
            for item in sorted(os.listdir(p)):
                item_path = os.path.join(p, item)
                if os.path.isdir(item_path):
                    lines.append(f"{indent}?? {item}")
                    walk(item_path, lvl+1)
                else:
                    lines.append(f"{indent}?? {item}")
        walk(path, level)
        return "Folder tree:\n" + "\n".join(lines[:50])
    except Exception as e:
        return f"Error: {str(e)}"

# ========== AI RESPONSE ==========
async def get_ai_response(user_text: str) -> str:
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": """You are JARVIS, a British AI assistant.
                Be very brief (1-2 sentences). Address user as 'sir' (lowercase).
                Be helpful. Never repeat user's words back. Provide actual answers."""},
                {"role": "user", "content": user_text}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "I'm having trouble, sir. Please try again."

# ========== COMMAND PARSER ==========
async def process_command(text: str) -> str:
    t = text.lower().strip()
    # Remove "jarvis" prefix
    if t.startswith("jarvis"):
        t = t[6:].strip()

    # File Explorer
    if "open file explorer" in t or "open my files" in t:
        await open_file_explorer()
        return "Opening File Explorer, sir."
    if "open downloads" in t:
        await open_downloads()
        return "Opening Downloads folder, sir."
    if "open desktop" in t:
        await open_desktop()
        return "Opening Desktop folder, sir."
    if "open documents" in t:
        await open_documents()
        return "Opening Documents folder, sir."

    # Folder operations
    m = re.search(r'(?:create|make|new) folder (?:(?:called )?["\']?([^"\']+)["\']?)', t)
    if m:
        return await create_folder(m.group(1))
    m = re.search(r'(?:delete|remove) folder (?:(?:called )?["\']?([^"\']+)["\']?)', t)
    if m:
        return await delete_folder(m.group(1))
    m = re.search(r'rename folder (?:(?:called )?["\']?([^"\']+)["\']?) to ["\']?([^"\']+)["\']?', t)
    if m:
        return await rename_folder(m.group(1), m.group(2))
    m = re.search(r'move folder (?:(?:called )?["\']?([^"\']+)["\']?) to ["\']?([^"\']+)["\']?', t)
    if m:
        return await move_folder(m.group(1), m.group(2))
    m = re.search(r'copy folder (?:(?:called )?["\']?([^"\']+)["\']?) to ["\']?([^"\']+)["\']?', t)
    if m:
        return await copy_folder(m.group(1), m.group(2))
    m = re.search(r'(?:list contents of|show files in|what\'s in) (?:folder )?["\']?([^"\']+)["\']?', t)
    if m:
        return await list_folder_contents(m.group(1))
    m = re.search(r'folder details (?:about )?["\']?([^"\']+)["\']?', t)
    if m:
        return await folder_details(m.group(1))
    m = re.search(r'open folder (?:called )?["\']?([^"\']+)["\']?', t)
    if m:
        return await open_folder(m.group(1))

    # File operations
    m = re.search(r'(?:create|make|new) file (?:(?:called )?["\']?([^"\']+)["\']?)', t)
    if m:
        return await create_file(m.group(1))
    m = re.search(r'(?:delete|remove) file (?:(?:called )?["\']?([^"\']+)["\']?)', t)
    if m:
        return await delete_file(m.group(1))
    m = re.search(r'rename file (?:(?:called )?["\']?([^"\']+)["\']?) to ["\']?([^"\']+)["\']?', t)
    if m:
        return await rename_file(m.group(1), m.group(2))
    m = re.search(r'read file (?:(?:called )?["\']?([^"\']+)["\']?)', t)
    if m:
        return await read_file(m.group(1))
    m = re.search(r'(?:write to|save to) file (?:(?:called )?["\']?([^"\']+)["\']?) (?:saying|with) ["\']?([^"\']+)["\']?', t)
    if m:
        return await write_to_file(m.group(1), m.group(2))
    m = re.search(r'append to file (?:(?:called )?["\']?([^"\']+)["\']?) (?:saying|with) ["\']?([^"\']+)["\']?', t)
    if m:
        return await write_to_file(m.group(1), m.group(2), append=True)
    m = re.search(r'file details (?:about )?["\']?([^"\']+)["\']?', t)
    if m:
        return await file_details(m.group(1))
    m = re.search(r'open file (?:(?:called )?["\']?([^"\']+)["\']?)', t)
    if m:
        return await open_file(m.group(1))
    m = re.search(r'search (?:for|files) ["\']?([^"\']+)["\']?', t)
    if m:
        return await search_files(m.group(1))
    m = re.search(r'copy file (?:(?:called )?["\']?([^"\']+)["\']?) to ["\']?([^"\']+)["\']?', t)
    if m:
        return await copy_file(m.group(1), m.group(2))

    # Advanced
    m = re.search(r'folder size (?:of )?["\']?([^"\']+)["\']?', t)
    if m:
        return await folder_size(m.group(1))
    if "find large files" in t:
        return await find_large_files()
    m = re.search(r'recent files (?:last )?(\d+)? ?days?', t)
    if m:
        days = int(m.group(1)) if m.group(1) else 7
        return await recent_files(days)
    m = re.search(r'count files (?:in )?["\']?([^"\']+)["\']?', t)
    if m:
        return await count_files(m.group(1))
    if "tree view" in t:
        m = re.search(r'tree view (?:of )?["\']?([^"\']+)["\']?', t)
        return await tree_view(m.group(1) if m else ".")

    # Simple commands
    if "hello" in t or "hi" in t:
        return "Hello sir, how may I help you?"
    if "time" in t:
        return f"The time is {datetime.now().strftime('%I:%M %p')}, sir."

    # AI conversation
    return await get_ai_response(text)

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

@app.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "transcript":
                user_text = msg.get("text", "")
                log.info(f"User: {user_text}")
                response = await process_command(user_text)
                log.info(f"JARVIS: {response}")
                await websocket.send_json({"type": "audio", "text": response})
    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
