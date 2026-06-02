import asyncpg
from .config import settings

_pool: asyncpg.Pool | None = None


async def connect() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=1, max_size=10)


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool não inicializado. Chame connect() no startup.")
    return _pool


async def fetch(query: str, *args):
    async with pool().acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args):
    async with pool().acquire() as conn:
        return await conn.fetchrow(query, *args)


async def execute(query: str, *args):
    async with pool().acquire() as conn:
        return await conn.execute(query, *args)


async def default_tenant_id():
    """Conveniência p/ MVP single-tenant demo: pega o primeiro tenant."""
    row = await fetchrow("SELECT id FROM tenants ORDER BY criado_em LIMIT 1")
    return row["id"] if row else None
