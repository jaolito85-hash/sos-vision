"""Abrigo mais próximo com vaga + instrução de fuga (§5.4 / Fase 2).

MVP: escolhe o abrigo aberto mais próximo (haversine) respeitando capacidade e,
se a pessoa tem pets, prioriza pet-friendly. Devolve link de navegação e uma
instrução textual de fuga simples (subir / afastar-se da água).

TODO (fase 2): rota real evitando vias alagadas via OSRM/Mapbox Directions,
cruzando com `vias_bloqueadas`.
"""
from .. import db
from .geo import haversine_m


async def abrigo_mais_proximo(tenant_id, lat: float, lng: float, precisa_pet: bool = False):
    abrigos = await db.fetch(
        "SELECT * FROM abrigos WHERE tenant_id=$1 AND lat IS NOT NULL", tenant_id
    )
    candidatos = []
    for a in abrigos:
        if a["ocupacao"] >= a["capacidade"]:
            continue  # lotado
        if precisa_pet and not a["pet_friendly"]:
            continue  # quem tem animal só vai a abrigo que aceita
        dist = haversine_m(lat, lng, a["lat"], a["lng"])
        candidatos.append((dist, a))
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: x[0])
    dist, a = candidatos[0]
    return {
        "abrigo_id": str(a["id"]),
        "nome": a["nome"],
        "lat": a["lat"], "lng": a["lng"],
        "vagas": a["capacidade"] - a["ocupacao"],
        "pet_friendly": a["pet_friendly"],
        "tem_medico": a["tem_medico"],
        "distancia_m": round(dist),
        "rota_url": f"https://www.google.com/maps/dir/?api=1&destination={a['lat']},{a['lng']}",
        "instrucao": _instrucao_fuga(dist),
    }


def _instrucao_fuga(dist_m: float) -> str:
    km = dist_m / 1000
    return (
        "Saia AGORA para um ponto alto. Não entre na água nem dirija por ruas alagadas. "
        f"O abrigo mais próximo com vaga fica a ~{km:.1f} km — toque no link para a rota."
    )


async def texto_orientacao(tenant_id, telefone: str, preventivo: bool) -> str | None:
    """Monta a mensagem de abrigo/rota para uma pessoa cadastrada (usa o GPS do
    cadastro). Retorna None se não houver dados suficientes."""
    p = await db.fetchrow(
        "SELECT lat, lng, tem_pets FROM pessoas_protegidas WHERE tenant_id=$1 AND telefone=$2",
        tenant_id, telefone,
    )
    if not p or p["lat"] is None:
        return None
    ab = await abrigo_mais_proximo(tenant_id, p["lat"], p["lng"], precisa_pet=p["tem_pets"])
    if not ab:
        return "No momento não há abrigo com vaga próximo. Procure um ponto alto e aguarde a equipe."
    cab = "Fique atento. Se a água subir, " if preventivo else "Vá para o abrigo agora. "
    pet = " 🐾 (aceita animais)" if ab["pet_friendly"] else ""
    return (
        f"{cab}abrigo mais próximo com vaga: *{ab['nome']}*{pet}, a ~{ab['distancia_m']} m.\n"
        f"Rota: {ab['rota_url']}"
    )
