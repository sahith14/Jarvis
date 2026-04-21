"use client";

import { useEffect, useState, useRef } from "react";
import { JarvisWebSocket } from "@/lib/websocket";
import { VoiceController } from "@/lib/voice";
import type { AIResponse, PendingEdit } from "@/lib/types";
import ActionLog from "./ActionLog";
import CodeApprovalPanel from "./CodeApprovalPanel";

export default function VoiceInterface() {
  const [status, setStatus] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [pendingEdit, setPendingEdit] = useState<PendingEdit | null>(null);
  const [isAwake, setIsAwake] = useState(false);
  const wsRef = useRef<JarvisWebSocket | null>(null);
  const voiceRef = useRef<VoiceController | null>(null);
  const synth = typeof window !== "undefined" ? window.speechSynthesis : null;

  useEffect(() => {
    const ws = new JarvisWebSocket("ws://localhost:8000/ws/voice");
    wsRef.current = ws;
    ws.connect();

    ws.onMessage((msg) => {
      if (msg.type === "response") {
        const data = msg.data as AIResponse;
        if (data.action === "chat" || data.message) {
          const responseText = data.message || "Done.";
          setMessages((prev) => [...prev, { role: "jarvis", content: responseText }]);
          speak(responseText);
        } else {
          const actionMsg = data.message || `Executed ${data.action}`;
          setMessages((prev) => [...prev, { role: "jarvis", content: actionMsg }]);
          speak(actionMsg);
        }
        setStatus("idle");
      } else if (msg.type === "propose_edit") {
        setPendingEdit({
          path: msg.path,
          oldContent: msg.old_content,
          newContent: msg.new_content,
          diff: msg.diff,
        });
        setStatus("idle");
      } else if (msg.type === "file_content") {
        setMessages((prev) => [...prev, { role: "system", content: `File read: ${msg.path}` }]);
      }
    });

    const voice = new VoiceController(
      (text) => {
        setMessages((prev) => [...prev, { role: "user", content: text }]);
        setStatus("thinking");
        ws.send({ type: "transcript", text });
      },
      () => {
        setIsAwake(true);
        setStatus("listening");
        speak("Yes sir?");
      },
      (err) => setMessages((prev) => [...prev, { role: "system", content: `Error: ${err}` }])
    );
    voiceRef.current = voice;
    voice.start();

    return () => {
      voice.stop();
      ws.disconnect();
    };
  }, []);

  const speak = (text: string) => {
    if (!synth) return;
    setStatus("speaking");
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-GB";
    utterance.onend = () => {
      setStatus(isAwake ? "listening" : "idle");
    };
    synth.cancel();
    synth.speak(utterance);
  };

  const handleApproveEdit = async () => {
    if (!pendingEdit) return;
    const res = await fetch(
      `/api/apply-patch?path=${encodeURIComponent(pendingEdit.path)}&content=${encodeURIComponent(pendingEdit.newContent)}`,
      { method: "POST" }
    );
    const data = await res.json();
    setMessages((prev) => [...prev, { role: "system", content: data.message }]);
    setPendingEdit(null);
    speak(data.message);
  };

  const handleRejectEdit = () => {
    setPendingEdit(null);
    speak("Edit rejected, sir.");
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-blue-400">JARVIS</h1>
          <div className="flex items-center gap-2">
            <span className={`h-3 w-3 rounded-full ${status === "listening" ? "bg-green-500 animate-pulse" : "bg-gray-500"}`} />
            <span className="text-sm text-gray-400">{status}</span>
          </div>
        </div>

        <ActionLog messages={messages} />

        {pendingEdit && (
          <CodeApprovalPanel
            edit={pendingEdit}
            onApprove={handleApproveEdit}
            onReject={handleRejectEdit}
          />
        )}

        <div className="mt-4 text-center text-gray-500 text-sm">
          {isAwake ? "Listening for commands..." : 'Say "JARVIS" to wake'}
        </div>
      </div>
    </div>
  );
}
