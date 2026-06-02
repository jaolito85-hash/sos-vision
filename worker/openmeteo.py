"""Conector Open-Meteo (gratuito, sem API key) — clima + vazão de rio.

- Forecast API  → precipitação prevista (mm) por lat/lng.
- Flood API (GloFAS) → vazão do rio (m³/s) e previsão de pico/tendência.

Degradação graciosa: qualquer falha retorna None nos campos — nunca derruba o worker.
"""
import httpx

FORECAST = "https://api.open-meteo.com/v1/forecast"
FLOOD = "https://flood-api.open-meteo.com/v1/flood"


async def chuva_prevista_mm(lat: float, lng: float) -> float | None:
    """Pico diário de precipitação previsto (hoje/amanhã), em mm."""
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(FORECAST, params={
                "latitude": lat, "longitude": lng,
                "daily": "precipitation_sum", "forecast_days": 2,
                "timezone": "America/Sao_Paulo",
            })
            r.raise_for_status()
            vals = [v for v in r.json().get("daily", {}).get("precipitation_sum", []) if v is not None]
        return round(max(vals), 1) if vals else None
    except Exception:
        return None


async def vazao_rio(lat: float, lng: float) -> dict:
    """Vazão atual + pico previsto (m³/s) e tendência (subindo|estavel|descendo)."""
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(FLOOD, params={
                "latitude": lat, "longitude": lng,
                "daily": "river_discharge", "forecast_days": 7,
            })
            r.raise_for_status()
            vals = [v for v in r.json().get("daily", {}).get("river_discharge", []) if v is not None]
        if not vals:
            return {"vazao_m3s": None, "vazao_pico_m3s": None, "tendencia": None}
        atual, pico, vale = vals[0], max(vals), min(vals)
        if atual and pico > atual * 1.15:
            tend = "subindo"
        elif atual and vale < atual * 0.85:
            tend = "descendo"
        else:
            tend = "estavel"
        return {"vazao_m3s": round(atual, 2), "vazao_pico_m3s": round(pico, 2), "tendencia": tend}
    except Exception:
        return {"vazao_m3s": None, "vazao_pico_m3s": None, "tendencia": None}
