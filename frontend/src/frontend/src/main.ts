import { createOrb } from "./orb";
import { createVoiceInput, speak } from "./voice";
import { createSocket } from "./ws";

const statusEl = document.getElementById("status-text")!;
const canvas = document.getElementById("orb-canvas") as HTMLCanvasElement;
const orb = createOrb(canvas);

const WS_URL = "ws://localhost:8001/ws/voice";
const socket = createSocket(WS_URL);

let isAwake = false;
let currentUtterance: SpeechSynthesisUtterance | null = null;
let state: "idle" | "listening" | "thinking" | "speaking" = "idle";

function setState(newState: typeof state) {
  state = newState;
  orb.setState(newState);
  statusEl.textContent = newState === "idle" ? "" : newState + "...";
}

const voice = createVoiceInput(
  (text) => {
    console.log("[voice]", text);
    if (!isAwake && text.toLowerCase().includes("jarvis")) {
      isAwake = true;
      setState("listening");
      speak("Yes sir?");
      return;
    }
    if (isAwake && text.trim()) {
      setState("thinking");
      socket.send({ type: "transcript", text, isFinal: true });
    }
  },
  (err) => console.error("[voice error]", err)
);
voice.start();

socket.onMessage((msg) => {
  if (msg.type === "audio" && msg.text) {
    setState("speaking");
    if (currentUtterance) window.speechSynthesis.cancel();
    currentUtterance = speak(msg.text);
    currentUtterance.onend = () => {
      setState(isAwake ? "listening" : "idle");
      currentUtterance = null;
    };
  } else if (msg.type === "status") {
    if (msg.state === "idle") setState(isAwake ? "listening" : "idle");
    else if (msg.state === "thinking") setState("thinking");
  }
});

document.getElementById("btn-mute")?.addEventListener("click", () => {
  isAwake = false;
  setState("idle");
  if (currentUtterance) window.speechSynthesis.cancel();
});
