// Alle Oberflächentexte an einer Stelle (Deutsch). Erleichtert spätere i18n.
export const T = {
  appTitle: "ChronoMap Deutschland",
  subtitle: "Völker, Mächte und Grenzen im Wandel der Zeit",
  loading: "Lädt Karte …",
  errorLoad: "Daten konnten nicht geladen werden.",
  yearLabel: (y) => (y < 0 ? `${-y} v. Chr.` : `${y} n. Chr.`),
  factionsHeading: "Mächte zu dieser Zeit",
  factionsHint: "Auf eine Macht tippen, um sie hervorzuheben.",
  noTerritory: "Übergeordnete Ordnung – kein eigenes Territorium auf der Karte hervorgehoben.",
  close: "Schließen",
  layers: "Ebenen",
  layerTerritories: "Territorien",
  layerSettlements: "Städte",
  layerCultures: "Kultur & Sprache",
  field: {
    rulingHouse: "Herrscherhaus",
    religion: "Religion",
    capital: "Residenz/Hauptort",
    origin: "Ursprung",
    keyFacts: "Wissenswertes",
    rank: "Rang",
  },
  rank: {
    empire: "Reich", kingdom: "Königreich", archduchy: "Erzherzogtum",
    duchy: "Herzogtum", electorate: "Kurfürstentum", margraviate: "Markgrafschaft",
    landgraviate: "Landgrafschaft", county: "Grafschaft", confederation: "Bund",
  },
  kind: {
    residenz: "Residenz", reichsstadt: "Reichsstadt", hansestadt: "Hansestadt",
    bischofssitz: "Bischofssitz", stadt: "Stadt", dorf: "Ort",
  },
};
