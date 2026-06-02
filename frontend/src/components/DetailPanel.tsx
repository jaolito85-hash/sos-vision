import { useEffect, useState } from "react";
import type { Chamado, Equipe } from "../types";
import { api } from "../api";

interface Props {
  chamado: Chamado | null;
  onChanged: () => void;
}

export default function DetailPanel({ chamado, onChanged }: Props) {
  const [sugestoes, setSugestoes] = useState<Equipe[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setErro(null);
    if (chamado && ["aguardando", "triado", "despachado"].includes(chamado.estado)) {
      api.sugestoes(chamado.id).then(setSugestoes).catch(() => setSugestoes([]));
    } else {
      setSugestoes([]);
    }
  }, [chamado?.id, chamado?.estado]);

  if (!chamado) {
    return <div className="p-4 text-sm text-slate-500">Selecione um chamado na fila ou no mapa.</div>;
  }

  async function despachar(equipe_id: string) {
    setBusy(true); setErro(null);
    try {
      await api.despachar(chamado!.id, equipe_id);
      onChanged();
    } catch (e: any) {
      setErro(e.message.includes("409") ? "Já existe equipe a caminho deste chamado." : e.message);
    } finally { setBusy(false); }
  }

  async function transitar(estado: string) {
    setBusy(true);
    try { await api.transitar(chamado!.id, estado); onChanged(); }
    catch (e: any) { setErro(e.message); }
    finally { setBusy(false); }
  }

  // Em produção o PWA da vítima é servido em /vitima do mesmo domínio da Sala.
  // Em dev, defina VITE_VITIMA_URL (ex.: http://localhost:5180).
  const vitimaBase = import.meta.env.VITE_VITIMA_URL || `${location.origin}/vitima`;
  const track = chamado.track_token
    ? `${vitimaBase}/index.html?token=${chamado.track_token}&api=${api.base}`
    : null;

  return (
    <div className="p-3 text-sm overflow-y-auto h-full text-slate-200">
      <h3 className="font-semibold text-base text-slate-100">{chamado.nome ?? "Anônimo"}</h3>
      <div className="text-slate-500 text-xs mb-2">{chamado.telefone ?? "sem telefone"} · {chamado.origem}</div>

      <dl className="grid grid-cols-2 gap-1 text-xs mb-3">
        <dt className="text-slate-500">Estado</dt><dd className="font-medium text-slate-100">{chamado.estado}</dd>
        <dt className="text-slate-500">Prioridade</dt><dd className="font-mono text-slate-100">{chamado.prioridade_score}</dd>
        <dt className="text-slate-500">Gravidade IA</dt><dd className="text-slate-200">{chamado.gravidade_ia}/5</dd>
        <dt className="text-slate-500">Pessoas</dt><dd className="text-slate-200">{chamado.num_pessoas}</dd>
        <dt className="text-slate-500">Contexto</dt><dd className="text-slate-200">{chamado.contexto_vertical ?? "—"}</dd>
        <dt className="text-slate-500">Água</dt><dd className="text-slate-200">{chamado.agua ?? "—"}</dd>
        <dt className="text-slate-500">GPS</dt>
        <dd className="text-slate-200">{chamado.lat ? `${chamado.lat.toFixed(5)}, ${chamado.lng!.toFixed(5)}` : "sem ponto"}</dd>
        {chamado.acuracia_m != null && (<><dt className="text-slate-500">± precisão</dt><dd className="text-slate-200">{Math.round(chamado.acuracia_m)} m</dd></>)}
      </dl>

      {track && (
        <a href={track} target="_blank" rel="noreferrer"
           className="block text-xs text-sky-400 underline mb-3 break-all">
          Abrir token-link da vítima (PWA) ↗
        </a>
      )}

      {erro && <div className="bg-red-950 text-red-300 text-xs p-2 rounded mb-2 border border-red-800">{erro}</div>}

      {["aguardando", "triado", "despachado"].includes(chamado.estado) && (
        <div className="mb-3">
          <div className="font-medium text-xs mb-1 text-slate-300">Despachar equipe (mais próximas):</div>
          {sugestoes.length === 0 && <div className="text-xs text-slate-500">Nenhuma equipe disponível.</div>}
          {sugestoes.map((e) => (
            <button key={e.id} disabled={busy} onClick={() => despachar(e.id)}
              className="w-full flex justify-between items-center px-2 py-1.5 mb-1 rounded bg-slate-800 hover:bg-sky-900 disabled:opacity-50 text-xs text-slate-100">
              <span>🚤 {e.nome} <span className="text-slate-500">({e.tipo})</span></span>
              <span className="text-slate-400">{e.distancia_m != null ? `${Math.round(e.distancia_m)} m` : ""}</span>
            </button>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-1">
        {chamado.estado === "no_local" && (
          <button disabled={busy} onClick={() => transitar("resgatado")}
            className="px-2 py-1 bg-green-600 text-white rounded text-xs">Marcar resgatado</button>
        )}
        {["resgatado"].includes(chamado.estado) && (
          <button disabled={busy} onClick={() => transitar("em_abrigo")}
            className="px-2 py-1 bg-blue-600 text-white rounded text-xs">Encaminhado a abrigo</button>
        )}
        {!["encerrado", "cancelado", "duplicado"].includes(chamado.estado) && (
          <button disabled={busy} onClick={() => transitar("cancelado")}
            className="px-2 py-1 bg-slate-700 text-slate-200 rounded text-xs">Cancelar</button>
        )}
      </div>
    </div>
  );
}
