# listener.py — JARVIS 24/7 Background Voice Listener
# ══════════════════════════════════════════════════════════════════════════════
# Uses the microphone directly to listen for "Jarvis" or commands.
# Connects to the server via WebSocket to process speech.
# ══════════════════════════════════════════════════════════════════════════════

import json
import time
import threading
import websocket # pip install websocket-client
import speech_recognition as sr # pip install SpeechRecognition

WS_URL = "ws://localhost:8340/ws/voice"

class JarvisListener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.ws = None
        self.active = True
        
        # Adjust for ambient noise on start
        with self.mic as source:
            print("[LISTENER] Adjusting for ambient noise... Please be quiet.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[LISTENER] Ready.")

    def connect_ws(self):
        def on_message(ws, message):
            pass # We only send, server sends audio back via WS (which we might ignore if using system TTS)
            
        def on_error(ws, error):
            print(f"[LISTENER] WS Error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            print("[LISTENER] WS Closed. Reconnecting in 5s...")
            time.sleep(5)
            self.connect_ws()

        def on_open(ws):
            print("[LISTENER] Connected to JARVIS Server")

        self.ws = websocket.WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def listen_loop(self):
        print("[LISTENER] [MIC] Listening 24/7...")
        
        while self.active:
            try:
                with self.mic as source:
                    # phrase_time_limit keeps it from listening forever to silence
                    audio = self.recognizer.listen(source, phrase_time_limit=10, timeout=None)
                
                print("[LISTENER] Processing speech...")
                # Use Google Web Speech (Free, no key needed for small projects)
                text = self.recognizer.recognize_google(audio)
                
                if text:
                    print(f"[LISTENER] Heard: {text}")
                    if self.ws and self.ws.sock and self.ws.sock.connected:
                        payload = {
                            "type": "transcript",
                            "text": text,
                            "isFinal": True
                        }
                        self.ws.send(json.dumps(payload))
                    else:
                        print("[LISTENER] WS not connected. Skipping.")
                        
            except sr.UnknownValueError:
                # Silence or noise
                pass
            except sr.RequestError as e:
                print(f"[LISTENER] Speech Service Error: {e}")
                time.sleep(2)
            except Exception as e:
                print(f"[LISTENER] Loop Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    listener = JarvisListener()
    listener.connect_ws()
    try:
        listener.listen_loop()
    except KeyboardInterrupt:
        listener.active = False
        print("[LISTENER] Shutting down.")
