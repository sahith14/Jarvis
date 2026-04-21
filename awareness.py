# awareness.py — JARVIS Mark IV Awareness Engine
import os, random, threading, time
from collections import deque
from datetime import datetime
from typing import Callable, Optional
from intelligence import intelligence
from learning import UsageLearner
usage_learner = UsageLearner()
try: import pygetwindow as gw
except: gw = None
try: import psutil
except: psutil = None

CONTEXT_RULES = {
    "video_editing": ["premiere","davinci","resolve","after effects","filmora","shotcut","kdenlive","capcut"],
    "coding": ["visual studio code","vscode","code -","pycharm","intellij","sublime","atom","vim","neovim","terminal","powershell","cmd.exe","git"],
    "browsing": ["chrome","firefox","edge","opera","brave","safari"],
    "file_management": ["explorer","file explorer","this pc","downloads"],
    "music": ["spotify","vlc","music","soundcloud","youtube music"],
    "gaming": ["steam","discord","epic games","riot","valorant","minecraft","fortnite"],
    "communication": ["whatsapp","telegram","slack","teams","zoom","discord"],
    "design": ["photoshop","illustrator","figma","canva","gimp"],
    "writing": ["word","docs","notion","obsidian","notepad"],
}
CONTEXT_PROMPTS = {
    "video_editing": "User is editing video. Be encouraging.",
    "coding": "User is coding. Be supportive.",
    "browsing": "User is browsing. Light observation only.",
    "file_management": "User is managing files. Only comment if helpful.",
    "music": "User is listening to music. Light mood comment.",
    "gaming": "User is gaming. Minimal interruption.",
    "communication": "User is chatting. Don't interrupt.",
    "design": "User is designing. Supportive.",
    "writing": "User is writing. Minimal interruption.",
    "general": "User is doing something general. Only speak if useful.",
}

class AwarenessEngine:
    def __init__(self):
        self.active = False
        self.last_context = ""
        self.last_window_title = ""
        self.last_spoke = 0.0
        self.last_context_change = 0.0
        self.context_history = deque(maxlen=20)
        self.speak_cooldown = 45.0
        self.speak_probability = 0.20
        self.system_warn_cooldown = 120.0
        self.last_system_warn = 0.0
        self._speak_callback = None
        self._generate_callback = None
        self._analyze_image_callback = None
        self._thread = None
        self.last_deep_vision = 0.0
        self.deep_vision_cooldown = 300.0

    def start(self, speak_fn, generate_fn=None, analyze_image_fn=None):
        if self.active: return "Already active"
        self._speak_callback = speak_fn
        self._generate_callback = generate_fn
        self._analyze_image_callback = analyze_image_fn
        self.active = True
        self._thread = threading.Thread(target=self._main_loop, daemon=True)
        self._thread.start()
        return "Awareness activated."

    def stop(self):
        self.active = False
        return "Awareness deactivated."

    def detect_activity(self):
        if not gw: return "unknown"
        try:
            active = gw.getActiveWindow()
            return active.title.lower() if active and active.title else "unknown"
        except: return "unknown"

    def detect_context(self, title):
        for ctx, kws in CONTEXT_RULES.items():
            if any(kw in title for kw in kws): return ctx
        return "general"

    def can_speak(self):
        if not self.active: return False
        if time.time() - self.last_spoke < self.speak_cooldown: return False
        if intelligence.should_suppress("low"): return False
        if random.random() > self.speak_probability: return False
        return True

    def should_warn_system(self):
        if not psutil: return False
        if time.time() - self.last_system_warn < self.system_warn_cooldown: return False
        try:
            cpu = psutil.cpu_percent(interval=0.3)
            ram = psutil.virtual_memory().percent
            if cpu > 90 or ram > 92:
                self.last_system_warn = time.time()
                return True
        except: pass
        return False

    def generate_comment(self, context):
        if self._generate_callback:
            try:
                prompt = f"You are JARVIS observing: {context}. Active window: {self.last_window_title}. Generate ONE short natural observation (max 15 words)."
                return self._generate_callback(prompt)
            except: pass
        return {"coding":"Coding session. Need anything?","video_editing":"Editing mode.","browsing":"Browsing.","music":"Good taste.","gaming":"Game on."}.get(context,"I'm here.")

    def generate_system_warning(self):
        try:
            cpu = psutil.cpu_percent(interval=0.3)
            ram = psutil.virtual_memory().percent
            if cpu > 90 and ram > 90: return f"CPU at {cpu:.0f}% and RAM at {ram:.0f}%. Want me to check?"
            elif cpu > 90: return f"CPU running hot at {cpu:.0f}%."
            elif ram > 92: return f"RAM at {ram:.0f}%."
        except: pass
        return ""

    def _main_loop(self):
        while self.active:
            try:
                title = self.detect_activity()
                context = self.detect_context(title)
                context_changed = context != self.last_context and context != "general"
                if context_changed:
                    self.last_context_change = time.time()
                    self.context_history.append({"context":context,"title":title,"time":time.time()})
                self.last_window_title = title
                self.last_context = context
                deep_vision_insight = ""
                now = time.time()
                if self._analyze_image_callback and (now - self.last_deep_vision > self.deep_vision_cooldown) and intelligence.detect_user_state() != "focused":
                    if random.random() > 0.5:
                        self.last_deep_vision = now
                        deep_vision_insight = self._analyze_image_callback()
                should_generate = (context_changed or deep_vision_insight) and self.can_speak()
                if should_generate and self._speak_callback:
                    comment = self.generate_comment(context)
                    if comment:
                        self.last_spoke = time.time()
                        self._speak_callback(comment)
                if self.should_warn_system() and self._speak_callback:
                    warn = self.generate_system_warning()
                    if warn:
                        self.last_spoke = time.time()
                        self._speak_callback(warn)
            except Exception as e:
                print(f"[AWARENESS] Error: {e}")
            time.sleep(5)

awareness = AwarenessEngine()
