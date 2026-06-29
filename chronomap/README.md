# ChronoMap Deutschland

Eine interaktive Geschichtskarte Mitteleuropas im europäischen Kontext – von
der Antike bis heute. Mit **Zeitschieber** über 23 Epochen und einer Liste der
**Mächte** zu jedem Zeitpunkt, die sich anklicken, hervorheben und im Detail
anzeigen lassen. Territorien tragen **Namensbeschriftungen**, die beim
Hineinzoomen immer feiner werden.

> Optik im **Pergament-Stil** (Sepia, Serifenschrift). Reine statische Web-App
> ohne Build-Schritt.

## Epochen (45)

45 Zeitschnitte von **1000 v. Chr. bis heute**, europaweit. **Ab 850
mindestens alle 50 Jahre** (Antike und Moderne zusätzlich verdichtet), damit
die Entwicklung sichtbar wird – z. B. der deutsche Bogen: Ostfrankenreich (850) → Königreich
Deutschland (900) → Heiliges Römisches Reich (ab ~1000) → Kurfürsten-
Flickenteppich (ab ~1350) → Deutscher Bund (1815) → Kaiserreich (1871) →
geteilt (1961) → 16 Bundesländer (heute).

- **Antike (historical-basemaps):** 500/200 v. Chr., Christi Geburt, 100, 300,
  500, 700 (Kelten, Germanen, Rom, Völkerwanderung, Franken)
- **850–1800 (Cliopatria, alle 50 Jahre):** 850, 900, … , 1800
- **Modern (dichter):** 1815, 1848, 1871, 1900, 1914, 1938, 1961, 1990, heute

Der index-basierte Zeitschieber gibt jeder Epoche gleich viel Platz.

## Daten & Genauigkeit (mehrere Datenbanken zusammengeführt)

- **Antike (bis ~700):** **historical-basemaps** von A. Ourednik — echte,
  geografisch eingepasste Verläufe mit kultureller Tiefe (keltische/germanische
  Stämme, Rom). Lizenz **GPL**.
  <https://github.com/aourednik/historical-basemaps>
- **Ab 850 (Hauptquelle):** **Cliopatria** (Seshat Global History Databank,
  **CC BY 4.0**) — ein **kontinuierlicher** Datensatz, der ein dichtes
  50-Jahres-Raster erlaubt; das deutsche Detail (Kurfürstentümer, Staaten,
  Bundesländer) ergibt sich direkt aus den Daten.
  <https://github.com/Seshat-Global-History-Databank/cliopatria>
- **Bundesländer** (Epoche „Heute“): **deutschlandGeoJSON** (Public Domain).
  <https://github.com/isellsoap/deutschlandGeoJSON>
- **Binnengliederung des Reiches (~843–1250):** Stammesherzogtümer und
  Territorien (Sachsen, Bayern, Schwaben, Franken, Lothringen, Kärnten,
  Böhmen, Brandenburg, Österreich …) sind **von Hand und näherungsweise**
  angelegt und über den echten Reichsumriss gelegt — für diese Zeit gibt es
  keine offenen Vektordaten der Reichsterritorien. Ab ~1300 zeigt Cliopatria
  das echte Kurfürsten-/Kleinstaaten-Detail.
- **Wappen:** Wikimedia Commons (im Browser geladen).
- **Pergament-Untergrund (ganz Europa):** **Natural Earth 50 m** (gemeinfrei).
- Das **20. Jahrhundert** ist bewusst nüchtern dargestellt; die NS-Zeit
  (1938) zeigt historische Tatsachen (auch besetzte Gebiete) ohne Verherrlichung.
- **Nachbarmächte** werden gedämpft dargestellt, damit die deutschen Lande
  hervortreten.

Grenzen sind vereinfacht und zwischen den Stichjahren auf den nächsten
Zeitschnitt gerundet; vor wissenschaftlicher Verwendung mit Fachquellen
abgleichen.

## Funktionen

- **Zeitschieber** mit Markierungen für die definierten Epochen.
- **Ebenen** zum Ein-/Ausblenden: Territorien, Städte, Kultur & Sprache
  (Sprachzonen nur im Hochmittelalter).
- **Mächte-Liste**: anklicken → Hervorhebung auf der Karte + Infobereich
  (Herrscherhaus, Religion, Residenz, Ursprung, Wissenswertes – jeweils
  passend zum gewählten Jahr).
- **Offline-fähig** (Service Worker), keine API-Schlüssel, kein Kachelanbieter.

## Starten

Wegen ES-Modulen über HTTP ausliefern (nicht per `file://`):

```bash
cd chronomap
python3 -m http.server 8000   # → http://localhost:8000
```

## Architektur

- `index.html` – Gerüst; lädt Leaflet (klassisch) + `js/app.js` (Modul).
- `css/` – `theme.css` (Pergament-Variablen), `layout.css`, `map.css`.
- `js/` – `app.js` (Einstieg), `eras.js` (Laden/Cache), `timeline.js`
  (Jahr→Snapshot), `mapView.js` (Leaflet + Ebenen-Tausch), `factions.js`
  (Liste/Detail), `layers/*`, `i18n.js`, `config.js`.
- `data/` – statische, erzeugte Daten: `eras/index.json` (+ `eras/<jahr>.json`),
  `layers/territories|cultures/*.geojson`, `layers/settlements/*.json`,
  `factions/factions.json`, `geo/land|lakes.geojson`.
- `vendor/leaflet/` – Leaflet 1.9.4, lokal eingebunden (offline).
- `tools/build_data.py` – **einmaliges** Autorenwerkzeug, das aus Cliopatria +
  den Näherungszonen die `data/`-Dateien erzeugt. Keine Laufzeit-Abhängigkeit.

### Daten neu erzeugen

```bash
python3 chronomap/tools/build_data.py
```

Das Skript lädt bei Bedarf die Cliopatria-Datei (~44 MB) herunter, schneidet
die Polygone auf Mitteleuropa zu, vereinfacht sie und schreibt alle
`data/`-Dateien. Eine neue Epoche ergänzt man durch einen Eintrag in der
`ERAS`-Liste; `view.bounds` passt den Kartenausschnitt automatisch an.

## Lizenzen

- Code: wie Repository.
- Grenzdaten (Hauptquelle): **GPL** (historical-basemaps, A. Ourednik).
  Die hieraus abgeleiteten Dateien stehen entsprechend unter GPL.
- Deutsches Detail: **CC BY 4.0** (Cliopatria / Seshat Global History Databank).
- Bundesländer: Public Domain / Unlicense (deutschlandGeoJSON).
- Küstendaten: Natural Earth (gemeinfrei).
- Kartenbibliothek: Leaflet (BSD-2-Clause).

## Roadmap

- Verfeinerte antike Epochen, mehr Zwischenschritte (z. B. 1789, 1848).
- Wirtschaft/Religion/Bevölkerung als zusätzliche thematische Ebenen.
- Detailtiefe der Reichsterritorien (Kleinstaaten einzeln).
