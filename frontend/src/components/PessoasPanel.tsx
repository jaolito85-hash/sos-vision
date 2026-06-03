import { useState } from "react";
import type { Pessoa, Geofence } from "../types";
import { api } from "../api";

interface Props {
  pessoas: Pessoa[];
  geofences: Geofence[];
  onChanged: () => void;
}

export default function PessoasPanel({ pessoas, geofences, onChanged }: Props) {
  const [f, setF] = useState({ nome: "", telefone: "", lat: "", lng: "", geofence_id: "", vuln: "", pet: false });
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function salvar() {
    if (!f.telefone.trim()) { setErro("Telefone é obrigatório."); return; }
    setBusy(true); setErro(null);
    try {
      await api.criarPessoa({
        telefone: f.telefone.trim(), nome: f.nome.trim() || null,
        lat: f.lat ? parseFloat(f.lat) : null, lng: f.lng ? parseFloat(f.lng) : null,
        geofence_id: f.geofence_id || null, tem_pets: f.pet,
        vulnerabilidades: f.vuln ? f.vuln.split(",").map((s) => s.trim()).filter(Boolean) : [],
      });
      setF({ nome: "", telefone: "", lat: "", lng: "", geofence_id: "", vuln: "", pet: false });
      onChanged();
    } catch (e: any) { setErro("Falha ao cadastrar."); }
    finally { setBusy(false); }
  }

  const inp = "w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100";
  return (
    <div className="p-3 text-sm overflow-y-auto h-full text-slate-200 space-y-3">
      <section className="space-y-1.5">
        <h3 className="font-semibold text-slate-100">➕ Cadastrar pessoa</h3>
        <input className={inp} placeholder="Nome" value={f.nome} onChange={(e) => setF({ ...f, nome: e.target.value })} />
        <input className={inp} placeholder="Telefone (5551...)" value={f.telefone} onChange={(e) => setF({ ...f, telefone: e.target.value })} />
        <div className="flex gap-1.5">
          <input className={inp} placeholder="lat" value={f.lat} onChange={(e) => setF({ ...f, lat: e.target.value })} />
          <input className={inp} placeholder="lng" value={f.lng} onChange={(e) => setF({ ...f, lng: e.target.value })} />
        </div>
        <select className={inp} value={f.geofence_id} onChange={(e) => setF({ ...f, geofence_id: e.target.value })}>
          <option value="">— área de risco —</option>
          {geofences.map((g) => <option key={g.id} value={g.id}>{g.nome}</option>)}
        </select>
        <input className={inp} placeholder="vulnerabilidades (ex: idoso_so, acamado)" value={f.vuln} onChange={(e) => setF({ ...f, vuln: e.target.value })} />
        <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={f.pet} onChange={(e) => setF({ ...f, pet: e.target.checked })} /> Tem pets</label>
        {erro && <div className="text-red-400 text-xs">{erro}</div>}
        <button onClick={salvar} disabled={busy} className="w-full bg-sky-700 hover:bg-sky-600 disabled:opacity-50 rounded px-2 py-1.5 text-xs font-semibold text-white">
          {busy ? "Salvando…" : "Cadastrar"}
        </button>
      </section>
      <section>
        <div className="text-xs text-slate-400 mb-1">{pessoas.length} pessoa(s) protegida(s)</div>
        {pessoas.map((p) => (
          <div key={p.id} className="px-2 py-1.5 mb-1 rounded bg-slate-800 text-xs flex justify-between">
            <span>{p.nome ?? "—"} {p.tem_pets && "🐾"} {p.vulnerabilidades?.length ? <span className="text-amber-400">⚠</span> : ""}</span>
            <span className="text-slate-500">{p.telefone}</span>
          </div>
        ))}
      </section>
    </div>
  );
}
