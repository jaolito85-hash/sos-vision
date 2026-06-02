// PWA de campo — equipe de resgate (§4.4). Login por token assinado na URL.
// ?token=campo-b01 (ver seed) &api=http://localhost:8000

const params = new URLSearchParams(location.search);
const TOKEN = params.get("token");
// API: usa ?api= se vier no link; senão deduz do próprio domínio (api.<host>);
// só cai em localhost no dev. Permite link curto (/campo/?token=campo-b01).
const _h = location.hostname;
const API = params.get("api") || (
  /^(localhost|127\.|0\.0\.0\.0$)/.test(_h)
    ? "http://localhost:8000"
    : `${location.protocol}//api.${_h}`
);
const ACTION_QUEUE = `campo_actions_${TOKEN}`;

const $ = (id) => document.getElementById(id);

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});

const CTX = { telhado: "🏔️ telhado", na_agua: "🌊 na água", carro_muro: "🚗 carro/muro",
              andar: "🪜 andar de cima", terreo: "🏠 térreo" };

function loadActions() { try { return JSON.parse(localStorage.getItem(ACTION_QUEUE) || "[]"); } catch { return []; } }
function saveActions(a) { localStorage.setItem(ACTION_QUEUE, JSON.stringify(a)); }

async function flushActions() {
  const q = loadActions(); const rest = [];
  for (const a of q) {
    try {
      const r = await fetch(a.url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(a.body) });
      if (!r.ok) throw new Error();
    } catch { rest.push(a); }
  }
  saveActions(rest);
}

// Ação resiliente: tenta enviar; se falhar, enfileira offline e atualiza a UI otimista.
async function acao(chamado_id, estado) {
  const url = `${API}/equipes/despacho/${chamado_id}/${TOKEN}/estado`;
  const body = { estado };
  try {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error();
  } catch {
    const q = loadActions(); q.push({ url, body }); saveActions(q);
  }
  setTimeout(render, 400);
}

async function render() {
  if (!TOKEN) { $("sub").textContent = "token ausente"; return; }
  await flushActions();
  let data;
  try {
    data = await (await fetch(`${API}/equipes/por-token/${TOKEN}`)).json();
  } catch {
    $("sub").textContent = "offline — mostrando última lista";
    return;
  }
  $("equipe").textContent = data.equipe.nome;
  $("sub").textContent = `${data.equipe.tipo} · cap. ${data.equipe.capacidade} · ${data.chamados.length} chamado(s)`;

  const list = $("list");
  if (!data.chamados.length) { list.innerHTML = '<div class="empty">Nenhum chamado atribuído.</div>'; return; }

  list.innerHTML = data.chamados.map((c) => {
    const nav = c.lat ? `https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}` : "#";
    const water = c.agua === "subindo_rapido" ? '<span class="water">água subindo rápido!</span>' : "";
    return `<div class="card">
      <h2>${c.nome || "Anônimo"} ${c.num_pessoas > 1 ? "👥 " + c.num_pessoas : ""}</h2>
      <div class="meta"><span class="tag">${CTX[c.contexto_vertical] || c.contexto_vertical || "?"}</span> ${water}</div>
      <div class="meta">estado: ${c.estado_despacho || c.estado} · prioridade ${c.prioridade_score}</div>
      <div class="btns">
        ${c.lat ? `<button class="b-rota" onclick="abrirRota(${c.lat},${c.lng},'${(c.nome || "Vítima").replace(/'/g, "")}')">🗺️ Traçar rota</button>` : ""}
        <a class="nav" style="text-align:center;text-decoration:none;display:block;line-height:1.4" href="${nav}" target="_blank">🧭 Navegar</a>
        <button class="b1" onclick="acao('${c.id}','a_caminho')">A caminho</button>
        <button class="b2" onclick="acao('${c.id}','no_local')">No local</button>
        <button class="b3" onclick="acao('${c.id}','resgatado')">✓ Resgatado</button>
      </div>
    </div>`;
  }).join("");
}
window.acao = acao;

