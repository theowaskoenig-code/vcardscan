// Einstiegspunkt: lädt Daten, baut Karte, Zeitleiste und Fraktionsbereich.
import { DEFAULT_YEAR } from "./config.js";
import { T } from "./i18n.js";
import { loadIndex, loadFactions, loadSnapshot } from "./eras.js";
import { Timeline } from "./timeline.js";
import { MapView } from "./mapView.js";
import { FactionPanel } from "./factions.js";

const $ = (id) => document.getElementById(id);

const visibility = { territories: true, settlements: true, cultures: false };

let map, panel, timeline;
let currentSnapshot = null; // {meta, territories, cultures, settlements}
let indexByYear = new Map(); // year -> index-entry

function setStatus(msg, isError) {
  const el = $("status");
  if (!msg) { el.style.display = "none"; return; }
  el.style.display = "block";
  el.textContent = msg;
  el.classList.toggle("error", !!isError);
}

// Auswahl einer Fraktion: zweiter Klick hebt die Auswahl auf.
function handleSelect(fid) {
  if (panel.selectedId === fid) {
    panel.clearInfo();
    map.clearHighlight();
    return;
  }
  const hasTerritory = !!(currentSnapshot.territories &&
    currentSnapshot.territories.features.some((f) => f.properties.factionId === fid));
  panel.select(fid, hasTerritory);
  if (hasTerritory) map.highlightFaction(fid);
  else map.clearHighlight();
}

async function showSnapshot(entry) {
  setStatus(T.loading);
  try {
    currentSnapshot = await loadSnapshot(entry);
    map.renderSnapshot(currentSnapshot, visibility);
    panel.render(currentSnapshot.meta.factionIds || [], entry.year);
    $("blurb").textContent = currentSnapshot.meta.blurb || "";
    setStatus(null);
  } catch (err) {
    console.error(err);
    setStatus(T.errorLoad + " " + err.message, true);
  }
}

function wireLayerToggles() {
  const map3 = { layerTerritories: "territories", layerSettlements: "settlements", layerCultures: "cultures" };
  for (const [id, name] of Object.entries(map3)) {
    const cb = $(id);
    cb.checked = visibility[name];
    cb.addEventListener("change", () => {
      visibility[name] = cb.checked;
      map.setLayerVisible(name, cb.checked);
    });
  }
}

async function boot() {
  // Statische Texte setzen.
  $("appTitle").textContent = T.appTitle;
  $("subtitle").textContent = T.subtitle;
  $("factionsHeading").textContent = T.factionsHeading;
  $("factionsHint").textContent = T.factionsHint;
  $("layersLabel").textContent = T.layers;
  $("lblTerritories").textContent = T.layerTerritories;
  $("lblSettlements").textContent = T.layerSettlements;
  $("lblCultures").textContent = T.layerCultures;

  setStatus(T.loading);
  map = new MapView("map");

  try {
    const [index, factions] = await Promise.all([loadIndex(), loadFactions()]);
    await map.drawBase();
    map.setContext(factions, handleSelect);

    for (const s of index.snapshots) indexByYear.set(s.year, s);

    panel = new FactionPanel({ list: $("factionList"), info: $("factionInfo") }, factions, handleSelect);

    timeline = new Timeline(
      index,
      { slider: $("slider"), yearOut: $("yearOut"), labelOut: $("eraLabel"), ticks: $("ticks") },
      (entry) => showSnapshot(entry)
    );

    wireLayerToggles();

    const startYear = indexByYear.has(DEFAULT_YEAR) ? DEFAULT_YEAR : index.snapshots[0].year;
    timeline.start(startYear);
  } catch (err) {
    console.error(err);
    setStatus(T.errorLoad + " " + err.message, true);
  }
}

boot();

// Offline-Unterstützung (nur über http(s), nicht bei file://).
if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((err) => console.warn("SW:", err));
  });
}
