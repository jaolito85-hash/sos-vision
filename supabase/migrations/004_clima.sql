-- SOS VISION · Defesa Civil RS — previsão climática/hidrológica (Open-Meteo)
-- Campos preenchidos pelo worker a partir do Open-Meteo (Forecast + Flood/GloFAS).
ALTER TABLE estacoes_hidrologicas
  ADD COLUMN IF NOT EXISTS chuva_prevista_mm DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS vazao_m3s          DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS vazao_pico_m3s     DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS tendencia          TEXT,  -- subindo | estavel | descendo
  ADD COLUMN IF NOT EXISTS prev_severidade    TEXT,  -- normal | atencao | alerta | inundacao
  ADD COLUMN IF NOT EXISTS prev_atualizado_em TIMESTAMPTZ;
