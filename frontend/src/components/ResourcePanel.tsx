import type { Equipe, Abrigo } from "../types";

interface Props {
  equipes: Equipe[];
  abrigos: Abrigo[];
}

const ICONE_TIPO: Record<string, string> = {
  bombeiro: "🚒", brigada: "🪖", voluntario: "🙋", samu: "🚑", defesa_civil: "🛡️",
};
const COR_STATUS: Record<string, string> = {
  disponivel: "#22c55e", ocupada: "#f59e0b", offline: "#6b7280",
};
const ROTULO_STATUS: Record<string, string> = {
  disponivel: "Disponíveis", ocupada: "Ocupadas", offline: "Offline",
};

function barraCor(pct: number): string {
  if (pct >= 90) return "#ef4444";
  if (pct >= 70) return "#f59e0b";
  return "#22c55e";
}

export default function ResourcePanel({ equipes, abrigos }: Props) {
  const disponiveis = equipes.filter((e) => e.status === "disponivel").length;
  const vagasTotais = abrigos.reduce((s, a) => s + Math.max(0, a.capacidade - a.ocupacao), 0);

  // Agrupa equipes por status, na ordem disponivel → ocupada → offline.
  const grupos = ["disponivel", "ocupada", "offline"].map((st) => ({
    st, lista: equipes.filter((e) => e.status === st),
  })).filter((g) => g.lista.length > 0);

  return (
    <div className="p-3 text-sm overflow-y-auto h-full text-slate-200 space-y-4">
      {/* Frota */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-slate-100">🚤 Frota</h3>
          <span className="text-xs text-slate-400">{equipes.length} equipes · <span className="text-green-400">{disponiveis} livres</span></span>
        </div>
        {equipes.length === 0 && <div className="text-xs text-slate-500">Nenhuma equipe cadastrada.</div>}
        {grupos.map((g) => (
          <div key={g.st} className="mb-2">
            <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-1">{ROTULO_STATUS[g.st] ?? g.st}</div>
            {g.lista.map((e) => (
              <div key={e.id} className="flex items-center justify-between px-2 py-1.5 mb-1 rounded bg-slate-800 text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: COR_STATUS[e.status] ?? "#6b7280" }} />
                  <span>{ICONE_TIPO[e.tipo] ?? "🚐"} {e.nome}</span>
                </span>
                <span className="text-slate-500">cap. {e.capacidade}</span>
              </div>
            ))}
          </div>
        ))}
      </section>

      {/* Abrigos */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-slate-100">🏠 Abrigos</h3>
          <span className="text-xs text-slate-400">{vagasTotais} vagas livres</span>
        </div>
        {abrigos.length === 0 && <div className="text-xs text-slate-500">Nenhum abrigo cadastrado.</div>}
        {abrigos.map((a) => {
          const pct = a.capacidade > 0 ? Math.round((100 * a.ocupacao) / a.capacidade) : 0;
          const vagas = Math.max(0, a.capacidade - a.ocupacao);
          return (
            <div key={a.id} className="px-2 py-2 mb-1.5 rounded bg-slate-800 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-100">{a.nome}</span>
                <span className="flex items-center gap-1">
                  {a.pet_friendly && <span title="Aceita pets">🐾</span>}
                  {a.tem_medico && <span title="Tem médico">⚕️</span>}
                </span>
              </div>
              <div className="h-2 bg-slate-700 rounded mt-1.5 overflow-hidden">
                <div className="h-full rounded" style={{ width: `${Math.min(100, pct)}%`, background: barraCor(pct) }} />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 mt-0.5">
                <span>{a.ocupacao}/{a.capacidade} ({pct}%)</span>
                <span>{vagas} vaga(s)</span>
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
