// PWA da vítima — token-link de rastreamento (§5.1 + §5.3).
// Estratégias contra o "fechar a tela" que a WEB PURA permite (ver DEFESA_CIVIL_RS.md §13):
//   1. Wake Lock API — impede o aparelho de suspender a tela enquanto aberto.
//   2. Reaquisição automática ao voltar o foco (visibilitychange).
//   3. Buffer offline + retransmissão (resiliência).
// LIMITE DE PLATAFORMA: com o app realmente FECHADO, web não rastreia GPS.
// Rastreamento com app fechado exige camada nativa (Capacitor) — fase futura.

const params = new URLSearchParams(location.search);
const TOKEN = params.get("token");
const API = params.get("api") || "http://localhost:8000";
const QUEUE_KEY = `sos_queue_${TOKEN}`;

const $ = (id) => document.getElementById(id);
let enviados = 0;
let wakeLock = null;

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});

function setStatus(txt, cls) {
  $("status").textContent = txt;
  $("status").className = "val " + (cls || "");
}

// ---- Wake Lock: mantém a tela acesa para o GPS não ser suspenso ----
async function requestWakeLock() {
  try {
    if ("wakeLock" in navigator) {
      wakeLock = await navigator.wakeLock.request("screen");
      $("lock").textContent = "🔒 Tela mantida ligada automaticamente";
      wakeLock.addEventListener("release", () => { $("lock").textContent = ""; });
    } else {
      $("lock").textContent = "Mantenha a tela ligada manualmente.";
    }
  } catch {
    $("lock").textContent = "Mantenha a tela ligada manualmente.";
  }
}
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    requestWakeLock();
    flush(); // ao voltar, tenta drenar o buffer offline
  }
});

// ---- Buffer offline ----
function loadQueue() { try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]"); } catch { return []; } }
function saveQueue(q) { localStorage.setItem(QUEUE_KEY, JSON.stringify(q)); }
function showQueued() {
  const n = loadQueue().length;
  $("queued").textContent = n > 0 ? `📡 ${n} posição(ões) guardada(s) — enviando quando o sinal voltar` : "";
}

async function resolverChamado() {
  if (!TOKEN) { setStatus("link inválido", "err"); $("titulo").textContent = "Link inválido"; return false; }
  try {
    const r = await fetch(`${API}/track/${TOKEN}`);
    if (!r.ok) throw new Error();
    await r.json();
    $("titulo").textContent = "A AJUDA ESTÁ A CAMINHO";
    $("sub").textContent = "A Defesa Civil está vendo onde você está, em tempo real.";
    setStatus("conectado", "ok");
    return true;
  } catch {
    setStatus("não foi possível validar o link", "err");
    return false;
  }
}

async function flush() {
  if (!navigator.onLine) return;
  const q = loadQueue(); const rest = [];
  for (const p of q) {
    try {
      const r = await fetch(`${API}/track/${TOKEN}/ponto`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p),
      });
      if (!r.ok) throw new Error();
      enviados++;
    } catch { rest.push(p); }
  }
  saveQueue(rest);
  $("sent").textContent = enviados;
  showQueued();
}

async function enviarPonto(p) {
  try {
    const r = await fetch(`${API}/track/${TOKEN}/ponto`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p),
    });
    if (!r.ok) throw new Error();
    enviados++;
    $("sent").textContent = enviados;
    $("last").textContent = new Date().toLocaleTimeString("pt-BR");
    setStatus("enviando localização ✓", "ok");
    await flush();
  } catch {
    const q = loadQueue(); q.push(p); saveQueue(q);
    setStatus("sem internet — guardando", "warn");
    showQueued();
  }
}

function start() {
  if (!navigator.geolocation) { setStatus("GPS indisponível", "err"); return; }
  navigator.geolocation.watchPosition(
    (pos) => {
      const acc = pos.coords.accuracy;
      $("acc").textContent = `${Math.round(acc)} metros`;
      enviarPonto({ lat: pos.coords.latitude, lng: pos.coords.longitude, acuracia_m: acc, fonte: "gps" });
    },
    () => setStatus("toque em PERMITIR localização", "err"),
    { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 }
  );
}

window.addEventListener("online", flush);

(async () => {
  showQueued();
  await requestWakeLock();
  if (await resolverChamado()) start();
})();
