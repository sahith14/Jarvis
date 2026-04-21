import os, time, threading, ast
from pathlib import Path
from datetime import datetime
ROOT_DIR = Path(__file__).parent
EXTENSIONS = {".py", ".ts", ".html", ".css", ".js"}

class CodeMonitor:
    def __init__(self, report_cb):
        self.report_cb = report_cb
        self.last_hashes = {}
        self.active = True
        self.error_log = set()
    def check_file_error(self, file_path):
        try:
            if file_path.suffix == ".py":
                with open(file_path, "r", encoding="utf-8") as f:
                    ast.parse(f.read())
            return None
        except SyntaxError as e: return f"Syntax error in {file_path.name} line {e.lineno}: {e.msg}"
        except Exception as e: return f"Error in {file_path.name}: {e}"
    def watch_loop(self):
        while self.active:
            for root, _, files in os.walk(ROOT_DIR):
                if any(ignore in root for ignore in ["node_modules", ".git", "whatsapp_data", "__pycache__", "_archive"]): continue
                for file in files:
                    p = Path(root) / file
                    if p.suffix in EXTENSIONS:
                        try:
                            mtime = p.stat().st_mtime
                            if p not in self.last_hashes or self.last_hashes[p] != mtime:
                                self.last_hashes[p] = mtime
                                err = self.check_file_error(p)
                                if err: self.report_cb(f"Error in {p.name}: {err}")
                                else:
                                    resolved = [e for e in self.error_log if p.name in e]
                                    for r in resolved:
                                        self.error_log.remove(r)
                                        self.report_cb(f"Fixed: {p.name}")
                        except: pass
            time.sleep(2)
    def periodic_scan_loop(self):
        while self.active:
            for root, _, files in os.walk(ROOT_DIR):
                if any(ignore in root for ignore in ["node_modules", ".git", "whatsapp_data", "__pycache__", "_archive"]): continue
                for file in files:
                    p = Path(root) / file
                    if p.suffix in EXTENSIONS:
                        err = self.check_file_error(p)
                        if err and err not in self.error_log:
                            self.error_log.add(err)
                            self.report_cb(f"Issue detected: {err}")
            time.sleep(600)

def start_monitoring(report_callback):
    monitor = CodeMonitor(report_callback)
    threading.Thread(target=monitor.watch_loop, daemon=True).start()
    threading.Thread(target=monitor.periodic_scan_loop, daemon=True).start()
    return monitor
