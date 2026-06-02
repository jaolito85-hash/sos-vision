"""Roteamento rua-a-rua para 'Traçar rota' (Sala + Campo).

Motor primário: OpenRouteService (precisa ORS_API_KEY) — escolhido porque suporta
`avoid_polygons`, o que permitirá na FASE 2 evitar `vias_bloqueadas` + área de
inundação (geofence). Sem a chave, cai automaticamente no OSRM público (demo),
para a feature já funcionar antes de configurar a chave.

Retorno normalizado dos dois motores:
    { "geometry": <GeoJSON LineString>, "distancia_m": int, "duracao_s": int, "fonte": str }
"""
import httpx
from ..config import settings

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


class RotaIndisponivel(Exception):
    pass


async def tracar(de_lat: float, de_lng: float, para_lat: float, para_lng: float) -> dict:
    """Traça a rota de carro entre dois pontos. ORS se houver chave; senão OSRM."""
    if settings.ORS_API_KEY:
        try:
            return await _ors(de_lat, de_lng, para_lat, para_lng)
        except Exception:
            # Resiliência: se o ORS falhar (cota, indisponível), tenta o OSRM.
            pass
    return await _osrm(de_lat, de_lng, para_lat, para_lng)


async def _ors(de_lat, de_lng, para_lat, para_lng) -> dict:
    body = {"coordinates": [[de_lng, de_lat], [para_lng, para_lat]]}
    # FASE 2: body["options"] = {"avoid_polygons": <MultiPolygon de vias_bloqueadas + geofence>}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            ORS_URL,
            headers={"Authorization": settings.ORS_API_KEY, "Content-Type": "application/json"},
            json=body,
        )
        r.raise_for_status()
        data = r.json()
    feat = data["features"][0]
    summ = feat["properties"]["summary"]
    return {
        "geometry": feat["geometry"],
        "distancia_m": round(summ.get("distance", 0)),
        "duracao_s": round(summ.get("duration", 0)),
        "fonte": "ors",
    }


async def _osrm(de_lat, de_lng, para_lat, para_lng) -> dict:
    url = f"{OSRM_URL}/{de_lng},{de_lat};{para_lng},{para_lat}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params={"overview": "full", "geometries": "geojson"})
        r.raise_for_status()
        data = r.json()
    if not data.get("routes"):
        raise RotaIndisponivel("Nenhuma rota encontrada")
    rt = data["routes"][0]
    return {
        "geometry": rt["geometry"],
        "distancia_m": round(rt.get("distance", 0)),
        "duracao_s": round(rt.get("duration", 0)),
        "fonte": "osrm",
    }
