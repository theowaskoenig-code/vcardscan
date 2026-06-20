// Baut die Städte-/Siedlungs-Ebene als Kreismarker (Größe nach Bedeutung).
import { T } from "../i18n.js";

const RADIUS = { 1: 3, 2: 4.5, 3: 6 };

export function buildSettlements(L, data) {
  const layer = L.layerGroup([], { pane: "settlements" });
  const list = (data && data.settlements) || [];

  for (const s of list) {
    const marker = L.circleMarker([s.lat, s.lon], {
      pane: "settlements",
      radius: RADIUS[s.importance] || 4,
      color: "#3a2a14",
      weight: 1,
      fillColor: "#fbf4e0",
      fillOpacity: 1,
    });
    const kind = T.kind[s.kind] || "";
    if (s.importance >= 3) {
      // Bedeutende Orte tragen ein dauerhaftes Label.
      marker.bindTooltip(s.name, {
        permanent: true, direction: "right", className: "cm-place-label", offset: [6, 0],
      });
    } else {
      marker.bindTooltip(
        `<strong>${s.name}</strong>${kind ? "<br>" + kind : ""}`,
        { direction: "top", className: "cm-tooltip", offset: [0, -4] }
      );
    }
    marker.addTo(layer);
  }
  return { layer };
}
