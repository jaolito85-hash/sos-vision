"""Score de prioridade (§5.5).

score = gravidade × peso + vulnerabilidade + velocidade_da_agua + contexto + tempo_de_fila
Quanto maior, mais no topo. Acamado/O2/criança e "água subindo rápido" sobem.
"""

PESO_GRAVIDADE = 10

VULNERABILIDADE = {
    "acamado": 30, "oxigenio": 35, "dialise": 30,
    "cadeirante": 20, "idoso_so": 15, "crianca": 20,
}

AGUA = {"subindo_rapido": 25, "subindo_devagar": 10, "parada": 0}

CONTEXTO = {"na_agua": 40, "telhado": 25, "carro_muro": 20, "andar": 5, "terreo": 0}


def calcular(
    gravidade_ia: int = 3,
    vulnerabilidades: list[str] | None = None,
    agua: str | None = None,
    contexto: str | None = None,
    num_pessoas: int = 1,
    minutos_na_fila: float = 0.0,
) -> int:
    score = gravidade_ia * PESO_GRAVIDADE
    for v in (vulnerabilidades or []):
        score += VULNERABILIDADE.get(v, 0)
    score += AGUA.get(agua or "", 0)
    score += CONTEXTO.get(contexto or "", 0)
    score += max(0, num_pessoas - 1) * 5
    score += int(minutos_na_fila)  # 1 ponto por minuto esperando (anti-starvation)
    return score
