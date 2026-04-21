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
    source.onended = () => {
      if (currentSource === source) playNext();
    };
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
      if (currentSource) {
        try { currentSource.stop(); } catch {}
        currentSource = null;
      }
      isPlaying = false;
    },
    getAnalyser() {
      if (!analyser) {
        // Dummy analyser that won't crash the orb
        return {
          getByteFrequencyData: () => {},
          connect: () => {},
          disconnect: () => {},
          frequencyBinCount: 0,
        } as unknown as AnalyserNode;
      }
      return analyser;
    },
    onFinished(cb: () => void) { finishedCallback = cb; },
  };
}

export function createVoiceInput(
  onTranscript: (text: string) => void,
  onError: (msg: string) => void
): VoiceInput {
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  let recognition: any = null;
  let isActive = false;
  let isPaused = false;
  let isStarted = false;

  if (!SR) {
    onError("Speech recognition not supported");
    return { start() {}, stop() {}, pause() {}, resume() {}, pauseForWakeWord() {} };
  }

  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onstart = () => { isStarted = true; };
  recognition.onend = () => {
    isStarted = false;
    if (isActive && !isPaused) {
      try {
        recognition.start();
      } catch (e) {
        console.error("[mic] restart failed:", e);
      }
    }
  };
  recognition.onresult = (event: any) => {
    if (isPaused) return;
    let finalText = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        finalText += event.results[i][0].transcript;
      }
    }
    if (finalText && isActive && !isPaused) {
      console.log("[mic]", finalText);
      onTranscript(finalText);
    }
  };

  recognition.onerror = (event: any) => {
    if (event.error === "not-allowed") {
      onError("Microphone access denied");
    } else if (event.error !== "no-speech") {
      console.warn("[mic] error:", event.error);
    }
  };


  async function start() {
    if (!recognition) return;
    if (isActive) return;
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!isStarted) recognition.start();
      isActive = true;
      isPaused = false;
      console.log("[mic] started");
    } catch (err) {
      onError("Could not access microphone");
    }
  }

  function stop() {
    if (recognition) {
      try { recognition.stop(); } catch {}
    }
    isActive = false;
  }

  function pause() {
    if (recognition) {
      try { recognition.stop(); } catch {}
    }
    isPaused = true;
    console.log("[mic] paused");
  }

  function resume() {
    if (!recognition) return;
    if (!isActive) return;
    if (!isPaused) return;
    try {
      if (!isStarted) recognition.start();
      console.log("[mic] resumed");
    } catch (e) {
      console.warn("[mic] resume failed", e);
    }
    isPaused = false;
  }

  function pauseForWakeWord() {
    pause();
  }

  return { start, stop, pause, resume, pauseForWakeWord };
}
