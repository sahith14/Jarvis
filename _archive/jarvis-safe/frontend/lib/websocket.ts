export class JarvisWebSocket {
  private ws: WebSocket | null = null;
  private messageHandlers: ((msg: any) => void)[] = [];
  private reconnectTimer: NodeJS.Timeout | null = null;

  constructor(private url: string) {}

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => console.log('WebSocket connected');
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this.messageHandlers.forEach(h => h(msg));
    };
    this.ws.onclose = () => {
      console.log('WebSocket closed, reconnecting...');
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };
    this.ws.onerror = (err) => console.error('WebSocket error', err);
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  onMessage(handler: (msg: any) => void) {
    this.messageHandlers.push(handler);
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
  }
}
