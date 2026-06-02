"""Vigilância hidrológica + ciclo de alerta (Fases 1-2)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db
from ..services import hidrologia

router = APIRouter(prefix="/hidrologia", tags=["hidrologia"])


@router.get("/estacoes")
async def estacoes():
    rows = await db.fetch(
        """SELECT e.*, g.nome AS geofence_nome
           FROM estacoes_hidrologicas e
           LEFT JOIN geofences g ON g.id = e.geofence_id
           ORDER BY e.nome"""
    )
    return [dict(r) for r in rows]


class LeituraIn(BaseModel):
    valor: float


@router.post("/estacoes/{estacao_id}/leitura")
async def leitura(estacao_id: str, inp: LeituraIn):
    """Ingere uma leitura (de qualquer fonte). Pode disparar o gatilho de alerta."""
    try:
        res = await hidrologia.ingerir_leitura(estacao_id, inp.valor)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return res


class PrevisaoIn(BaseModel):
    chuva_prevista_mm: float
    vazao_m3s: float | None = None
    vazao_pico_m3s: float | None = None
    tendencia: str | None = None  # subindo | estavel | descendo


@router.post("/estacoes/{estacao_id}/previsao")
async def previsao(estacao_id: str, inp: PrevisaoIn):
    """Ingere previsão climática/hidrológica (Open-Meteo, via worker). Atualiza a
    estação e pode disparar o gatilho preventivo (recomenda evacuação à Sala)."""
    try:
        return await hidrologia.ingerir_previsao(
            estacao_id, inp.chuva_prevista_mm, inp.vazao_m3s, inp.vazao_pico_m3s, inp.tendencia
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/recomendacoes")
async def recomendacoes():
    """Eventos hidrológicos ativos (alerta/inundação) aguardando decisão de evacuação.
    A Sala mostra isto; o operador confirma e dispara o broadcast (humano no loop)."""
    rows = await db.fetch(
        """SELECT ev.id AS evento_id, ev.nome, ev.severidade, ev.geofence_impacto AS geofence_id,
                  e.nome AS estacao, e.rio, e.nivel_atual, e.unidade,
                  (SELECT COUNT(*) FROM pessoas_protegidas p WHERE p.geofence_id = ev.geofence_impacto) AS pessoas_na_area
           FROM eventos ev
           LEFT JOIN estacoes_hidrologicas e ON e.id = ev.estacao_id
           -- "severidade preenchida" = cruzou nível de alerta/inundação (gatilho tocou),
           -- independ. de o evento ter nascido manual ou hidrológico.
           WHERE ev.status='ativo' AND ev.severidade IS NOT NULL
           ORDER BY ev.severidade DESC, ev.iniciado_em DESC"""
    )
    return [dict(r) for r in rows]
