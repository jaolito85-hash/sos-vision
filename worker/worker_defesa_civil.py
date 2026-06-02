"""Worker da vertical Defesa Civil — standalone, modular (§5 do blueprint).

Responsabilidades (loop periódico):
  1. Anti-starvation: re-pontua chamados abertos somando o tempo de fila, para
     que ninguém esquecido afunde para sempre na lista.
  2. "Sem resposta": (placeholder) marcaria como perdido_contato chamados sem
     GPS há muito tempo — aqui só registra para não agir agressivamente no MVP.
  3. Publica um tick no canal realtime para a Sala re-ordenar a fila.

Conecta direto ao Postgres + Redis (não importa o backend — é processo separado).
Em produção: quebrar em consumidores de fila Redis por tipo de tarefa.
"""
import asyncio
import json
import os
import time
import asyncpg
import httpx
import redis.asyncio as aioredis
import openmeteo

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sos:sos@localhost:5432/sosvision")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
INTERVALO_S = 30
INTERVALO_HIDRO_S = int(os.getenv("INTERVALO_HIDRO_S", "600"))  # puxa clima/vazão a cada 10min
ABERTOS = ("aguardando", "triado", "despachado")


async def repontuar(pool, r):
    """Anti-starvation: +1 no score por ciclo para chamados ainda não assumidos,
    para que pedidos antigos não afundem para sempre na fila."""
    async with pool.acquire() as conn:
        atualizados = await conn.fetch(
            """UPDATE chamados_resgate
               SET prioridade_score = prioridade_score + 1
               WHERE estado = ANY($1::text[])
               RETURNING id""",
            list(ABERTOS),
        )
    if atualizados:
        await r.publish("events", json.dumps({"type": "fila_repontuada", "data": {"n": len(atualizados)}}))
        print(f"[worker] re-pontuados {len(atualizados)} chamados")


async def puxar_clima_hidro(pool):
    """Puxa chuva (Forecast) + vazão (Flood) do Open-Meteo para cada estação com
    coordenadas e empurra a previsão ao backend, que aciona o gatilho preventivo."""
    async with pool.acquire() as conn:
        estacoes = await conn.fetch(
            "SELECT id, nome, lat, lng FROM estacoes_hidrologicas WHERE lat IS NOT NULL AND lng IS NOT NULL"
        )
    async with httpx.AsyncClient(timeout=25) as client:
        for e in estacoes:
            chuva = await openmeteo.chuva_prevista_mm(e["lat"], e["lng"])
            vaz = await openmeteo.vazao_rio(e["lat"], e["lng"])
            try:
                await client.post(f"{BACKEND_URL}/hidrologia/estacoes/{e['id']}/previsao", json={
                    "chuva_prevista_mm": chuva or 0.0,
                    "vazao_m3s": vaz["vazao_m3s"],
                    "vazao_pico_m3s": vaz["vazao_pico_m3s"],
                    "tendencia": vaz["tendencia"],
                })
                print(f"[worker] previsao {e['nome']}: chuva={chuva}mm vazao={vaz['vazao_m3s']} tend={vaz['tendencia']}")
            except Exception as ex:
                print(f"[worker] falha previsao {e['nome']}: {ex}")


async def main():
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=4)
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    print("[worker] defesa_civil iniciado.")
    ultimo_hidro = 0.0
    while True:
        try:
            await repontuar(pool, r)
            if time.monotonic() - ultimo_hidro >= INTERVALO_HIDRO_S:
                await puxar_clima_hidro(pool)
                ultimo_hidro = time.monotonic()
        except Exception as e:  # nunca derruba o worker
            print(f"[worker] erro: {e}")
        await asyncio.sleep(INTERVALO_S)


if __name__ == "__main__":
    asyncio.run(main())
