// Zentrale Konfiguration. Keine Build-Schritte – reine ES-Module.
export const DATA_BASE = "data/";

export const GEO = {
  land: DATA_BASE + "geo/land.geojson",
  lakes: DATA_BASE + "geo/lakes.geojson",
};

export const ERAS_INDEX = DATA_BASE + "eras/index.json";
export const FACTIONS_FILE = DATA_BASE + "factions/factions.json";

// Farbe, falls eine Fraktion bzw. ein Territorium keine eigene definiert.
export const FALLBACK_COLOR = "#8a6d4f";

// Pergament-/Wasser-Töne für den selbst gezeichneten Untergrund.
export const PALETTE = {
  sea: "#a9b7a0",   // gedämpftes Graugrün für Meer/Seen
  land: "#e9dcc0",  // Pergament
  landStroke: "#b89b6a",
};

// Startjahr beim Laden (fällt auf das erste Snapshot-Jahr zurück).
export const DEFAULT_YEAR = 1356;
