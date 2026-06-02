import { useCallback, useEffect, useMemo, useState } from "react";
import CommandMap from "./components/CommandMap";
import QueuePanel from "./components/QueuePanel";
import DetailPanel from "./components/DetailPanel";
import AlertPanel from "./components/AlertPanel";
import { api } from "./api";
import { connectRealtime } from "./realtime";
import type { Chamado, Equipe, Abrigo, Estacao, Geofence, Recomendacao, Rota } from "./types";

const SEV_ORDEM = ["normal", "atencao", "alerta", "inundacao"];

export default function App() {
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [equipes, setEquipes] = useState<Equipe[]>([]);
  const [abrigos, setAbrigos] = useState<Abrigo[]>([]);
  const [estacoes, setEstacoes] = useState<Estacao[]>([]);
  const [geofencesRaw, setGeofencesRaw] = useState<Geofence[]>([]);
  const [recomendacoes, setRecomendacoes] = useState<Recomendacao[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rota, setRota] = useState<Rota | null>(null);
  const [online, setOnline] = useState(false);

  const carregar = useCallback(async () => {
    const [c, e, a, est, gf, rec] = await Promise.all([
      api.listarChamados(), api.equipes(), api.abrigos(),
      api.estacoes(), api.geofences(), api.recomendacoes(),
    ]);
    setChamados(c); setEquipes(e); setAbrigos(a);
    setEstacoes(est); setGeofencesRaw(gf); setRecomendacoes(rec);
  }, []);

  useEffect(() => {
    carregar().catch(console.error);
    const poll = setInterval(() => carregar().catch(() => {}), 15000);
    const disconnect = connectRealtime((ev) => {
      setOnline(true);
      if (["chamado_novo", "chamado_estado", "ponto_gps", "equipe_pos", "abrigo_update",
           "fila_repontuada", "hidro_leitura", "recomendacao_evacuacao"].includes(ev.type)) {
        carregar().catch(() => {});
      }
    });
    return () => { clearInterval(poll); disconnect(); };
  }, [carregar]);

  // Anota cada geofence com a severidade da recomendação ativa (mancha de inundação).
  const geofences = useMemo(() => {
    const sevPorGeo: Record<string, string> = {};
    recomendacoes.forEach((r) => {
      const atual = sevPorGeo[r.geofence_id];
      if (!atual || SEV_ORDEM.indexOf(r.severidade) > SEV_ORDEM.indexOf(atual)) {
        sevPorGeo[r.geofence_id] = r.severidade;
      }
    });
    return geofencesRaw.map((g) => ({ ...g, severidade: sevPorGeo[g.id] ?? null }));
  }, [geofencesRaw, recomendacoes]);

  // Trocar de chamado limpa a rota desenhada (evita rota órfã de outro chamado).
  const selecionar = useCallback((id: string) => { setSelectedId(id); setRota(null); }, []);

  const selecionado = chamados.find((c) => c.id === selectedId) ?? null;
  const ativos = chamados.filter((c) =>
    ["aguardando", "triado", "despachado", "assumido", "no_local", "perdido_contato"].includes(c.estado)
  );
  const resgatados = chamados.filter((c) => ["resgatado", "em_abrigo"].includes(c.estado)).length;

  // Estação mais crítica para o KPI do header.
  const estacaoCritica = useMemo(() => {
    return [...estacoes].sort(
      (a, b) => SEV_ORDEM.indexOf(b.severidade) - SEV_ORDEM.indexOf(a.severidade)
    )[0];
  }, [estacoes]);
  const sevCor: Record<string, string> = {
    normal: "text-slate-400", atencao: "text-yellow-400",
    alerta: "text-orange-400", inundacao: "text-red-400",
  };

  return (
    <div className="h-full flex flex-col bg-slate-950 text-slate-100">
      <header className="bg-slate-900 border-b border-slate-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-black tracking-tight">SOS<span className="text-sky-400">VISION</span></span>
          <span className="text-slate-400 text-sm">Defesa Civil · Lajeado/RS</span>
        </div>
        <div className="flex items-center gap-5 text-sm">
          {estacaoCritica && (
            <span className="flex items-center gap-1.5">
              🌊 <span className="text-slate-400">{estacaoCritica.rio ?? estacaoCritica.nome}</span>
              <b className={sevCor[estacaoCritica.severidade] ?? "text-slate-300"}>
                {estacaoCritica.nivel_atual}{estacaoCritica.unidade}
              </b>
              <span className={`uppercase text-xs ${sevCor[estacaoCritica.severidade]}`}>
                {estacaoCritica.severidade}
              </span>
            </span>
          )}
          {recomendacoes.length > 0 && (
            <span className="text-red-400 font-bold animate-pulse">
              ⚠ {recomendacoes.length} evacuação(ões)
            </span>
          )}
          <span>🔴 {ativos.length} ativos</span>
          <span>🟢 {resgatados} resgatados</span>
          <span className={online ? "text-green-400" : "text-yellow-400"}>
            {online ? "● realtime" : "○ conectando"}
          </span>
        </div>
      </header>

      <div className="flex-1 flex min-h-0">
        <aside className="w-80 border-r border-slate-800 flex flex-col min-h-0 bg-slate-900">
          <QueuePanel chamados={chamados} selectedId={selectedId} onSelect={selecionar} />
        </aside>

        <main className="flex-1 min-w-0 relative">
          <AlertPanel recomendacoes={recomendacoes} onConfirmado={carregar} />
          <CommandMap
            chamados={chamados}
            equipes={equipes}
            abrigos={abrigos}
            estacoes={estacoes}
            geofences={geofences}
            selectedId={selectedId}
            onSelect={selecionar}
            rota={rota}
          />
        </main>

        <aside className="w-80 border-l border-slate-800 min-h-0 bg-slate-900">
          <DetailPanel chamado={selecionado} equipes={equipes} rota={rota}
                       onRota={setRota} onChanged={carregar} />
        </aside>
      </div>
    </div>
  );
}
