# ChronoMap Deutschland

Eine interaktive Geschichtskarte des Raums des heutigen Deutschland – von der
Vorgeschichte bis zur Gegenwart. Mit durchgehendem **Zeitschieber** und einer
Liste der **wichtigsten Mächte** zu jedem Zeitpunkt, die sich anklicken,
auf der Karte hervorheben und im Detail anzeigen lassen.

> Optik im **Pergament-Stil** (Sepia, Serifenschrift). Reine statische Web-App
> ohne Build-Schritt – passend zum Stil dieses Repos.

## Stand (MVP)

Vertikaler Schnitt mit Fokus auf das **Heilige Römische Reich, Hochmittelalter
(ca. 1000–1500)**. Vier ausgearbeitete Zeitschnitte:

- **Um 1000** – Ottonisches Reich, Stammesherzogtümer
- **Um 1200** – Stauferzeit
- **1356** – Goldene Bulle (vollständig ausgearbeitet: 7 Kurfürsten, Herzogtümer, Städte, Sprachzonen)
- **Um 1500** – Reichsreform, Aufstieg der Habsburger

Der Zeitschieber läuft durchgehend; die Karte zeigt jeweils den **nächst­gelegenen**
definierten Zeitschnitt.

## Funktionen

- **Zeitschieber** mit Markierungen für die definierten Epochen.
- **Ebenen** zum Ein-/Ausblenden: Territorien, Städte, Kultur & Sprache.
- **Mächte-Liste**: anklicken → Hervorhebung auf der Karte + Infobereich
  (Herrscherhaus, Religion, Residenz, Ursprung, Wissenswertes – jeweils
  passend zum gewählten Jahr).
- **Offline-fähig** (Service Worker), keine API-Schlüssel, kein Kachelanbieter.

## Starten

Wegen ES-Modulen über HTTP ausliefern (nicht per `file://`):

```bash
cd chronomap
python3 -m http.server 8000
# http://localhost:8000
```

## Architektur

- `index.html` – Gerüst; lädt Leaflet (klassisch) + `js/app.js` (Modul).
- `css/` – `theme.css` (Pergament-Variablen), `layout.css`, `map.css` (Leaflet-Styling).
- `js/` – `app.js` (Einstieg), `eras.js` (Laden/Cache), `timeline.js`
  (Jahr→Snapshot), `mapView.js` (Leaflet + Ebenen-Tausch), `factions.js`
  (Liste/Detail), `layers/*` (Territorien/Städte/Kultur), `i18n.js`, `config.js`.
- `data/` – statische, von Hand recherchierte Daten:
  - `eras/index.json` – Zeitleisten-Manifest, `eras/<jahr>.json` – Snapshots.
  - `layers/territories|cultures/*.geojson`, `layers/settlements/*.json`.
  - `factions/factions.json` – Mächte (Basisdaten + epochenspezifische Blöcke).
  - `geo/land.geojson`, `geo/lakes.geojson` – Pergament-Untergrund (Natural Earth).
- `vendor/leaflet/` – Leaflet 1.9.4, lokal eingebunden (offline).
- `tools/build_data.py` – **einmaliges** Autorenwerkzeug, das die `data/`-Dateien
  erzeugt. Keine Laufzeit-Abhängigkeit.

### Eine neue Epoche ergänzen

Reine Datenarbeit, **kein Code**: neue Dateien unter `data/layers/.../` und
`data/eras/<jahr>.json` anlegen und einen Eintrag in `eras/index.json` hinzufügen.
`view.bounds` im Snapshot passt den Kartenausschnitt automatisch an die Epoche an.
So lassen sich später frühere Epochen (Kelten/Hallstatt, römischer Limes,
Völkerwanderung) anschließen.

## Daten & Lizenzen

- **Grenzverläufe sind bewusst stark vereinfacht** ("Zonen", keine exakten
  Linien) und ausdrücklich näherungsweise. Sachangaben nach gängiger
  Geschichtsliteratur (u. a. zur Goldenen Bulle 1356).
- Küsten/Seen: **Natural Earth** (gemeinfrei).
- Kartenbibliothek: **Leaflet** (BSD-2-Clause).

## Roadmap

- Frühere Epochen (Kelten, römischer Limes, Völkerwanderung, Neuzeit, 19./20. Jh.).
- Verfeinerte Geometrie und mehr Territorien je Schnitt.
- Wirtschaft/Religion/Bevölkerung als zusätzliche thematische Ebenen.
