-- Seed demo — Lajeado/RS (Vale do Taquari), área castigada em maio/2024.
DO $$
DECLARE
  t_id   UUID;
  gf_id  UUID;
  ev_id  UUID;
BEGIN
  INSERT INTO tenants (nome, uf, centro_lat, centro_lng)
  VALUES ('Lajeado', 'RS', -29.4669, -51.9614)
  RETURNING id INTO t_id;

  -- Geofence de risco: faixa ribeirinha que acompanha o curso do rio Taquari em
  -- Lajeado (margem oeste, bairros baixos). APROXIMAÇÃO geográfica do leito —
  -- em produção, substituir pela mancha oficial do CPRM/Defesa Civil (shapefile/GeoJSON).
  INSERT INTO geofences (tenant_id, nome, tipo, poligono)
  VALUES (t_id, 'Faixa ribeirinha do Taquari (aprox.)', 'alagamento',
    '{"type":"Polygon","coordinates":[[
      [-51.9485,-29.4475],[-51.9448,-29.4545],[-51.9442,-29.4625],[-51.9468,-29.4702],
      [-51.9505,-29.4768],[-51.9548,-29.4815],[-51.9592,-29.4795],[-51.9598,-29.4705],
      [-51.9582,-29.4615],[-51.9576,-29.4528],[-51.9542,-29.4472],[-51.9485,-29.4475]
    ]]}'::jsonb)
  RETURNING id INTO gf_id;

  INSERT INTO eventos (tenant_id, nome, gatilho, geofence_impacto)
  VALUES (t_id, 'Cheia do Taquari - demo', 'manual', gf_id)
  RETURNING id INTO ev_id;

  -- Equipes de campo (frota).
  INSERT INTO equipes_campo (tenant_id, nome, tipo, capacidade, status, lat, lng, token) VALUES
    (t_id, 'Bombeiros B-01',     'bombeiro',   6, 'disponivel', -29.4640, -51.9600, 'campo-b01'),
    (t_id, 'Brigada Voluntária', 'voluntario', 4, 'disponivel', -29.4700, -51.9650, 'campo-vol1'),
    (t_id, 'Defesa Civil DC-1',  'defesa_civil',4, 'disponivel', -29.4680, -51.9580, 'campo-dc1');

  -- Abrigos.
  INSERT INTO abrigos (tenant_id, nome, lat, lng, capacidade, ocupacao, pet_friendly, tem_medico) VALUES
    (t_id, 'Ginásio Municipal',     -29.4580, -51.9700, 300, 120, FALSE, TRUE),
    (t_id, 'Escola Estadual Centro',-29.4610, -51.9550, 150,  40, TRUE,  FALSE);

  -- Pessoa vulnerável pré-cadastrada (acamada) dentro da área de risco.
  INSERT INTO pessoas_protegidas
    (tenant_id, telefone, nome, endereco, lat, lng, household_size, vulnerabilidades, tem_pets, geofence_id)
  VALUES
    (t_id, '5551988887777', 'Dona Alzira', 'Rua das Flores, 123', -29.4660, -51.9520, 1,
     ARRAY['acamado','idoso_so'], TRUE, gf_id);
END $$;
