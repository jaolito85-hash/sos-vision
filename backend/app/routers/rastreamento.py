"""Token-link de rastreamento (§5.1). A PWA da vítima envia pontos GPS aqui.
Sem autenticação por senha — o token assinado É a credencial (expirável)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db
from ..realtime import hub
from ..services import chamados as chamados_svc

router = APIRouter(prefix="/track", tags=["rastreamento"])


class AtivarIn(BaseModel):
    telefone: str
    nome: str | None = None


@router.post("/ativar")
async def ativar(inp: AtivarIn):
    """App nativo do vulnerável (camada B, §13): ativa a proteção pelo telefone
    cadastrado. Cria/recupera um chamado + sessão de rastreamento e devolve o
    token para o app transmitir GPS em background (mesmo com o app fechado)."""
    tenant_id = await db.default_tenant_id()
    if tenant_id is None:
        raise HTTPException(500, "Sem tenant. Rode as migrations.")
    res = await chamados_svc.criar_chamado(
        tenant_id, telefone=inp.telefone, nome=inp.nome, origem="link",
    )
    token = res.get("token")
    # Se já havia uma sessão ativa (dedup), reusa o token existente.
    if token is None and res.get("dup_de"):
        row = await db.fetchrow(
            "SELECT token FROM rastreamento_sessoes WHERE chamado_id=$1", res["dup_de"]
        )
        token = row["token"] if row else None
    return {"chamado_id": str(res["id"]), "token": token, "estado": res["estado"]}


class PontoIn(BaseModel):
    lat: float
    lng: float
    acuracia_m: float | None = None
    fonte: str = "gps"


@router.get("/{token}")
async def resolver(token: str):
    sess = await db.fetchrow(
        """SELECT s.id, s.chamado_id, c.nome, c.estado
           FROM rastreamento_sessoes s JOIN chamados_resgate c ON c.id = s.chamado_id
           WHERE s.token = $1""",
        token,
    )
    if not sess:
        raise HTTPException(404, "Token inválido")
    return {"chamado_id": str(sess["chamado_id"]), "nome": sess["nome"], "estado": sess["estado"]}


@router.post("/{token}/ponto")
async def ingerir_ponto(token: str, p: PontoIn):
    sess = await db.fetchrow(
        "SELECT id, chamado_id FROM rastreamento_sessoes WHERE token=$1", token
    )
    if not sess:
        raise HTTPException(404, "Token inválido")
    await db.execute(
        """INSERT INTO rastreamento_pontos (sessao_id, lat, lng, acuracia_m, fonte)
           VALUES ($1,$2,$3,$4,$5)""",
        sess["id"], p.lat, p.lng, p.acuracia_m, p.fonte,
    )
    # Atualiza posição "corrente" do chamado p/ a Sala.
    await db.execute(
        "UPDATE chamados_resgate SET lat=$1, lng=$2, acuracia_m=$3, atualizado_em=now() WHERE id=$4",
        p.lat, p.lng, p.acuracia_m, sess["chamado_id"],
    )
    await hub.publish("ponto_gps", {
        "chamado_id": str(sess["chamado_id"]),
        "lat": p.lat, "lng": p.lng, "acuracia_m": p.acuracia_m,
    })
    return {"ok": True}
