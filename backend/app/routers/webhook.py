"""Webhook de mensagens + simulador.

Canais de RECEBIMENTO (parsers distintos, mesma lógica de roteamento):
  POST /webhook            → WhatsApp Cloud API (Meta) — pós-MVP
  POST /webhook/evolution  → Evolution API — MVP
  POST /webhook/simulate   → injeta mensagem fake (dev/demo)
  GET  /webhook            → verificação do Meta (hub.challenge)
  GET  /webhook/outbox     → inspeciona envios do canal simulador
"""
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel
from .. import db
from ..config import settings
from ..services import chamados, rota_fuga
from ..messaging.registry import get_channel
from ..messaging.simulator import outbox

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _classificar_resposta(texto: str) -> str:
    """Mapeia a resposta de triagem 1/2/3 (Fase 2)."""
    t = (texto or "").strip().lower()
    if t in ("1", "1️⃣") or "em casa" in t:
        return "ok"
    if t in ("2", "2️⃣") or "já saí" in t or "ja sai" in t or "sai" in t:
        return "evacuado"
    if t in ("3", "3️⃣") or "ajuda" in t or "socorro" in t:
        return "sos"
    return "texto"


async def _registrar_resposta_broadcast(tenant_id, telefone: str):
    """Se quem respondeu foi alvo de um broadcast recente (mesma geofence), conta a
    resposta — fecha a malha enviados → respondidos do alerta em massa."""
    try:
        row = await db.fetchrow(
            """SELECT b.id FROM pessoas_protegidas p
               JOIN broadcasts b ON b.geofence_id = p.geofence_id AND b.tenant_id = p.tenant_id
               WHERE p.tenant_id=$1 AND p.telefone=$2
                 AND b.criado_em > now() - interval '24 hours'
               ORDER BY b.criado_em DESC LIMIT 1""",
            tenant_id, telefone,
        )
        if row:
            await db.execute("UPDATE broadcasts SET respondidos = respondidos + 1 WHERE id=$1", row["id"])
    except Exception:
        pass  # rastreamento é best-effort; nunca bloqueia o atendimento


async def _rotear(tenant_id, telefone: str, texto: str | None,
                  lat: float | None = None, lng: float | None = None):
    """Lógica única de roteamento, compartilhada por todos os canais de entrada."""
    await _registrar_resposta_broadcast(tenant_id, telefone)
    ch = get_channel()

    # Localização recebida → vira/atualiza chamado de resgate.
    if lat is not None and lng is not None:
        await chamados.criar_chamado(tenant_id, telefone=telefone, origem="link", lat=lat, lng=lng)
        await ch.send_text(telefone, "Recebemos sua localização. Equipe a caminho. 🚤")
        return

    intent = _classificar_resposta(texto or "")
    if intent == "sos":
        res = await chamados.criar_chamado(tenant_id, telefone=telefone, origem="broadcast", texto_livre=texto)
        link = f"{settings.PUBLIC_APP_URL}/vitima/?token={res.get('token')}&api={settings.PUBLIC_BASE_URL}"
        await ch.send_text(telefone, "Estamos com você. Toque para compartilhar sua localização ao vivo:")
        await ch.send_text(telefone, link)
    elif intent == "ok":
        await ch.send_text(telefone, "Que bom que está seguro. 🟢 Fique atento aos avisos.")
        orient = await rota_fuga.texto_orientacao(tenant_id, telefone, preventivo=True)
        if orient:
            await ch.send_text(telefone, orient)
    elif intent == "evacuado":
        await ch.send_text(telefone, "Ótimo que já saiu. 🔵")
        orient = await rota_fuga.texto_orientacao(tenant_id, telefone, preventivo=False)
        await ch.send_text(telefone, orient or "Procure o abrigo mais próximo. Se precisar de ajuda, responda 3.")
    else:
        await chamados.criar_chamado(tenant_id, telefone=telefone, origem="broadcast", texto_livre=texto)
        await ch.send_text(telefone, "Recebido. Estamos avaliando sua situação.")


# ───────────────────────── Meta Cloud API (pós-MVP) ──────────────────────────
@router.get("")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403, "verify_token inválido")


@router.post("")
async def inbound_meta(request: Request):
    body = await request.json()
    tenant_id = await db.default_tenant_id()
    try:
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        wa_from = msg["from"]
    except (KeyError, IndexError):
        return {"status": "ignored"}
    mtype = msg.get("type")
    if mtype == "location":
        loc = msg["location"]
        await _rotear(tenant_id, wa_from, None, loc["latitude"], loc["longitude"])
    elif mtype == "text":
        await _rotear(tenant_id, wa_from, msg["text"]["body"])
    elif mtype == "interactive":
        await _rotear(tenant_id, wa_from, msg["interactive"].get("button_reply", {}).get("title", ""))
    return {"status": "ok"}


# ───────────────────────── Evolution API (MVP) ───────────────────────────────
@router.post("/evolution")
async def inbound_evolution(request: Request):
    """Recebe eventos do Evolution API (messages.upsert)."""
    body = await request.json()
    if body.get("event") not in ("messages.upsert", "messages.update", None):
        return {"status": "ignored"}
    data = body.get("data") or {}
    key = data.get("key") or {}
    if key.get("fromMe"):
        return {"status": "ignored"}  # mensagem enviada por nós
    jid = key.get("remoteJid") or ""
    telefone = jid.split("@")[0]
    if not telefone:
        return {"status": "ignored"}

    tenant_id = await db.default_tenant_id()
    message = data.get("message") or {}

    loc = message.get("locationMessage")
    if loc:
        await _rotear(tenant_id, telefone, None,
                      loc.get("degreesLatitude"), loc.get("degreesLongitude"))
        return {"status": "ok"}

    texto = message.get("conversation") or \
        (message.get("extendedTextMessage") or {}).get("text") or \
        (message.get("buttonsResponseMessage") or {}).get("selectedDisplayText") or ""
    await _rotear(tenant_id, telefone, texto)
    return {"status": "ok"}


# ───────────────────────── Simulador (dev/demo) ──────────────────────────────
class SimulateIn(BaseModel):
    phone: str
    name: str | None = None
    kind: str = "sos"
    texto: str | None = None
    lat: float | None = None
    lng: float | None = None
    acuracia_m: float | None = None
    contexto: str | None = None
    num_pessoas: int = 1
    agua: str | None = None


@router.post("/simulate")
async def simulate(inp: SimulateIn):
    tenant_id = await db.default_tenant_id()
    if tenant_id is None:
        raise HTTPException(500, "Nenhum tenant. Rode as migrations/seed.")
    res = await chamados.criar_chamado(
        tenant_id, telefone=inp.phone, nome=inp.name, origem="simulador",
        lat=inp.lat, lng=inp.lng, acuracia_m=inp.acuracia_m,
        contexto=inp.contexto, num_pessoas=inp.num_pessoas, agua=inp.agua,
        texto_livre=inp.texto,
    )
    return {
        "chamado_id": str(res["id"]),
        "estado": res["estado"],
        "prioridade_score": res["prioridade_score"],
        "duplicado_de": str(res["dup_de"]) if res.get("dup_de") else None,
        "token": res.get("token"),
    }


@router.get("/outbox")
async def get_outbox():
    return outbox()
