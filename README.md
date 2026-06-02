# SOS VISION · Defesa Civil RS — MVP executável

Monorepo do MVP da vertical **Defesa Civil** (enchente/alagamento/deslizamento) do SOS VISION,
especializado para o Rio Grande do Sul. Materializa o §10 do `../DEFESA_CIVIL_RS.md`.

> **Tese:** não é "botão de pânico" — é **coordenação de resgate em massa**. O moat:
> anti-duplicação + despacho com lock, localização precisa quando o endereço não serve,
> resiliência quando a internet cai, e cadastro prévio de vulneráveis.

---

## O que já funciona nesta fatia vertical

Caminho ponta-a-ponta demonstrável:

1. **Webhook WhatsApp** (Cloud API) recebe `3` / localização / foto → cria **chamado de resgate**.
2. Backend roda **anti-duplicação** (clustering geográfico + telefone) e **score de prioridade**.
3. Chamado aparece na **Sala de Comando** (mapa MapLibre + fila) **em tempo real** (WebSocket).
4. Operador **despacha** uma equipe → **lock** impede atendimento duplicado.
5. **PWA de campo** mostra o chamado à equipe → botões `A caminho → No local → Resgatado`.
6. **PWA da vítima** (token-link) transmite **GPS ao vivo** (offline-first) → trilha no mapa.

**Ciclo de alerta (Fases 1-2)** — vigilância hidrológica → gatilho → recomendação → evacuação:

7. **Leitura hidrológica** (de qualquer fonte) → classifica severidade contra os níveis de
   referência da estação (atenção/alerta/inundação).
8. Ao cruzar **alerta/inundação**, o **gatilho arma um evento** e **recomenda evacuação à
   Sala** — sem broadcast automático (humano no loop, evita falso positivo/pânico — §8).
9. Operador **confirma** → **broadcast** por geofence (triagem 1/2/3).
10. Cidadão responde **1/2** → recebe **abrigo mais próximo com vaga** (respeitando pets) **+ rota**.

Stubs com TODO claros: conector externo ANA/CEMADEN (estrutura pronta em
`services/hidro_fontes.py`; ingestão principal via POST), broadcast real por template Cloud,
SMS/satélite fallback, reunificação, UI da recomendação na Sala, rota real evitando vias alagadas.

### Demonstrar o ciclo de alerta

```powershell
# pega o id da estação seedada (Régua Taquari - Lajeado)
$EST = (curl -s http://localhost:8000/hidrologia/estacoes | ConvertFrom-Json)[0].id
# rio sobe e cruza o nível de alerta (22m) -> dispara o gatilho
curl -X POST "http://localhost:8000/hidrologia/estacoes/$EST/leitura" -H "Content-Type: application/json" -d '{"valor":23.0}'
# a Sala veria a recomendação:
curl http://localhost:8000/hidrologia/recomendacoes
# operador confirma -> broadcast por geofence (responda 1/2/3 no WhatsApp p/ ver abrigo+rota)
```

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + asyncpg + redis (pub/sub + fila) |
| Banco | Postgres 16 (compatível Supabase; RLS documentado em `supabase/migrations`) |
| Realtime | WebSocket (backend) — em produção troca por Supabase `postgres_changes` |
| Worker | Python standalone, modular (`worker_defesa_civil.py`) |
| Sala de Comando | Vite + React + TS + Tailwind + **MapLibre GL** |
| PWA vítima / campo | HTML + JS offline-first (Service Worker + localStorage) |
| Mensageria | Camada plugável: WhatsApp Cloud API (prod) · simulador (dev) · SMS (stub) |

---

## Subir local (Windows / PowerShell)

Pré-requisitos: **Docker Desktop** e **Node 20+**.

```powershell
# 1. infra + backend + worker
Copy-Item .env.example .env
docker compose up --build         # postgres, redis, backend (:8000), worker

# 2. Sala de Comando (outro terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173

# 3. PWAs (outro terminal) — servidor estático simples
cd pwa-vitima ; npx serve -l 5180 .     # vítima  → use o link gerado no fluxo
cd pwa-campo  ; npx serve -l 5181 .      # campo
```

Backend health: http://localhost:8000/health · API docs: http://localhost:8000/docs

### Demonstrar sem WhatsApp real

Use o endpoint **simulador** (mesmo parser do webhook real):

```powershell
# cria um SOS "3" com localização em Lajeado/Vale do Taquari
curl -X POST http://localhost:8000/webhook/simulate -H "Content-Type: application/json" -d '{
  "phone": "5551999990001", "name": "Maria",
  "kind": "sos", "lat": -29.4669, "lng": -51.9614,
  "contexto": "telhado", "num_pessoas": 3, "agua": "subindo_rapido"
}'
```

O chamado aparece na Sala em tempo real. Despache uma equipe, abra a PWA de campo,
e abra o token-link da vítima (retornado na resposta) para ver o GPS ao vivo.

---

## Estrutura

```
sos-vision-defesa-civil/
├─ docker-compose.yml
├─ supabase/migrations/      # schema (§7) + seed demo (tenant, geofence, abrigo, equipes)
├─ backend/app/
│  ├─ messaging/             # camada plugável (cloud api / simulador / sms)
│  ├─ services/              # dedup, priority, dispatch, classifier
│  ├─ routers/               # webhook, chamados, equipes, abrigos, eventos, rastreamento, ws
│  └─ state_machine.py       # estados canônicos do chamado
├─ worker/                   # timers (sem-resposta, follow-up) + fila async
├─ frontend/                 # Sala de Comando (React + MapLibre)
├─ pwa-vitima/               # token-link de rastreamento GPS
└─ pwa-campo/                # app de campo da equipe de resgate
```

Veja o ciclo de vida do chamado em `backend/app/state_machine.py` e o modelo de dados
em `supabase/migrations/001_init.sql`.
