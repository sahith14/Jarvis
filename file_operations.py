import os
import shutil
import glob
from datetime import datetime
import logging

log = logging.getLogger("jarvis.files")

# Helper to get safe path
def _get_safe_path(path: str, base: str = None) -> str:
    if base:
        full_path = os.path.join(base, path)
    else:
        full_path = os.path.expanduser(path)
    return os.path.abspath(full_path)

# ============= FOLDER OPERATIONS =============

async def create_folder(folder_name: str, location: str = None) -> dict:
    """Create a new folder"""
    try:
        if location:
            path = _get_safe_path(folder_name, location)
        else:
            path = _get_safe_path(folder_name)
        
        os.makedirs(path, exist_ok=True)
        return {"success": True, "message": f"Created folder: {folder_name}", "path": path}
    except Exception as e:
        return {"success": False, "message": f"Failed to create folder: {str(e)}"}

async def delete_folder(folder_name: str, location: str = None) -> dict:
    """Delete a folder (requires confirmation)"""
    try:
        if location:
            path = _get_safe_path(folder_name, location)
        else:
            path = _get_safe_path(folder_name)
        
        if os.path.exists(path):
            shutil.rmtree(path)
            return {"success": True, "message": f"Deleted folder: {folder_name}"}
        else:
            return {"success": False, "message": f"Folder not found: {folder_name}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete: {str(e)}"}

async def rename_folder(old_name: str, new_name: str, location: str = None) -> dict:
    """Rename a folder"""
    try:
        if location:
            old_path = _get_safe_path(old_name, location)
            new_path = _get_safe_path(new_name, location)
        else:
            old_path = _get_safe_path(old_name)
            new_path = _get_safe_path(new_name)
        
        os.rename(old_path, new_path)
        return {"success": True, "message": f"Renamed '{old_name}' to '{new_name}'"}
    except Exception as e:
        return {"success": False, "message": f"Failed to rename: {str(e)}"}

async def list_folder_contents(folder_path: str = ".") -> dict:
    """List contents of a folder"""
    try:
        path = _get_safe_path(folder_path)
        items = os.listdir(path)
        
        folders = [f for f in items if os.path.isdir(os.path.join(path, f))]
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        
        result = f"?? Folders ({len(folders)}): {', '.join(folders[:10])}"
        if len(folders) > 10:
            result += f" and {len(folders)-10} more"
        result += f"\n?? Files ({len(files)}): {', '.join(files[:10])}"
        if len(files) > 10:
            result += f" and {len(files)-10} more"
        
        return {"success": True, "contents": items, "message": result}
    except Exception as e:
        return {"success": False, "message": f"Error reading folder: {str(e)}"}

async def get_folder_details(folder_name: str, location: str = None) -> dict:
    """Get folder details like size, modified date"""
    try:
        if location:
            path = _get_safe_path(folder_name, location)
        else:
            path = _get_safe_path(folder_name)
        
        if not os.path.exists(path):
            return {"success": False, "message": f"Folder not found: {folder_name}"}
        
        stat = os.stat(path)
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        # Count items
        item_count = len(os.listdir(path))
        
        return {
            "success": True,
            "message": f"?? {folder_name}\nSize: {size} bytes\nModified: {modified}\nContains: {item_count} items"
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

# ============= FILE OPERATIONS =============

async def create_file(file_name: str, content: str = "", location: str = None) -> dict:
    """Create a new file"""
    try:
        if location:
            path = _get_safe_path(file_name, location)
        else:
            path = _get_safe_path(file_name)
        
        with open(path, 'w') as f:
            f.write(content)
        return {"success": True, "message": f"Created file: {file_name}", "path": path}
    except Exception as e:
        return {"success": False, "message": f"Failed to create file: {str(e)}"}

async def delete_file(file_name: str, location: str = None) -> dict:
    """Delete a file"""
    try:
        if location:
            path = _get_safe_path(file_name, location)
        else:
            path = _get_safe_path(file_name)
        
        if os.path.exists(path):
            os.remove(path)
            return {"success": True, "message": f"Deleted file: {file_name}"}
        else:
            return {"success": False, "message": f"File not found: {file_name}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to delete: {str(e)}"}

async def rename_file(old_name: str, new_name: str, location: str = None) -> dict:
    """Rename a file"""
    try:
        if location:
            old_path = _get_safe_path(old_name, location)
            new_path = _get_safe_path(new_name, location)
        else:
            old_path = _get_safe_path(old_name)
            new_path = _get_safe_path(new_name)
        
        os.rename(old_path, new_path)
        return {"success": True, "message": f"Renamed '{old_name}' to '{new_name}'"}
    except Exception as e:
        return {"success": False, "message": f"Failed to rename: {str(e)}"}

async def read_file(file_name: str, location: str = None) -> dict:
    """Read file content and return it"""
    try:
        if location:
            path = _get_safe_path(file_name, location)
        else:
            path = _get_safe_path(file_name)
        
        if not os.path.exists(path):
            return {"success": False, "message": f"File not found: {file_name}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Limit content length for voice
        if len(content) > 500:
            preview = content[:500] + "... (file is long, only showing first 500 characters)"
        else:
            preview = content
        
        return {"success": True, "message": f"?? {file_name}:\n{preview}", "full_content": content}
    except Exception as e:
        return {"success": False, "message": f"Error reading file: {str(e)}"}

async def write_to_file(file_name: str, content: str, location: str = None, append: bool = False) -> dict:
    """Write or append to a file"""
    try:
        if location:
            path = _get_safe_path(file_name, location)
        else:
            path = _get_safe_path(file_name)
        
        mode = 'a' if append else 'w'
        with open(path, mode) as f:
            f.write(content + '\n')
        
        action = "Appended to" if append else "Wrote to"
        return {"success": True, "message": f"{action} file: {file_name}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to write: {str(e)}"}

async def get_file_details(file_name: str, location: str = None) -> dict:
    """Get file details: size, type, modified date"""
    try:
        if location:
            path = _get_safe_path(file_name, location)
        else:
            path = _get_safe_path(file_name)
        
        if not os.path.exists(path):
            return {"success": False, "message": f"File not found: {file_name}"}
        
        stat = os.stat(path)
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        file_ext = os.path.splitext(file_name)[1] or "No extension"
        
        # Format size nicely
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size/(1024*1024):.1f} MB"
        
        return {
            "success": True,
            "message": f"?? {file_name}\nType: {file_ext}\nSize: {size_str}\nModified: {modified}"
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

async def search_files(keyword: str, search_path: str = ".") -> dict:
    """Search for files by name containing keyword"""
    try:
        path = _get_safe_path(search_path)
        matches = []
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if keyword.lower() in file.lower():
                    matches.append(os.path.join(root, file))
                    if len(matches) >= 10:
                        break
            if len(matches) >= 10:
                break
        
        if matches:
            result = f"Found {len(matches)} files containing '{keyword}':\n" + "\n".join(matches)
        else:
            result = f"No files found containing '{keyword}'"
        
        return {"success": True, "message": result, "matches": matches}
    except Exception as e:
        return {"success": False, "message": f"Search error: {str(e)}"}
