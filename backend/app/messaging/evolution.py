"""Canal Evolution API (WhatsApp não-oficial) — usado no MVP.

Docs: https://doc.evolution-api.com  (API v2)
Envio: POST {base}/message/sendText/{instance}  header `apikey`  body {number, text}.

⚠️ DECISÃO DE PRODUTO: Evolution é o canal do MVP (rápido/barato p/ demo e piloto).
Há risco de ban e não há SLA. Pós-MVP, migrar para a WhatsApp Cloud API oficial (Meta)
— ver `whatsapp_cloud.py`, já implementado. A troca é só de MESSAGING_CHANNEL=cloud,
sem mexer no fluxo (camada de mensageria plugável, §6.3 do blueprint).
"""
import httpx
from .base import Channel
from ..config import settings


class EvolutionChannel(Channel):
    name = "evolution"

    def __init__(self) -> None:
        self.base = settings.EVOLUTION_URL.rstrip("/")
        self.key = settings.EVOLUTION_INSTANCE and settings.EVOLUTION_KEY
        self.instance = settings.EVOLUTION_INSTANCE

    async def _post(self, path: str, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{self.base}{path}",
                headers={"apikey": settings.EVOLUTION_KEY, "Content-Type": "application/json"},
                json=payload,
            )
            r.raise_for_status()

    async def send_text(self, to: str, text: str) -> None:
        await self._post(f"/message/sendText/{self.instance}", {"number": to, "text": text})

    async def send_buttons(self, to: str, text: str, buttons: list[str]) -> None:
        # Botões nativos via Evolution são instáveis; o texto da triagem já traz as
        # opções (1/2/3), então enviamos como texto simples — mais robusto.
        await self.send_text(to, text)

    async def send_template(self, to: str, template: str, params: dict | None = None) -> None:
        await self.send_text(to, template)
