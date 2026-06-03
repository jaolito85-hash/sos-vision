export interface Chamado {
  id: string;
  nome: string | null;
  telefone: string | null;
  estado: string;
  origem: string;
  gravidade_ia: number;
  prioridade_score: number;
  contexto_vertical: string | null;
  num_pessoas: number;
  agua: string | null;
  lat: number | null;
  lng: number | null;
  acuracia_m: number | null;
  dup_de: string | null;
  track_token: string | null;
  criado_em: string;
}

export interface Equipe {
  id: string;
  nome: string;
  tipo: string;
  capacidade: number;
  status: string;
  lat: number | null;
  lng: number | null;
  distancia_m?: number | null;
}

export interface Abrigo {
  id: string;
  nome: string;
  lat: number;
  lng: number;
  capacidade: number;
  ocupacao: number;
  pet_friendly: boolean;
  tem_medico: boolean;
}

export interface Estacao {
  id: string;
  nome: string;
  rio: string | null;
  tipo: string;
  lat: number | null;
  lng: number | null;
  unidade: string;
  nivel_atual: number | null;
  ref_atencao: number | null;
  ref_alerta: number | null;
  ref_inundacao: number | null;
  severidade: string; // normal | atencao | alerta | inundacao
  geofence_id: string | null;
  geofence_nome?: string | null;
  // Previsão (Open-Meteo, via worker)
  chuva_prevista_mm?: number | null;
  vazao_m3s?: number | null;
  vazao_pico_m3s?: number | null;
  tendencia?: string | null; // subindo | estavel | descendo
  prev_severidade?: string | null;
}

export interface Geofence {
  id: string;
  nome: string;
  tipo: string;
  poligono: any; // GeoJSON Polygon
  severidade?: string | null; // derivado das recomendações ativas
}

export interface Rota {
  geometry: any; // GeoJSON LineString
  distancia_m: number;
  duracao_s: number;
  fonte: string; // ors | osrm
  evitou: number; // nº de vias bloqueadas desviadas
}

export interface ViaBloqueada {
  id: string;
  lat: number;
  lng: number;
  motivo: string | null;
  ts: string;
}

export interface Broadcast {
  id: string;
  evento_id: string | null;
  geofence_id: string;
  enviados: number;
  entregues: number;
  respondidos: number;
  criado_em: string;
}

export interface Pessoa {
  id: string;
  telefone: string;
  nome: string | null;
  lat: number | null;
  lng: number | null;
  vulnerabilidades: string[];
  tem_pets: boolean;
  geofence_id: string | null;
}

export interface Recomendacao {
  evento_id: string;
  nome: string;
  severidade: string;
  geofence_id: string;
  estacao: string | null;
  rio: string | null;
  nivel_atual: number | null;
  unidade: string | null;
  pessoas_na_area: number;
}
