"""Interface única de mensageria (§6.3) — canal plugável.

O bot core não sabe qual canal está embaixo. Trocar Evolution/Cloud/SMS/satélite
não exige reescrever o fluxo. Cada canal implementa Channel.
"""
from abc import ABC, abstractmethod


class Channel(ABC):
    name: str

    @abstractmethod
    async def send_text(self, to: str, text: str) -> None: ...

    @abstractmethod
    async def send_buttons(self, to: str, text: str, buttons: list[str]) -> None: ...

    async def send_template(self, to: str, template: str, params: dict | None = None) -> None:
        # Default: degrada para texto simples.
        await self.send_text(to, template)
