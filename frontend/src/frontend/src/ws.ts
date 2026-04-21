export function createSocket(url: string) {
  let ws: WebSocket | null = null;
  let handlers: ((msg: any) => void)[] = [];
  function connect() {
    ws = new WebSocket(url);
    ws.onopen = () => console.log("[ws] connected");
    ws.onmessage = (e) => handlers.forEach(h => h(JSON.parse(e.data)));
    ws.onclose = () => setTimeout(connect, 3000);
  }
  connect();
  return {
    send(data: any) { if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(data)); },
    onMessage(h: (msg: any) => void) { handlers.push(h); },
    close() { ws?.close(); }
  };
}
