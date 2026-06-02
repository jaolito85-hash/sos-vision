"""Pessoas protegidas (cadastro prévio) — quem recebe o alerta em massa por geofence."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import db

router = APIRouter(prefix="/pessoas", tags=["pessoas"])


@router.get("")
async def listar():
    rows = await db.fetch(
        """SELECT id, telefone, nome, endereco, lat, lng, household_size,
                  vulnerabilidades, tem_pets, geofence_id, criado_em
           FROM pessoas_protegidas ORDER BY criado_em DESC LIMIT 1000"""
    )
    return [dict(r) for r in rows]


class PessoaIn(BaseModel):
    telefone: str
    nome: str | None = None
    endereco: str | None = None
    lat: float | None = None
    lng: float | None = None
    household_size: int = 1
    vulnerabilidades: list[str] = []
    tem_pets: bool = False
    geofence_id: str | None = None


@router.post("")
async def cadastrar(inp: PessoaIn):
    """Cadastra (ou atualiza por telefone) uma pessoa protegida no tenant padrão."""
    tenant_id = await db.default_tenant_id()
    if tenant_id is None:
        raise HTTPException(500, "Sem tenant. Rode as migrations/seed.")
    row = await db.fetchrow(
        """INSERT INTO pessoas_protegidas
             (tenant_id, telefone, nome, endereco, lat, lng, household_size,
              vulnerabilidades, tem_pets, geofence_id)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
           ON CONFLICT (tenant_id, telefone) DO UPDATE SET
             nome=EXCLUDED.nome, endereco=EXCLUDED.endereco, lat=EXCLUDED.lat,
             lng=EXCLUDED.lng, household_size=EXCLUDED.household_size,
             vulnerabilidades=EXCLUDED.vulnerabilidades, tem_pets=EXCLUDED.tem_pets,
             geofence_id=EXCLUDED.geofence_id
           RETURNING id""",
        tenant_id, inp.telefone, inp.nome, inp.endereco, inp.lat, inp.lng,
        inp.household_size, inp.vulnerabilidades, inp.tem_pets, inp.geofence_id,
    )
    return {"ok": True, "id": str(row["id"])}
