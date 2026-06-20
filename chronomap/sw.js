/* ChronoMap Service Worker — App-Shell und Daten für Offline-Betrieb cachen.
   Strategie: network-first (immer aktuell, wenn online), Cache nur als
   Offline-Reserve. So erscheinen Updates ohne manuelles Leeren des Caches. */
const CACHE = "chronomap-v4";

const YEARS = [-100, 100, 500, 1000, 1200, 1356, 1500, 1648, 1815, 1871,
  1914, 1919, 1938, 1942, 1961, 1990, 2024];
const SETTLEMENT_YEARS = [100, 500, 1000, 1200, 1356, 1500, 1648, 1815, 1871,
  1914, 1919, 1938, 1942, 1961, 1990, 2024];
const CULTURE_YEARS = [1000, 1200, 1356, 1500];

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
]
  .concat(YEARS.map((y) => `data/eras/${y}.json`))
  .concat(YEARS.map((y) => `data/layers/territories/${y}.geojson`))
  .concat(SETTLEMENT_YEARS.map((y) => `data/layers/settlements/${y}.json`))
  .concat(CULTURE_YEARS.map((y) => `data/layers/cultures/${y}.geojson`));

self.addEventListener("install", (e) => {
  // Einzeln cachen, damit ein fehlendes Asset den Install nicht abbricht.
  e.waitUntil(
    caches.open(CACHE).then((c) =>
      Promise.allSettled(ASSETS.map((u) => c.add(u)))
    ).then(() => self.skipWaiting())
  );
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
  if (new URL(e.request.url).origin !== self.location.origin) return;
  // Network-first: online stets frische Inhalte, Cache als Reserve (offline).
  e.respondWith(
    fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(e.request))
  );
});
