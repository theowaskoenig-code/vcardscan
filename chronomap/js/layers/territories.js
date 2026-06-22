// Baut die Territorien-Ebene (GeoJSON-Polygone) und liefert einen Index
// factionId -> [Leaflet-Layer] für die Hervorhebung.
import { FALLBACK_COLOR } from "../config.js";

export function colorFor(props, factions) {
  if (props && props.color) return props.color;
  const f = props && factions[props.factionId];
  return (f && f.color) || FALLBACK_COLOR;
}

// Nachbarmächte (foreign) treten gedämpft zurück, damit die deutschen
// Lande hervorstechen.
const baseStyle = (props, factions) => ({
  color: props.foreign ? "#7a6a55" : "#5c4326",
  weight: props.foreign ? 0.8 : 1,
  fillColor: colorFor(props, factions),
  fillOpacity: props.fillOpacity != null ? props.fillOpacity
    : (props.foreign ? 0.32 : 0.55),
});

const highlightStyle = (props, factions) => ({
  color: "#3a2a14",
  weight: 3,
  fillColor: colorFor(props, factions),
  fillOpacity: 0.8,
});

// L: das globale Leaflet, geojson: FeatureCollection, factions: Metadaten,
// onSelect(factionId): Klick-Handler.
export function buildTerritories(L, geojson, factions, onSelect) {
  const index = new Map(); // factionId -> [layer]

  const layer = L.geoJSON(geojson, {
    pane: "territories",
    style: (feat) => baseStyle(feat.properties, factions),
    onEachFeature: (feat, lyr) => {
      const fid = feat.properties.factionId;
      if (!index.has(fid)) index.set(fid, []);
      index.get(fid).push(lyr);

      const name = feat.properties.name || fid;
      lyr.bindTooltip(name, { sticky: true, direction: "top", className: "cm-tooltip" });
      lyr.on("click", () => onSelect(fid));
    },
  });

  // Beschriftungen: pro Fraktion an der größten Fläche; mit dem Zoom werden
  // immer kleinere Territorien sichtbar (Namen statt nur Farben).
  const labels = L.layerGroup();
  const labelData = [];
  for (const [fid, lyrs] of index) {
    let best = null, bestArea = 0;
    for (const l of lyrs) {
      const b = l.getBounds();
      const a = (b.getNorth() - b.getSouth()) * (b.getEast() - b.getWest());
      if (a > bestArea) { bestArea = a; best = l; }
    }
    if (!best) continue;
    const name = best.feature.properties.name || fid;
    const marker = L.marker(best.getBounds().getCenter(), {
      pane: "labels",
      interactive: false,
      keyboard: false,
      icon: L.divIcon({ className: "cm-label", html: `<span>${name}</span>` }),
    });
    labelData.push({ marker, area: bestArea, on: false });
  }

  function refreshLabels(zoom) {
    const thr = 3.2 / Math.pow(2, Math.max(0, zoom - 4)); // kleiner Schwellwert bei höherem Zoom
    for (const d of labelData) {
      const show = d.area >= thr;
      if (show && !d.on) { labels.addLayer(d.marker); d.on = true; }
      else if (!show && d.on) { labels.removeLayer(d.marker); d.on = false; }
    }
  }

  function resetAll() {
    layer.eachLayer((lyr) => {
      if (lyr.feature) lyr.setStyle(baseStyle(lyr.feature.properties, factions));
    });
  }

  function highlight(fid) {
    resetAll();
    const layers = index.get(fid);
    if (!layers) return null;
    let bounds = null;
    for (const lyr of layers) {
      lyr.setStyle(highlightStyle(lyr.feature.properties, factions));
      lyr.bringToFront();
      bounds = bounds ? bounds.extend(lyr.getBounds()) : lyr.getBounds();
    }
    return bounds;
  }

  return { layer, index, highlight, resetAll, labels, refreshLabels };
}
