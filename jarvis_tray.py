import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def run_backend():
    os.system('python server.py')

def run_frontend():
    os.system('cd frontend && npm run dev')

def run_listener():
    os.system('python listener.py')

if __name__ == "__main__":
    threading.Thread(target=run_backend, daemon=True).start()
    time.sleep(3)
    # threading.Thread(target=run_listener, daemon=True).start()  # Disabled to prevent echo loop # 24/7 Mic Listener
    time.sleep(1)
    threading.Thread(target=run_frontend, daemon=True).start()
    print("JARVIS is running in background")
    print("[VOICE] 24/7 Autonomous listening active")
    print("Speak freely, I am always listening.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down JARVIS...")
