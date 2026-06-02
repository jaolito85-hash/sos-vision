"""Realtime via WebSocket + ponte Redis pub/sub.

O backend mantém as conexões WS da Sala de Comando. Mudanças de estado
(novo chamado, despacho, ponto GPS) são publicadas no canal Redis "events";
uma task de fundo assina o canal e repassa a todos os WS conectados.
O worker também publica nesse canal. Em produção, troca-se por Supabase
postgres_changes (ver 001_init.sql).
"""
import asyncio
import json
import redis.asyncio as aioredis
from fastapi import WebSocket
from .config import settings

CHANNEL = "events"


class Hub:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()
        self._redis: aioredis.Redis | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        if self._redis:
            await self._redis.aclose()

    async def _listen(self) -> None:
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        async for msg in pubsub.listen():
            if msg.get("type") != "message":
                continue
            await self._fanout(msg["data"])

    async def _fanout(self, data: str) -> None:
        dead = []
        for ws in self.clients:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def unregister(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def publish(self, event_type: str, payload: dict) -> None:
        """Publica um evento para todas as Salas conectadas."""
        if self._redis is None:
            return
        await self._redis.publish(CHANNEL, json.dumps({"type": event_type, "data": payload}, default=str))


hub = Hub()
