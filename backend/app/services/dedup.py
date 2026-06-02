"""Anti-duplicação (o moat do RS — §5.2).

Antes de criar um chamado, procura um chamado aberto que seja provável duplicata:
  - mesmo telefone, OU
  - dentro de ~30m e criado nos últimos 30 min.
Retorna o id do chamado-pai (ou None). A Sala pode confirmar/desfazer o merge.
"""
from datetime import datetime, timedelta, timezone
from .. import db
from .geo import haversine_m

RAIO_M = 30.0
JANELA_MIN = 30
ESTADOS_ABERTOS = ("aguardando", "triado", "despachado", "assumido", "no_local")


async def encontrar_duplicata(
    tenant_id, telefone: str | None, lat: float | None, lng: float | None
):
    desde = datetime.now(timezone.utc) - timedelta(minutes=JANELA_MIN)

    # 1) Mesmo telefone com chamado aberto = duplicata forte.
    if telefone:
        row = await db.fetchrow(
            """SELECT id FROM chamados_resgate
               WHERE tenant_id=$1 AND telefone=$2 AND estado = ANY($3::text[])
               ORDER BY criado_em DESC LIMIT 1""",
            tenant_id, telefone, list(ESTADOS_ABERTOS),
        )
        if row:
            return row["id"]

    # 2) Proximidade geográfica recente.
    if lat is not None and lng is not None:
        candidatos = await db.fetch(
            """SELECT id, lat, lng FROM chamados_resgate
               WHERE tenant_id=$1 AND estado = ANY($2::text[])
                 AND criado_em >= $3 AND lat IS NOT NULL AND lng IS NOT NULL""",
            tenant_id, list(ESTADOS_ABERTOS), desde,
        )
        for c in candidatos:
            if haversine_m(lat, lng, c["lat"], c["lng"]) <= RAIO_M:
                return c["id"]

    return None
