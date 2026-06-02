"""Utilidades geográficas sem dependência de PostGIS (MVP)."""
import math


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em metros entre dois pontos."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def ponto_em_poligono(lat: float, lng: float, geojson: dict) -> bool:
    """Ray casting. geojson = GeoJSON Polygon (coordenadas [lng,lat])."""
    try:
        ring = geojson["coordinates"][0]
    except (KeyError, IndexError, TypeError):
        return False
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lng < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside
