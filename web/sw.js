// Offline support (spec §6.1): cache the app shell on install, serve it cache-first, and
// refresh the cache in the background so a new version arrives on the next visit.
// Bump CACHE when the file list changes.

const CACHE = "horn-hero-v1";
const FILES = [
  "./", "index.html", "manifest.webmanifest", "css/app.css", "data/levels.json",
  "assets/cover.jpg", "assets/icon-192.png", "assets/icon-512.png",
  "js/app.js", "js/audio/mic.js", "js/audio/sfx.js", "js/audio/simulator.js", "js/audio/tracker.js",
  "js/audio/yin.js", "js/core/feedback.js", "js/core/holdTimer.js", "js/core/levels.js", "js/core/notes.js",
  "js/core/profile.js", "js/core/session.js", "js/core/transpose.js", "js/core/tuning.js",
  "js/storage/store.js", "js/ui/clef.js", "js/ui/game.js", "js/ui/screens.js", "js/ui/settings.js",
  "js/ui/widgets.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== location.origin) return;
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(event.request, { ignoreSearch: true });
      const network = fetch(event.request)
        .then((response) => {
          if (response.ok) cache.put(event.request, response.clone());
          return response;
        })
        .catch(() => cached);
      return cached ?? network;
    }),
  );
});
