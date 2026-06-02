"""Triagem por IA (§5.5) com humano no loop.

Provedor: OpenAI (se OPENAI_API_KEY) → Anthropic (se ANTHROPIC_API_KEY) →
heurístico por palavras-chave (sempre como fallback). Sempre devolve um dict
estruturado {gravidade, contexto, agua, num_pessoas?, fonte}; a Sala decide.
"""
import json
import httpx
from ..config import settings

PROMPT = (
    "Você é um classificador de emergências de enchente. Dada a mensagem da vítima, "
    "responda APENAS um JSON com: gravidade (1-5), contexto "
    "(terreo|andar|telhado|carro_muro|na_agua|null), agua "
    "(parada|subindo_devagar|subindo_rapido|null), num_pessoas (int)."
)

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


def _extrai_json(txt: str) -> dict:
    return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])


async def _openai(texto: str) -> dict:
    model = settings.CLASSIFIER_MODEL or "gpt-4o-mini"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                     "Content-Type": "application/json"},
            json={
                "model": model,
                "max_tokens": 200,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": texto or ""},
                ],
            },
        )
        r.raise_for_status()
        data = _extrai_json(r.json()["choices"][0]["message"]["content"])
    data["fonte"] = "openai"
    return data


async def _anthropic(texto: str) -> dict:
    model = settings.CLASSIFIER_MODEL or "claude-haiku-4-5-20251001"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": settings.ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": model, "max_tokens": 200,
                  "messages": [{"role": "user", "content": f"{PROMPT}\nMensagem: {texto!r}"}]},
        )
        r.raise_for_status()
        data = _extrai_json(r.json()["content"][0]["text"])
    data["fonte"] = "anthropic"
    return data


async def classificar(texto: str) -> dict:
    try:
        if settings.OPENAI_API_KEY:
            return await _openai(texto)
        if settings.ANTHROPIC_API_KEY:
            return await _anthropic(texto)
    except Exception:
        pass  # degradação graciosa
    return _heuristico(texto)
