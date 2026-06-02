"""Máquina de estados canônica do chamado de resgate (§5.2 do blueprint).

aguardando → triado → despachado → assumido → no_local → resgatado → em_abrigo → encerrado
                                                                  ↘ perdido_contato
qualquer → cancelado | duplicado
"""

TRANSICOES: dict[str, set[str]] = {
    "aguardando":      {"triado", "despachado", "cancelado", "duplicado", "perdido_contato"},
    "triado":          {"despachado", "cancelado", "duplicado", "perdido_contato"},
    "despachado":      {"assumido", "aguardando", "cancelado"},
    "assumido":        {"no_local", "despachado", "cancelado", "perdido_contato"},
    "no_local":        {"resgatado", "perdido_contato", "cancelado"},
    "resgatado":       {"em_abrigo", "encerrado"},
    "em_abrigo":       {"encerrado"},
    "perdido_contato": {"aguardando", "assumido", "encerrado"},
    "encerrado":       set(),
    "cancelado":       set(),
    "duplicado":       set(),
}


class TransicaoInvalida(Exception):
    pass


def pode_transitar(de: str, para: str) -> bool:
    return para in TRANSICOES.get(de, set())


def validar(de: str, para: str) -> None:
    if not pode_transitar(de, para):
        raise TransicaoInvalida(f"Transição inválida: {de} → {para}")
