import subprocess
import os
import logging

log = logging.getLogger("jarvis.terminal")

async def open_file_explorer(path: str = None) -> dict:
    """Open Windows File Explorer at specified path"""
    try:
        if path:
            os.startfile(path)
        else:
            subprocess.Popen('explorer')
        return {"success": True, "output": f"Opened File Explorer at {path if path else 'default location'}"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}

async def open_file(path: str) -> dict:
    """Open a specific file with default application"""
    try:
        os.startfile(path)
        return {"success": True, "output": f"Opened {path}"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}

async def open_downloads() -> dict:
    """Open Downloads folder"""
    downloads = os.path.expanduser("~/Downloads")
    return await open_file_explorer(downloads)

async def open_desktop() -> dict:
    """Open Desktop folder"""
    desktop = os.path.expanduser("~/Desktop")
    return await open_file_explorer(desktop)

async def open_documents() -> dict:
    """Open Documents folder"""
    documents = os.path.expanduser("~/Documents")
    return await open_file_explorer(documents)

async def run_terminal_command(command: str) -> dict:
    """Execute a terminal command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
