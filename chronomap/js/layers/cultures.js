// Kultur-/Sprachzonen als durchscheinende, schraffierte Flächen.
// Die Schraffur signalisiert: unscharfe Zonen, keine harten Grenzen.
let patternSeq = 0;

function hatchPattern(svg, color) {
  const id = "cm-hatch-" + (patternSeq++);
  const ns = "http://www.w3.org/2000/svg";
  let defs = svg.querySelector("defs");
  if (!defs) { defs = document.createElementNS(ns, "defs"); svg.appendChild(defs); }
  const pat = document.createElementNS(ns, "pattern");
  pat.setAttribute("id", id);
  pat.setAttribute("patternUnits", "userSpaceOnUse");
  pat.setAttribute("width", "8");
  pat.setAttribute("height", "8");
  pat.setAttribute("patternTransform", "rotate(45)");
  const line = document.createElementNS(ns, "line");
  line.setAttribute("x1", "0"); line.setAttribute("y1", "0");
  line.setAttribute("x2", "0"); line.setAttribute("y2", "8");
  line.setAttribute("stroke", color);
  line.setAttribute("stroke-width", "2.5");
  pat.appendChild(line);
  defs.appendChild(pat);
  return id;
}

export function buildCultures(L, geojson) {
  const layer = L.geoJSON(geojson, {
    pane: "cultures",
    style: (feat) => ({
      color: feat.properties.color || "#7a6a4a",
      weight: 1,
      dashArray: "4 4",
      fillColor: feat.properties.color || "#7a6a4a",
      fillOpacity: 0.18,
    }),
    onEachFeature: (feat, lyr) => {
      const p = feat.properties;
      lyr.bindTooltip(`<strong>${p.name}</strong>${p.note ? "<br>" + p.note : ""}`,
        { sticky: true, direction: "top", className: "cm-tooltip" });
    },
  });

  // Nach dem Hinzufügen zur Karte echte SVG-Schraffur als Füllung setzen.
  layer.on("add", () => {
    layer.eachLayer((lyr) => {
      const el = lyr.getElement && lyr.getElement();
      const p = lyr.feature && lyr.feature.properties;
      if (!el || !p || p.pattern !== "hatch") return;
      const svg = el.ownerSVGElement;
      if (!svg) return;
      const id = hatchPattern(svg, p.color || "#7a6a4a");
      el.setAttribute("fill", `url(#${id})`);
      el.setAttribute("fill-opacity", "0.55");
    });
  });

  return { layer };
}
