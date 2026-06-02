"""Orquestra a criação de um chamado de resgate a partir de uma entrada
(webhook WhatsApp ou simulador). Pipeline:

  dedup → (se dup, anexa) → classificação IA → prioridade → grava →
  cria sessão de rastreamento (token-link) → publica realtime.
"""
import secrets
from .. import db
from ..realtime import hub
from . import dedup, priority as prio, classifier


async def criar_chamado(
    tenant_id,
    *,
    telefone: str | None = None,
    nome: str | None = None,
    origem: str = "broadcast",
    lat: float | None = None,
    lng: float | None = None,
    acuracia_m: float | None = None,
    contexto: str | None = None,
    num_pessoas: int = 1,
    agua: str | None = None,
    texto_livre: str | None = None,
) -> dict:
    # 1) Anti-duplicação
    dup_de = await dedup.encontrar_duplicata(tenant_id, telefone, lat, lng)

    # 2) Classificação (texto livre, se houver; senão usa o que veio estruturado)
    if texto_livre:
        cls = await classifier.classificar(texto_livre)
        contexto = contexto or cls.get("contexto")
        agua = agua or cls.get("agua")
        gravidade = cls.get("gravidade", 3)
        if cls.get("num_pessoas"):
            num_pessoas = cls["num_pessoas"]
    else:
        gravidade = 5 if (contexto in ("telhado", "na_agua") or agua == "subindo_rapido") else 3

    # 3) Vincula pessoa pré-cadastrada (puxa vulnerabilidades p/ prioridade)
    pessoa = None
    if telefone:
        pessoa = await db.fetchrow(
            "SELECT id, nome, vulnerabilidades FROM pessoas_protegidas WHERE tenant_id=$1 AND telefone=$2",
            tenant_id, telefone,
        )
    vulnerabilidades = list(pessoa["vulnerabilidades"]) if pessoa else []

    # 4) Score de prioridade
    score = prio.calcular(
        gravidade_ia=gravidade, vulnerabilidades=vulnerabilidades,
        agua=agua, contexto=contexto, num_pessoas=num_pessoas,
    )

    estado = "duplicado" if dup_de else "triado"

    row = await db.fetchrow(
        """INSERT INTO chamados_resgate
           (tenant_id, pessoa_id, telefone, nome, origem, estado, gravidade_ia,
            prioridade_score, contexto_vertical, num_pessoas, agua, lat, lng, acuracia_m, dup_de)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
           RETURNING *""",
        tenant_id, pessoa["id"] if pessoa else None, telefone,
        nome or (pessoa["nome"] if pessoa else None), origem, estado, gravidade,
        score, contexto, num_pessoas, agua, lat, lng, acuracia_m, dup_de,
    )
    chamado = dict(row)

    # 5) Sessão de rastreamento (token-link GPS) — só para chamados reais
    token = None
    if not dup_de:
        token = secrets.token_urlsafe(16)
        await db.execute(
            "INSERT INTO rastreamento_sessoes (chamado_id, token) VALUES ($1,$2)",
            chamado["id"], token,
        )

    await db.execute(
        "INSERT INTO eventos_audit (tenant_id, ator, acao, alvo, detalhe) VALUES ($1,$2,$3,$4,$5)",
        tenant_id, "bot", "criar_chamado", str(chamado["id"]),
        db_json({"dup_de": str(dup_de) if dup_de else None, "score": score}),
    )

    # 6) Realtime → Sala de Comando
    await hub.publish("chamado_novo", {**chamado, "token": token})

    return {**chamado, "token": token, "dup_de": dup_de}


def db_json(d: dict):
    import json
    return json.dumps(d, default=str)
