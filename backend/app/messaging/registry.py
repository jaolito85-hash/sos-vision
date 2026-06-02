"""Seleciona o canal ativo conforme config, com fallback p/ simulador."""
from .base import Channel
from .simulator import SimulatorChannel
from .evolution import EvolutionChannel
from .whatsapp_cloud import WhatsAppCloudChannel
from ..config import settings

_channel: Channel | None = None


def get_channel() -> Channel:
    global _channel
    if _channel is None:
        canal = settings.MESSAGING_CHANNEL
        if canal == "cloud" and settings.WHATSAPP_TOKEN:
            _channel = WhatsAppCloudChannel()
        elif canal == "evolution" and settings.EVOLUTION_URL:
            _channel = EvolutionChannel()
        else:
            _channel = SimulatorChannel()
    return _channel
