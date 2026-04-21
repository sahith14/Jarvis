import sys
import os, subprocess, threading, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class AgentInfo:
    name: str
    script: str
    description: str
    process: Optional[subprocess.Popen] = field(default=None, repr=False)
    status: str = "stopped"
    started_at: float = 0.0
    restart_count: int = 0
    auto_restart: bool = True
    max_restarts: int = 3

class AgentManager:
    def __init__(self):
        self.agents = {}
        self._monitor_thread = None
        self._running = False
        self._register_defaults()
    def _register_defaults(self):
        self.register_agent("whatsapp", "whatsapp_agent.py", "WhatsApp auto-reply agent", auto_restart=False)
    def register_agent(self, name, script, description="", auto_restart=True):
        self.agents[name.lower()] = AgentInfo(name=name.lower(), script=script, description=description, auto_restart=auto_restart)
    def start_agent(self, name):
        name = name.lower()
        agent = self.agents.get(name)
        if not agent: return f"Unknown agent '{name}'."
        if agent.status == "running" and agent.process and agent.process.poll() is None: return f"{name} already running."
        script_path = Path(__file__).parent / agent.script
        if not script_path.exists():
            print(f"[AGENT ERROR] Script not found: {agent.script}")
            return f"Script not found: {agent.script}"
        try:
            agent.status = "starting"
            agent.process = subprocess.Popen(["python", str(script_path)], cwd=Path(__file__).parent, creationflags=0x08000000)
            agent.status = "running"
            agent.started_at = time.time()
            agent.restart_count = 0
            self._ensure_monitor()
            return f"{name} agent started."
        except Exception as e: return f"Failed: {e}"
    def stop_agent(self, name):
        name = name.lower()
        agent = self.agents.get(name)
        if not agent or agent.status != "running": return f"{name} not running."
        agent.auto_restart = False
        agent.process.terminate()
        try: agent.process.wait(timeout=5)
        except: agent.process.kill()
        agent.status = "stopped"
        agent.process = None
        return f"{name} stopped."
    def list_agents(self):
        if not self.agents: return "No agents."
        lines = [f"  [{a.status.upper()}] {n}: {a.description}" for n,a in self.agents.items()]
        return "\n".join(lines)
    def _ensure_monitor(self):
        if self._running: return
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    def _monitor_loop(self):
        while self._running:
            for name, agent in self.agents.items():
                if agent.status == "running" and agent.process and agent.process.poll() is not None:
                    agent.status = "error"
                    if agent.auto_restart and agent.restart_count < agent.max_restarts:
                        agent.restart_count += 1
                        time.sleep(2)
                        self.start_agent(name)
            time.sleep(15)
    def shutdown_all(self):
        self._running = False
        for name in list(self.agents.keys()):
            if self.agents[name].status == "running":
                self.stop_agent(name)

agent_manager = AgentManager()
