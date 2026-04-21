import json
import asyncio
import webbrowser
import subprocess
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are JARVIS, a smart AI assistant.
Respond naturally and clearly.
Keep responses short and useful.
"""

# ---------- AI ----------
async def generate_response(text):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Something went wrong."

# ---------- ACTIONS ----------
def open_youtube():
    webbrowser.open("https://youtube.com")

def open_google():
    webbrowser.open("https://google.com")

def open_chrome():
    webbrowser.open("https://google.com")

def open_folder(path):
    try:
        os.startfile(path)
    except:
        pass

def open_notepad():
    subprocess.Popen("notepad.exe")

def open_cmd():
    subprocess.Popen("cmd.exe")

def type_text(text):
    try:
        import pyautogui
        pyautogui.write(text)
    except:
        pass

# ---------- COMMAND ROUTER ----------
async def handle_command(text):
    t = text.lower()

    if "youtube" in t:
        open_youtube()
        return "Opening YouTube"

    elif "google" in t:
        open_google()
        return "Opening Google"

    elif "chrome" in t:
        open_chrome()
        return "Opening Chrome"

    elif "notepad" in t:
        open_notepad()
        return "Opening Notepad"

    elif "command prompt" in t or "cmd" in t:
        open_cmd()
        return "Opening Command Prompt"

    elif "downloads" in t:
        open_folder(os.path.join(os.path.expanduser("~"), "Downloads"))
        return "Opening Downloads"

    elif "documents" in t:
        open_folder(os.path.join(os.path.expanduser("~"), "Documents"))
        return "Opening Documents"

    elif "type" in t:
        text_to_type = t.replace("type", "").strip()
        type_text(text_to_type)
        return f"Typing {text_to_type}"

    return None

# ---------- WEBSOCKET ----------
@app.websocket("/ws/voice")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        try:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "transcript":
                text = msg.get("text", "")

                await websocket.send_text(json.dumps({
                    "type": "status",
                    "state": "thinking"
                }))

                # COMMAND FIRST
                command_result = await handle_command(text)

                if command_result:
                    response_text = command_result
                else:
                    response_text = await generate_response(text)

                await websocket.send_text(json.dumps({
                    "type": "response",
                    "text": response_text
                }))

                await websocket.send_text(json.dumps({
                    "type": "status",
                    "state": "idle"
                }))

        except Exception as e:
            print("Error:", e)
            break


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8340)