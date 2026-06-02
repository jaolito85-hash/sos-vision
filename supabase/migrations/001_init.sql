-- SOS VISION · Defesa Civil RS — schema núcleo (§7 do blueprint)
-- Compatível com Postgres 16 puro e Supabase.
-- Geometria como GeoJSON em JSONB (point-in-polygon no app) p/ não exigir PostGIS no MVP.
-- Em produção Supabase: ativar PostGIS + RLS (ver bloco comentado ao final).

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- ───────────────────────── Tenants (multi-município) ─────────────────────────
CREATE TABLE tenants (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome        TEXT NOT NULL,
  uf          TEXT NOT NULL DEFAULT 'RS',
  centro_lat  DOUBLE PRECISION,
  centro_lng  DOUBLE PRECISION,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Áreas de risco (geofences) ────────────────────────
CREATE TABLE geofences (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome        TEXT NOT NULL,
  tipo        TEXT NOT NULL DEFAULT 'alagamento'
              CHECK (tipo IN ('alagamento','deslizamento','vendaval')),
  poligono    JSONB NOT NULL,           -- GeoJSON Polygon (lista de [lng,lat])
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Pessoas protegidas (cadastro prévio) ──────────────
CREATE TABLE pessoas_protegidas (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  telefone          TEXT NOT NULL,
  nome              TEXT,
  endereco          TEXT,
  lat               DOUBLE PRECISION,
  lng               DOUBLE PRECISION,
  household_size    INT DEFAULT 1,
  vulnerabilidades  TEXT[] DEFAULT '{}', -- acamado|oxigenio|dialise|idoso_so|crianca|cadeirante
  tem_pets          BOOLEAN DEFAULT FALSE,
  contato_confianca TEXT,
  geofence_id       UUID REFERENCES geofences(id) ON DELETE SET NULL,
  dados_sensiveis   BYTEA,               -- campos extra cifrados (AES-256) — TODO app-side
  criado_em         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, telefone)
);

-- ───────────────────────── Eventos (uma enchente/operação) ───────────────────
CREATE TABLE eventos (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome              TEXT NOT NULL,
  gatilho           TEXT,                -- cemaden|regua|manual
  geofence_impacto  UUID REFERENCES geofences(id),
  status            TEXT NOT NULL DEFAULT 'ativo' CHECK (status IN ('ativo','encerrado')),
  iniciado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
  encerrado_em      TIMESTAMPTZ
);

-- ───────────────────────── Broadcasts (alerta em massa) ──────────────────────
CREATE TABLE broadcasts (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  evento_id    UUID REFERENCES eventos(id) ON DELETE CASCADE,
  template     TEXT NOT NULL,
  geofence_id  UUID REFERENCES geofences(id),
  enviados     INT DEFAULT 0,
  entregues    INT DEFAULT 0,
  respondidos  INT DEFAULT 0,
  criado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Equipes de campo (frota) ──────────────────────────
CREATE TABLE equipes_campo (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome          TEXT NOT NULL,
  tipo          TEXT NOT NULL DEFAULT 'bombeiro'
                CHECK (tipo IN ('bombeiro','brigada','voluntario','samu','defesa_civil')),
  capacidade    INT DEFAULT 4,
  status        TEXT NOT NULL DEFAULT 'disponivel'
                CHECK (status IN ('disponivel','ocupada','offline')),
  lat           DOUBLE PRECISION,
  lng           DOUBLE PRECISION,
  token         TEXT UNIQUE,             -- login por link assinado (PWA campo)
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Chamados de resgate ───────────────────────────────
CREATE TABLE chamados_resgate (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  evento_id         UUID REFERENCES eventos(id) ON DELETE SET NULL,
  pessoa_id         UUID REFERENCES pessoas_protegidas(id) ON DELETE SET NULL,
  telefone          TEXT,
  nome              TEXT,
  origem            TEXT NOT NULL DEFAULT 'broadcast'
                    CHECK (origem IN ('broadcast','foto','link','terceiro','simulador')),
  estado            TEXT NOT NULL DEFAULT 'aguardando'
                    CHECK (estado IN ('aguardando','triado','despachado','assumido',
                                      'no_local','resgatado','em_abrigo','encerrado',
                                      'cancelado','duplicado','perdido_contato')),
  gravidade_ia      INT DEFAULT 3,       -- 1..5
  prioridade_score  INT DEFAULT 0,
  contexto_vertical TEXT,                -- terreo|andar|telhado|carro_muro|na_agua
  num_pessoas       INT DEFAULT 1,
  agua              TEXT,                -- parada|subindo_devagar|subindo_rapido
  lat               DOUBLE PRECISION,
  lng               DOUBLE PRECISION,
  acuracia_m        DOUBLE PRECISION,
  what3words        TEXT,
  dup_de            UUID REFERENCES chamados_resgate(id) ON DELETE SET NULL,
  criado_em         TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chamados_estado  ON chamados_resgate(tenant_id, estado);
CREATE INDEX idx_chamados_tel     ON chamados_resgate(tenant_id, telefone);
CREATE INDEX idx_chamados_criado  ON chamados_resgate(criado_em);

-- ───────────────────────── Despachos (chamado ↔ equipe + lock) ───────────────
CREATE TABLE despachos (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chamado_id    UUID NOT NULL REFERENCES chamados_resgate(id) ON DELETE CASCADE,
  equipe_id     UUID NOT NULL REFERENCES equipes_campo(id) ON DELETE CASCADE,
  estado        TEXT NOT NULL DEFAULT 'assumido'
                CHECK (estado IN ('assumido','a_caminho','no_local','resgatado','cancelado')),
  ts_assumido   TIMESTAMPTZ NOT NULL DEFAULT now(),
  ts_a_caminho  TIMESTAMPTZ,
  ts_no_local   TIMESTAMPTZ,
  ts_resgatado  TIMESTAMPTZ
);
-- Lock geográfico: um chamado só pode ter UM despacho ativo (não-cancelado).
CREATE UNIQUE INDEX uniq_despacho_ativo
  ON despachos(chamado_id) WHERE estado <> 'cancelado';

-- ───────────────────────── Rastreamento GPS (token-link) ─────────────────────
CREATE TABLE rastreamento_sessoes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chamado_id  UUID NOT NULL REFERENCES chamados_resgate(id) ON DELETE CASCADE,
  token       TEXT NOT NULL UNIQUE,
  expira_em   TIMESTAMPTZ,
  criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE rastreamento_pontos (
  id         BIGSERIAL PRIMARY KEY,
  sessao_id  UUID NOT NULL REFERENCES rastreamento_sessoes(id) ON DELETE CASCADE,
  lat        DOUBLE PRECISION NOT NULL,
  lng        DOUBLE PRECISION NOT NULL,
  acuracia_m DOUBLE PRECISION,
  fonte      TEXT DEFAULT 'gps' CHECK (fonte IN ('gps','w3w','cell','manual')),
  ts         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pontos_sessao ON rastreamento_pontos(sessao_id, ts);

-- ───────────────────────── Abrigos + check-ins ───────────────────────────────
CREATE TABLE abrigos (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome          TEXT NOT NULL,
  lat           DOUBLE PRECISION,
  lng           DOUBLE PRECISION,
  capacidade    INT DEFAULT 0,
  ocupacao      INT DEFAULT 0,
  pet_friendly  BOOLEAN DEFAULT FALSE,
  tem_medico    BOOLEAN DEFAULT FALSE,
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE abrigo_checkins (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  abrigo_id   UUID NOT NULL REFERENCES abrigos(id) ON DELETE CASCADE,
  chamado_id  UUID REFERENCES chamados_resgate(id) ON DELETE SET NULL,
  nome        TEXT,
  telefone    TEXT,
  ts          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Reunificação familiar ─────────────────────────────
CREATE TABLE reunificacao (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  quem_procura  TEXT,
  procurado     TEXT,
  ultimo_local  TEXT,
  status        TEXT NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto','encontrado')),
  match_id      UUID,
  criado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Vias bloqueadas (reportadas pela frota) ────────────
CREATE TABLE vias_bloqueadas (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  lat          DOUBLE PRECISION,
  lng          DOUBLE PRECISION,
  motivo       TEXT,
  reportado_por UUID REFERENCES equipes_campo(id),
  ts           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Audit LGPD ────────────────────────────────────────
CREATE TABLE eventos_audit (
  id        BIGSERIAL PRIMARY KEY,
  tenant_id UUID,
  ator      TEXT,
  acao      TEXT,
  alvo      TEXT,
  detalhe   JSONB,
  ts        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ───────────────────────── Produção Supabase (ativar depois) ─────────────────
-- ALTER TABLE chamados_resgate ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY tenant_isolation ON chamados_resgate
--   USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);
-- (repetir por tabela). Em prod, trocar WebSocket próprio por Realtime:
-- ALTER PUBLICATION supabase_realtime ADD TABLE chamados_resgate, despachos, rastreamento_pontos;
