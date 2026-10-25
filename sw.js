// SchoolFlow — service worker per il funzionamento offline.
// NON tocca i voti: quelli restano nel localStorage del telefono.
// Strategia: con internet scarica sempre la versione più recente (e la salva);
// senza internet usa l'ultima versione salvata.
const CACHE = "schoolflow-v1";
const FILES = ["/", "/index.html", "/SchoolFlow-logo.png", "/manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Pagina dell'app: prima la rete (aggiornamenti immediati), poi la copia salvata
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put("/index.html", copy));
          }
          return res;
        })
        .catch(() =>
          caches.match("/index.html").then((r) => r || caches.match("/"))
        )
    );
    return;
  }

  // Altri file (logo, manifest): prima la copia salvata, poi la rete
  event.respondWith(
    caches.match(req).then(
      (cached) =>
        cached ||
        fetch(req).then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
    )
  );
});
