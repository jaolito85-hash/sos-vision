"""Triagem por IA (§5.5) com humano no loop.

Se ANTHROPIC_API_KEY estiver setada, usa um LLM barato p/ extrair gravidade e
contexto de texto livre. Caso contrário, cai num classificador heurístico por
palavras-chave. Sempre devolve um dict estruturado; a Sala decide.
"""
import json
import httpx
from ..config import settings

PALAVRAS_GRAVES = ["telhado", "afog", "criança", "crianca", "bebê", "bebe",
                   "idoso", "acamad", "não sei nadar", "preso", "subindo rápido",
                   "socorro", "morrer", "ferido", "sangue"]


def _heuristico(texto: str) -> dict:
    t = (texto or "").lower()
    gravidade = 3
    contexto = None
    agua = None
    if any(p in t for p in PALAVRAS_GRAVES):
        gravidade = 5
    if "telhado" in t or "laje" in t:
        contexto = "telhado"
    if "água" in t or "agua" in t:
        contexto = contexto or "na_agua"
    if "subindo rápido" in t or "subindo rapido" in t:
        agua = "subindo_rapido"
    elif "subindo" in t:
        agua = "subindo_devagar"
    return {"gravidade": gravidade, "contexto": contexto, "agua": agua, "fonte": "heuristico"}


async def classificar(texto: str) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        return _heuristico(texto)
    try:
        prompt = (
            "Você é um classificador de emergências de enchente. Dada a mensagem da vítima, "
            "responda APENAS um JSON com: gravidade (1-5), contexto "
            "(terreo|andar|telhado|carro_muro|na_agua|null), agua "
            "(parada|subindo_devagar|subindo_rapido|null), num_pessoas (int). "
            f"Mensagem: {texto!r}"
        )
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.CLASSIFIER_MODEL,
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            txt = r.json()["content"][0]["text"]
            data = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
            data["fonte"] = "llm"
            return data
    except Exception:
        return _heuristico(texto)  # degradação graciosa
