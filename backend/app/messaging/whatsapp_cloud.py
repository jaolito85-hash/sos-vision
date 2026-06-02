"""Canal WhatsApp Cloud API (Meta Business) — produção.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
Envio via Graph API /{phone_id}/messages. Broadcast em massa exige TEMPLATES
aprovados (send_template). Mensagens interativas usam botões de reply.
"""
import httpx
from .base import Channel
from ..config import settings

GRAPH = "https://graph.facebook.com/v21.0"


class WhatsAppCloudChannel(Channel):
    name = "cloud"

    def __init__(self) -> None:
        self.phone_id = settings.WHATSAPP_PHONE_ID
        self.token = settings.WHATSAPP_TOKEN

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    async def _post(self, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{GRAPH}/{self.phone_id}/messages", headers=self._headers(), json=payload
            )
            r.raise_for_status()

    async def send_text(self, to: str, text: str) -> None:
        await self._post({
            "messaging_product": "whatsapp", "to": to, "type": "text",
            "text": {"body": text},
        })

    async def send_buttons(self, to: str, text: str, buttons: list[str]) -> None:
        await self._post({
            "messaging_product": "whatsapp", "to": to, "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {"buttons": [
                    {"type": "reply", "reply": {"id": f"btn_{i}", "title": b[:20]}}
                    for i, b in enumerate(buttons)
                ]},
            },
        })

    async def send_template(self, to: str, template: str, params: dict | None = None) -> None:
        # Broadcast em massa (Fase 2). Template precisa estar aprovado no Meta Business.
        await self._post({
            "messaging_product": "whatsapp", "to": to, "type": "template",
            "template": {"name": template, "language": {"code": "pt_BR"}},
        })
