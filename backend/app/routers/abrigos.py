from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db
from ..realtime import hub
from ..services import rota_fuga

router = APIRouter(prefix="/abrigos", tags=["abrigos"])


@router.get("")
async def listar():
    rows = await db.fetch("SELECT * FROM abrigos ORDER BY nome")
    return [dict(r) for r in rows]


@router.get("/mais-proximo")
async def mais_proximo(lat: float, lng: float, pet: bool = False):
    """Abrigo aberto mais próximo com vaga (+ rota e instrução de fuga)."""
    tenant_id = await db.default_tenant_id()
    ab = await rota_fuga.abrigo_mais_proximo(tenant_id, lat, lng, precisa_pet=pet)
    if not ab:
        raise HTTPException(404, "Nenhum abrigo com vaga disponível no momento.")
    return ab


class CheckinIn(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    chamado_id: str | None = None


@router.post("/{abrigo_id}/checkin")
async def checkin(abrigo_id: str, inp: CheckinIn):
    ab = await db.fetchrow("SELECT capacidade, ocupacao FROM abrigos WHERE id=$1", abrigo_id)
    if not ab:
        raise HTTPException(404, "Abrigo não encontrado")
    await db.execute(
        "INSERT INTO abrigo_checkins (abrigo_id, chamado_id, nome, telefone) VALUES ($1,$2,$3,$4)",
        abrigo_id, inp.chamado_id, inp.nome, inp.telefone,
    )
    await db.execute(
        "UPDATE abrigos SET ocupacao=ocupacao+1, atualizado_em=now() WHERE id=$1", abrigo_id
    )
    # Tira o chamado da fila de resgate (resolve o bug de 2024: resgatado seguia na lista).
    if inp.chamado_id:
        await db.execute(
            "UPDATE chamados_resgate SET estado='em_abrigo', atualizado_em=now() WHERE id=$1",
            inp.chamado_id,
        )
        await hub.publish("chamado_estado", {"id": inp.chamado_id, "estado": "em_abrigo"})
    await hub.publish("abrigo_update", {"abrigo_id": abrigo_id})
    return {"ok": True}
