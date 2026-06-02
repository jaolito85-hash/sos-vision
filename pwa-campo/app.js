// PWA de campo — equipe de resgate (§4.4). Login por token assinado na URL.
// ?token=campo-b01 (ver seed) &api=http://localhost:8000

const params = new URLSearchParams(location.search);
const TOKEN = params.get("token");
const API = params.get("api") || "http://localhost:8000";
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
        <a class="nav" style="text-align:center;text-decoration:none;display:block;line-height:1.4" href="${nav}" target="_blank">🧭 Navegar</a>
        <button class="b1" onclick="acao('${c.id}','a_caminho')">A caminho</button>
        <button class="b2" onclick="acao('${c.id}','no_local')">No local</button>
        <button class="b3" onclick="acao('${c.id}','resgatado')">✓ Resgatado</button>
      </div>
    </div>`;
  }).join("");
}
window.acao = acao;

// Reporta posição da equipe ao vivo (aparece no mapa da Sala).
if (navigator.geolocation && TOKEN) {
  navigator.geolocation.watchPosition((pos) => {
    $("pos").textContent = `sua posição: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
    fetch(`${API}/equipes/por-token/${TOKEN}/posicao`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
    }).catch(() => {});
  }, () => {}, { enableHighAccuracy: true, maximumAge: 10000 });
}

window.addEventListener("online", flushActions);
render();
setInterval(render, 10000);
