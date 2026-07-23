// sw.js: オフライン閲覧のためのService Worker
// バージョンを上げると古いキャッシュが破棄され、新しいファイルに置き換わります。
const CACHE_VERSION = "us-rock-history-v4";

const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./css/style.css",
  "./js/main.js",
  "./js/router.js",
  "./js/data.js",
  "./js/components/artist-card.js",
  "./js/views/timeline.js",
  "./js/views/artists.js",
  "./js/views/artist-detail.js",
  "./js/views/genres.js",
  "./js/views/relations.js",
  "./js/views/guide.js",
  "./js/views/glossary.js",
  "./js/views/favorites.js",
  "./js/views/stats.js",
  "./js/vendor/d3.v7.min.js",
  "./data/artists.json",
  "./data/genres.json",
  "./data/relations.json",
  "./data/album_guide.json",
  "./data/glossary.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  if (new URL(request.url).origin !== location.origin) return; // Spotify等の外部リンクは対象外

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => cached);
    })
  );
});
