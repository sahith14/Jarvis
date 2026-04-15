import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from file_operations import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

async def process_command(user_text: str) -> str:
    """Process file and folder commands"""
    text = user_text.lower().strip()
    
    # Remove "jarvis" from the beginning if present
    if text.startswith("jarvis"):
        text = text[6:].strip()
    
    # ===== FOLDER COMMANDS =====
    if "create folder" in text or "make folder" in text or "new folder" in text:
        # Extract folder name
        import re
        match = re.search(r'(?:create|make|new) folder (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            folder_name = match.group(1).strip()
            result = await create_folder(folder_name)
            return result["message"]
        return "What should I name the folder, sir?"
    
    elif "delete folder" in text or "remove folder" in text:
        match = re.search(r'(?:delete|remove) folder (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            folder_name = match.group(1).strip()
            result = await delete_folder(folder_name)
            return result["message"]
        return "Which folder should I delete, sir?"
    
    elif "rename folder" in text:
        match = re.search(r'rename folder (?:called )?["\']?([^"\']+)["\']? to ["\']?([^"\']+)["\']?', text)
        if match:
            old_name = match.group(1).strip()
            new_name = match.group(2).strip()
            result = await rename_folder(old_name, new_name)
            return result["message"]
        return "Please tell me the current name and new name for the folder, sir."
    
    elif "list contents" in text or "show files" in text or "what's in" in text:
        match = re.search(r'(?:list contents of|show files in|what\'s in) (?:folder )?["\']?([^"\']+)["\']?', text)
        if match:
            folder = match.group(1).strip()
            result = await list_folder_contents(folder)
        else:
            result = await list_folder_contents(".")
        return result["message"]
    
    elif "folder details" in text or "folder info" in text:
        match = re.search(r'(?:folder details|folder info) (?:about )?["\']?([^"\']+)["\']?', text)
        if match:
            folder_name = match.group(1).strip()
            result = await get_folder_details(folder_name)
            return result["message"]
        return "Which folder details would you like, sir?"
    
    elif "open folder" in text:
        match = re.search(r'open folder (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            folder_name = match.group(1).strip()
            await open_file_explorer(folder_name)
            return f"Opening {folder_name} folder, sir."
        return "Which folder should I open, sir?"
    
    # ===== FILE COMMANDS =====
    elif "create file" in text or "make file" in text or "new file" in text:
        match = re.search(r'(?:create|make|new) file (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            file_name = match.group(1).strip()
            result = await create_file(file_name)
            return result["message"]
        return "What should I name the file, sir?"
    
    elif "delete file" in text or "remove file" in text:
        match = re.search(r'(?:delete|remove) file (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            file_name = match.group(1).strip()
            result = await delete_file(file_name)
            return result["message"]
        return "Which file should I delete, sir?"
    
    elif "rename file" in text:
        match = re.search(r'rename file (?:called )?["\']?([^"\']+)["\']? to ["\']?([^"\']+)["\']?', text)
        if match:
            old_name = match.group(1).strip()
            new_name = match.group(2).strip()
            result = await rename_file(old_name, new_name)
            return result["message"]
        return "Please tell me the current name and new name for the file, sir."
    
    elif "read file" in text:
        match = re.search(r'read file (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            file_name = match.group(1).strip()
            result = await read_file(file_name)
            return result["message"]
        return "Which file should I read, sir?"
    
    elif "write to file" in text or "save to file" in text:
        match = re.search(r'(?:write to|save to) file (?:called )?["\']?([^"\']+)["\']? (?:saying|with) ["\']?([^"\']+)["\']?', text)
        if match:
            file_name = match.group(1).strip()
            content = match.group(2).strip()
            result = await write_to_file(file_name, content)
            return result["message"]
        return "What should I write to the file, sir?"
    
    elif "file details" in text or "file info" in text:
        match = re.search(r'(?:file details|file info) (?:about )?["\']?([^"\']+)["\']?', text)
        if match:
            file_name = match.group(1).strip()
            result = await get_file_details(file_name)
            return result["message"]
        return "Which file details would you like, sir?"
    
    elif "search for" in text or "find file" in text:
        match = re.search(r'(?:search for|find file) ["\']?([^"\']+)["\']?', text)
        if match:
            keyword = match.group(1).strip()
            result = await search_files(keyword)
            return result["message"]
        return "What should I search for, sir?"
    
    # ===== BASIC COMMANDS =====
    elif "open file explorer" in text or "open my files" in text:
        await open_file_explorer()
        return "Opening File Explorer, sir."
    
    elif "open downloads" in text:
        await open_downloads()
        return "Opening Downloads folder, sir."
    
    elif "open desktop" in text:
        await open_desktop()
        return "Opening Desktop folder, sir."
    
    elif "open documents" in text:
        await open_documents()
        return "Opening Documents folder, sir."
    
    elif "hello" in text or "hi" in text:
        return "Hello sir, how can I help you today?"
    
    elif "time" in text:
        from datetime import datetime
        return f"The time is {datetime.now().strftime('%I:%M %p')}, sir."
    
    else:
        return f"I heard you say: {user_text[:100]}"

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
