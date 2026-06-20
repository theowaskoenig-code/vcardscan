/* ChronoMap Service Worker — App-Shell und Daten für Offline-Betrieb cachen. */
const CACHE = "chronomap-v1";

const ASSETS = [
  "./", "index.html", "manifest.json", "icon.png",
  "css/theme.css", "css/layout.css", "css/map.css",
  "vendor/leaflet/leaflet.js", "vendor/leaflet/leaflet.css",
  "vendor/leaflet/images/marker-icon.png",
  "vendor/leaflet/images/marker-icon-2x.png",
  "vendor/leaflet/images/marker-shadow.png",
  "vendor/leaflet/images/layers.png",
  "vendor/leaflet/images/layers-2x.png",
  "js/app.js", "js/config.js", "js/i18n.js", "js/eras.js",
  "js/timeline.js", "js/mapView.js", "js/factions.js",
  "js/layers/territories.js", "js/layers/cultures.js", "js/layers/settlements.js",
  "data/geo/land.geojson", "data/geo/lakes.geojson",
  "data/eras/index.json", "data/factions/factions.json",
  "data/eras/1000.json", "data/eras/1200.json", "data/eras/1356.json", "data/eras/1500.json",
  "data/layers/territories/1000.geojson", "data/layers/territories/1200.geojson",
  "data/layers/territories/1356.geojson", "data/layers/territories/1500.geojson",
  "data/layers/cultures/1356.geojson",
  "data/layers/settlements/1000.json", "data/layers/settlements/1200.json",
  "data/layers/settlements/1356.json", "data/layers/settlements/1500.json",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => hit)
    )
  );
});
