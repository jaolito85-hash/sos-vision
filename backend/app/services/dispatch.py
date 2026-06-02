"""Despacho com lock geográfico (§5.2).

Atribui uma equipe a um chamado de forma atômica: usa SELECT ... FOR UPDATE no
chamado e confia no índice único uniq_despacho_ativo para impedir dois despachos
ativos no mesmo chamado (anti-duplicação de resgate — a dor #1 de 2024).
"""
import asyncpg
from .. import db
from .geo import haversine_m


class JaDespachado(Exception):
    pass


async def equipes_sugeridas(tenant_id, lat, lng, limit=3):
    """Equipes disponíveis ordenadas por proximidade (despacho assistido)."""
    rows = await db.fetch(
        """SELECT id, nome, tipo, capacidade, lat, lng FROM equipes_campo
           WHERE tenant_id=$1 AND status='disponivel'""",
        tenant_id,
    )
    out = []
    for r in rows:
        dist = None
        if lat is not None and r["lat"] is not None:
            dist = haversine_m(lat, lng, r["lat"], r["lng"])
        out.append({**dict(r), "distancia_m": dist})
    out.sort(key=lambda e: (e["distancia_m"] is None, e["distancia_m"] or 0))
    return out[:limit]


async def despachar(chamado_id, equipe_id):
    """Cria o despacho e trava o chamado. Levanta JaDespachado se já houver lock."""
    async with db.pool().acquire() as conn:
        async with conn.transaction():
            chamado = await conn.fetchrow(
                "SELECT id, estado FROM chamados_resgate WHERE id=$1 FOR UPDATE",
                chamado_id,
            )
            if chamado is None:
                raise ValueError("Chamado inexistente")
            if chamado["estado"] in ("resgatado", "em_abrigo", "encerrado", "cancelado"):
                raise JaDespachado(f"Chamado já está em estado {chamado['estado']}")
            try:
                desp = await conn.fetchrow(
                    """INSERT INTO despachos (chamado_id, equipe_id, estado)
                       VALUES ($1,$2,'assumido') RETURNING id""",
                    chamado_id, equipe_id,
                )
            except asyncpg.UniqueViolationError:
                raise JaDespachado("Chamado já tem equipe a caminho")

            await conn.execute(
                "UPDATE chamados_resgate SET estado='assumido', atualizado_em=now() WHERE id=$1",
                chamado_id,
            )
            await conn.execute(
                "UPDATE equipes_campo SET status='ocupada', atualizado_em=now() WHERE id=$1",
                equipe_id,
            )
            return desp["id"]
