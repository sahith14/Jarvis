# controller.py — JARVIS Mark IV Desktop Control Layer
import subprocess, time
try: import pygetwindow as gw
except: gw = None
try: import pyperclip
except: pyperclip = None
try: import pyautogui; pyautogui.FAILSAFE = True; pyautogui.PAUSE = 0.1
except: pyautogui = None
try: import psutil
except: psutil = None

def focus_app(name):
    if not gw: return "Window control unavailable"
    for win in gw.getAllWindows():
        if win.title and name.lower() in win.title.lower():
            if win.isMinimized: win.restore()
            win.activate()
            return f"Switched to {win.title}."
    return f"Window '{name}' not found."

def minimize_app(name):
    if not gw: return "Unavailable"
    for win in gw.getAllWindows():
        if win.title and name.lower() in win.title.lower():
            win.minimize()
            return f"Minimized {win.title}."
    return f"Window '{name}' not found."

def maximize_app(name):
    if not gw: return "Unavailable"
    for win in gw.getAllWindows():
        if win.title and name.lower() in win.title.lower():
            win.maximize()
            return f"Maximized {win.title}."
    return f"Window '{name}' not found."

def close_app(name):
    if not gw: return "Unavailable"
    for win in gw.getAllWindows():
        if win.title and name.lower() in win.title.lower():
            win.close()
            return f"Closed {win.title}."
    return f"Window '{name}' not found."

def list_windows():
    if not gw: return "Unavailable"
    wins = [f"  • {w.title}" for w in gw.getAllWindows() if w.title and w.visible][:15]
    return f"{len(wins)} windows:\n" + "\n".join(wins) if wins else "No windows."

def get_active_window_title():
    if not gw: return "unknown"
    try:
        a = gw.getActiveWindow()
        return a.title if a else "unknown"
    except: return "unknown"

def copy_text(text):
    if pyperclip: pyperclip.copy(text); return "Copied."
    return "Clipboard unavailable."

def get_clipboard():
    if pyperclip:
        c = pyperclip.paste()
        return f"Clipboard: {c[:200]}" if c else "Empty."
    return "Unavailable."

def type_text(text):
    if pyautogui:
        time.sleep(0.3); pyautogui.write(text, interval=0.02)
        return "Done."
    return "Unavailable."

def press_key(key):
    if pyautogui: pyautogui.press(key); return f"Pressed {key}."
    return "Unavailable."

def hotkey(*keys):
    if pyautogui: pyautogui.hotkey(*keys); return f"Pressed {'+'.join(keys)}."
    return "Unavailable."

def get_system_stats():
    if not psutil: return "Unavailable"
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    bat = psutil.sensors_battery()
    parts = [f"CPU: {cpu}%", f"RAM: {ram.percent}%", f"Disk: {disk.percent}%"]
    if bat: parts.append(f"Battery: {bat.percent}%")
    return " | ".join(parts)

def get_running_processes(top_n=5):
    if not psutil: return "Unavailable"
    procs = []
    for p in psutil.process_iter(["name","cpu_percent","memory_percent"]):
        try:
            if p.info["cpu_percent"]: procs.append(p.info)
        except: pass
    procs.sort(key=lambda x: x.get("cpu_percent",0), reverse=True)
    top = procs[:top_n]
    if not top: return "No processes."
    lines = [f"  • {p['name']}: CPU {p['cpu_percent']:.1f}%, RAM {p['memory_percent']:.1f}%" for p in top]
    return f"Top processes:\n" + "\n".join(lines)

def is_cpu_high(th=85): return psutil.cpu_percent(interval=0.5) > th if psutil else False
def is_ram_high(th=90): return psutil.virtual_memory().percent > th if psutil else False
def is_app_running(name):
    if not psutil: return False
    for p in psutil.process_iter(["name"]):
        if name.lower() in p.info["name"].lower(): return True
    return False
