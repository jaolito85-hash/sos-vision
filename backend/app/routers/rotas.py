"""Endpoint de roteamento — 'Traçar rota' (Sala + Campo).

GET /rotas?de=lat,lng&para=lat,lng  → { geometry, distancia_m, duracao_s, fonte }
A geometria é um GeoJSON LineString pronto p/ desenhar no MapLibre.
"""
from fastapi import APIRouter, HTTPException, Query
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
):
    de_lat, de_lng = _par(de)
    para_lat, para_lng = _par(para)
    try:
        return await rotas_svc.tracar(de_lat, de_lng, para_lat, para_lng)
    except rotas_svc.RotaIndisponivel as e:
        raise HTTPException(502, str(e))
    except Exception:
        raise HTTPException(502, "Não foi possível traçar a rota agora.")
