"""Roteamento rua-a-rua para 'Traçar rota' (Sala + Campo).

Motor primário: OpenRouteService (ORS_API_KEY) — suporta `avoid_polygons`, usado
na FASE 2 para DESVIAR das vias bloqueadas reportadas pela frota (`vias_bloqueadas`).
Sem a chave, cai no OSRM público (que NÃO suporta avoid → ignora os bloqueios).

Retorno normalizado:
    { "geometry": <GeoJSON LineString>, "distancia_m": int, "duracao_s": int,
      "fonte": "ors"|"osrm", "evitou": int }
"""
import httpx
from ..config import settings

ORS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

# Raio do buffer (em graus, ~44 m) ao redor de cada ponto bloqueado.
_BUF = 0.0004


class RotaIndisponivel(Exception):
    pass


def _buffer(lat: float, lng: float) -> list:
    """Quadradinho (Polygon ring) ao redor de um ponto bloqueado."""
    r = _BUF
    return [[[lng - r, lat - r], [lng + r, lat - r], [lng + r, lat + r],
             [lng - r, lat + r], [lng - r, lat - r]]]


def _avoid_multipolygon(pontos: list) -> dict:
    return {"type": "MultiPolygon", "coordinates": [_buffer(lat, lng) for (lat, lng) in pontos]}


async def tracar(de_lat, de_lng, para_lat, para_lng, evitar: list | None = None) -> dict:
    """Traça rota de carro. `evitar` = lista de (lat,lng) de vias bloqueadas (só ORS)."""
    if settings.ORS_API_KEY:
        try:
            return await _ors(de_lat, de_lng, para_lat, para_lng, evitar)
        except Exception:
            # Se o ORS falhar (cota/indisponível/avoid impossível), tenta o OSRM (sem avoid).
            pass
    return await _osrm(de_lat, de_lng, para_lat, para_lng)


async def _ors(de_lat, de_lng, para_lat, para_lng, evitar: list | None) -> dict:
    body = {"coordinates": [[de_lng, de_lat], [para_lng, para_lat]]}
    if evitar:
        body["options"] = {"avoid_polygons": _avoid_multipolygon(evitar)}
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
        "evitou": len(evitar or []),
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
        "evitou": 0,
    }
