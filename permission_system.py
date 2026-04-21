import time, uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

SAFE_COMMANDS = ["open","play","search","volume","screenshot","weather","what time","remember","recall","switch to","focus","minimize","maximize","type","copy","clipboard","system stats","start my setup","awareness","agent status"]
RESTRICTED_COMMANDS = ["shutdown","restart","delete","remove","taskkill","close everything","lock","run command","stop whatsapp"]
DANGEROUS_COMMANDS = ["format c:","rm -rf","reg delete"]

CONFIRMATION_MESSAGES = {
    "shutdown": "Shut down PC in 5 seconds. Proceed?",
    "restart": "Restart PC. Unsaved work will be lost. Proceed?",
    "delete": "Permanently delete files. Sure?",
    "taskkill": "Force-close processes. Proceed?",
    "close everything": "Close all windows. Proceed?",
    "lock": "Lock screen. Proceed?",
    "run command": "Execute system command. Proceed?",
    "stop whatsapp": "Stop WhatsApp agent. Proceed?",
}

@dataclass
class PendingAction:
    action_id: str
    command_text: str
    confirmation_message: str
    execute_fn: Optional[Callable] = None
    execute_args: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    timeout: float = 30.0
    @property
    def expired(self): return time.time() - self.created_at > self.timeout

class PermissionManager:
    def __init__(self): self._pending = {}
    def classify_command(self, text):
        t = text.lower()
        for p in DANGEROUS_COMMANDS:
            if p in t: return "dangerous"
        for p in RESTRICTED_COMMANDS:
            if t.startswith(p) or f" {p}" in f" {t}": return "restricted"
        return "safe"
    def get_confirmation_message(self, text):
        for t, msg in CONFIRMATION_MESSAGES.items():
            if t in text.lower(): return msg
        return "This action could affect your system. Proceed?"
    def create_pending_action(self, command_text, execute_fn=None, execute_args=None):
        self._cleanup_expired()
        aid = str(uuid.uuid4())[:8]
        action = PendingAction(action_id=aid, command_text=command_text, confirmation_message=self.get_confirmation_message(command_text), execute_fn=execute_fn, execute_args=execute_args or {})
        self._pending[aid] = action
        return action
    def get_latest_pending(self):
        self._cleanup_expired()
        return max(self._pending.values(), key=lambda a: a.created_at) if self._pending else None
    def confirm_action(self, action_id=None):
        self._cleanup_expired()
        if action_id and action_id in self._pending: return self._pending.pop(action_id)
        if not action_id:
            a = self.get_latest_pending()
            if a: self._pending.pop(a.action_id, None); return a
        return None
    def deny_action(self, action_id=None):
        return self.confirm_action(action_id)
    def has_pending(self):
        self._cleanup_expired()
        return len(self._pending) > 0
    def _cleanup_expired(self):
        expired = [aid for aid, a in self._pending.items() if a.expired]
        for aid in expired: del self._pending[aid]

permissions = PermissionManager()
