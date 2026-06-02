"""Equipes de campo (frota) + PWA de campo (login por token assinado)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db
from ..realtime import hub

router = APIRouter(prefix="/equipes", tags=["equipes"])


@router.get("")
async def listar():
    rows = await db.fetch("SELECT * FROM equipes_campo ORDER BY nome")
    return [dict(r) for r in rows]


@router.get("/por-token/{token}")
async def por_token(token: str):
    """PWA de campo: resolve a equipe e devolve seus chamados ativos."""
    eq = await db.fetchrow("SELECT * FROM equipes_campo WHERE token=$1", token)
    if not eq:
        raise HTTPException(404, "Equipe não encontrada")
    chamados = await db.fetch(
        """SELECT c.id, c.nome, c.lat, c.lng, c.contexto_vertical, c.num_pessoas,
                  c.agua, c.prioridade_score, c.estado, d.estado AS estado_despacho
           FROM despachos d JOIN chamados_resgate c ON c.id = d.chamado_id
           WHERE d.equipe_id=$1 AND d.estado <> 'cancelado'
             AND c.estado NOT IN ('encerrado','em_abrigo')
           ORDER BY c.prioridade_score DESC""",
        eq["id"],
    )
    return {"equipe": dict(eq), "chamados": [dict(c) for c in chamados]}


class PosIn(BaseModel):
    lat: float
    lng: float


@router.post("/por-token/{token}/posicao")
async def atualizar_posicao(token: str, p: PosIn):
    eq = await db.fetchrow("SELECT id FROM equipes_campo WHERE token=$1", token)
    if not eq:
        raise HTTPException(404, "Equipe não encontrada")
    await db.execute(
        "UPDATE equipes_campo SET lat=$1, lng=$2, atualizado_em=now() WHERE id=$3",
        p.lat, p.lng, eq["id"],
    )
    await hub.publish("equipe_pos", {"equipe_id": str(eq["id"]), "lat": p.lat, "lng": p.lng})
    return {"ok": True}


class DespachoEstadoIn(BaseModel):
    estado: str  # a_caminho | no_local | resgatado


@router.post("/despacho/{chamado_id}/{token}/estado")
async def estado_despacho(chamado_id: str, token: str, inp: DespachoEstadoIn):
    """Botões da PWA de campo: A caminho → No local → Resgatado."""
    eq = await db.fetchrow("SELECT id FROM equipes_campo WHERE token=$1", token)
    if not eq:
        raise HTTPException(404, "Equipe não encontrada")

    coluna_ts = {"a_caminho": "ts_a_caminho", "no_local": "ts_no_local", "resgatado": "ts_resgatado"}
    if inp.estado not in coluna_ts:
        raise HTTPException(400, "Estado de despacho inválido")

    await db.execute(
        f"""UPDATE despachos SET estado=$1, {coluna_ts[inp.estado]}=now()
            WHERE chamado_id=$2 AND equipe_id=$3 AND estado <> 'cancelado'""",
        inp.estado, chamado_id, eq["id"],
    )

    # Espelha no chamado. "resgatado" libera a equipe e tenta confirmar com a vítima.
    novo_estado = {"a_caminho": "assumido", "no_local": "no_local", "resgatado": "resgatado"}[inp.estado]
    await db.execute(
        "UPDATE chamados_resgate SET estado=$1, atualizado_em=now() WHERE id=$2",
        novo_estado, chamado_id,
    )
    if inp.estado == "resgatado":
        await db.execute("UPDATE equipes_campo SET status='disponivel' WHERE id=$1", eq["id"])

    await hub.publish("chamado_estado", {"id": chamado_id, "estado": novo_estado})
    return {"ok": True, "estado": novo_estado}
