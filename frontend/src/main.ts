import { createOrb, type OrbState } from "./orb";
import { createVoiceInput, createAudioPlayer } from "./voice";
import { createSocket } from "./ws";
import { openSettings, checkFirstTimeSetup } from "./settings";
import "./style.css";

type State = "idle" | "listening" | "thinking" | "speaking";
let currentState: State = "idle";
let isMuted = false;
let isAwake = false;
let currentUtterance: SpeechSynthesisUtterance | null = null;
let inactivityTimer: any = null;
let useTextInput = false;

const statusEl = document.getElementById("status-text")!;
const canvas = document.getElementById("orb-canvas") as HTMLCanvasElement;
const orb = createOrb(canvas);
const WS_URL = "ws://localhost:8001/ws/voice";
const socket = createSocket(WS_URL);
const audioPlayer = createAudioPlayer();
orb.setAnalyser(audioPlayer.getAnalyser());

function transition(newState: State) {
  if (newState === currentState) return;
  currentState = newState;
  orb.setState(newState as OrbState);
  const labels = { idle: "", listening: "listening...", thinking: "thinking...", speaking: "" };
  statusEl.textContent = labels[newState];
  if (newState === "speaking") voiceInput.pause();
  else if (newState === "listening" && isAwake && !isMuted && !useTextInput) voiceInput.resume();
}

function resetInactivityTimer() {
  if (inactivityTimer) clearTimeout(inactivityTimer);
  if (isAwake) {
    inactivityTimer = setTimeout(() => {
      if (isAwake && currentState === "listening") {
        isAwake = false;
        transition("idle");
      }
    }, 300000);
  }
}

function interruptAndListen() {
  if (currentUtterance) { window.speechSynthesis.cancel(); currentUtterance = null; }
  isAwake = true;
  transition("listening");
  pendingText = "";
  if (speechTimeout) clearTimeout(speechTimeout);
  resetInactivityTimer();
}

function addInterruptButton() {
  const controls = document.getElementById("controls");
  if (controls && !document.getElementById("btn-interrupt")) {
    const btn = document.createElement("button");
    btn.id = "btn-interrupt";
    btn.innerHTML = "⏹️";
    btn.title = "Interrupt JARVIS";
    btn.style.marginRight = "8px";
    btn.onclick = (e) => { e.stopPropagation(); interruptAndListen(); };
    controls.insertBefore(btn, controls.firstChild);
  }
}

function showTextFallback() {
  if (document.getElementById("text-fallback")) return;
  const div = document.createElement("div");
  div.id = "text-fallback";
  div.style.cssText = "position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%); background: #1a1a2e; border: 1px solid #0ea5e9; border-radius: 8px; padding: 8px 12px; z-index: 100; display: flex; gap: 8px;";
  const input = document.createElement("input");
  input.type = "text";
  input.id = "cmd-input";
  input.placeholder = "Type command (microphone not available)...";
  input.style.cssText = "background: transparent; border: none; color: white; outline: none; width: 300px;";
  const btn = document.createElement("button");
  btn.textContent = "Send";
  btn.style.cssText = "background: #0ea5e9; border: none; border-radius: 4px; padding: 4px 12px; cursor: pointer;";
  btn.onclick = () => { const txt = input.value.trim(); if (txt) { input.value = ""; handleUserText(txt); } };
  input.onkeypress = (e) => { if (e.key === "Enter") btn.click(); };
  div.appendChild(input); div.appendChild(btn);
  document.body.appendChild(div);
  useTextInput = true;
}

function handleUserText(text: string) {
  if (currentState === "speaking") {
    if (text.toLowerCase().includes("jarvis") || text.toLowerCase().includes("stop")) interruptAndListen();
    return;
  }
  if (!isAwake && text.toLowerCase().includes("jarvis")) {
    isAwake = true;
    transition("listening");
    resetInactivityTimer();
    return;
  }
  if (isAwake && currentState === "listening" && text.trim() && !text.toLowerCase().includes("jarvis")) {
    if (speechTimeout) clearTimeout(speechTimeout);
    pendingText += " " + text;
    speechTimeout = setTimeout(() => {
      if (pendingText.trim()) {
        socket.send({ type: "transcript", text: pendingText.trim(), isFinal: true });
        transition("thinking");
        pendingText = "";
      }
    }, 500);
  }
}

let speechTimeout: any = null;
let pendingText = "";

const voiceInput = createVoiceInput(
  (text) => handleUserText(text),
  (errMsg) => { console.error("[mic error]", errMsg); showTextFallback(); }
);

socket.onMessage((msg) => {
  if (msg.type === "audio" && msg.text) {
    transition("speaking");
    resetInactivityTimer();
    currentUtterance = new SpeechSynthesisUtterance(msg.text);
    currentUtterance.rate = 0.9;
    currentUtterance.lang = "en-GB";
    currentUtterance.onend = () => {
      currentUtterance = null;
      if (isAwake && !isMuted && !useTextInput) transition("listening");
      else transition("idle");
    };
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(currentUtterance);
  }
});

setTimeout(() => {
  voiceInput.start();
  transition("idle");
  addInterruptButton();
}, 1000);

document.getElementById("btn-mute")?.addEventListener("click", () => {
  isMuted = !isMuted;
  if (isMuted) {
    voiceInput.pause();
    transition("idle");
    isAwake = false;
    if (currentUtterance) window.speechSynthesis.cancel();
  } else {
    voiceInput.resume();
    if (isAwake) transition("listening");
  }
});

const orbCanvas = document.getElementById("orb-canvas");
if (orbCanvas) {
  orbCanvas.addEventListener("click", () => {
    if (!isAwake) {
      isAwake = true;
      transition("listening");
      resetInactivityTimer();
    }
  });
}

setTimeout(() => checkFirstTimeSetup(), 2000);
