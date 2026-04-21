export class JarvisWebSocket {
  private ws: WebSocket | null = null;
  private handlers: ((msg: any) => void)[] = [];
  constructor(private url: string) {}
  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => console.log('WS connected');
    this.ws.onmessage = (e) => this.handlers.forEach(h => h(JSON.parse(e.data)));
    this.ws.onclose = () => setTimeout(() => this.connect(), 3000);
  }
  send(data: any) { if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(data)); }
  onMessage(h: (msg: any) => void) { this.handlers.push(h); }
  disconnect() { this.ws?.close(); }
}
