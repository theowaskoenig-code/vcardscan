# ChronoMap Deutschland

Eine interaktive Geschichtskarte Mitteleuropas im europäischen Kontext – von
der Antike bis heute. Mit **Zeitschieber** über 23 Epochen und einer Liste der
**Mächte** zu jedem Zeitpunkt, die sich anklicken, hervorheben und im Detail
anzeigen lassen. Territorien tragen **Namensbeschriftungen**, die beim
Hineinzoomen immer feiner werden.

> Optik im **Pergament-Stil** (Sepia, Serifenschrift). Reine statische Web-App
> ohne Build-Schritt.

## Epochen (23)

23 Zeitschnitte von **500 v. Chr. bis heute**, europaweit:

- **Antike:** 500 v. Chr., 200 v. Chr., Christi Geburt, 200, 400 (Kelten,
  Germanen, Römisches Reich, Spätantike)
- **Mittelalter:** 500 (Völkerwanderung), 700, 800 (Karl d. Gr.), 1000, 1200,
  1356 (Goldene Bulle), 1500
- **Neuzeit:** 1648 (Westfälischer Friede), 1700, 1789, 1815 (Deutscher Bund),
  1880 (Kaiserreich)
- **20./21. Jh.:** 1914, 1920 (Weimar), 1938 (NS-Staat), 1945 (Besatzung),
  1960 (geteiltes Deutschland), heute (16 Bundesländer)

Der index-basierte Zeitschieber gibt jeder Epoche gleich viel Platz.

## Daten & Genauigkeit (mehrere Datenbanken zusammengeführt)

- **Grenzen aller Epochen, europaweit:** **historical-basemaps** von
  A. Ourednik — echte, geografisch eingepasste Verläufe für ~40 Stichjahre.
  Lizenz **GPL**. <https://github.com/aourednik/historical-basemaps>
- **Deutsches Detail** (Kurfürstentümer/Flickenteppich 1356/1500/1648):
  **Cliopatria** (Seshat Global History Databank, **CC BY 4.0**) als Overlay.
  <https://github.com/Seshat-Global-History-Databank/cliopatria>
- **Bundesländer** (Epoche „Heute“): **deutschlandGeoJSON** (Public Domain).
  <https://github.com/isellsoap/deutschlandGeoJSON>
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
