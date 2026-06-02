from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db
from ..realtime import hub
from ..state_machine import validar, TransicaoInvalida
from ..services import dispatch

router = APIRouter(prefix="/chamados", tags=["chamados"])

ABERTOS = ("aguardando", "triado", "despachado", "assumido", "no_local", "perdido_contato")


@router.get("")
async def listar(somente_abertos: bool = True):
    """Fila ordenada por prioridade (desc) e antiguidade. Inclui último ponto GPS."""
    if somente_abertos:
        rows = await db.fetch(
            """SELECT c.*, s.token AS track_token
               FROM chamados_resgate c
               LEFT JOIN rastreamento_sessoes s ON s.chamado_id = c.id
               WHERE c.estado = ANY($1::text[])
               ORDER BY c.prioridade_score DESC, c.criado_em ASC""",
            list(ABERTOS),
        )
    else:
        rows = await db.fetch(
            """SELECT c.*, s.token AS track_token
               FROM chamados_resgate c
               LEFT JOIN rastreamento_sessoes s ON s.chamado_id = c.id
               ORDER BY c.criado_em DESC LIMIT 500"""
        )
    return [dict(r) for r in rows]


@router.get("/{chamado_id}")
async def detalhe(chamado_id: str):
    row = await db.fetchrow("SELECT * FROM chamados_resgate WHERE id=$1", chamado_id)
    if not row:
        raise HTTPException(404, "Chamado não encontrado")
    pontos = await db.fetch(
        """SELECT p.lat, p.lng, p.acuracia_m, p.fonte, p.ts
           FROM rastreamento_pontos p
           JOIN rastreamento_sessoes s ON s.id = p.sessao_id
           WHERE s.chamado_id = $1 ORDER BY p.ts""",
        chamado_id,
    )
    return {**dict(row), "trilha": [dict(p) for p in pontos]}


class TransicaoIn(BaseModel):
    estado: str
    ator: str = "operador"


@router.post("/{chamado_id}/estado")
async def transitar(chamado_id: str, inp: TransicaoIn):
    row = await db.fetchrow("SELECT estado, tenant_id FROM chamados_resgate WHERE id=$1", chamado_id)
    if not row:
        raise HTTPException(404, "Chamado não encontrado")
    try:
        validar(row["estado"], inp.estado)
    except TransicaoInvalida as e:
        raise HTTPException(409, str(e))
    await db.execute(
        "UPDATE chamados_resgate SET estado=$1, atualizado_em=now() WHERE id=$2",
        inp.estado, chamado_id,
    )
    await db.execute(
        "INSERT INTO eventos_audit (tenant_id, ator, acao, alvo) VALUES ($1,$2,$3,$4)",
        row["tenant_id"], inp.ator, f"estado:{row['estado']}→{inp.estado}", chamado_id,
    )
    await hub.publish("chamado_estado", {"id": chamado_id, "estado": inp.estado})
    return {"ok": True, "estado": inp.estado}


class DespacharIn(BaseModel):
    equipe_id: str


@router.get("/{chamado_id}/sugestoes")
async def sugestoes(chamado_id: str):
    row = await db.fetchrow("SELECT tenant_id, lat, lng FROM chamados_resgate WHERE id=$1", chamado_id)
    if not row:
        raise HTTPException(404, "Chamado não encontrado")
    return await dispatch.equipes_sugeridas(row["tenant_id"], row["lat"], row["lng"])


@router.post("/{chamado_id}/despachar")
async def despachar(chamado_id: str, inp: DespacharIn):
    try:
        desp_id = await dispatch.despachar(chamado_id, inp.equipe_id)
    except dispatch.JaDespachado as e:
        raise HTTPException(409, str(e))   # lock ativo → impede resgate duplicado
    except ValueError as e:
        raise HTTPException(404, str(e))
    await hub.publish("chamado_estado", {"id": chamado_id, "estado": "assumido", "despacho": str(desp_id)})
    return {"ok": True, "despacho_id": str(desp_id)}


class MergeIn(BaseModel):
    pai_id: str


@router.post("/{chamado_id}/marcar-duplicado")
async def marcar_duplicado(chamado_id: str, inp: MergeIn):
    """Operador confirma manualmente que é duplicata de outro chamado."""
    await db.execute(
        "UPDATE chamados_resgate SET estado='duplicado', dup_de=$1, atualizado_em=now() WHERE id=$2",
        inp.pai_id, chamado_id,
    )
    await hub.publish("chamado_estado", {"id": chamado_id, "estado": "duplicado"})
    return {"ok": True}
