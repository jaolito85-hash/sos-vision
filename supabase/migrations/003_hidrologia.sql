-- SOS VISION · Defesa Civil RS — Ciclo de alerta (Fases 1-2 do blueprint, §5.6)
-- Vigilância hidrológica → gatilho → evento → (recomendação de) evacuação.

-- ───────────────────────── Estações hidrológicas (régua / pluviômetro) ───────
CREATE TABLE estacoes_hidrologicas (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  codigo        TEXT,                 -- código ANA/CEMADEN (p/ o conector externo)
  nome          TEXT NOT NULL,
  tipo          TEXT NOT NULL DEFAULT 'regua_rio'
                CHECK (tipo IN ('regua_rio','pluviometro')),
  rio           TEXT,
  lat           DOUBLE PRECISION,
  lng           DOUBLE PRECISION,
  geofence_id   UUID REFERENCES geofences(id) ON DELETE SET NULL,  -- área que cobre
  unidade       TEXT NOT NULL DEFAULT 'm',  -- m (régua) | mm_h (chuva)
  nivel_atual   DOUBLE PRECISION,
  -- Níveis de referência (a Defesa Civil define por estação).
  ref_atencao   DOUBLE PRECISION,
  ref_alerta    DOUBLE PRECISION,
  ref_inundacao DOUBLE PRECISION,
  severidade    TEXT NOT NULL DEFAULT 'normal'
                CHECK (severidade IN ('normal','atencao','alerta','inundacao')),
  fonte         TEXT DEFAULT 'manual',  -- ana | cemaden | sensor_proprio | manual
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_estacoes_tenant ON estacoes_hidrologicas(tenant_id);

-- ───────────────────────── Série temporal de leituras ────────────────────────
CREATE TABLE leituras_hidrologicas (
  id         BIGSERIAL PRIMARY KEY,
  estacao_id UUID NOT NULL REFERENCES estacoes_hidrologicas(id) ON DELETE CASCADE,
  valor      DOUBLE PRECISION NOT NULL,
  ts         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_leituras_estacao ON leituras_hidrologicas(estacao_id, ts);

-- ───────────────────────── Eventos: origem do gatilho + severidade ───────────
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS severidade TEXT
  CHECK (severidade IN ('atencao','alerta','inundacao'));
ALTER TABLE eventos ADD COLUMN IF NOT EXISTS estacao_id UUID
  REFERENCES estacoes_hidrologicas(id) ON DELETE SET NULL;
-- Evita dois eventos ativos para o mesmo geofence (1 operação por área).
CREATE UNIQUE INDEX IF NOT EXISTS uniq_evento_ativo_geofence
  ON eventos(geofence_impacto) WHERE status = 'ativo';

-- ───────────────────────── Seed: estação do Taquari em Lajeado ────────────────
-- Níveis ILUSTRATIVOS (a Defesa Civil calibra na implantação). Em maio/2024 o
-- Taquari no Vale bateu recordes históricos muito acima da cota de inundação.
DO $$
DECLARE t_id UUID; gf_id UUID;
BEGIN
  SELECT id INTO t_id FROM tenants WHERE nome = 'Lajeado' LIMIT 1;
  SELECT id INTO gf_id FROM geofences WHERE tenant_id = t_id LIMIT 1;
  IF t_id IS NOT NULL THEN
    INSERT INTO estacoes_hidrologicas
      (tenant_id, codigo, nome, tipo, rio, lat, lng, geofence_id, unidade,
       nivel_atual, ref_atencao, ref_alerta, ref_inundacao, fonte)
    VALUES
      (t_id, '86720000', 'Régua Taquari - Lajeado', 'regua_rio', 'Rio Taquari',
       -29.4665, -51.9490, gf_id, 'm', 17.5, 19.0, 22.0, 26.0, 'manual');
  END IF;
END $$;
