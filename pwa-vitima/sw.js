// Service Worker mínimo — cacheia o shell p/ a página abrir mesmo com rede ruim.
const CACHE = "sos-vitima-v2";
const SHELL = ["index.html", "app.js", "manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // Nunca cacheia chamadas de API (POST de pontos etc.) — só o shell estático.
  if (e.request.method !== "GET" || url.pathname.includes("/track/")) return;
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
