"""Endpoint de roteamento — 'Traçar rota' (Sala + Campo).

GET /rotas?de=lat,lng&para=lat,lng[&evitar=true]
  → { geometry, distancia_m, duracao_s, fonte, evitou }
Por padrão desvia das vias bloqueadas do tenant (fase 2). `evitar=false` ignora.
A geometria é um GeoJSON LineString pronto p/ desenhar no MapLibre.
"""
from fastapi import APIRouter, HTTPException, Query
from .. import db
from ..services import rotas as rotas_svc

router = APIRouter(prefix="/rotas", tags=["rotas"])


def _par(coord: str) -> tuple[float, float]:
    try:
        lat, lng = (float(x) for x in coord.split(","))
        return lat, lng
    except Exception:
        raise HTTPException(422, "Coordenada inválida; use 'lat,lng'.")


@router.get("")
async def tracar_rota(
    de: str = Query(..., description="origem 'lat,lng'"),
    para: str = Query(..., description="destino 'lat,lng'"),
    evitar: bool = Query(True, description="desviar das vias bloqueadas"),
):
    de_lat, de_lng = _par(de)
    para_lat, para_lng = _par(para)

    pontos = None
    if evitar:
        tenant_id = await db.default_tenant_id()
        if tenant_id is not None:
            rows = await db.fetch(
                "SELECT lat, lng FROM vias_bloqueadas WHERE tenant_id=$1 AND lat IS NOT NULL",
                tenant_id,
            )
            pontos = [(r["lat"], r["lng"]) for r in rows] or None

    try:
        return await rotas_svc.tracar(de_lat, de_lng, para_lat, para_lng, evitar=pontos)
    except rotas_svc.RotaIndisponivel as e:
        raise HTTPException(502, str(e))
    except Exception:
        raise HTTPException(502, "Não foi possível traçar a rota agora.")
