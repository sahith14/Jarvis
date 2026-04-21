import json, time
from collections import deque
from datetime import datetime
from pathlib import Path

PROFILE_FILE = Path(__file__).parent / "user_profile.json"
DEFAULT_PROFILE = {
    "name": "", "preferences": {}, "patterns": {}, "relationships": {}, "custom_workflows": {}, "stats": {"total_commands":0,"favorite_commands":{},"last_active":""}
}

class UserProfile:
    def __init__(self):
        self.data = self._load()
    def _load(self):
        if PROFILE_FILE.exists():
            try: return {**DEFAULT_PROFILE, **json.load(open(PROFILE_FILE))}
            except: pass
        return DEFAULT_PROFILE.copy()
    def save(self): json.dump(self.data, open(PROFILE_FILE,"w"), indent=2)
    @property
    def name(self): return self.data.get("name","")
    @name.setter
    def name(self, v): self.data["name"] = v; self.save()
    def update(self, key, value):
        keys = key.split(".")
        t = self.data
        for k in keys[:-1]: t = t.setdefault(k, {})
        t[keys[-1]] = value
        self.save()
    def get_greeting(self):
        h = datetime.now().hour
        n = self.name
        s = f", {n}" if n else ""
        if 5<=h<12: return f"Good morning{s}."
        if 12<=h<17: return f"Good afternoon{s}."
        if 17<=h<21: return f"Good evening{s}."
        return f"Burning the midnight oil{s}?"
    def get_profile_summary(self):
        parts = [f"Name: {self.name}"] if self.name else []
        return "\n".join(parts) or "No profile."

class ContextEngine:
    def __init__(self, max_history=10):
        self.last_command = ""
        self.last_command_type = ""
        self.last_app = ""
        self.last_query = ""
        self.last_response = ""
        self.last_tool_called = ""
        self.last_tool_args = {}
        self.conversation_history = deque(maxlen=max_history)
    def record_exchange(self, user, resp, cmd_type="ai"):
        self.last_command = user
        self.last_command_type = cmd_type
        self.last_response = resp
        self.conversation_history.append({"user":user,"jarvis":resp,"time":time.time()})
    def record_tool_call(self, name, args):
        self.last_tool_called = name
        self.last_tool_args = args.copy()
    def record_app(self, app): self.last_app = app
    def record_query(self, q): self.last_query = q
    def is_continuation(self, text): return text.lower() in ("continue","do that again","repeat","again")
    def get_continuation_info(self):
        if not self.last_command: return None
        return {"command":self.last_command,"type":self.last_command_type,"tool":self.last_tool_called,"args":self.last_tool_args}
    def get_history_for_prompt(self):
        if not self.conversation_history: return ""
        lines = ["RECENT:"]
        for ex in list(self.conversation_history)[-5:]:
            lines.append(f"  User: {ex['user']}")
            lines.append(f"  Jarvis: {ex['jarvis'][:100]}")
        return "\n".join(lines)
    def get_context_summary(self):
        parts = []
        if self.last_app: parts.append(f"App: {self.last_app}")
        if self.last_query: parts.append(f"Query: {self.last_query}")
        if self.last_tool_called: parts.append(f"Action: {self.last_tool_called}")
        return " | ".join(parts)

class PersonalityEngine:
    def __init__(self): self.mood = "calm"
    def set_mood(self, mood): self.mood = mood if mood in ["calm","focused","playful"] else "calm"
    def get_personality_prompt(self):
        return "Be concise, confident, slightly witty. Address user by name."

profile = UserProfile()
context = ContextEngine()
personality = PersonalityEngine()
