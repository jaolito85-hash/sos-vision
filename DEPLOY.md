# Deploy — Demo pública (Coolify + Evolution API)

Guia para subir o MVP como **ambiente online estável para demonstrar a prefeituras**.
Stack: backend (FastAPI) + worker + Postgres + Redis + frontend (nginx servindo Sala + PWAs).
WhatsApp via **Evolution API** no MVP.

> **Decisão de produto:** o MVP usa **Evolution API** (rápido e barato para demo/piloto).
> **Após o MVP, migrar para a WhatsApp Cloud API oficial (Meta)** — mais cara, mas com SLA
> e menor risco de ban. A troca é só `MESSAGING_CHANNEL=cloud` + credenciais `WHATSAPP_*`,
> sem mexer no fluxo (camada de mensageria plugável). Ver `backend/app/messaging/`.

---

## 0. Pré-requisitos
- VPS com **Coolify** instalado e funcionando.
- **Domínio** registrado (você já tem).
- Acesso ao painel de DNS do domínio.

## 1. DNS — apontar subdomínios para o VPS
Crie 2 (ou 3) registros **A** apontando para o IP do VPS:
| Subdomínio | Aponta para | Serve |
|---|---|---|
| `app.SEU_DOMINIO` | IP do VPS | Sala de Comando + `/vitima` + `/campo` |
| `api.SEU_DOMINIO` | IP do VPS | Backend/API (inclui WebSocket `wss://.../ws`) |
| `evo.SEU_DOMINIO` | IP do VPS | Evolution API (opcional, passo 5) |

## 2. Criar o recurso no Coolify
1. **New Resource → Docker Compose** (a partir do repositório Git do projeto).
2. Selecione o arquivo **`docker-compose.prod.yml`**.
3. Em **Environment Variables**, cole o conteúdo de `.env.prod.example` já preenchido
   (senha do Postgres, `SEU_DOMINIO`, chaves do Evolution). O Coolify usa isso como `.env`.
4. **Build arg do frontend:** garanta que `VITE_API=https://api.SEU_DOMINIO` está nas variáveis
   (o compose já repassa como build arg).

## 3. Associar domínios aos serviços (Coolify)
No recurso, em cada serviço, configure o domínio + porta:
- **frontend** → `https://app.SEU_DOMINIO` · porta **80**
  (serve a **landing** em `/`, a **Sala de Comando** em `/sala`, e os PWAs em `/vitima` e `/campo`)
- **backend** → `https://api.SEU_DOMINIO` · porta **8000**

O Coolify (Traefik) emite o **HTTPS via Let's Encrypt** automaticamente e faz o proxy,
inclusive o **upgrade de WebSocket** (o realtime da Sala usa `wss://api.SEU_DOMINIO/ws`).
`postgres`, `redis` e `worker` **não** recebem domínio (ficam internos).

## 4. Deploy
Clique **Deploy**. Na primeira subida o Postgres roda as migrations
(`supabase/migrations/001..003`), criando o schema + o seed de demo (Lajeado/RS).
Verifique:
- `https://api.SEU_DOMINIO/health` → `{"status":"ok","tenant":"..."}`
- `https://api.SEU_DOMINIO/docs` → Swagger
- `https://app.SEU_DOMINIO` → Sala (abre no satélite)

## 5. Evolution API (WhatsApp do MVP)
Suba o Evolution como **outro recurso** no Coolify (imagem oficial `atendai/evolution-api`),
com seu próprio Postgres/Redis (segue a doc do Evolution), domínio `evo.SEU_DOMINIO` e uma
`AUTHENTICATION_API_KEY`. Depois:
1. Crie uma **instância** (ex.: `sosvision`) e conecte o número escaneando o **QR code**.
2. Configure o **webhook** da instância para:
   `https://api.SEU_DOMINIO/webhook/evolution` (evento `messages.upsert`).
3. No `.env` do nosso stack, preencha `EVOLUTION_URL=https://evo.SEU_DOMINIO`,
   `EVOLUTION_KEY=...`, `EVOLUTION_INSTANCE=sosvision` e `MESSAGING_CHANNEL=evolution`. Redeploy.

> Sem o Evolico configurado, o sistema cai no canal **simulador** — a demo na Sala continua
> funcionando via `POST /webhook/simulate` (útil para apresentar sem depender de um número).

## 6. Demonstração
- Abra a Sala em `app.SEU_DOMINIO`.
- Suba o rio (gatilho de evacuação):
  ```bash
  EST=$(curl -s https://api.SEU_DOMINIO/hidrologia/estacoes | python -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
  curl -X POST https://api.SEU_DOMINIO/hidrologia/estacoes/$EST/leitura -H "Content-Type: application/json" -d '{"valor":27.5}'
  ```
- Crie um SOS de exemplo: `POST https://api.SEU_DOMINIO/webhook/simulate` (ver README).
- Com Evolution conectado, manda mensagem real do WhatsApp para o número da instância.

## 7. ⚠️ Avisos para uma demo PÚBLICA
- **Sem autenticação ainda:** a Sala fica aberta. Para a demo, **use apenas dados
  fictícios** (o seed é de exemplo) — **não cadastre cidadãos reais** (LGPD). Se quiser
  restringir o acesso, ative **Basic Auth** no Coolify para o domínio `app.`.
- Antes de um **piloto real** com dados de pessoas: implementar login de operadores + RLS
  multi-tenant + criptografia AES-256 dos campos sensíveis (próxima fase).
- **Backups:** habilite backup automático do volume `pgdata` no Coolify.

## 8. Atualizações
Novo commit → **Redeploy** no Coolify. Mudanças de schema: adicione uma migration
`004_*.sql` (as do initdb só rodam em banco novo; para banco existente, rode a migration
manualmente via console do Postgres no Coolify).
