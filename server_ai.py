import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq
from file_operations import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Initialize Groq
GROQ_API_KEY = "os.getenv("GROQ_API_KEY")"
groq_client = Groq(api_key=GROQ_API_KEY)

@app.get("/api/settings/status")
async def status():
    return JSONResponse({"status": "ok"})

# File operation keywords - check before sending to AI
FILE_KEYWORDS = [
    "create folder", "make folder", "new folder",
    "delete folder", "remove folder",
    "rename folder",
    "list contents", "show files", "what's in",
    "folder details", "folder info",
    "open folder",
    "create file", "make file", "new file",
    "delete file", "remove file",
    "rename file",
    "read file",
    "write to file", "save to file",
    "file details", "file info",
    "search for", "find file",
    "open file explorer", "open my files",
    "open downloads", "open desktop", "open documents"
]

async def is_file_operation(text: str) -> bool:
    """Check if the command is a file operation"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FILE_KEYWORDS)

async def handle_file_operation(user_text: str) -> str:
    """Handle file operations locally"""
    text = user_text.lower().strip()
    
    import re
    
    # Remove "jarvis" from beginning
    if text.startswith("jarvis"):
        text = text[6:].strip()
    
    # Folder operations
    if "create folder" in text or "make folder" in text or "new folder" in text:
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
        return "Please tell me the current name and new name, sir."
    
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
    
    # File operations
    elif "create file" in text or "make file" in text or "new file" in text:
        match = re.search(r'(?:create|make|new) file (?:called )?["\']?([^"\']+)["\']?', text)
        if match:
            file_name = match.group(1).strip()
            result = await create_file(file_name)
            return result["message"]
        return "What should I name the file, sir?"
    
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
    
    elif "search for" in text or "find file" in text:
        match = re.search(r'(?:search for|find file) ["\']?([^"\']+)["\']?', text)
        if match:
            keyword = match.group(1).strip()
            result = await search_files(keyword)
            return result["message"]
        return "What should I search for, sir?"
    
    # Quick access
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
    
    return None  # Not a file operation

async def get_ai_response(user_text: str) -> str:
    """Get intelligent response from Groq AI"""
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": """You are JARVIS, a British AI assistant. 
                Be very brief (1-2 sentences maximum). 
                Address the user as 'sir' (lowercase).
                Be helpful and conversational.
                Never repeat the user's words back to them.
                Provide actual answers, not echoes."""},
                {"role": "user", "content": user_text}
            ],
            max_tokens=100,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        log.error(f"Groq error: {e}")
        return "I'm having trouble connecting to my systems, sir. Please try again."

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
                
                # Check if it's a file operation first
                file_response = await handle_file_operation(user_text)
                
                if file_response:
                    response = file_response
                else:
                    # Use AI for conversation
                    response = await get_ai_response(user_text)
                
                log.info(f"JARVIS: {response}")
                await websocket.send_json({"type": "audio", "text": response})
                
    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
