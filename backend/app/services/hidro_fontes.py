"""Conectores de fontes hidrológicas externas (plugável, §5.6).

O caminho PRINCIPAL de ingestão é o POST /hidrologia/estacoes/{id}/leitura — qualquer
fonte (sensor próprio da Defesa Civil, gateway CEMADEN, script agendado) empurra leituras
por ali. Este módulo traz conectores de PULL de referência para as fontes nacionais.

— ANA HidroWebService (telemetria nacional) —
  Swagger: https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html
  Requer autenticação (Identificador/Senha → token Bearer). Endpoints REST de estações
  telemétricas em https://www.snirh.gov.br/hidroweb/rest/api/ .

— CEMADEN —
  Dados de estações pluviométricas/hidrológicas; acesso via convênio/portal de dados.

Como NÃO há credenciais neste ambiente, as funções abaixo são esqueletos prontos para
preencher na implantação. O parser de exemplo mostra o mapeamento esperado → ingestão.
"""
import os
import httpx

ANA_BASE = "https://www.ana.gov.br/hidrowebservice"
ANA_TOKEN = os.getenv("ANA_TOKEN", "")  # obter via login no HidroWebService


def parse_leitura_ana(item: dict) -> float | None:
    """Mapeia um registro de telemetria do ANA para o nível em metros.
    Ajuste os nomes dos campos conforme o payload real (ver Swagger)."""
    for campo in ("Cota", "cota", "nivel", "Nivel_Adotado", "valor"):
        if campo in item and item[campo] is not None:
            try:
                # ANA costuma reportar cota em cm → converte p/ metros.
                return float(item[campo]) / 100.0
            except (TypeError, ValueError):
                return None
    return None


async def puxar_ana(codigo_estacao: str) -> float | None:
    """PULL de referência da última cota de uma estação telemétrica do ANA.
    Stub: completar a rota/headers conforme o Swagger e o token. Não chama sem token."""
    if not ANA_TOKEN:
        return None  # sem credencial → ingestão fica por POST
    url = f"{ANA_BASE}/EstacoesTelemetricas/HidroinfoanaSerieTelemetricaAdotada/v1"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                url,
                params={"Código da Estação": codigo_estacao, "Tipo Filtro Data": "DATA_LEITURA"},
                headers={"Authorization": f"Bearer {ANA_TOKEN}"},
            )
            r.raise_for_status()
            items = r.json().get("items") or []
            return parse_leitura_ana(items[-1]) if items else None
    except Exception:
        return None  # degradação graciosa — nunca derruba o ciclo
