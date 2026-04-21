export class VoiceController {
  private recognition: any; private listening = false; private awake = false;
  constructor(
    private onTranscript: (text: string) => void,
    private onWake: () => void,
    private onError: (err: string) => void
  ) {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { onError('Speech recognition not supported'); return; }
    this.recognition = new SR();
    this.recognition.continuous = true; this.recognition.interimResults = true; this.recognition.lang = 'en-US';
    this.recognition.onresult = (e: any) => {
      let final = '', interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        e.results[i].isFinal ? final += t : interim += t;
      }
      const text = final || interim;
      if (text.toLowerCase().includes('jarvis')) {
        if (!this.awake) { this.awake = true; this.onWake(); }
        const cmd = text.replace(/jarvis/i, '').trim();
        if (cmd && final) this.onTranscript(cmd);
      } else if (this.awake && final) this.onTranscript(text);
    };
    this.recognition.onerror = (e: any) => { if (e.error !== 'no-speech') this.onError(e.error); };
    this.recognition.onend = () => { if (this.listening) this.recognition.start(); };
  }
  start() { this.listening = true; this.recognition.start(); }
  stop() { this.listening = false; this.recognition.stop(); }
  reset() { this.awake = false; }
}
