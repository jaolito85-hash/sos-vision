import type { Chamado, Equipe, Abrigo, Estacao, Geofence, Recomendacao } from "./types";

const API = import.meta.env.VITE_API ?? "http://localhost:8000";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export const api = {
  base: API,
  listarChamados: () => fetch(`${API}/chamados`).then(j<Chamado[]>),
  detalhe: (id: string) => fetch(`${API}/chamados/${id}`).then(j<any>),
  sugestoes: (id: string) => fetch(`${API}/chamados/${id}/sugestoes`).then(j<Equipe[]>),
  despachar: (id: string, equipe_id: string) =>
    fetch(`${API}/chamados/${id}/despachar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ equipe_id }),
    }).then(j<any>),
  transitar: (id: string, estado: string) =>
    fetch(`${API}/chamados/${id}/estado`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado }),
    }).then(j<any>),
  equipes: () => fetch(`${API}/equipes`).then(j<Equipe[]>),
  abrigos: () => fetch(`${API}/abrigos`).then(j<Abrigo[]>),
  estacoes: () => fetch(`${API}/hidrologia/estacoes`).then(j<Estacao[]>),
  geofences: () => fetch(`${API}/eventos/geofences`).then(j<Geofence[]>),
  recomendacoes: () => fetch(`${API}/hidrologia/recomendacoes`).then(j<Recomendacao[]>),
  broadcast: (geofence_id: string, evento_id?: string) =>
    fetch(`${API}/eventos/broadcast`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ geofence_id, evento_id }),
    }).then(j<{ broadcast_id: string; enviados: number }>),
};
