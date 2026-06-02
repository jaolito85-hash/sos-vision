"""WebSocket da Sala de Comando. Recebe eventos realtime do Hub."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..realtime import hub

router = APIRouter()


@router.websocket("/ws")
async def ws(websocket: WebSocket):
    await hub.register(websocket)
    try:
        while True:
            # Mantém a conexão viva; a Sala não envia comandos por aqui (só recebe).
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.unregister(websocket)
    except Exception:
        hub.unregister(websocket)
