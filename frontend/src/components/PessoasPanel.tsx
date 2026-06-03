import { useState } from "react";
import type { Pessoa, Geofence } from "../types";
import { api } from "../api";

interface Props {
  pessoas: Pessoa[];
  geofences: Geofence[];
  onChanged: () => void;
}

export default function PessoasPanel({ pessoas, geofences, onChanged }: Props) {
  const vazio = { nome: "", telefone: "", endereco: "", lat: null as number | null, lng: null as number | null, geofence_id: "", vuln: "", pet: false };
  const [f, setF] = useState(vazio);
  const [busy, setBusy] = useState(false);
  const [geo, setGeo] = useState<"idle" | "buscando" | "ok" | "erro">("idle");
  const [erro, setErro] = useState<string | null>(null);

  // Geocodificação: endereço → lat/lng (Nominatim/OpenStreetMap, grátis, sem chave).
  async function localizar() {
    if (!f.endereco.trim()) { setErro("Digite o endereço primeiro."); return; }
    setGeo("buscando"); setErro(null);
    try {
      const q = encodeURIComponent(f.endereco + ", RS, Brasil");
      const r = await fetch(`https://nominatim.openstreetmap.org/search?q=${q}&format=json&limit=1&countrycodes=br`,
        { headers: { "Accept-Language": "pt-BR" } });
      const arr = await r.json();
      if (!arr.length) { setGeo("erro"); setErro("Endereço não encontrado. Tente incluir cidade/bairro."); return; }
      setF((s) => ({ ...s, lat: parseFloat(arr[0].lat), lng: parseFloat(arr[0].lon) }));
      setGeo("ok");
    } catch { setGeo("erro"); setErro("Falha ao localizar. Verifique a conexão."); }
  }

  async function salvar() {
    if (!f.telefone.trim()) { setErro("Telefone é obrigatório."); return; }
    if (f.lat == null && !f.geofence_id) { setErro("Localize o endereço ou escolha a área de risco."); return; }
    setBusy(true); setErro(null);
    try {
      await api.criarPessoa({
        telefone: f.telefone.trim(), nome: f.nome.trim() || null, endereco: f.endereco.trim() || null,
        lat: f.lat, lng: f.lng, geofence_id: f.geofence_id || null, tem_pets: f.pet,
        vulnerabilidades: f.vuln ? f.vuln.split(",").map((s) => s.trim()).filter(Boolean) : [],
      } as Partial<Pessoa>);
      setF(vazio); setGeo("idle");
      onChanged();
    } catch { setErro("Falha ao cadastrar."); }
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
          <input className={inp} placeholder="Endereço (rua, nº, bairro, cidade)" value={f.endereco}
            onChange={(e) => { setF({ ...f, endereco: e.target.value }); setGeo("idle"); }} />
          <button onClick={localizar} disabled={geo === "buscando"}
            className="shrink-0 bg-slate-700 hover:bg-slate-600 rounded px-2 text-xs whitespace-nowrap">📍 Localizar</button>
        </div>
        {geo === "buscando" && <div className="text-[11px] text-slate-400">buscando endereço…</div>}
        {geo === "ok" && f.lat != null && (
          <div className="text-[11px] text-green-400">✓ localizado ({f.lat.toFixed(4)}, {f.lng!.toFixed(4)})</div>
        )}
        <select className={inp} value={f.geofence_id} onChange={(e) => setF({ ...f, geofence_id: e.target.value })}>
          <option value="">— área de risco (bairro) —</option>
          {geofences.map((g) => <option key={g.id} value={g.id}>{g.nome}</option>)}
        </select>
        <input className={inp} placeholder="vulnerabilidades (ex: idoso_so, acamado)" value={f.vuln} onChange={(e) => setF({ ...f, vuln: e.target.value })} />
        <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={f.pet} onChange={(e) => setF({ ...f, pet: e.target.checked })} /> Tem pets</label>
        <p className="text-[11px] text-slate-500">Digite o endereço e toque em <b>Localizar</b> — o sistema acha as coordenadas. Ou escolha só a área de risco.</p>
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
