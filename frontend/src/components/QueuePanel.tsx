import type { Chamado } from "../types";

const ROTULO_ESTADO: Record<string, string> = {
  aguardando: "Aguardando", triado: "Na fila", despachado: "Despachado",
  assumido: "Equipe a caminho", no_local: "No local", resgatado: "Resgatado",
  em_abrigo: "Em abrigo", perdido_contato: "Sem contato", duplicado: "Duplicado",
};

const COR_ESTADO: Record<string, string> = {
  aguardando: "bg-red-500", triado: "bg-red-500", despachado: "bg-orange-500",
  assumido: "bg-orange-500", no_local: "bg-yellow-500", resgatado: "bg-green-500",
  em_abrigo: "bg-blue-500", perdido_contato: "bg-purple-500", duplicado: "bg-gray-400",
};

const ROTULO_CTX: Record<string, string> = {
  telhado: "🏔️ telhado", na_agua: "🌊 na água", carro_muro: "🚗 carro/muro",
  andar: "🪜 andar de cima", terreo: "🏠 térreo",
};

interface Props {
  chamados: Chamado[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function QueuePanel({ chamados, selectedId, onSelect }: Props) {
  const fila = chamados.filter((c) => c.estado !== "duplicado");
  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b border-slate-800 bg-slate-950 text-slate-100 text-sm font-semibold flex justify-between">
        <span>Fila de resgate</span>
        <span className="text-slate-400">{fila.length} ativos</span>
      </div>
      <div className="overflow-y-auto flex-1">
        {fila.length === 0 && (
          <div className="p-4 text-sm text-slate-500">Sem chamados ativos.</div>
        )}
        {fila.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={`w-full text-left px-3 py-2 border-b border-slate-800 hover:bg-slate-800 transition-colors ${
              c.id === selectedId ? "bg-slate-800 border-l-4 border-l-sky-500" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-sm text-slate-100">{c.nome ?? "Anônimo"}</span>
              <span className="text-xs font-mono bg-slate-700 text-slate-100 rounded px-1.5 py-0.5">
                {c.prioridade_score}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-400 flex-wrap">
              <span className={`inline-block w-2 h-2 rounded-full ${COR_ESTADO[c.estado] ?? "bg-red-500"}`} />
              {ROTULO_ESTADO[c.estado] ?? c.estado}
              {c.contexto_vertical && <span>· {ROTULO_CTX[c.contexto_vertical] ?? c.contexto_vertical}</span>}
              {c.num_pessoas > 1 && <span>· 👥 {c.num_pessoas}</span>}
              {c.agua === "subindo_rapido" && <span className="text-red-400 font-semibold">· água subindo!</span>}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
