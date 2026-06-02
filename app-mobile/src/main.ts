// App nativo da camada B (§13 do blueprint) — rastreamento que sobrevive ao
// app em background / tela bloqueada, via @capacitor-community/background-geolocation.
//
// Estratégia única de código para duas plataformas:
//   - NATIVO (Android/iOS via Capacitor): usa BackgroundGeolocation.addWatcher,
//     que mantém um foreground service e continua transmitindo com o app
//     minimizado e a tela bloqueada.
//   - WEB (navegador, durante o desenvolvimento): cai para navigator.geolocation.
//
// Fluxo: ATIVAR -> POST /track/ativar {telefone} -> recebe token -> inicia o
// watcher -> cada posição vira POST /track/{token}/ponto (mesma API do PWA).

import { Capacitor, registerPlugin } from "@capacitor/core";
import type { BackgroundGeolocationPlugin } from "@capacitor-community/background-geolocation";

const BackgroundGeolocation =
  registerPlugin<BackgroundGeolocationPlugin>("BackgroundGeolocation");

const $ = (id: string) => document.getElementById(id) as HTMLElement;
const elTel = () => (document.getElementById("tel") as HTMLInputElement).value.trim();
const elApi = () => (document.getElementById("api") as HTMLInputElement).value.trim().replace(/\/$/, "");

const isNative = Capacitor.isNativePlatform();
let watcherId: string | null = null;
let webWatchId: number | null = null;
let token: string | null = null;
let enviados = 0;

$("plat").textContent = isNative
  ? `modo nativo (${Capacitor.getPlatform()}) — rastreia com o app fechado`
  : "modo navegador — só rastreia com a aba aberta (build no celular p/ background)";

function setStatus(txt: string, cls = "") {
  const el = $("st");
  el.textContent = txt;
  el.className = "val " + cls;
}

async function enviarPonto(lat: number, lng: number, acc: number | null) {
  if (!token) return;
  try {
    const r = await fetch(`${elApi()}/track/${token}/ponto`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lng, acuracia_m: acc, fonte: "gps" }),
    });
    if (!r.ok) throw new Error();
    enviados++;
    $("sent").textContent = String(enviados);
    $("acc").textContent = acc != null ? `${Math.round(acc)} m` : "—";
    $("last").textContent = new Date().toLocaleTimeString("pt-BR");
    setStatus("protegido — transmitindo ✓", "ok");
  } catch {
    setStatus("sem conexão — tentando…", "warn");
  }
}

async function ativarSessao(): Promise<boolean> {
  try {
    const r = await fetch(`${elApi()}/track/ativar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telefone: elTel() }),
    });
    if (!r.ok) throw new Error();
    const d = await r.json();
    token = d.token;
    return !!token;
  } catch {
    setStatus("não conectou ao servidor", "err");
    return false;
  }
}

async function ligar() {
  setStatus("ativando…", "warn");
  if (!(await ativarSessao())) return;

  if (isNative) {
    watcherId = await BackgroundGeolocation.addWatcher(
      {
        backgroundMessage: "A Defesa Civil está te protegendo. Não desligue.",
        backgroundTitle: "SOS Defesa Civil — proteção ativa",
        requestPermissions: true,
        stale: false,
        distanceFilter: 10, // metros entre atualizações
      },
      (location, error) => {
        if (error) {
          setStatus("permita a localização 'o tempo todo'", "err");
          return;
        }
        if (location) enviarPonto(location.latitude, location.longitude, location.accuracy);
      }
    );
  } else {
    if (!navigator.geolocation) {
      setStatus("GPS indisponível", "err");
      return;
    }
    webWatchId = navigator.geolocation.watchPosition(
      (pos) => enviarPonto(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy),
      () => setStatus("permita a localização", "err"),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 }
    );
  }

  const btn = $("btn");
  btn.textContent = "DESATIVAR PROTEÇÃO";
  btn.className = "big-btn off";
  setStatus("protegido ✓", "ok");
}

async function desligar() {
  if (isNative && watcherId) {
    await BackgroundGeolocation.removeWatcher({ id: watcherId });
    watcherId = null;
  }
  if (webWatchId != null) {
    navigator.geolocation.clearWatch(webWatchId);
    webWatchId = null;
  }
  token = null;
  const btn = $("btn");
  btn.textContent = "ATIVAR PROTEÇÃO";
  btn.className = "big-btn on";
  setStatus("desativado");
}

$("btn").addEventListener("click", () => {
  if (watcherId || webWatchId != null) desligar();
  else ligar();
});
