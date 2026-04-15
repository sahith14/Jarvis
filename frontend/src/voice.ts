export interface VoiceInput {
  start(): void;
  stop(): void;
  pause(): void;
  resume(): void;
  pauseForWakeWord(): void;
}

export interface AudioPlayer {
  enqueue(base64: string): Promise<void>;
  stop(): void;
  getAnalyser(): AnalyserNode;
  onFinished(cb: () => void): void;
}

export function createAudioPlayer(): AudioPlayer {
  let audioCtx: AudioContext | null = null;
  let analyser: AnalyserNode | null = null;
  let queue: AudioBuffer[] = [];
  let isPlaying = false;
  let currentSource: AudioBufferSourceNode | null = null;
  let finishedCallback: (() => void) | null = null;

  async function ensureAudioContext() {
    if (audioCtx) return;
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.connect(audioCtx.destination);
    if (audioCtx.state === "suspended") await audioCtx.resume();
  }

  async function playNext() {
    if (!audioCtx) return;
    if (queue.length === 0) {
      isPlaying = false;
      currentSource = null;
      finishedCallback?.();
      return;
    }
    isPlaying = true;
    const buffer = queue.shift()!;
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(analyser!);
    currentSource = source;
    source.onended = () => { if (currentSource === source) playNext(); };
    source.start();
  }

  return {
    async enqueue(base64: string) {
      await ensureAudioContext();
      if (audioCtx!.state === "suspended") await audioCtx!.resume();
      try {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        const audioBuffer = await audioCtx!.decodeAudioData(bytes.buffer);
        queue.push(audioBuffer);
        if (!isPlaying) playNext();
      } catch (err) {
        console.error("[audio] decode error:", err);
        if (!isPlaying && queue.length > 0) playNext();
      }
    },
    stop() {
      queue = [];
      if (currentSource) { try { currentSource.stop(); } catch {} currentSource = null; }
      isPlaying = false;
    },
    getAnalyser() { return analyser || { connect: () => {}, disconnect: () => {} } as AnalyserNode; },
    onFinished(cb: () => void) { finishedCallback = cb; },
  };
}

export function createVoiceInput(
  onTranscript: (text: string) => void,
  onError: (msg: string) => void
): VoiceInput {
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  let recognition: any = null;
  let wakeWordRecognition: any = null;
  let isActive = false;
  let isPaused = false;
  let isStarting = false;
  let mediaStream: MediaStream | null = null;

  if (!SR) {
    onError("Speech recognition not supported");
    return { start() {}, stop() {}, pause() {}, resume() {}, pauseForWakeWord() {} };
  }

  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onresult = (event: any) => {
    if (isPaused) return;
    let finalText = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) finalText += event.results[i][0].transcript;
    }
    if (finalText && isActive && !isPaused) {
      console.log("[mic]", finalText);
      onTranscript(finalText);
    }
  };

  recognition.onerror = (event: any) => {
    if (event.error === "not-allowed") onError("Microphone access denied");
    else if (event.error !== "no-speech") console.warn("[mic] error:", event.error);
  };

  recognition.onend = () => {
    if (isActive && !isPaused && !isStarting && mediaStream) {
      try { recognition.start(); } catch {}
    }
  };

  wakeWordRecognition = new SR();
  wakeWordRecognition.continuous = true;
  wakeWordRecognition.interimResults = true;
  wakeWordRecognition.lang = "en-US";
  wakeWordRecognition.onresult = (event: any) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        const text = event.results[i][0].transcript.toLowerCase();
        if (text.includes("jarvis")) {
          console.log("[wake-word] JARVIS detected");
          onTranscript(text);
        }
      }
    }
  };
  wakeWordRecognition.onend = () => {
    if (isActive && mediaStream) try { wakeWordRecognition.start(); } catch {}
  };

  async function start() {
    if (isStarting) return;
    isStarting = true;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStream = stream;
      try { recognition.start(); } catch {}
      try { wakeWordRecognition.start(); } catch {}
      isActive = true;
      isPaused = false;
      console.log("[mic] started");
    } catch (err: any) {
      console.error("[mic] error:", err);
      if (err.name === "NotFoundError") onError("No microphone found. Please connect a microphone.");
      else if (err.name === "NotAllowedError") onError("Microphone access denied.");
      else onError(`Microphone error: ${err.message}`);
      isActive = false;
    } finally {
      isStarting = false;
    }
  }

  function stop() {
    if (recognition) try { recognition.stop(); } catch {}
    if (wakeWordRecognition) try { wakeWordRecognition.stop(); } catch {}
    if (mediaStream) mediaStream.getTracks().forEach(t => t.stop());
    isActive = false;
  }

  function pause() {
    if (recognition) try { recognition.stop(); } catch {}
    isPaused = true;
  }
  function resume() {
    if (recognition && isActive && mediaStream) try { recognition.start(); } catch {}
    isPaused = false;
  }
  function pauseForWakeWord() {
    if (recognition) try { recognition.stop(); } catch {}
    isPaused = true;
  }

  return { start, stop, pause, resume, pauseForWakeWord };
}
