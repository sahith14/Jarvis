# intelligence.py — JARVIS Phase 2 Intelligence Engine
import time
try:
    from controller import get_active_window_title
except ImportError:
    def get_active_window_title():
        return "unknown"

class IntelligenceEngine:
    def __init__(self):
        self.user_state = "idle"
        self.last_state_change = time.time()
        self.last_window_title = ""
        self.window_switch_times = []
        self.active_contexts = {
            "coding": ["code","vscode","pycharm","terminal","powershell","cmd"],
            "video_editing": ["premiere","davinci","resolve"],
            "gaming": ["steam","valorant","minecraft"],
            "reading": ["chrome","edge","firefox","pdf","notion"],
            "media": ["spotify","youtube","vlc"]
        }

    def get_priority(self, context, message=None):
        if message and any(k in message.lower() for k in ["urgent","emergency","now","critical","help","error","failed","crash"]):
            return "high"
        if context in ["video_editing","coding","gaming"]:
            return "low"
        if context == "communication":
            return "medium"
        return "low"

    def detect_user_state(self):
        current = get_active_window_title().lower()
        now = time.time()
        if current != self.last_window_title:
            self.window_switch_times.append(now)
            self.last_window_title = current
        self.window_switch_times = [t for t in self.window_switch_times if now - t < 60]
        ctx = "general"
        for c, kws in self.active_contexts.items():
            if any(k in current for k in kws):
                ctx = c
                break
        if len(self.window_switch_times) > 5:
            new_state = "active"
        elif ctx in ["coding","video_editing","gaming"] and len(self.window_switch_times) <= 2:
            new_state = "focused"
        else:
            new_state = "idle"
        if new_state != self.user_state:
            self.user_state = new_state
            self.last_state_change = now
        return self.user_state

    def should_suppress(self, priority):
        state = self.detect_user_state()
        if state == "focused":
            return priority != "high"
        if state == "active":
            return priority == "low"
        return False

intelligence = IntelligenceEngine()
