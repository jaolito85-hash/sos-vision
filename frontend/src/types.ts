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
