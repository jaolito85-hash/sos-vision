import type { Estacao } from "../types";

interface Props { estacoes: Estacao[]; }

const SEV_COR: Record<string, string> = {
  normal: "#64748b", atencao: "#eab308", alerta: "#f97316", inundacao: "#ef4444",
};
const SETA: Record<string, string> = { subindo: "↑", descendo: "↓", estavel: "→" };
const SETA_COR: Record<string, string> = { subindo: "#ef4444", descendo: "#22c55e", estavel: "#94a3c4" };

export default function HidroPanel({ estacoes }: Props) {
  if (!estacoes.length) {
    return <div className="p-4 text-sm text-slate-500">Nenhuma estação monitorada.</div>;
  }
  return (
    <div className="p-3 text-sm overflow-y-auto h-full text-slate-200 space-y-2">
      {estacoes.map((e) => {
        const sev = e.prev_severidade ?? e.severidade ?? "normal";
        const tend = e.tendencia ?? "estavel";
        // posição do nível atual entre atenção e inundação (para a barra)
        const refs = [e.ref_atencao, e.ref_alerta, e.ref_inundacao].filter((v): v is number => v != null);
        const max = refs.length ? Math.max(...refs) * 1.1 : null;
        const pct = max && e.nivel_atual != null ? Math.min(100, (100 * e.nivel_atual) / max) : null;
        return (
          <div key={e.id} className="rounded bg-slate-800 p-2.5">
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-100">{e.rio ?? e.nome}</span>
              <span className="text-xs font-bold uppercase" style={{ color: SEV_COR[sev] }}>{sev}</span>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-1.5 text-xs">
              <div className="flex justify-between"><span className="text-slate-400">☔ Chuva 24h</span>
                <b>{e.chuva_prevista_mm != null ? `${e.chuva_prevista_mm} mm` : "—"}</b></div>
              <div className="flex justify-between"><span className="text-slate-400">🌊 Vazão</span>
                <b>{e.vazao_m3s != null ? `${e.vazao_m3s} m³/s` : "—"}</b></div>
              <div className="flex justify-between"><span className="text-slate-400">Tendência</span>
                <b style={{ color: SETA_COR[tend] }}>{SETA[tend] ?? "→"} {tend}</b></div>
              <div className="flex justify-between"><span className="text-slate-400">Pico prev.</span>
                <b>{e.vazao_pico_m3s != null ? `${e.vazao_pico_m3s} m³/s` : "—"}</b></div>
            </div>
            {pct != null && (
              <div className="mt-2">
                <div className="h-2 bg-slate-700 rounded overflow-hidden">
                  <div className="h-full rounded" style={{ width: `${pct}%`, background: SEV_COR[sev] }} />
                </div>
                <div className="flex justify-between text-[11px] text-slate-500 mt-0.5">
                  <span>nível {e.nivel_atual ?? "?"}{e.unidade}</span>
                  <span>alerta {e.ref_alerta ?? "?"} · inund. {e.ref_inundacao ?? "?"}</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
