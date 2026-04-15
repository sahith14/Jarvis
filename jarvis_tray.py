import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def run_backend():
    os.system('python server_fresh.py')

def run_frontend():
    os.system('cd frontend && npm run dev')

if __name__ == "__main__":
    threading.Thread(target=run_backend, daemon=True).start()
    time.sleep(3)
    threading.Thread(target=run_frontend, daemon=True).start()
    print("JARVIS is running in background")
    print("Say 'JARVIS' to wake me")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down JARVIS...")
