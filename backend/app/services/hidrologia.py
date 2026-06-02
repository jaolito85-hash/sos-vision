"""Vigilância hidrológica e motor de gatilho (§5.6 do blueprint).

Fluxo:
  leitura (de qualquer fonte) → classifica severidade contra os níveis de
  referência da estação → se ESCALOU para alerta/inundação, dispara o gatilho:
  arma/atualiza um evento para o geofence coberto e RECOMENDA evacuação à Sala.

Decisão de segurança (§8): o gatilho NÃO dispara broadcast em massa sozinho.
Ele recomenda; um operador confirma e dispara. Isso evita falso positivo, pânico
e risco de ban do WhatsApp. Humano sempre no loop.
"""
from .. import db
from ..realtime import hub

NIVEIS = ["normal", "atencao", "alerta", "inundacao"]


def classificar(valor, ref_atencao, ref_alerta, ref_inundacao) -> str:
    """Severidade a partir do valor medido e dos níveis de referência."""
    if ref_inundacao is not None and valor >= ref_inundacao:
        return "inundacao"
    if ref_alerta is not None and valor >= ref_alerta:
        return "alerta"
    if ref_atencao is not None and valor >= ref_atencao:
        return "atencao"
    return "normal"


def escalou(antiga: str, nova: str) -> bool:
    """True se a severidade subiu (ex.: atencao → alerta)."""
    return NIVEIS.index(nova) > NIVEIS.index(antiga)


async def ingerir_leitura(estacao_id, valor: float) -> dict:
    """Grava a leitura, atualiza a estação e dispara o gatilho se escalou."""
    est = await db.fetchrow("SELECT * FROM estacoes_hidrologicas WHERE id=$1", estacao_id)
    if est is None:
        raise ValueError("Estação inexistente")

    sev_antiga = est["severidade"]
    sev_nova = classificar(valor, est["ref_atencao"], est["ref_alerta"], est["ref_inundacao"])

    await db.execute(
        "INSERT INTO leituras_hidrologicas (estacao_id, valor) VALUES ($1,$2)", estacao_id, valor
    )
    await db.execute(
        """UPDATE estacoes_hidrologicas
           SET nivel_atual=$1, severidade=$2, atualizado_em=now() WHERE id=$3""",
        valor, sev_nova, estacao_id,
    )

    await hub.publish("hidro_leitura", {
        "estacao_id": str(estacao_id), "nome": est["nome"], "rio": est["rio"],
        "valor": valor, "unidade": est["unidade"], "severidade": sev_nova,
        "lat": est["lat"], "lng": est["lng"],
    })

    subiu = escalou(sev_antiga, sev_nova)
    evento_id = None
    if subiu and sev_nova in ("alerta", "inundacao"):
        evento_id = await _processar_gatilho(est, sev_nova)

    return {
        "severidade": sev_nova, "anterior": sev_antiga, "escalou": subiu,
        "evento_id": str(evento_id) if evento_id else None,
    }


async def _processar_gatilho(est, severidade: str):
    """Arma/atualiza o evento do geofence e recomenda evacuação à Sala."""
    if not est["geofence_id"]:
        return None

    # 1 evento ativo por geofence (índice único cobre a corrida).
    evento = await db.fetchrow(
        "SELECT id FROM eventos WHERE geofence_impacto=$1 AND status='ativo'",
        est["geofence_id"],
    )
    if evento:
        evento_id = evento["id"]
        await db.execute(
            "UPDATE eventos SET severidade=$1, estacao_id=$2 WHERE id=$3",
            severidade, est["id"], evento_id,
        )
    else:
        gf = await db.fetchrow("SELECT nome FROM geofences WHERE id=$1", est["geofence_id"])
        nome = f"Cheia do {est['rio'] or 'rio'} — {gf['nome'] if gf else 'área de risco'}"
        row = await db.fetchrow(
            """INSERT INTO eventos
               (tenant_id, nome, gatilho, geofence_impacto, severidade, estacao_id, status)
               VALUES ($1,$2,'hidrologico',$3,$4,$5,'ativo') RETURNING id""",
            est["tenant_id"], nome, est["geofence_id"], severidade, est["id"],
        )
        evento_id = row["id"]

    # Quantas pessoas cadastradas estão na área (dimensiona a recomendação).
    alvos = await db.fetchrow(
        "SELECT COUNT(*) AS n FROM pessoas_protegidas WHERE geofence_id=$1", est["geofence_id"]
    )
    await db.execute(
        "INSERT INTO eventos_audit (tenant_id, ator, acao, alvo, detalhe) VALUES ($1,$2,$3,$4,$5)",
        est["tenant_id"], "sistema", "gatilho_hidrologico", str(evento_id),
        _json({"estacao": est["nome"], "severidade": severidade, "nivel": est["nivel_atual"]}),
    )

    # Recomenda à Sala (humano no loop). NÃO faz broadcast automático.
    await hub.publish("recomendacao_evacuacao", {
        "evento_id": str(evento_id),
        "geofence_id": str(est["geofence_id"]),
        "severidade": severidade,
        "estacao": est["nome"],
        "rio": est["rio"],
        "nivel_atual": est["nivel_atual"],
        "unidade": est["unidade"],
        "pessoas_na_area": alvos["n"] if alvos else 0,
    })
    return evento_id


def _json(d: dict) -> str:
    import json
    return json.dumps(d, default=str)
