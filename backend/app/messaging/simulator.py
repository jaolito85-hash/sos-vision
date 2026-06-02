"""Canal simulador para dev — não envia nada de verdade, só registra (log)."""
from .base import Channel

_outbox: list[dict] = []  # inspecionável em /webhook/outbox


class SimulatorChannel(Channel):
    name = "simulator"

    async def send_text(self, to: str, text: str) -> None:
        _outbox.append({"to": to, "type": "text", "text": text})
        print(f"[SIM →{to}] {text}")

    async def send_buttons(self, to: str, text: str, buttons: list[str]) -> None:
        _outbox.append({"to": to, "type": "buttons", "text": text, "buttons": buttons})
        print(f"[SIM →{to}] {text} {buttons}")


def outbox() -> list[dict]:
    return _outbox
