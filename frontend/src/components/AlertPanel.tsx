import { useState } from "react";
import type { Recomendacao, Broadcast } from "../types";
import { api } from "../api";

const SEV: Record<string, { rotulo: string; cls: string; icone: string }> = {
  atencao: { rotulo: "ATENÇÃO", cls: "bg-yellow-500/90 border-yellow-300", icone: "🟡" },
  alerta: { rotulo: "ALERTA", cls: "bg-orange-600/90 border-orange-400", icone: "🟠" },
  inundacao: { rotulo: "INUNDAÇÃO", cls: "bg-red-600/95 border-red-400", icone: "🔴" },
};

interface Props {
  recomendacoes: Recomendacao[];
  broadcasts: Broadcast[];
  onConfirmado: () => void;
}

export default function AlertPanel({ recomendacoes, broadcasts, onConfirmado }: Props) {
  const [disparados, setDisparados] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState<string | null>(null);

  if (recomendacoes.length === 0) return null;

  async function confirmar(r: Recomendacao) {
    setBusy(r.evento_id);
    try {
      const res = await api.broadcast(r.geofence_id, r.evento_id);
      setDisparados((d) => ({ ...d, [r.evento_id]: res.enviados }));
      onConfirmado();
    } catch {
      /* mostra erro inline poderia ser adicionado */
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 w-[min(680px,92%)] space-y-2">
      {recomendacoes.map((r) => {
        const sev = SEV[r.severidade] ?? SEV.alerta;
        const bc = broadcasts.find((b) => b.evento_id === r.evento_id);
        const enviados = disparados[r.evento_id] ?? bc?.enviados;
        return (
          <div key={r.evento_id}
            className={`text-white rounded-xl border-2 shadow-2xl backdrop-blur px-4 py-3 ${sev.cls}`}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="font-black text-sm tracking-wide flex items-center gap-2">
                  {sev.icone} EVACUAÇÃO RECOMENDADA · {sev.rotulo}
                </div>
                <div className="text-sm mt-0.5 opacity-95">
                  {r.estacao ?? "Estação"} — {r.rio ?? "rio"} em{" "}
                  <b>{r.nivel_atual}{r.unidade}</b> · <b>{r.pessoas_na_area}</b> pessoa(s) cadastrada(s) na área
                </div>
              </div>
              {enviados == null ? (
                <button
                  onClick={() => confirmar(r)}
                  disabled={busy === r.evento_id}
                  className="shrink-0 bg-white text-slate-900 font-bold rounded-lg px-4 py-2 text-sm hover:bg-slate-100 disabled:opacity-60">
                  {busy === r.evento_id ? "Enviando…" : "Confirmar e disparar broadcast"}
                </button>
              ) : (
                <span className="shrink-0 bg-black/30 rounded-lg px-3 py-2 text-sm font-bold text-right">
                  ✓ {enviados} enviados
                  {bc && <div className="text-xs font-normal opacity-90">{bc.respondidos} responderam</div>}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
