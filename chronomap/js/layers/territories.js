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

  return { layer, index, highlight, resetAll };
}
