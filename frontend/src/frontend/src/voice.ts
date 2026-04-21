export function createVoiceInput(
  onTranscript: (text: string) => void,
  onError: (err: string) => void
) {
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SR) { onError("Speech recognition not supported"); return { start() {}, stop() {} }; }
  const recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";
  recognition.onresult = (e: any) => {
    let final = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript;
    }
    if (final) onTranscript(final);
  };
  recognition.onerror = (e: any) => { if (e.error !== "no-speech") onError(e.error); };
  recognition.onend = () => { recognition.start(); };
  return {
    start: () => recognition.start(),
    stop: () => recognition.stop(),
  };
}

export function speak(text: string) {
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-GB";
  u.rate = 0.95;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
  return u;
}