// Reporta posição da equipe ao vivo (aparece no mapa da Sala) e guarda em `minhaPos`
// para usar como origem ao traçar a rota.
let minhaPos = null;
if (navigator.geolocation && TOKEN) {
  navigator.geolocation.watchPosition((pos) => {
    minhaPos = { lat: pos.coords.latitude, lng: pos.coords.longitude };
    $("pos").textContent = `sua posição: ${minhaPos.lat.toFixed(4)}, ${minhaPos.lng.toFixed(4)}`;
    fetch(`${API}/equipes/por-token/${TOKEN}/posicao`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: minhaPos.lat, lng: minhaPos.lng }),
    }).catch(() => {});
  }, () => {}, { enableHighAccuracy: true, maximumAge: 10000 });
}

// ───────────────────────── Mini-mapa de rota (MapLibre via CDN) ───────────────
let _map = null, _markers = [], _destino = null;
function ensureMap() {
  if (_map) return _map;
  _map = new maplibregl.Map({
    container: "mapa",
    style: "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    center: [-51.96, -29.46], zoom: 12,
  });
  _map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  return _map;
}
function clearMarkers() { _markers.forEach((m) => m.remove()); _markers = []; }

async function abrirRota(lat, lng, nome) {
  if (!minhaPos) { alert("Aguardando seu GPS. Permita a localização e tente novamente."); return; }
  _destino = { lat, lng };
  $("navMapa").href = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  $("rotaInfo").textContent = "Traçando rota…";
  $("mapaWrap").style.display = "block";
  const m = ensureMap();
  setTimeout(() => m.resize(), 60); // o container acabou de ficar visível
  try {
    const r = await fetch(`${API}/rotas?de=${minhaPos.lat},${minhaPos.lng}&para=${lat},${lng}`);
    if (!r.ok) throw new Error();
    desenharRota(m, await r.json(), nome);
  } catch {
    $("rotaInfo").textContent = "Não foi possível traçar a rota. Use o botão Navegar.";
  }
}

function desenharRota(m, rota, nome) {
  const fc = { type: "FeatureCollection", features: [{ type: "Feature", geometry: rota.geometry, properties: {} }] };
  const draw = () => {
    if (m.getSource("rota")) {
      m.getSource("rota").setData(fc);
    } else {
      m.addSource("rota", { type: "geojson", data: fc });
      m.addLayer({ id: "rota-casing", type: "line", source: "rota",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#0c4a6e", "line-width": 9 } });
      m.addLayer({ id: "rota-line", type: "line", source: "rota",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#38bdf8", "line-width": 5 } });
    }
    clearMarkers();
    _markers.push(new maplibregl.Marker({ color: "#22c55e" }).setLngLat([minhaPos.lng, minhaPos.lat]).addTo(m));
    _markers.push(new maplibregl.Marker({ color: "#ef4444" }).setLngLat([_destino.lng, _destino.lat]).addTo(m));
    const coords = rota.geometry.coordinates;
    const b = coords.reduce((bb, c) => bb.extend(c), new maplibregl.LngLatBounds(coords[0], coords[0]));
    m.fitBounds(b, { padding: 70, maxZoom: 16 });
    const km = (rota.distancia_m / 1000).toFixed(1), min = Math.round(rota.duracao_s / 60);
    $("rotaInfo").textContent = `${nome}: ${km} km · ~${min} min`;
  };
  if (m.isStyleLoaded()) draw(); else m.once("load", draw);
}
window.abrirRota = abrirRota;
document.getElementById("fecharMapa").onclick = () => { $("mapaWrap").style.display = "none"; };

// A frota marca a posição atual como via intransitável (rotas passam a desviar).
async function reportarVia() {
  if (!minhaPos) { alert("Aguardando seu GPS. Permita a localização e tente de novo."); return; }
  const motivo = prompt("Motivo (ex.: alagada, queda de árvore, deslizamento):", "alagada");
  if (motivo === null) return;
  try {
    const r = await fetch(`${API}/equipes/por-token/${TOKEN}/via-bloqueada`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: minhaPos.lat, lng: minhaPos.lng, motivo }),
    });
    if (!r.ok) throw new Error();
    alert("✅ Via bloqueada reportada. As próximas rotas vão desviar deste ponto.");
  } catch { alert("Falha ao reportar. Tente novamente."); }
}
document.getElementById("reportarVia").onclick = reportarVia;

window.addEventListener("online", flushActions);
render();
setInterval(render, 10000);
