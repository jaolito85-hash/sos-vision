const WS = (import.meta.env.VITE_API ?? "http://localhost:8000")
  .replace(/^http/, "ws") + "/ws";

export type RTEvent = { type: string; data: any };

/** Conecta ao WebSocket da Sala e reconecta automaticamente. */
export function connectRealtime(onEvent: (e: RTEvent) => void): () => void {
  let ws: WebSocket | null = null;
  let closed = false;
  let retry: number;

  function open() {
    ws = new WebSocket(WS);
    ws.onmessage = (m) => {
      try {
        onEvent(JSON.parse(m.data));
      } catch {
        /* ignora frames inválidos */
      }
    };
    ws.onclose = () => {
      if (!closed) retry = window.setTimeout(open, 2000);
    };
    ws.onerror = () => ws?.close();
  }
  open();

  return () => {
    closed = true;
    clearTimeout(retry);
    ws?.close();
  };
}
