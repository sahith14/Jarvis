export class VoiceController {
  private recognition: any;
  private isListening = false;
  private wakeWordDetected = false;
  private onTranscript: (text: string) => void;
  private onWakeWord: () => void;

  constructor(
    onTranscript: (text: string) => void,
    onWakeWord: () => void,
    onError: (err: string) => void
  ) {
    this.onTranscript = onTranscript;
    this.onWakeWord = onWakeWord;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onError('Speech recognition not supported');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onresult = (event: any) => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      const text = final || interim;
      if (text.toLowerCase().includes('jarvis')) {
        if (!this.wakeWordDetected) {
          this.wakeWordDetected = true;
          this.onWakeWord();
        }
        const command = text.replace(/jarvis/i, '').trim();
        if (command && final) {
          this.onTranscript(command);
        }
      } else if (this.wakeWordDetected && final) {
        this.onTranscript(text);
      }
    };

    this.recognition.onerror = (event: any) => {
      if (event.error !== 'no-speech') {
        onError(event.error);
      }
    };

    this.recognition.onend = () => {
      if (this.isListening) {
        this.recognition.start();
      }
    };
  }

  start() {
    this.isListening = true;
    this.recognition.start();
  }

  stop() {
    this.isListening = false;
    this.recognition.stop();
  }

  resetWakeWord() {
    this.wakeWordDetected = false;
  }
}
