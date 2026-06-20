// Leaflet-Karte: Pergament-Untergrund (selbst gezeichnet, ohne Kachelanbieter),
// Panes für die Ebenen und sauberes Austauschen der Snapshot-Ebenen.
import { GEO, PALETTE } from "./config.js";
import { buildTerritories } from "./layers/territories.js";
import { buildSettlements } from "./layers/settlements.js";
import { buildCultures } from "./layers/cultures.js";

const L = window.L;

export class MapView {
  constructor(containerId) {
    this.map = L.map(containerId, {
      zoomControl: true,
      attributionControl: true,
      minZoom: 4,
      maxZoom: 10,
      worldCopyJump: false,
    });
    this.map.attributionControl.setPrefix(
      'Territorien (1000–2024) © <a href="https://github.com/Seshat-Global-History-Databank/cliopatria">Cliopatria / Seshat</a> ' +
      '(<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>) · ' +
      'Bundesländer © <a href="https://github.com/isellsoap/deutschlandGeoJSON">deutschlandGeoJSON</a> (Public Domain) · ' +
      'Küsten © <a href="https://www.naturalearthdata.com/about/terms-of-use/">Natural Earth</a> · ' +
      '<a href="https://leafletjs.com">Leaflet</a> · ' +
      'antike Zonen & Grenzen vereinfacht/näherungsweise'
    );

    this.createPanes();
    this.map.setView([50.5, 10.5], 5);

    this.current = { territories: null, cultures: null, settlements: null };
    this.territoryCtl = null; // {layer, highlight, resetAll, index}
    this.factions = {};
    this.onSelect = () => {};
  }

  createPanes() {
    const defs = [
      ["base", 350], ["territories", 410], ["cultures", 420], ["settlements", 430],
    ];
    for (const [name, z] of defs) {
      this.map.createPane(name);
      this.map.getPane(name).style.zIndex = String(z);
    }
  }

  async drawBase() {
    const [land, lakes] = await Promise.all([
      fetch(GEO.land).then((r) => r.json()),
      fetch(GEO.lakes).then((r) => r.json()),
    ]);
    L.geoJSON(land, {
      pane: "base",
      style: { color: PALETTE.landStroke, weight: 1, fillColor: PALETTE.land, fillOpacity: 1 },
      interactive: false,
    }).addTo(this.map);
    L.geoJSON(lakes, {
      pane: "base",
      style: { color: PALETTE.landStroke, weight: 0.5, fillColor: PALETTE.sea, fillOpacity: 1 },
      interactive: false,
    }).addTo(this.map);
  }

  setContext(factions, onSelect) {
    this.factions = factions;
    this.onSelect = onSelect;
  }

  setLayerVisible(name, visible) {
    const lyr = this._layerObj(name);
    if (!lyr) return;
    if (visible) { if (!this.map.hasLayer(lyr)) lyr.addTo(this.map); }
    else { this.map.removeLayer(lyr); }
  }

  _layerObj(name) {
    if (name === "territories") return this.territoryCtl && this.territoryCtl.layer;
    if (name === "cultures") return this.current.cultures && this.current.cultures.layer;
    if (name === "settlements") return this.current.settlements && this.current.settlements.layer;
    return null;
  }

  clearLayers() {
    for (const obj of Object.values(this.current)) {
      if (obj && obj.layer) this.map.removeLayer(obj.layer);
    }
    this.current = { territories: null, cultures: null, settlements: null };
    this.territoryCtl = null;
  }

  // Snapshot-Daten rendern. visibility: {territories,cultures,settlements} (bool)
  renderSnapshot(snap, visibility) {
    this.clearLayers();

    if (snap.territories) {
      this.territoryCtl = buildTerritories(L, snap.territories, this.factions, this.onSelect);
      this.current.territories = this.territoryCtl;
      if (visibility.territories) this.territoryCtl.layer.addTo(this.map);
    }
    if (snap.cultures) {
      this.current.cultures = buildCultures(L, snap.cultures);
      if (visibility.cultures) this.current.cultures.layer.addTo(this.map);
    }
    if (snap.settlements) {
      this.current.settlements = buildSettlements(L, snap.settlements);
      if (visibility.settlements) this.current.settlements.layer.addTo(this.map);
    }

    const b = snap.meta.view && snap.meta.view.bounds;
    if (b) this.map.flyToBounds(b, { duration: 0.6, padding: [10, 10] });
  }

  highlightFaction(fid) {
    if (!this.territoryCtl) return false;
    const bounds = this.territoryCtl.highlight(fid);
    if (bounds && bounds.isValid()) {
      this.map.flyToBounds(bounds, { duration: 0.5, padding: [40, 40], maxZoom: 8 });
      return true;
    }
    return false;
  }

  clearHighlight() {
    if (this.territoryCtl) this.territoryCtl.resetAll();
  }
}
