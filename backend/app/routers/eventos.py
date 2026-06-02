"""Eventos + broadcast por geofence (Fase 2). O envio real depende de templates
aprovados no Meta Business; aqui registramos e disparamos via canal ativo."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db
from ..messaging.registry import get_channel
from ..services.geo import ponto_em_poligono

router = APIRouter(prefix="/eventos", tags=["eventos"])


@router.get("")
async def listar():
    rows = await db.fetch("SELECT * FROM eventos ORDER BY iniciado_em DESC")
    return [dict(r) for r in rows]


@router.get("/geofences")
async def geofences():
    rows = await db.fetch("SELECT id, nome, tipo, poligono FROM geofences")
    return [dict(r) for r in rows]


@router.get("/vias-bloqueadas")
async def vias_bloqueadas():
    """Vias intransitáveis reportadas pela frota — marcadas no mapa da Sala
    e usadas para desviar as rotas (fase 2)."""
    rows = await db.fetch(
        "SELECT id, lat, lng, motivo, ts FROM vias_bloqueadas WHERE lat IS NOT NULL ORDER BY ts DESC"
    )
    return [dict(r) for r in rows]


class BroadcastIn(BaseModel):
    geofence_id: str
    template: str = "alerta_enchente"
    evento_id: str | None = None   # quando confirma uma recomendação do gatilho


@router.post("/broadcast")
async def broadcast(inp: BroadcastIn):
    """Operador confirma a evacuação: dispara a triagem 1/2/3 para todos os
    cadastrados dentro do geofence (humano no loop — §8)."""
    gf = await db.fetchrow("SELECT tenant_id, poligono FROM geofences WHERE id=$1", inp.geofence_id)
    if not gf:
        raise HTTPException(404, "Geofence não encontrado")

    pessoas = await db.fetch(
        "SELECT telefone, lat, lng FROM pessoas_protegidas WHERE tenant_id=$1 AND lat IS NOT NULL",
        gf["tenant_id"],
    )
    poligono = gf["poligono"]
    if isinstance(poligono, str):
        import json
        poligono = json.loads(poligono)

    alvos = [p for p in pessoas if ponto_em_poligono(p["lat"], p["lng"], poligono)]
    ch = get_channel()
    texto = ("⚠️ Alerta da Defesa Civil: cheia forte prevista para sua região. "
             "Você está bem? 1) Em casa seguro  2) Já saí  3) PRECISO DE AJUDA")
    entregues = 0
    for p in alvos:
        try:
            await ch.send_buttons(p["telefone"], texto, ["1 Em casa", "2 Já saí", "3 Ajuda"])
            entregues += 1  # canal aceitou o envio (não é recibo de leitura)
        except Exception:
            pass  # um número inválido não derruba o disparo em massa

    bc = await db.fetchrow(
        """INSERT INTO broadcasts (tenant_id, evento_id, template, geofence_id, enviados, entregues)
           VALUES ($1,$2,$3,$4,$5,$6) RETURNING id""",
        gf["tenant_id"], inp.evento_id, inp.template, inp.geofence_id, len(alvos), entregues,
    )
    await db.execute(
        "INSERT INTO eventos_audit (tenant_id, ator, acao, alvo, detalhe) VALUES ($1,$2,$3,$4,$5)",
        gf["tenant_id"], "operador", "broadcast_evacuacao", str(bc["id"]),
        __import__("json").dumps({"geofence": inp.geofence_id, "enviados": len(alvos)}),
    )
    return {"broadcast_id": str(bc["id"]), "enviados": len(alvos), "entregues": entregues}
