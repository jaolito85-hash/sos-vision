const CACHE = "sos-campo-v2";
const SHELL = ["index.html", "app.js", "manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname.includes("/equipes/")) return;
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
