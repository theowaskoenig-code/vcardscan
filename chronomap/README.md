# ChronoMap Deutschland

Eine interaktive Geschichtskarte des Raums des heutigen Deutschland – von der
Antike bis zur Reichsgründung. Mit durchgehendem **Zeitschieber** und einer
Liste der **Mächte** zu jedem Zeitpunkt, die sich anklicken, auf der Karte
hervorheben und im Detail anzeigen lassen.

> Optik im **Pergament-Stil** (Sepia, Serifenschrift). Reine statische Web-App
> ohne Build-Schritt.

## Epochen (10)

| Jahr | Epoche | Datenquelle |
|------|--------|-------------|
| ~100 v. Chr. | Kelten & Germanen | Näherungszonen (eigene Arbeit) |
| ~100 n. Chr. | Römisches Reich & Limes | Näherungszonen (eigene Arbeit) |
| ~500 | Völkerwanderung | Näherungszonen (eigene Arbeit) |
| 1000 | Ottonisches Reich | Cliopatria |
| 1200 | Stauferzeit | Cliopatria |
| 1356 | Goldene Bulle | Cliopatria |
| 1500 | Reichsreform | Cliopatria |
| 1648 | Westfälischer Friede | Cliopatria |
| 1815 | Deutscher Bund | Cliopatria |
| 1871 | Deutsches Kaiserreich | Cliopatria |

Der Zeitschieber läuft durchgehend; die Karte zeigt jeweils den
**nächstgelegenen** definierten Zeitschnitt.

## Daten & Genauigkeit

- **Territorien 1000–1871** stammen aus **Cliopatria** (Seshat Global History
  Databank), einem recherchierten, offen lizenzierten Datensatz mit echten
  Grenzverläufen — **CC BY 4.0**. Für die Karte ausgewählt, auf Mitteleuropa
  zugeschnitten und vereinfacht.
  <https://github.com/Seshat-Global-History-Databank/cliopatria>
- **Antike Epochen** (~100 v. Chr., ~100, ~500) sind **von Hand angelegte
  Näherungszonen** (eigene Arbeit). Für diese Zeit gibt es keine exakten
  Vektordaten, und Stammesgrenzen waren ohnehin fließend — daher bewusst grob
  und als näherungsweise gekennzeichnet.
- **Küsten/Seen** (Pergament-Untergrund): **Natural Earth** (gemeinfrei).
- **Nachbarmächte** (Frankreich, Polen, Ungarn, Dänemark …) werden gedämpft
  dargestellt, damit die deutschen Lande hervortreten.

Sachangaben (Herrscherhäuser, Kurfürsten, Daten) nach gängiger
Geschichtsliteratur. Grenzen sind vereinfacht; vor wissenschaftlicher
Verwendung mit Fachquellen abgleichen.

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
- Territoriendaten: **CC BY 4.0** (Cliopatria / Seshat Global History Databank).
- Küstendaten: Natural Earth (gemeinfrei).
- Kartenbibliothek: Leaflet (BSD-2-Clause).

## Roadmap

- Verfeinerte antike Epochen, mehr Zwischenschritte (z. B. 1789, 1848).
- Wirtschaft/Religion/Bevölkerung als zusätzliche thematische Ebenen.
- Detailtiefe der Reichsterritorien (Kleinstaaten einzeln).
