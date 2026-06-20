// Lädt den Epochen-Index, einzelne Snapshots und deren Ebenendateien.
// Alles wird gecacht, damit erneutes Anfahren eines Jahres sofort ist.
import { DATA_BASE, ERAS_INDEX, FACTIONS_FILE } from "./config.js";

const cache = new Map();

async function getJSON(url) {
  if (cache.has(url)) return cache.get(url);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} bei ${url}`);
  const data = await res.json();
  cache.set(url, data);
  return data;
}

export async function loadIndex() {
  return getJSON(ERAS_INDEX);
}

export async function loadFactions() {
  const data = await getJSON(FACTIONS_FILE);
  return data.factions || {};
}

// Lädt ein Snapshot-Manifest samt aller referenzierten Ebenendaten.
export async function loadSnapshot(entry) {
  const snap = await getJSON(DATA_BASE + entry.file);
  const layers = snap.layers || {};
  const [territories, cultures, settlements] = await Promise.all([
    layers.territories ? getJSON(DATA_BASE + layers.territories) : null,
    layers.cultures ? getJSON(DATA_BASE + layers.cultures) : null,
    layers.settlements ? getJSON(DATA_BASE + layers.settlements) : null,
  ]);
  return { meta: snap, territories, cultures, settlements };
}
