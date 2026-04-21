import { createOrb, type OrbState } from "./orb";
import { createVoiceInput } from "./voice";
import { createSocket } from "./ws";

type State = "idle" | "listening" | "thinking" | "speaking";
let currentState: State = "idle";
let isAwake = false;
let currentUtterance: SpeechSynthesisUtterance | null = null;

const statusEl = document.getElementById("status-text")!;
const micStatusEl = document.getElementById("mic-status")!;
const canvas = document.getElementById("orb-canvas") as HTMLCanvasElement;
const orb = createOrb(canvas);

const WS_URL = "ws://localhost:8340/ws/voice";
const socket = createSocket(WS_URL);

function updateMicStatus(active: boolean) {
    micStatusEl.textContent = active ? "🎤 LISTENING" : "🎤 READY";
    micStatusEl.style.color = active ? "#0ea5e9" : "rgba(14, 165, 233, 0.3)";
}

function transition(newState: State) {
    if (newState === currentState) return;
    currentState = newState;
    orb.setState(newState as OrbState);
    const labels: Record<State, string> = { idle: "", listening: "listening...", thinking: "thinking...", speaking: "" };
    statusEl.textContent = labels[newState];
    if (newState === "speaking") {
        voiceInput.pause();
        updateMicStatus(false);
    } else if (newState === "listening" && isAwake) {
        voiceInput.resume();
        updateMicStatus(true);
    } else if (newState === "idle") {
        updateMicStatus(false);
    }
}

function speak(text: string) {
    if (currentUtterance) window.speechSynthesis.cancel();
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.rate = 0.95;
    currentUtterance.lang = "en-GB";
    currentUtterance.onend = () => {
        currentUtterance = null;
        // 800ms buffer to prevent mic from catching speaker echo
        setTimeout(() => {
            transition(isAwake ? "listening" : "idle");
        }, 800);
    };
    window.speechSynthesis.speak(currentUtterance);
}

const voiceInput = createVoiceInput(
    (text: string) => {
        if (!isAwake && text.toLowerCase().includes("jarvis")) {
            isAwake = true;
            transition("listening");
            speak("Yes sir?");
            return;
        }
        if (isAwake && text.trim()) {
            transition("thinking");
            socket.send({ type: "transcript", text, isFinal: true });
        }
    },
    (errMsg: string) => {
        console.error("[mic error]", errMsg);
        updateMicStatus(false);
    }
);

socket.onMessage((msg) => {
    if (msg.type === "audio" && msg.text) {
        transition("speaking");
        speak(msg.text);
    } else if (msg.type === "status") {
        if (msg.state === "idle") transition(isAwake ? "listening" : "idle");
        else if (msg.state === "thinking") transition("thinking");
    }
});

voiceInput.start();
transition("idle");

canvas.addEventListener("click", () => {
    if (!isAwake) {
        isAwake = true;
        transition("listening");
        speak("Yes sir?");
    }
});

