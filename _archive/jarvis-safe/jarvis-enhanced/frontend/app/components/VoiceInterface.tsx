"use client";
import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { JarvisWebSocket } from "@/lib/websocket";
import { VoiceController } from "@/lib/voice";
import type { AIResponse, PendingEdit } from "@/lib/types";
import ActionLog from "./ActionLog";
import CodeApprovalPanel from "./CodeApprovalPanel";

export default function VoiceInterface() {
  const [status, setStatus] = useState<"idle"|"listening"|"thinking"|"speaking">("idle");
  const [messages, setMessages] = useState<{role:string;content:string}[]>([]);
  const [pendingEdit, setPendingEdit] = useState<PendingEdit|null>(null);
  const [isAwake, setIsAwake] = useState(false);
  const [volume, setVolume] = useState(0);
  const wsRef = useRef<JarvisWebSocket|null>(null);
  const voiceRef = useRef<VoiceController|null>(null);
  const synth = typeof window !== "undefined" ? window.speechSynthesis : null;
  const audioContext = useRef<AudioContext|null>(null);

  useEffect(() => {
    const ws = new JarvisWebSocket("ws://localhost:8000/ws/voice");
    wsRef.current = ws; ws.connect();
    ws.onMessage((msg) => {
      if (msg.type === "response") {
        const data = msg.data as AIResponse;
        const responseText = data.message || (data.action === "chat" ? "Done." : `Executed ${data.action}`);
        setMessages(p => [...p, {role:"jarvis", content:responseText}]);
        speak(responseText);
        setStatus("idle");
      } else if (msg.type === "propose_edit") {
        setPendingEdit({
          path: msg.path, oldContent: msg.old_content, newContent: msg.new_content,
          diff: msg.diff, dangerLevel: msg.danger_level, warnings: msg.warnings
        });
        setStatus("idle");
      } else if (msg.type === "file_content") {
        setMessages(p => [...p, {role:"system", content:`File read: ${msg.path}`}]);
      }
    });

    const voice = new VoiceController(
      (text) => { setMessages(p => [...p, {role:"user", content:text}]); setStatus("thinking"); ws.send({type:"transcript", text}); },
      () => { setIsAwake(true); setStatus("listening"); speak("Yes sir?"); },
      (err) => setMessages(p => [...p, {role:"system", content:`Error: ${err}`}])
    );
    voiceRef.current = voice; voice.start();

    // Audio visualizer setup
    navigator.mediaDevices.getUserMedia({audio:true}).then(stream => {
      const ctx = new AudioContext(); audioContext.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser(); analyser.fftSize = 256;
      source.connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      const updateVolume = () => {
        analyser.getByteFrequencyData(data);
        const avg = data.reduce((a,b)=>a+b,0)/data.length;
        setVolume(avg/255);
        requestAnimationFrame(updateVolume);
      };
      updateVolume();
    }).catch(()=>{});

    return () => { voice.stop(); ws.disconnect(); };
  }, []);

  const speak = (text: string) => {
    if (!synth) return;
    setStatus("speaking");
    const u = new SpeechSynthesisUtterance(text); u.lang = "en-GB";
    u.onend = () => setStatus(isAwake ? "listening" : "idle");
    synth.cancel(); synth.speak(u);
  };

  const approveEdit = async () => {
    if (!pendingEdit) return;
    const res = await fetch(`/api/apply-patch?path=${encodeURIComponent(pendingEdit.path)}&content=${encodeURIComponent(pendingEdit.newContent)}`, {method:"POST"});
    const data = await res.json();
    setMessages(p => [...p, {role:"system", content:data.message}]);
    setPendingEdit(null); speak(data.message);
  };

  return (
    <div className="min-h-screen p-6 flex flex-col items-center">
      <div className="w-full max-w-5xl">
        <div className="flex justify-between items-center mb-6">
          <motion.h1 animate={{textShadow: volume>0.1 ? "0 0 30px #0ea5e9" : "0 0 10px #0ea5e9"}}
            className="text-4xl font-bold text-blue-400 glow-text tracking-wider">JARVIS</motion.h1>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <div className={`h-3 w-3 rounded-full ${status==="listening"?"bg-green-500 animate-pulse":status==="thinking"?"bg-yellow-500":status==="speaking"?"bg-blue-500":"bg-gray-500"}`}/>
              <span className="text-sm uppercase tracking-wider text-gray-400">{status}</span>
            </div>
            {/* Orb visualization */}
            <motion.div animate={{scale: 1 + volume*0.5, opacity: 0.5 + volume*0.5}}
              className="w-12 h-12 rounded-full bg-blue-500/20 border border-blue-400/50"/>
          </div>
        </div>

        <ActionLog messages={messages} />

        <AnimatePresence>
          {pendingEdit && (
            <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} exit={{opacity:0,y:20}}>
              <CodeApprovalPanel edit={pendingEdit} onApprove={approveEdit} onReject={()=>{setPendingEdit(null);speak("Edit rejected.");}} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mt-6 text-center">
          <p className="text-gray-400 text-sm">{isAwake ? "Listening..." : "Say \"JARVIS\" to wake"}</p>
        </div>
      </div>
    </div>
  );
}
