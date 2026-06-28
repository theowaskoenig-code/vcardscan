#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChronoMap Deutschland — Daten-Autorenwerkzeug v2 (one-off authoring helper).

Erzeugt die statischen Daten unter chronomap/data/ aus echten, offen
lizenzierten Quellen:

  * Territorien 1000–1871: Cliopatria (Seshat Global History Databank),
    CC BY 4.0 — https://github.com/Seshat-Global-History-Databank/cliopatria
    (Datei cliopatria.geojson.zip). Echte, recherchierte Grenzverläufe.
  * Antike Epochen (~100 v.Chr., ~100, ~500): von Hand angelegte
    Näherungszonen (eigene Arbeit). Für diese Zeit existieren keine exakten
    Vektordaten; Stammesgrenzen waren ohnehin fließend — daher bewusst grob.
  * Pergament-Untergrund (Küsten/Seen): Natural Earth (gemeinfrei).

KEINE Laufzeit-Abhängigkeit. Einmal ausführen, Ergebnis wird committet.
Sachangaben (Herrscherhäuser, Kurfürsten, Daten) nach gängiger
Geschichtsliteratur. Grenzen ausdrücklich vereinfacht.

Benötigt die Cliopatria-Datei lokal (wird bei Bedarf heruntergeladen):
  /tmp/clio_out/cliopatria_polities_only.geojson
"""
import json, os, math, re, zlib, urllib.request, zipfile, io

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
CLIO_LOCAL = "/tmp/clio_out/cliopatria_polities_only.geojson"
CLIO_URL = "https://raw.githubusercontent.com/Seshat-Global-History-Databank/cliopatria/main/cliopatria.geojson.zip"
BL_LOCAL = "/tmp/bl.geojson"
BL_URL = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/4_niedrig.geo.json"

# Anzeige-/Clip-Fenster.
CLIP_DE = (-1.0, 43.0, 23.0, 57.5)        # Mitteleuropa (Cliopatria-/Bundesländer-Overlay)
EUROPE_CLIP = (-25.0, 34.0, 45.0, 71.0)   # ganz Europa (Hauptquelle historical-basemaps)
VIEW_EUROPE = [[34.5, -11.0], [65.0, 39.0]]
VIEW_CEUROPE = [[43.0, -5.0], [58.5, 27.0]]   # Mitteleuropa (Detail-Epochen)

# Externe Datenquellen (werden bei Bedarf geladen und in /tmp gecacht).
HB_DIR = "/tmp/hb_cache"
HB_URL = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson/world_%s.geojson"
NE_DIR = "/tmp/ne_cache"
NE_LAND_URL = "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master/50m/physical/ne_50m_land.json"
NE_LAKES_URL = "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master/50m/physical/ne_50m_lakes.json"


# ---------------------------------------------------------------------------
# Geometrie-Helfer: Rechteck-Clipping (Sutherland–Hodgman), Douglas–Peucker.
# ---------------------------------------------------------------------------
def _clip_edge(poly, inside, inter):
    out = []
    n = len(poly)
    for i in range(n):
        cur, prv = poly[i], poly[i - 1]
        ci, pi = inside(cur), inside(prv)
        if ci:
            if not pi: out.append(inter(prv, cur))
            out.append(cur)
        elif pi:
            out.append(inter(prv, cur))
    return out

def _lerp(a, b, t): return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]

def clip_ring(ring, box):
    minx, miny, maxx, maxy = box
    p = ring
    p = _clip_edge(p, lambda q: q[0] >= minx, lambda a, b: _lerp(a, b, (minx - a[0]) / (b[0] - a[0])))
    if not p: return []
    p = _clip_edge(p, lambda q: q[0] <= maxx, lambda a, b: _lerp(a, b, (maxx - a[0]) / (b[0] - a[0])))
    if not p: return []
    p = _clip_edge(p, lambda q: q[1] >= miny, lambda a, b: _lerp(a, b, (miny - a[1]) / (b[1] - a[1])))
    if not p: return []
    p = _clip_edge(p, lambda q: q[1] <= maxy, lambda a, b: _lerp(a, b, (maxy - a[1]) / (b[1] - a[1])))
    return p

def _perp(pt, a, b):
    if a == b: return math.hypot(pt[0] - a[0], pt[1] - a[1])
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    px, py = a[0] + t * dx, a[1] + t * dy
    return math.hypot(pt[0] - px, pt[1] - py)

def dp(points, eps):
    if len(points) < 3: return points
    dmax, idx = 0, 0
    for i in range(1, len(points) - 1):
        d = _perp(points[i], points[0], points[-1])
        if d > dmax: dmax, idx = d, i
    if dmax > eps:
        left = dp(points[:idx + 1], eps)
        right = dp(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]

def simplify_ring(ring, eps, prec=3):
    if len(ring) >= 4:
        ring = dp(ring, eps)
    ring = [[round(x, prec), round(y, prec)] for x, y in ring]
    # Ring schließen
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring

def process_geometry(geom, box, eps):
    """Clippt + vereinfacht eine (Multi)Polygon-Geometrie. Gibt Polygon-Liste
    (Liste von Ringgruppen) zurück oder None."""
    if geom["type"] == "Polygon":
        groups = [geom["coordinates"]]
    elif geom["type"] == "MultiPolygon":
        groups = geom["coordinates"]
    else:
        return None
    out = []
    for poly in groups:
        new_rings = []
        for ri, ring in enumerate(poly):
            cr = clip_ring(ring, box)
            if len(cr) < 3:
                if ri == 0: new_rings = []; break
                continue
            sr = simplify_ring(cr, eps)
            if len(sr) >= 4:
                new_rings.append(sr)
            elif ri == 0:
                new_rings = []; break
        if new_rings:
            out.append(new_rings)
    return out or None

def shoelace(ring):
    s = 0
    for i in range(len(ring) - 1):
        s += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(s) / 2


# ---------------------------------------------------------------------------
# Fraktions-Stammdaten (Farben, dt. Namen, recherchierte Infotexte).
#   foreign=True  -> Nachbarmacht (gedämpft, hebt die deutschen Lande hervor)
# ---------------------------------------------------------------------------
def F(name, color, rank=None, foreign=False, origin=None, house=None,
      religion="Römisch-katholisch", capital=None, eras=None):
    d = {"name": name, "color": color}
    if rank: d["rank"] = rank
    if foreign: d["foreign"] = True
    if origin: d["origin"] = origin
    if house: d["rulingHouse"] = house
    if religion: d["religion"] = religion
    if capital: d["capital"] = capital
    if eras: d["eras"] = eras
    return d

FACTIONS = {
  # ---- Übergeordnet / Reich ----
  "hre": F("Heiliges Römisches Reich", "#6b4f2a", "empire",
    origin="Aus dem Ostfränkischen Reich hervorgegangen; Kaiserkrönung Ottos I. 962.",
    house="Wahlmonarchie", capital="keine feste Hauptstadt",
    eras={
      "1000": {"rulingHouse": "Liudolfinger (Ottonen)", "capital": "Pfalzen, u. a. Aachen & Magdeburg",
        "keyFacts": ["Gegliedert in die Stammesherzogtümer Sachsen, Bayern, Schwaben, Franken und Lothringen.",
                     "Kaiser Otto III. verfolgt die Idee einer „Renovatio imperii Romanorum“.",
                     "Reichskirche als Stütze der Königsherrschaft (ottonisch-salisches Reichskirchensystem)."]},
      "1200": {"rulingHouse": "Staufer", "capital": "Reisekönigtum (u. a. Hagenau, Goslar)",
        "keyFacts": ["Höhepunkt der Stauferzeit unter Heinrich VI.; größte Ausdehnung des Reiches.",
                     "Ab 1198 Thronstreit zwischen Staufern (Philipp von Schwaben) und Welfen (Otto IV.).",
                     "Fortschreitende Territorialisierung: Fürsten gewinnen an Macht."]},
    }),
  "hre_minor": F("Reichsterritorien (geistliche & weltliche Kleinstaaten)", "#c9b07a", "empire",
    origin="Der „Flickenteppich“ aus Hunderten von Herrschaften innerhalb des Reiches.",
    house="zahlreiche Dynastien, Bischöfe und Reichsstädte", capital=None,
    eras={
      "1356": {"keyFacts": ["Hunderte geistliche und weltliche Territorien sowie Reichsstädte.",
                            "Die Goldene Bulle von 1356 regelt die Königswahl durch sieben Kurfürsten.",
                            "Drei geistliche (Mainz, Köln, Trier) und vier weltliche Kurfürsten (Böhmen, Pfalz, Sachsen-Wittenberg, Brandenburg)."]},
      "1500": {"keyFacts": ["Reichsreform unter Maximilian I.: Ewiger Landfriede 1495, Reichskammergericht.",
                            "Einteilung in Reichskreise; Name nun „… Deutscher Nation“.",
                            "Über 300 reichsunmittelbare Territorien."]},
      "1648": {"keyFacts": ["Nach dem Westfälischen Frieden 1648: faktische Souveränität der Reichsstände.",
                            "Über 300 Territorien; das Reich als lockerer Verband.",
                            "Frankreich und Schweden werden Garantiemächte des Friedens."]},
    }),

  # ---- Böhmen ----
  "boehmen": F("Königreich Böhmen", "#7a5230", "kingdom",
    origin="Slawisches Herzogtum der Přemysliden, ab 1198 erbliches Königreich.",
    house="wechselnd", capital="Prag",
    eras={
      "1000": {"rank": "duchy", "name": "Herzogtum Böhmen", "rulingHouse": "Přemysliden",
               "keyFacts": ["Herzogtum der Přemysliden, dem Reich locker verbunden."]},
      "1200": {"rulingHouse": "Přemysliden", "keyFacts": ["1198 zum erblichen Königreich erhoben (Ottokar I. Přemysl)."]},
      "1356": {"rulingHouse": "Haus Luxemburg (Karl IV.)",
               "keyFacts": ["Kurstimme als eines der sieben Kurfürstentümer.",
                            "Kulturelles Zentrum des Reiches unter Karl IV.; Universität Prag 1348.",
                            "Mit Mähren, Schlesien und der Lausitz zur „Krone Böhmen“ verbunden."]},
      "1500": {"rulingHouse": "Jagiellonen", "keyFacts": ["Seit 1471 unter den Jagiellonen, ab 1490 in Personalunion mit Ungarn."]},
    }),

  # ---- Bayern ----
  "bayern": F("Herzogtum Bayern", "#5f7a5a", "duchy",
    origin="Bajuwarisches Stammesherzogtum; seit 1180 wittelsbachisch.",
    house="Haus Wittelsbach", capital="München",
    eras={
      "1356": {"keyFacts": ["Mehrfach geteilt; die Wittelsbacher halten zeitweise auch Brandenburg und die Pfalz."]},
      "1500": {"keyFacts": ["Nach dem Landshuter Erbfolgekrieg (1504/05) weitgehend wiedervereinigt.",
                            "Primogenitur sichert künftig die Einheit des Herzogtums."]},
      "1648": {"name": "Kurfürstentum Bayern", "rank": "electorate",
               "keyFacts": ["1623 mit der pfälzischen Kurwürde belehnt (Maximilian I.).",
                            "Im Westfälischen Frieden als Kurfürstentum bestätigt; achte Kur für die Pfalz neu geschaffen."]},
    }),
  "bayern_kgr": F("Königreich Bayern", "#5f7a5a", "kingdom",
    origin="1806 durch Napoleon zum Königreich erhoben.",
    house="Haus Wittelsbach", capital="München",
    eras={"1815": {"keyFacts": ["Im Deutschen Bund zweitgrößter deutscher Staat.",
                                "Erhielt 1814/15 u. a. Franken und Teile Schwabens.",
                                "Verfassung von 1818 — früher Konstitutionalismus."]}}),

  # ---- Brandenburg / Preußen ----
  "askanien": F("Haus Askanien", "#8a6d3b", "margraviate",
    origin="Markgrafen von Brandenburg seit Albrecht dem Bären (1157).",
    house="Askanier", capital="Brandenburg/Tangermünde",
    eras={"1356": {"name": "Mark Brandenburg (Askanier/Wittelsbach)",
                   "keyFacts": ["Inhaber der brandenburgischen Kurstimme (Erzkämmerer).",
                                "Um 1356 unter wittelsbachischer Herrschaft; 1373 an die Luxemburger."]}}),
  "brandenburg": F("Kurfürstentum Brandenburg", "#4a5a6e", "electorate",
    origin="Markgrafschaft im Zuge der Ostsiedlung ausgebaut; Kurfürstentum.",
    house="Haus Hohenzollern (seit 1415)", capital="Berlin-Cölln",
    eras={"1500": {"keyFacts": ["Seit 1415 unter den Hohenzollern, die das Land bis 1918 regieren.",
                                "Weltlicher Kurfürst (Erzkämmerer des Reiches)."]}}),
  "brandenburg_preussen": F("Brandenburg-Preußen", "#3f5066", "electorate",
    origin="Personalunion Brandenburgs mit dem Herzogtum Preußen (1618).",
    house="Haus Hohenzollern", capital="Berlin",
    eras={"1648": {"keyFacts": ["Gewinnt im Westfälischen Frieden u. a. Hinterpommern und Magdeburg.",
                                "Unter dem „Großen Kurfürsten“ Friedrich Wilhelm Aufstieg zur Militärmacht."]}}),
  "preussen": F("Königreich Preußen", "#3f5066", "kingdom",
    origin="1701 zum Königreich erhoben; nach 1815 Großmacht im Deutschen Bund.",
    house="Haus Hohenzollern", capital="Berlin",
    eras={"1815": {"keyFacts": ["Auf dem Wiener Kongress um Rheinland, Westfalen und Teile Sachsens vergrößert.",
                                "Führt den Deutschen Zollverein (ab 1834) und rivalisiert mit Österreich.",
                                "Zwei getrennte Landesteile (Ost und West) im Deutschen Bund."]}}),

  # ---- Sachsen ----
  "sachsen_kur": F("Kurfürstentum Sachsen", "#8a6d3b", "electorate",
    origin="Askanisches Kurfürstentum an der Elbe; ab 1423 wettinisch.",
    house="Haus Wettin", capital="Wittenberg/Dresden",
    eras={
      "1356": {"name": "Kursachsen (Sachsen-Wittenberg)", "rulingHouse": "Askanier",
               "keyFacts": ["Die Goldene Bulle weist die sächsische Kur Sachsen-Wittenberg zu.",
                            "Weltlicher Kurfürst und Erzmarschall des Reiches."]},
      "1500": {"keyFacts": ["1485 Leipziger Teilung in ernestinische (Kur) und albertinische Linie.",
                            "Bald darauf Ausgangspunkt der Reformation (Wittenberg, 1517)."]},
      "1648": {"keyFacts": ["Führende protestantische Macht; erhält 1635 die Lausitz.",
                            "Im Dreißigjährigen Krieg schwankend zwischen den Lagern."]},
    }),

  # ---- Habsburg / Österreich ----
  "habsburg": F("Habsburgische Erblande", "#a8554a", "archduchy",
    origin="Hausmacht der Habsburger um Österreich, Steiermark, Kärnten und Tirol.",
    house="Haus Habsburg", capital="Wien/Innsbruck",
    eras={
      "1356": {"name": "Haus Habsburg (Österreich)", "rank": "duchy",
               "keyFacts": ["Habsburgisch seit 1278 (Schlacht bei Dürnkrut).",
                            "Mit dem gefälschten Privilegium Maius beanspruchen sie Sonderrechte.",
                            "Nicht unter den sieben Kurfürsten der Goldenen Bulle."]},
      "1500": {"rulingHouse": "Haus Habsburg (Maximilian I.)",
               "keyFacts": ["Maximilian I. ist römisch-deutscher König und Erzherzog von Österreich.",
                            "Durch Heiratspolitik (Burgund, Spanien) Aufstieg zur Weltmacht.",
                            "„Bella gerant alii, tu felix Austria nube.“"]},
      "1648": {"name": "Habsburgermonarchie", "rulingHouse": "Haus Habsburg",
               "keyFacts": ["Stellt fast durchgehend den Kaiser; Zentrum der katholischen Gegenreformation.",
                            "Verliert mit dem Westfälischen Frieden den Kampf um ein zentralisiertes Reich.",
                            "Erblande Österreich, Böhmen und (königliches) Ungarn."]},
    }),
  "oesterreich_kaisertum": F("Kaisertum Österreich", "#a8554a", "empire",
    origin="1804 von Franz I. als Erbkaisertum begründet (Ende des Alten Reiches 1806).",
    house="Haus Habsburg-Lothringen", capital="Wien",
    eras={"1815": {"keyFacts": ["Führungsmacht (Präsidialmacht) des Deutschen Bundes.",
                                "Staatskanzler Metternich prägt die europäische Restauration.",
                                "Vielvölkerstaat über deutsche, ungarische, italienische und slawische Länder."]}}),

  # ---- Geistliche Kurfürsten ----
  "mainz": F("Kurmainz (Erzbistum Mainz)", "#9c5a52", "electorate",
    origin="Erzbistum seit dem 8. Jh.; der Erzbischof ist Erzkanzler für Deutschland.",
    house="geistliches Fürstentum (Erzbischof)", capital="Mainz",
    eras={"1356": {"keyFacts": ["Erster geistlicher Kurfürst; leitet als Erzkanzler die Königswahl."]}}),
  "koeln": F("Kurköln (Erzbistum Köln)", "#7d4a44", "electorate",
    origin="Erzbistum seit der Spätantike; einer der reichsten Kirchenfürsten.",
    house="geistliches Fürstentum (Erzbischof)", capital="Köln (Residenz Bonn)",
    eras={"1356": {"keyFacts": ["Geistlicher Kurfürst und Erzkanzler für Italien.",
                                "Die Stadt Köln selbst ist faktisch Freie Reichsstadt."]}}),
  "trier": F("Kurtrier (Erzbistum Trier)", "#b06a4e", "electorate",
    origin="Ältestes Bistum nördlich der Alpen.",
    house="geistliches Fürstentum (Erzbischof)", capital="Trier (später Koblenz)",
    eras={"1356": {"keyFacts": ["Geistlicher Kurfürst und Erzkanzler für Burgund.",
                                "Territorium entlang der Mosel."]}}),
  "pfalz": F("Kurpfalz", "#8c5a3c", "electorate",
    origin="Pfalzgrafschaft bei Rhein, seit 1214 wittelsbachisch.",
    house="Haus Wittelsbach", capital="Heidelberg",
    eras={"1356": {"keyFacts": ["Weltlicher Kurfürst; der Pfalzgraf ist Reichsvikar."]}}),

  # ---- Weitere deutsche Territorien ----
  "wuerttemberg": F("Württemberg", "#6e6240", "county",
    origin="Schwäbisches Grafengeschlecht, von Stuttgart aus expandierend.",
    house="Haus Württemberg", capital="Stuttgart",
    eras={"1500": {"name": "Herzogtum Württemberg", "rank": "duchy",
                   "keyFacts": ["1495 von König Maximilian I. zum Herzogtum erhoben."]}}),
  "wuerttemberg_kgr": F("Königreich Württemberg", "#6e6240", "kingdom",
    origin="1806 zum Königreich erhoben.", house="Haus Württemberg", capital="Stuttgart",
    eras={"1815": {"keyFacts": ["Mittelstaat im Deutschen Bund; Verfassung 1819."]}}),
  "baden": F("Großherzogtum Baden", "#b5894f", "grandduchy",
    origin="1806 aus der Markgrafschaft Baden zum Großherzogtum erhoben.",
    house="Haus Zähringen-Baden", capital="Karlsruhe",
    eras={"1815": {"keyFacts": ["Im Rheinbund stark vergrößert; liberaler Musterstaat des Vormärz."]}}),
  "hessen": F("Landgrafschaft Hessen", "#7c8456", "landgraviate",
    origin="1264 aus dem thüringischen Erbe entstanden.",
    house="Haus Hessen", capital="Kassel/Marburg",
    eras={"1356": {"keyFacts": ["Eigenständige Landgrafschaft zwischen Rhein, Main und Weser."]}}),

  # ---- Welfen / Braunschweig / Norddeutschland ----
  "welfen": F("Welfische Herzogtümer (Braunschweig-Lüneburg)", "#94794e", "duchy",
    origin="Welfischer Restbesitz nach dem Sturz Heinrichs des Löwen (1180).",
    house="Welfen", capital="Braunschweig/Lüneburg",
    eras={"1648": {"keyFacts": ["Mehrfach geteilt (u. a. Calenberg, Lüneburg, Wolfenbüttel).",
                                "Aus der Linie Calenberg geht später Hannover hervor."]}}),

  # ---- Schweiz / Deutscher Orden ----
  "eidgenossenschaft": F("Eidgenossenschaft (Schweiz)", "#8a8d92", "confederation",
    foreign=True,
    origin="1291 als Bund der Waldstätte entstanden.",
    house="Bund autonomer Orte", capital=None,
    eras={
      "1356": {"keyFacts": ["Um 1353 zum „Bund der acht Orte“ gewachsen (u. a. Zürich, Luzern, Bern).",
                            "Formal Teil des Reiches, faktisch zunehmend eigenständig."]},
      "1500": {"keyFacts": ["Nach dem Schwabenkrieg 1499 faktisch vom Reich unabhängig.",
                            "Im Frieden von Basel von der Reichsgerichtsbarkeit gelöst."]},
      "1648": {"foreign": True, "keyFacts": ["Im Westfälischen Frieden 1648 formell aus dem Reichsverband entlassen."]},
    }),
  "deutschorden": F("Deutschordensstaat", "#4a4f5e", "theocracy",
    origin="Geistlicher Ritterorden, 1190 im Heiligen Land (Akkon) gegründet; ab 1226 Eroberung und Christianisierung Preußens.",
    house="Deutscher Orden (Hochmeister)", capital="Marienburg (ab 1309)",
    eras={
      "1356": {"keyFacts": ["Mächtiger deutscher Kreuzritterstaat in Preußen und im Baltikum.",
                            "Residenz des Hochmeisters ist die Marienburg, die größte Backsteinburg Europas.",
                            "Wirtschaftlich über die Hanse eng mit dem Reich verbunden.",
                            "Dauerkonflikt mit dem christlichen Polen-Litauen."]},
      "1500": {"name": "Deutschordensstaat (Preußen)",
               "keyFacts": ["Nach der Niederlage bei Tannenberg/Grunwald (1410) im Niedergang.",
                            "Zweiter Thorner Frieden (1466): Verlust Westpreußens an Polen, Ostpreußen wird polnisches Lehen.",
                            "1525 wandelt Albrecht von Brandenburg den Ordensstaat in das weltliche Herzogtum Preußen um."]},
    }),

  # ---- Deutscher Bund / Kaiserreich ----
  "deutscher_bund": F("Deutscher Bund", "#b8a06a", "confederation",
    origin="1815 auf dem Wiener Kongress als Staatenbund gegründet.",
    house="Staatenbund unter österreichischem Vorsitz", capital="Bundestag in Frankfurt am Main",
    eras={"1815": {"keyFacts": ["Lockerer Bund von 39 souveränen Staaten als Nachfolge des Alten Reiches.",
                                "Österreich führt den Vorsitz; wachsende Rivalität mit Preußen.",
                                "Bundestag (Bundesversammlung) tagt in Frankfurt."]}}),
  "deutsches_reich": F("Deutsches Kaiserreich", "#7a3b2a", "empire",
    origin="1871 nach den Einigungskriegen unter preußischer Führung gegründet.",
    house="Haus Hohenzollern (Kaiser)", capital="Berlin",
    religion="Mehrheitlich evangelisch, große katholische Minderheit",
    eras={"1871": {"keyFacts": ["Reichsgründung am 18. Januar 1871 in Versailles; Wilhelm I. wird Kaiser.",
                                "Bundesstaat aus 25 Gliedstaaten unter Vorherrschaft Preußens.",
                                "Reichskanzler Otto von Bismarck prägt die Politik.",
                                "Österreich bleibt außerhalb (kleindeutsche Lösung)."]},
          "1914": {"rulingHouse": "Haus Hohenzollern (Wilhelm II.)",
                   "keyFacts": ["Am Vorabend des Ersten Weltkriegs eine führende Industrie- und Militärmacht.",
                                "Kolonialreich in Afrika und im Pazifik.",
                                "Bündnis mit Österreich-Ungarn (Mittelmächte)."]},
          "1919": {"name": "Deutsches Reich (Weimarer Republik)", "rank": "republic",
                   "rulingHouse": "Parlamentarische Republik", "capital": "Berlin (Nationalversammlung in Weimar)",
                   "keyFacts": ["Nach Kriegsniederlage und Novemberrevolution 1918 wird das Reich Republik.",
                                "Der Versailler Vertrag erzwingt Gebietsabtretungen: Elsass-Lothringen an Frankreich, "
                                "Westpreußen und Posen an Polen, Nordschleswig an Dänemark, Eupen-Malmedy an Belgien.",
                                "Danzig wird Freie Stadt; das Saargebiet unter Völkerbundsverwaltung."]}}),
  "ns_reich": F("Deutsches Reich (NS-Diktatur)", "#5a534b", "dictatorship",
    origin="Nach der Machtübernahme der Nationalsozialisten 1933 errichtete Diktatur.",
    house="NS-Diktatur (Adolf Hitler)", religion="—", capital="Berlin",
    eras={
      "1938": {"keyFacts": ["1933 Ende der Weimarer Republik, Errichtung der NS-Diktatur.",
                            "März 1938 „Anschluss“ Österreichs, Oktober 1938 Angliederung des Sudetenlands.",
                            "Verfolgung politischer Gegner und der jüdischen Bevölkerung."]},
      "1942": {"name": "Deutsches Reich & besetzte Gebiete (1942)",
               "keyFacts": ["Größte Ausdehnung der deutschen Herrschaft im Zweiten Weltkrieg.",
                            "Weite Teile Europas sind militärisch besetzt oder annektiert (kein legitimer Staatsbesitz).",
                            "Zeit von Vernichtungskrieg und Holocaust.",
                            "1945 vollständige Niederlage und Ende der NS-Herrschaft."]},
    }),
  "brd": F("Bundesrepublik Deutschland", "#3a6ea5", "republic",
    origin="1949 im Westen aus den drei westlichen Besatzungszonen gegründet (Grundgesetz, 23. Mai 1949).",
    house="Parlamentarische Demokratie", religion="Christlich geprägt, pluralistisch", capital="Bonn",
    eras={
      "1961": {"keyFacts": ["Westlicher Teilstaat, in NATO und (ab 1957) Europäische Gemeinschaft eingebunden.",
                            "„Wirtschaftswunder“ unter Konrad Adenauer und Ludwig Erhard.",
                            "1957 tritt das Saarland als zehntes Bundesland bei."]},
      "1990": {"keyFacts": ["Am 3. Oktober 1990 tritt die DDR der Bundesrepublik bei — Wiedervereinigung.",
                            "Zwei-plus-Vier-Vertrag (12. September 1990) regelt die volle Souveränität.",
                            "Hauptstadt wird wieder Berlin."]},
    }),
  "ddr": F("Deutsche Demokratische Republik", "#a8472e", "republic",
    origin="1949 im Osten unter sowjetischem Einfluss gegründet (7. Oktober 1949).",
    house="Sozialistischer Einparteienstaat (SED)", religion="Staatlich atheistisch geprägt", capital="Ost-Berlin",
    eras={
      "1961": {"keyFacts": ["Sozialistischer Staat im Ostblock (Warschauer Pakt).",
                            "Am 13. August 1961 Bau der Berliner Mauer.",
                            "Planwirtschaft und Herrschaft der SED."]},
      "1990": {"keyFacts": ["1989 Friedliche Revolution; Fall der Berliner Mauer am 9. November 1989.",
                            "Erste freie Volkskammerwahl im März 1990.",
                            "Beitritt zur Bundesrepublik am 3. Oktober 1990."]},
    }),

  # ---- Antike (eigene Näherungszonen) ----
  "kelten": F("Keltische Stämme (La Tène)", "#7a8a5a", "people", religion="Keltische Religion",
    origin="Träger der La-Tène-Kultur in Süd- und Westmitteleuropa.",
    eras={"-100": {"keyFacts": ["Oppida (befestigte Großsiedlungen) als wirtschaftliche Zentren.",
                                "Eisenverarbeitung, Münzprägung, weitreichender Handel.",
                                "Werden ab dem 1. Jh. v. Chr. von Germanen und Römern verdrängt."]}}),
  "germanen": F("Germanische Stämme", "#8a6d4f", "people", religion="Germanische Religion",
    origin="Lockerer Verband germanischer Stämme nördlich von Rhein und Donau.",
    eras={
      "-100": {"keyFacts": ["Stämme wie Sueben, Cherusker und Chatten.",
                            "Bäuerliche Gesellschaft ohne feste Staatlichkeit.",
                            "Beginnende Wanderbewegungen (Kimbern und Teutonen)."]},
      "100": {"name": "Freies Germanien (Magna Germania)",
              "keyFacts": ["Nach der Varusschlacht 9 n. Chr. bleibt das rechtsrheinische Germanien unabhängig.",
                           "Stammesgebiete der Cherusker, Chatten, Markomannen u. a.",
                           "Rege Handelskontakte mit dem Römischen Reich."]},
    }),
  "boier": F("Boier (keltisch)", "#6e8a6a", "people", religion="Keltische Religion",
    origin="Keltischer Stamm im Gebiet des heutigen Böhmen („Boiohaemum“).",
    eras={"-100": {"keyFacts": ["Geben Böhmen seinen Namen.",
                                "Werden um die Zeitenwende von den germanischen Markomannen verdrängt."]}}),
  "roemer": F("Römisches Reich", "#b07050", "empire", foreign=True, religion="Römische Religion",
    origin="Antikes Imperium rund um das Mittelmeer.",
    house="Republik bzw. Kaiser", capital="Rom",
    eras={
      "-100": {"name": "Römische Republik", "keyFacts": ["Beherrscht den Mittelmeerraum und Gallia Narbonensis.",
                                                         "Steht noch vor Caesars Gallischen Kriegen (58–51 v. Chr.)."]},
      "100": {"keyFacts": ["Grenze (Limes) entlang von Rhein und Donau.",
                           "Provinzen Germania, Raetia und Noricum mit Städten wie Köln und Trier.",
                           "Pax Romana unter den Kaisern Trajan und Hadrian."]},
    }),
  "weibrom": F("Weströmisches Reich", "#b07050", "empire", foreign=True, religion="Christlich (spätantik)",
    origin="Westhälfte des spätantiken Römischen Reiches.",
    eras={"500": {"keyFacts": ["Das Weströmische Reich ist 476 untergegangen; Reststrukturen im Süden.",
                               "Germanische Reiche treten an seine Stelle."]}}),
  "franken_v": F("Franken", "#8c5a3c", "people",
    origin="Germanischer Stammesverband am Niederrhein.",
    eras={"500": {"keyFacts": ["Unter Chlodwig I. (Merowinger) Aufstieg zur Großmacht.",
                               "Übertritt zum katholischen Christentum um 500.",
                               "Keimzelle des späteren Frankenreichs und damit des Reiches."]}}),
  "sachsen_v": F("Sachsen", "#7d6b4a", "people", religion="Germanische Religion",
    origin="Germanischer Stammesverband zwischen Rhein, Elbe und Nordsee.",
    eras={"500": {"keyFacts": ["Bauern und Seefahrer im norddeutschen Tiefland.",
                               "Beteiligt an der Besiedlung Britanniens (Angelsachsen).",
                               "Erst Karl der Große unterwirft sie (772–804)."]}}),
  "thueringer_v": F("Thüringer", "#8c6d4a", "people", religion="Germanische Religion",
    origin="Germanisches Königreich in Mitteldeutschland.",
    eras={"500": {"keyFacts": ["Eigenes Königreich um 500; 531 von Franken und Sachsen zerschlagen."]}}),
  "alemannen_v": F("Alemannen", "#6e8a8d", "people", religion="Germanische Religion",
    origin="Germanischer Stammesverband am Oberrhein und an der oberen Donau.",
    eras={"500": {"keyFacts": ["Siedeln im alten Dekumatland (heute Südwestdeutschland/Schweiz).",
                               "496/506 von den Franken unterworfen."]}}),
  "burgunden": F("Burgunden", "#9c7b4f", "people", religion="Arianisches Christentum",
    origin="Ostgermanischer Stamm, im 5. Jh. an Rhône und Saône angesiedelt.",
    eras={"500": {"keyFacts": ["Reich um Lyon und Genf.",
                               "534 von den Franken erobert."]}}),
  "ostgoten": F("Ostgoten", "#a8554a", "people", foreign=True, religion="Arianisches Christentum",
    origin="Ostgermanisches Volk; gründet unter Theoderich ein Reich in Italien.",
    eras={"500": {"keyFacts": ["Theoderich der Große herrscht von Ravenna aus.",
                               "Kontrolliert auch Noricum und das Alpenvorland."]}}),
}

# Cliopatria-Name -> Fraktions-ID
NAME_MAP = {
  "Holy Roman Empire": "hre",
  "Holy Roman Empire Minor States": "hre_minor",
  "Duchy of Bohemia": "boehmen", "Kingdom of Bohemia": "boehmen",
  "Duchy of Bavaria": "bayern", "Kingdom of Bavaria": "bayern_kgr",
  "House of Ascania": "askanien",
  "Electorate of Brandenburg": "brandenburg",
  "Brandenburg-Prussia": "brandenburg_preussen", "Kingdom of Prussia": "preussen",
  "Electorate of Saxony": "sachsen_kur",
  "House of Habsburg": "habsburg", "Habsburg Monarchy": "habsburg",
  "Austrian Empire": "oesterreich_kaisertum",
  "Electorate of Trier": "trier",
  "Duchy of Styria": "habsburg",
  "House of Luxembourg": "luxemburg",
  "Swiss Confederation": "eidgenossenschaft",
  "Teutonic Order": "deutschorden",
  "Kingdom of Württemberg": "wuerttemberg_kgr",
  "Grand Duchy of Baden": "baden",
  "German Confederation": "deutscher_bund",
  "German Empire": "deutsches_reich",
  # Nachbarn / foreign
  "Kingdom of France": "frankreich", "Bourbon Kingdom of France": "frankreich",
  "French Third Republic": "frankreich_rep", "House of Bourbon": "frankreich",
  "Kingdom of Poland": "polen", "Polish-Lithuanian Commonwealth": "polen_litauen",
  "House of Jagiellon": "polen_litauen",
  "Kingdom of Hungary": "ungarn",
  "Kingdom of Denmark": "daenemark", "Denmark-Norway": "daenemark",
  "Kalmar Union": "kalmar", "United Kingdoms of Sweden and Norway": "schweden_norwegen",
  "Swedish Empire": "schweden",
  "Ottoman Empire": "osmanen",
  "Republic of Venice": "venedig", "Republic of Genoa": "genua",
  "Duchy of Milan": "mailand", "Duchy of Lorraine": "lothringen_hzm",
  "Kingdom of Arles": "arelat", "Free County of Burgundy": "burgund_frei",
  "County of Savoy": "savoyen", "House of Savoy": "savoyen",
  "County of Brabant": "brabant", "County of Champagne": "champagne",
  "Kingdom of Croatia": "kroatien", "Old Kingdom of Norway": "norwegen",
  "Patriarchate of Aquileia": "aquileia", "Dutch Republic": "niederlande",
  "Netherlands": "niederlande", "Kingdom of Belgium": "belgien",
  "Kingdom of Spain": "spanien", "Kingdom of Italy": "italien",
  "Russian Empire": "russland", "Austria-Hungary": "oesterreich_ungarn",
  "Duchy of Greater Poland": "polen", "Duchy of Silesia": "schlesien",
  "Duchy of Sandomierz": "polen", "Duchy of Opole": "schlesien",
  "Duchy of Wrocław": "schlesien", "Duchy of Kuyavia": "polen",
  # 20./21. Jahrhundert
  "German Empire": "deutsches_reich", "Weimar Republic": "deutsches_reich",
  "Nazi Germany": "ns_reich",
  "Federal Republic of Germany": "brd", "German Democratic Republic": "ddr",
  "Republic of Austria": "oesterreich_rep", "Second Republic of Austria": "oesterreich_rep",
  "Czechoslovakia": "tschechoslowakei", "Czech Republic": "tschechien",
  "Slovakia": "slowakei", "Republic of Slovenia": "slowenien",
  "Republic of Croatia": "kroatien_rep", "Independent State of Croatia": "kroatien_ns",
  "Second Polish Republic": "polen_2", "Republic of Poland": "polen_rep",
  "Hungarian Republic": "ungarn_rep", "Hungary": "ungarn_rep",
  "Hungarian People's Republic": "ungarn_rep",
  "Yugoslavia": "jugoslawien", "Socialist Federal Republic of Yugoslavia": "jugoslawien",
  "Free City of Danzig": "danzig", "Luxembourg": "luxemburg_staat",
  "Union of Soviet Socialist Republics": "sowjetunion",
  "Vichy France": "frankreich_vichy", "Republic of Italy": "italien",
  "Kingdom of Belgium": "belgien", "Kingdom of Sweden": "schweden",
}
# Hinweis: „German Empire“ deckt Kaiserreich (1871/1914) und Weimarer Reich
# (1919) ab; „Federated Republic of Germany“ (2024) wird bewusst NICHT
# kartiert, weil die Gegenwart stattdessen in Bundesländer aufgeteilt wird.

# Zusätzliche (meist ausländische) Fraktionen, knapp gehalten.
FOREIGN = {
  "frankreich": ("Frankreich", "#8a98a8"),
  "frankreich_rep": ("Französische Republik", "#8a98a8"),
  "polen": ("Polen", "#9aa48a"),
  "polen_litauen": ("Polen-Litauen", "#9aa48a"),
  "schlesien": ("Schlesische Herzogtümer", "#9a8a6a"),
  "ungarn": ("Ungarn", "#a89a78"),
  "daenemark": ("Dänemark", "#7a98a0"),
  "kalmar": ("Kalmarer Union", "#7a98a0"),
  "schweden": ("Schweden", "#8aa0a8"),
  "schweden_norwegen": ("Schweden-Norwegen", "#8aa0a8"),
  "norwegen": ("Königreich Norwegen", "#8aa0a8"),
  "osmanen": ("Osmanisches Reich", "#a88a7a"),
  "venedig": ("Republik Venedig", "#a094a8"),
  "genua": ("Republik Genua", "#a094a8"),
  "mailand": ("Herzogtum Mailand", "#a094a8"),
  "italien": ("Italien", "#a094a8"),
  "lothringen_hzm": ("Herzogtum Lothringen", "#9a8a8a"),
  "arelat": ("Königreich Arelat (Burgund)", "#9a8a6a"),
  "burgund_frei": ("Freigrafschaft Burgund", "#9a8a6a"),
  "savoyen": ("Savoyen", "#9a9a8a"),
  "brabant": ("Herzogtum Brabant", "#8a9a9a"),
  "champagne": ("Grafschaft Champagne", "#9aa0a8"),
  "kroatien": ("Königreich Kroatien", "#a0a890"),
  "aquileia": ("Patriarchat Aquileia", "#a094a8"),
  "niederlande": ("Niederlande", "#8a9aa0"),
  "belgien": ("Königreich Belgien", "#8a9aa0"),
  "spanien": ("Spanien", "#a89888"),
  "russland": ("Russland", "#9aa0a8"),
  "oesterreich_ungarn": ("Österreich-Ungarn", "#a8554a"),
  # 20./21. Jahrhundert
  "oesterreich_rep": ("Republik Österreich", "#c08878"),
  "tschechoslowakei": ("Tschechoslowakei", "#a89878"),
  "tschechien": ("Tschechien", "#a89878"),
  "slowakei": ("Slowakei", "#b0a088"),
  "slowenien": ("Slowenien", "#a0a8a0"),
  "kroatien_rep": ("Kroatien", "#a0a890"),
  "polen_2": ("Zweite Polnische Republik", "#9aa48a"),
  "polen_rep": ("Republik Polen", "#9aa48a"),
  "ungarn_rep": ("Ungarn", "#a89a78"),
  "jugoslawien": ("Jugoslawien", "#9aa090"),
  "danzig": ("Freie Stadt Danzig", "#b0a89a"),
  "luxemburg_staat": ("Luxemburg", "#b0a87a"),
  "schweiz": ("Schweiz", "#9a9a92"),
  "sowjetunion": ("Sowjetunion", "#9a8a8a"),
  "frankreich_vichy": ("Vichy-Frankreich", "#9a9088"),
  "kroatien_ns": ("Unabhängiger Staat Kroatien", "#9a9088"),
  "luxemburg": ("Haus Luxemburg", "#b59a5a"),
}
for fid, (nm, col) in FOREIGN.items():
    if fid not in FACTIONS:
        FACTIONS[fid] = F(nm, col, foreign=(fid not in ("luxemburg",)))

# Die 16 Bundesländer (für die Epoche „Heute“).
LAENDER = [
  ("Baden-Württemberg", "bl_bw", "Stuttgart", "#8a6d3b", "1952 aus Baden und Württemberg gebildet."),
  ("Bayern", "bl_by", "München", "#5f7a5a", "Größtes Bundesland; Freistaat mit langer eigener Geschichte."),
  ("Berlin", "bl_be", "Berlin", "#b0724a", "Hauptstadt und Stadtstaat; bis 1990 geteilt."),
  ("Brandenburg", "bl_bb", "Potsdam", "#6e8a6a", "Umschließt Berlin; Kern der alten Mark Brandenburg."),
  ("Bremen", "bl_hb", "Bremen", "#7a98a0", "Kleinstes Bundesland; alte Hansestadt (Stadtstaat)."),
  ("Hamburg", "bl_hh", "Hamburg", "#6a8a8d", "Größter deutscher Hafen; Hansestadt und Stadtstaat."),
  ("Hessen", "bl_he", "Wiesbaden", "#7c8456", "Finanzzentrum Frankfurt am Main."),
  ("Mecklenburg-Vorpommern", "bl_mv", "Schwerin", "#6f8f92", "Ostseeland mit Seenplatte; dünn besiedelt."),
  ("Niedersachsen", "bl_ni", "Hannover", "#94794e", "Flächenmäßig zweitgrößtes Bundesland."),
  ("Nordrhein-Westfalen", "bl_nw", "Düsseldorf", "#a8724a", "Bevölkerungsreichstes Land; Ruhrgebiet."),
  ("Rheinland-Pfalz", "bl_rp", "Mainz", "#9c5a52", "Weinland an Rhein und Mosel."),
  ("Saarland", "bl_sl", "Saarbrücken", "#b06a4e", "1957 als zehntes Land der Bundesrepublik beigetreten."),
  ("Sachsen", "bl_sn", "Dresden", "#9a7a3b", "Freistaat; Kultur und Industrie (Dresden, Leipzig)."),
  ("Sachsen-Anhalt", "bl_st", "Magdeburg", "#8a7b5a", "Welterbe in Wittenberg, Dessau und Quedlinburg."),
  ("Schleswig-Holstein", "bl_sh", "Kiel", "#7a98a0", "Land zwischen Nord- und Ostsee."),
  ("Thüringen", "bl_th", "Erfurt", "#8c6d4a", "„Grünes Herz“ Deutschlands; Weimar und Wartburg."),
]
LAENDER_ID = {nm: fid for nm, fid, cap, col, fact in LAENDER}
for nm, fid, cap, col, fact in LAENDER:
    FACTIONS[fid] = F(nm, col, "state", capital=cap,
                      religion="Christlich geprägt, pluralistisch",
                      origin="Bundesland der Bundesrepublik Deutschland.",
                      eras={"2024": {"keyFacts": [fact]}})


# ---------------------------------------------------------------------------
# Antike Epochen — von Hand angelegte Näherungszonen (eigene Arbeit).
# ---------------------------------------------------------------------------
ANCIENT = {
  -100: [
    ("germanen", [[6.0,51.0],[6.5,54.0],[10.0,55.0],[14.0,54.5],[15.5,53.0],[14.0,51.0],[11.0,50.3],[8.0,50.3],[6.0,51.0]]),
    ("kelten",   [[5.5,47.0],[5.5,50.5],[8.0,50.5],[11.0,49.3],[13.0,48.3],[12.0,46.8],[8.5,46.6],[6.0,46.8],[5.5,47.0]]),
    ("boier",    [[12.2,49.0],[12.6,50.4],[14.6,50.8],[16.2,50.0],[15.2,48.7],[13.4,48.6],[12.2,49.0]]),
    ("roemer",   [[3.0,43.5],[3.0,45.2],[8.0,46.2],[13.5,46.4],[17.0,46.0],[15.0,43.5],[3.0,43.5]]),
  ],
  100: [
    ("roemer",   [[3.0,43.5],[3.0,50.0],[6.2,51.2],[7.0,50.0],[8.2,49.0],[11.0,48.7],[13.5,48.4],[17.0,48.0],[18.0,46.0],[16.0,43.5],[3.0,43.5]]),
    ("germanen", [[6.3,50.2],[6.8,54.0],[10.0,55.0],[14.0,54.5],[16.5,53.0],[18.0,49.5],[14.0,48.7],[11.2,48.9],[8.4,49.2],[7.0,50.2],[6.3,50.2]]),
    ("boier",    [[12.2,49.0],[12.6,50.4],[14.6,50.8],[16.2,50.0],[15.2,48.7],[13.4,48.6],[12.2,49.0]]),
  ],
  500: [
    ("franken_v",   [[3.5,49.0],[3.5,51.8],[6.0,52.8],[8.2,51.6],[8.4,49.8],[6.6,48.9],[4.5,48.8],[3.5,49.0]]),
    ("sachsen_v",   [[6.8,52.2],[6.8,54.2],[10.0,55.0],[12.8,54.6],[12.2,52.4],[9.5,51.8],[6.8,52.2]]),
    ("thueringer_v",[[9.5,50.0],[9.4,52.2],[12.6,52.2],[13.2,50.3],[11.5,49.6],[10.0,49.7],[9.5,50.0]]),
    ("alemannen_v", [[6.3,47.0],[6.3,49.6],[9.0,49.4],[10.8,48.6],[10.2,47.0],[8.0,46.5],[6.3,47.0]]),
    ("burgunden",   [[3.5,45.5],[3.5,48.0],[6.6,48.6],[7.2,46.4],[6.0,44.8],[3.5,45.5]]),
    ("ostgoten",    [[11.5,45.8],[11.5,48.4],[15.0,48.6],[18.0,47.6],[17.0,45.8],[13.5,45.6],[11.5,45.8]]),
    ("weibrom",     [[6.5,43.5],[6.5,45.8],[12.0,46.2],[18.0,45.8],[17.0,43.5],[6.5,43.5]]),
  ],
}


# ---------------------------------------------------------------------------
# Siedlungen (Städte) je Epoche — kuratiert.
# ---------------------------------------------------------------------------
def C(id, name, lat, lon, kind, imp, fid):
    return {"id": id, "name": name, "lat": lat, "lon": lon, "kind": kind, "importance": imp, "factionId": fid}

SETTLEMENTS = {
  100: [C("koeln","Colonia (Köln)",50.94,6.96,"stadt",3,"roemer"),
        C("trier","Augusta Treverorum (Trier)",49.76,6.64,"stadt",3,"roemer"),
        C("mainz","Mogontiacum (Mainz)",50.00,8.27,"stadt",2,"roemer"),
        C("regensburg","Castra Regina (Regensburg)",49.02,12.10,"stadt",2,"roemer"),
        C("augsburg","Augusta Vindelicorum",48.37,10.90,"stadt",2,"roemer")],
  500: [C("koeln","Köln",50.94,6.96,"stadt",2,"franken_v"),
        C("trier","Trier",49.76,6.64,"stadt",2,"franken_v"),
        C("ravenna","Ravenna",44.42,12.20,"residenz",2,"ostgoten")],
  1000:[C("aachen","Aachen",50.78,6.08,"residenz",3,"hre"),
        C("magdeburg","Magdeburg",52.13,11.63,"bischofssitz",3,"hre"),
        C("regensburg","Regensburg",49.02,12.10,"residenz",2,"hre"),
        C("mainz","Mainz",50.00,8.27,"bischofssitz",2,"hre"),
        C("prag","Prag",50.09,14.42,"residenz",2,"boehmen")],
  1200:[C("goslar","Goslar",51.91,10.43,"residenz",2,"hre"),
        C("nuernberg","Nürnberg",49.45,11.08,"reichsstadt",2,"hre"),
        C("koeln","Köln",50.94,6.96,"stadt",3,"hre"),
        C("wien","Wien",48.21,16.37,"residenz",2,"hre"),
        C("prag","Prag",50.09,14.42,"residenz",3,"boehmen")],
  1350:[C("prag","Prag",50.09,14.42,"residenz",3,"boehmen"),
        C("frankfurt","Frankfurt am Main",50.11,8.68,"reichsstadt",3,"hre_minor"),
        C("nuernberg","Nürnberg",49.45,11.08,"reichsstadt",3,"hre_minor"),
        C("koeln","Köln",50.94,6.96,"reichsstadt",3,"hre_minor"),
        C("luebeck","Lübeck",53.87,10.69,"hansestadt",3,"hre_minor"),
        C("wien","Wien",48.21,16.37,"residenz",3,"habsburg"),
        C("muenchen","München",48.14,11.58,"residenz",2,"bayern"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"hre_minor"),
        C("mainz","Mainz",50.00,8.27,"bischofssitz",2,"mainz"),
        C("trier","Trier",49.76,6.64,"bischofssitz",2,"trier"),
        C("augsburg","Augsburg",48.37,10.90,"reichsstadt",2,"hre_minor"),
        C("heidelberg","Heidelberg",49.40,8.69,"residenz",2,"pfalz"),
        C("zuerich","Zürich",47.37,8.54,"stadt",2,"eidgenossenschaft")],
  1500:[C("wien","Wien",48.21,16.37,"residenz",3,"habsburg"),
        C("nuernberg","Nürnberg",49.45,11.08,"reichsstadt",3,"hre_minor"),
        C("augsburg","Augsburg",48.37,10.90,"reichsstadt",3,"hre_minor"),
        C("koeln","Köln",50.94,6.96,"reichsstadt",3,"hre_minor"),
        C("prag","Prag",50.09,14.42,"residenz",2,"boehmen"),
        C("wittenberg","Wittenberg",51.87,12.65,"residenz",2,"sachsen_kur"),
        C("muenchen","München",48.14,11.58,"residenz",2,"bayern"),
        C("luebeck","Lübeck",53.87,10.69,"hansestadt",2,"hre_minor")],
  1650:[C("wien","Wien",48.21,16.37,"residenz",3,"habsburg"),
        C("berlin","Berlin",52.52,13.40,"residenz",2,"brandenburg_preussen"),
        C("muenchen","München",48.14,11.58,"residenz",2,"bayern"),
        C("dresden","Dresden",51.05,13.74,"residenz",2,"sachsen_kur"),
        C("prag","Prag",50.09,14.42,"residenz",2,"habsburg"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"hre_minor"),
        C("koeln","Köln",50.94,6.96,"reichsstadt",2,"hre_minor"),
        C("muenster","Münster",51.96,7.63,"bischofssitz",2,"hre_minor")],
  1815:[C("wien","Wien",48.21,16.37,"residenz",3,"oesterreich_kaisertum"),
        C("berlin","Berlin",52.52,13.40,"residenz",3,"preussen"),
        C("muenchen","München",48.14,11.58,"residenz",2,"bayern_kgr"),
        C("frankfurt","Frankfurt am Main",50.11,8.68,"reichsstadt",2,"deutscher_bund"),
        C("dresden","Dresden",51.05,13.74,"residenz",2,"sachsen_kur"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"deutscher_bund"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"preussen"),
        C("stuttgart","Stuttgart",48.78,9.18,"residenz",2,"wuerttemberg_kgr")],
  1900:[C("berlin","Berlin",52.52,13.40,"residenz",3,"deutsches_reich"),
        C("wien","Wien",48.21,16.37,"residenz",3,"oesterreich_ungarn"),
        C("muenchen","München",48.14,11.58,"residenz",2,"deutsches_reich"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",3,"deutsches_reich"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"deutsches_reich"),
        C("frankfurt","Frankfurt am Main",50.11,8.68,"stadt",2,"deutsches_reich"),
        C("leipzig","Leipzig",51.34,12.37,"stadt",2,"deutsches_reich"),
        C("dresden","Dresden",51.05,13.74,"residenz",2,"deutsches_reich")],
  1914:[C("berlin","Berlin",52.52,13.40,"residenz",3,"deutsches_reich"),
        C("wien","Wien",48.21,16.37,"residenz",3,"oesterreich_ungarn"),
        C("muenchen","München",48.14,11.58,"stadt",2,"deutsches_reich"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",3,"deutsches_reich"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"deutsches_reich"),
        C("leipzig","Leipzig",51.34,12.37,"stadt",2,"deutsches_reich")],
  1920:[C("berlin","Berlin",52.52,13.40,"residenz",3,"deutsches_reich"),
        C("muenchen","München",48.14,11.58,"stadt",2,"deutsches_reich"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"deutsches_reich"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"deutsches_reich"),
        C("danzig","Danzig",54.35,18.65,"hansestadt",2,"danzig")],
  1938:[C("berlin","Berlin",52.52,13.40,"residenz",3,"ns_reich"),
        C("wien","Wien",48.21,16.37,"stadt",3,"ns_reich"),
        C("muenchen","München",48.14,11.58,"stadt",2,"ns_reich"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"ns_reich")],
  1942:[C("berlin","Berlin",52.52,13.40,"residenz",3,"ns_reich"),
        C("wien","Wien",48.21,16.37,"stadt",2,"ns_reich"),
        C("muenchen","München",48.14,11.58,"stadt",2,"ns_reich"),
        C("prag","Prag",50.09,14.42,"stadt",2,"ns_reich")],
  1961:[C("bonn","Bonn",50.74,7.10,"residenz",3,"brd"),
        C("ostberlin","Ost-Berlin",52.52,13.40,"residenz",2,"ddr"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"brd"),
        C("muenchen","München",48.14,11.58,"stadt",2,"brd"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"brd"),
        C("frankfurt","Frankfurt am Main",50.11,8.68,"stadt",2,"brd"),
        C("leipzig","Leipzig",51.34,12.37,"stadt",2,"ddr"),
        C("dresden","Dresden",51.05,13.74,"stadt",2,"ddr")],
  1990:[C("bonn","Bonn",50.74,7.10,"residenz",2,"brd"),
        C("berlin","Berlin",52.52,13.40,"residenz",3,"ddr"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",2,"brd"),
        C("muenchen","München",48.14,11.58,"stadt",2,"brd"),
        C("leipzig","Leipzig",51.34,12.37,"stadt",2,"ddr"),
        C("dresden","Dresden",51.05,13.74,"stadt",2,"ddr")],
  2024:[C("berlin","Berlin",52.52,13.40,"residenz",3,"bl_be"),
        C("muenchen","München",48.14,11.58,"stadt",3,"bl_by"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",3,"bl_hh"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"bl_nw"),
        C("frankfurt","Frankfurt am Main",50.11,8.68,"stadt",2,"bl_he"),
        C("stuttgart","Stuttgart",48.78,9.18,"stadt",2,"bl_bw"),
        C("dresden","Dresden",51.05,13.74,"stadt",2,"bl_sn"),
        C("hannover","Hannover",52.37,9.74,"stadt",2,"bl_ni")],
}

# Kultur-/Sprachzonen (nur Hochmittelalter, durchscheinend).
LANG_ZONES = [
  {"cultureId":"niederdeutsch","name":"Niederdeutsche Mundarten","color":"#5a6b7a","pattern":"hatch",
   "note":"Sprachgrenzen fließend.","ring":[[6.5,51.4],[6.5,53.6],[9.5,54.0],[12.5,54.3],[14.2,53.6],[13.5,51.8],[11.0,51.5],[8.0,51.3],[6.5,51.4]]},
  {"cultureId":"hochdeutsch","name":"Hochdeutsche Mundarten","color":"#8a6b3a","pattern":"hatch",
   "note":"Ober- und mitteldeutsches Sprachgebiet.","ring":[[6.0,47.0],[6.0,51.4],[9.0,51.4],[12.0,51.6],[15.5,51.0],[17.0,48.5],[13.0,46.6],[9.0,46.7],[6.5,46.9],[6.0,47.0]]},
  {"cultureId":"sorbisch","name":"Sorbisch/Wendisches Gebiet","color":"#6a8a5a","pattern":"hatch",
   "note":"Westslawische Restbevölkerung in der Lausitz.","ring":[[13.4,50.9],[13.3,51.9],[14.0,52.0],[14.8,51.4],[14.5,50.9],[13.4,50.9]]},
]

# Epochen: (Jahr, Label, Quelle, View, Blurb). Quelle:
#   "hb:<jahr>"      -> historical-basemaps (Antike, kulturelle Tiefe)
#   "clio"           -> Cliopatria, europaweit (kontinuierlich, jedes Jahr)
#   "clio+laender"   -> Cliopatria + 16 Bundesländer (Gegenwart)
# Ab 850 ein dichtes Raster (mind. alle 50 Jahre), modern noch feiner.
_ANCIENT = [
  (-1000,"Um 1000 v. Chr. — Bronzezeit","hb:bc1000",VIEW_EUROPE,
   "Bronzezeit: die Urnenfelderkultur prägt Mitteleuropa, lange vor Kelten und Germanen."),
  (-500,"Um 500 v. Chr. — Kelten & frühe Völker","hb:bc500",VIEW_EUROPE,
   "Vor Rom und den großen Wanderungen prägen keltische Kulturen West- und Mitteleuropa, im Norden frühe Germanen."),
  (-300,"Um 300 v. Chr. — Keltische Welt","hb:bc300",VIEW_EUROPE,
   "Die Kelten auf dem Höhepunkt ihrer Ausdehnung; Keltenzüge reichen bis Griechenland und Kleinasien."),
  (-200,"Um 200 v. Chr. — Kelten & Germanen","hb:bc200",VIEW_EUROPE,
   "Die keltische La-Tène-Kultur auf ihrem Höhepunkt; germanische Stämme drängen nach Süden, Rom wächst."),
  (-100,"Um 100 v. Chr. — Vor Caesar","hb:bc100",VIEW_EUROPE,
   "Kurz vor Caesars Gallischem Krieg; germanische Stämme drängen über den Rhein."),
  (-1,"Christi Geburt — Rom & Germanien","hb:bc1",VIEW_EUROPE,
   "Rom reicht bis an Rhein und Donau; östlich liegt das freie Germanien. 9 n. Chr. stoppt die Varusschlacht Roms Vormarsch."),
  (100,"Um 100 — Römisches Reich","hb:100",VIEW_EUROPE,
   "Pax Romana: Rom beherrscht den Mittelmeerraum, die Grenze verläuft am Limes."),
  (200,"Um 200 — Hochphase des Imperiums","hb:200",VIEW_EUROPE,
   "Das Römische Reich nahe seiner größten Ausdehnung; jenseits des Limes leben die Germanen."),
  (300,"Um 300 — Spätantike","hb:300",VIEW_EUROPE,
   "Das Römische Reich gerät unter Druck; an den Grenzen formieren sich germanische Verbände."),
  (400,"Um 400 — Hunnensturm","hb:400",VIEW_EUROPE,
   "Hunnen und germanische Wanderungen erschüttern das Weströmische Reich."),
  (500,"Um 500 — Völkerwanderung","hb:500",VIEW_EUROPE,
   "Nach dem Untergang Westroms entstehen germanische Reiche: Franken, Goten, Sachsen, Thüringer, Alemannen."),
  (600,"Um 600 — Germanische Reiche","hb:600",VIEW_EUROPE,
   "Franken, Westgoten und Langobarden teilen das alte weströmische Gebiet."),
  (700,"Um 700 — Fränkisches Reich","hb:700",VIEW_EUROPE,
   "Das Frankenreich der Merowinger wird zur beherrschenden Macht westlich des Rheins."),
  (800,"800 — Karl der Große","hb:800",VIEW_EUROPE,
   "Karl der Große eint weite Teile Europas; 800 Kaiserkrönung — eine Wurzel des Reiches."),
]
_NOTE = {
  850:"Nach der Teilung von Verdun (843): Ost- und Westfrankenreich",
  900:"Das Ostfrankenreich wird zum Königreich Deutschland",
  950:"Ottonische Königsherrschaft unter Otto dem Großen",
  1000:"Ottonisches Kaiserreich; Otto III. und die Idee Roms",
  1050:"Salierzeit",
  1100:"Investiturstreit zwischen Kaiser und Papst",
  1150:"Stauferzeit unter Friedrich Barbarossa",
  1200:"Höhepunkt der Stauferzeit",
  1250:"Ende der Staufer; Beginn des Interregnums",
  1300:"Aufstieg von Habsburg und Luxemburg",
  1350:"Goldene Bulle (1356); die großen Pestwellen",
  1400:"Spätmittelalter; Zeit der Konzilien",
  1450:"Um die Erfindung des Buchdrucks",
  1500:"Reichsreform unter Maximilian I.",
  1550:"Reformation und Konfessionalisierung",
  1600:"Vorabend des Dreißigjährigen Krieges",
  1650:"Nach dem Westfälischen Frieden (1648)",
  1700:"Barock; Aufstieg Brandenburg-Preußens",
  1750:"Preußen wird unter Friedrich II. Großmacht",
  1800:"Napoleonische Umwälzung; das Alte Reich endet 1806",
}
_MODERN = [
  (1815,"1815 — Deutscher Bund","Wiener Kongress: 39 Staaten unter österreichischem Vorsitz, Preußen als Rivale."),
  (1848,"1848 — Revolution","Die Revolution von 1848/49 und die Frankfurter Nationalversammlung scheitern."),
  (1871,"1871 — Deutsches Kaiserreich","Reichsgründung unter preußischer Führung (kleindeutsche Lösung)."),
  (1900,"Um 1900 — Kaiserreich","Industrialisierung, Weltmachtstreben, Bündnissysteme."),
  (1914,"1914 — Erster Weltkrieg","Das Kaiserreich, verbündet mit Österreich-Ungarn, zieht in den Krieg."),
  (1925,"1925 — Weimarer Republik","Die junge Republik zwischen Inflation, Krisen und kurzer Stabilisierung."),
  (1938,"1938 — NS-Staat","Anschluss Österreichs und des Sudetenlands; aggressive Expansion."),
  (1942,"1942 — Zweiter Weltkrieg","Größte Ausdehnung der deutschen Herrschaft; weite Teile Europas sind besetzt. Zeit von Vernichtungskrieg und Holocaust."),
  (1961,"1961 — Geteiltes Deutschland","BRD und DDR im Kalten Krieg; Bau der Berliner Mauer."),
  (1990,"1990 — Wiedervereinigung","Die DDR tritt am 3. Oktober 1990 der Bundesrepublik bei."),
  (2024,"Heute — Bundesrepublik Deutschland","16 Bundesländer, eingebunden in EU und NATO. Tippe ein Bundesland an."),
]
ERAS = list(_ANCIENT)
for _y in range(850, 1801, 50):
    _n = _NOTE.get(_y, "")
    _lab = f"Um {_y}" + (" — " + _n.split(";")[0] if _n else "")
    ERAS.append((_y, _lab, "clio", VIEW_CEUROPE if _y >= 1200 else VIEW_EUROPE, _n))
for _y, _lab, _bl in _MODERN:
    ERAS.append((_y, _lab, "clio+laender" if _y == 2024 else "clio", VIEW_CEUROPE, _bl))

_OLD_ERAS = [
  (-500,"Um 500 v. Chr. — Kelten & frühe Völker","bc500",None,VIEW_EUROPE,
   "Vor Rom und den großen Wanderungen: keltische Kulturen prägen weite Teile West- und Mitteleuropas, im Norden frühe germanische Stämme."),
  (-200,"Um 200 v. Chr. — Kelten & Germanen","bc200",None,VIEW_EUROPE,
   "Die keltische La-Tène-Kultur ist auf ihrem Höhepunkt; aus dem Norden drängen germanische Stämme nach Süden, Rom wächst im Mittelmeerraum."),
  (-1,"Um Christi Geburt — Rom & Germanien","bc1",None,VIEW_EUROPE,
   "Das Römische Reich reicht bis an Rhein und Donau. Östlich davon liegt das freie Germanien; 9 n. Chr. stoppt die Varusschlacht die römische Expansion."),
  (200,"Um 200 — Römisches Reich","200",None,VIEW_EUROPE,
   "Die Pax Romana: Rom beherrscht den Mittelmeerraum, die Grenze (Limes) verläuft an Rhein und Donau, dahinter die germanischen Stämme."),
  (400,"Um 400 — Spätantike","400",None,VIEW_EUROPE,
   "Das Römische Reich ist geteilt und unter Druck. Germanische Verbände wandern ins Reich; das Zeitalter der Völkerwanderung beginnt."),
  (500,"Um 500 — Völkerwanderung","500",None,VIEW_EUROPE,
   "Nach dem Untergang Westroms entstehen germanische Reiche: Franken, Westgoten, Ostgoten, dazu Sachsen, Thüringer und Alemannen."),
  (700,"Um 700 — Fränkisches Reich","700",None,VIEW_EUROPE,
   "Das Frankenreich der Merowinger wird zur beherrschenden Macht westlich des Rheins und dehnt sich nach Germanien aus."),
  (800,"800 — Karl der Große","800",None,VIEW_EUROPE,
   "Karl der Große eint weite Teile West- und Mitteleuropas; 800 wird er zum Kaiser gekrönt — eine Wurzel des späteren Heiligen Römischen Reiches."),
  (1000,"Um 1000 — Ottonisches Reich","1000",None,VIEW_CEUROPE,
   "Das ottonische Reich gliedert sich in große Stammesherzogtümer. Kaiser Otto III. träumt von der Erneuerung des Römischen Reiches."),
  (1200,"Um 1200 — Stauferzeit","1200",None,VIEW_CEUROPE,
   "Unter den Staufern erreicht das Reich seine größte Ausdehnung; neue Mächte wie das Königreich Böhmen treten hervor."),
  (1356,"1356 — Goldene Bulle","1400","clio",VIEW_CEUROPE,
   "Karl IV. erlässt die Goldene Bulle: Sieben Kurfürsten wählen fortan den König. Das Reich ist ein Flickenteppich aus Hunderten Territorien — im Nordosten der Deutschordensstaat."),
  (1500,"Um 1500 — Reichsreform","1500","clio",VIEW_CEUROPE,
   "An der Schwelle zur Neuzeit: Reichsreform unter Maximilian I., Aufstieg der Habsburger, faktische Unabhängigkeit der Eidgenossenschaft."),
  (1648,"1648 — Westfälischer Friede","1650","clio",VIEW_CEUROPE,
   "Das Ende des Dreißigjährigen Krieges. Die Reichsstände werden faktisch souverän; Brandenburg-Preußen und Sachsen steigen auf."),
  (1700,"Um 1700 — Barock & Aufstieg Preußens","1700",None,VIEW_CEUROPE,
   "Im Zeitalter des Barock ringen Habsburg, Frankreich und das aufstrebende Brandenburg-Preußen um Vormacht in Mitteleuropa."),
  (1789,"1789 — Vor der Französischen Revolution","1783",None,VIEW_EUROPE,
   "Das Alte Reich am Vorabend der Französischen Revolution, die ganz Europa umstürzen wird."),
  (1815,"1815 — Deutscher Bund","1815",None,VIEW_CEUROPE,
   "Nach Napoleon ordnet der Wiener Kongress Mitteleuropa neu: 39 Staaten bilden den Deutschen Bund unter österreichischem Vorsitz, mit Preußen als Rivalen."),
  (1880,"Um 1880 — Deutsches Kaiserreich","1880",None,VIEW_CEUROPE,
   "1871 unter preußischer Führung gegründet (kleindeutsche Lösung); Österreich bleibt außen vor. Bismarck prägt die Politik."),
  (1914,"1914 — Erster Weltkrieg","1914",None,VIEW_EUROPE,
   "Das Kaiserreich auf dem Höhepunkt seiner Macht, verbündet mit Österreich-Ungarn. 1914 beginnt der Erste Weltkrieg."),
  (1920,"1920 — Weimarer Republik","1920",None,VIEW_CEUROPE,
   "Nach Niederlage und Revolution wird Deutschland Republik. Der Versailler Vertrag erzwingt große Gebietsverluste; neue Staaten wie Polen und die Tschechoslowakei entstehen."),
  (1938,"1938 — NS-Staat","1938",None,VIEW_EUROPE,
   "Unter der NS-Diktatur gliedert das Deutsche Reich Österreich („Anschluss“) und das Sudetenland an — aggressive Expansion vor dem Zweiten Weltkrieg."),
  (1945,"1945 — Kriegsende & Besatzung","1945",None,VIEW_CEUROPE,
   "Nach der totalen Niederlage wird Deutschland von den Siegermächten besetzt und verliert die Gebiete östlich von Oder und Neiße."),
  (1960,"1960 — Geteiltes Deutschland","1960",None,VIEW_CEUROPE,
   "Im Kalten Krieg ist Deutschland geteilt: die Bundesrepublik im Westen, die DDR im Osten; 1961 wird die Berliner Mauer errichtet."),
  (2000,"Heute — Bundesrepublik Deutschland","2000","laender",VIEW_CEUROPE,
   "Das wiedervereinigte Deutschland besteht aus 16 Bundesländern und ist in EU und NATO eingebunden. Tippe ein Bundesland an."),
]

EPS = 0.02  # Vereinfachung (~2 km)


def write(path, obj):
    full = os.path.join(DATA, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(full)


def load_clio():
    if not os.path.exists(CLIO_LOCAL):
        print("  downloading Cliopatria (~44 MB) …")
        raw = urllib.request.urlopen(CLIO_URL, timeout=180).read()
        z = zipfile.ZipFile(io.BytesIO(raw))
        os.makedirs(os.path.dirname(CLIO_LOCAL), exist_ok=True)
        z.extract(os.path.basename(CLIO_LOCAL), os.path.dirname(CLIO_LOCAL))
    print("  loading Cliopatria …")
    return json.load(open(CLIO_LOCAL))


def load_laender():
    """Bundesländer-Polygone (public domain, deutschlandGeoJSON) als
    Liste (factionId, Polygon-Liste, Fläche)."""
    if not os.path.exists(BL_LOCAL):
        print("  downloading Bundesländer …")
        data = urllib.request.urlopen(BL_URL, timeout=120).read()
        with open(BL_LOCAL, "wb") as fh:
            fh.write(data)
    gj = json.load(open(BL_LOCAL))
    out = []
    for f in gj["features"]:
        fid = LAENDER_ID.get(f["properties"].get("name"))
        if not fid:
            continue
        geom = process_geometry(f["geometry"], CLIP_DE, EPS)
        if not geom:
            continue
        area = sum(shoelace(poly[0]) for poly in geom)
        out.append((fid, geom, area))
    return out


def clio_features_for(clio, year, clip=CLIP_DE, auto=False, skip=None):
    skip = skip or set()
    feats = []
    for f in clio["features"]:
        p = f["properties"]
        if p.get("Type") != "POLITY":
            continue
        nm = p.get("Name", "")
        if nm.startswith("(") or nm in skip:
            continue
        fy, ty = p.get("FromYear"), p.get("ToYear")
        if fy is None or ty is None or not (fy <= year <= ty):
            continue
        geom = process_geometry(f.get("geometry"), clip, EPS)
        if not geom:
            continue
        fid = NAME_MAP.get(nm)
        if fid is None:
            if not auto:
                continue  # Unkartierte (meist ferne) Polities überspringen
            fid = hb_faction(nm)  # europaweit: automatische Fraktion erzeugen
        # Jede Fraktion mit Wikipedia-Link und Bestandszeitraum anreichern,
        # damit jedes Gebiet beim Antippen Details zeigt.
        fac = FACTIONS[fid]
        w = p.get("Wikipedia")
        if w and not fac.get("wiki"):
            fac["wiki"] = w
        fy0, ty0 = p.get("FromYear"), p.get("ToYear")
        if fy0 is not None:
            fac["from"] = fy0 if fac.get("from") is None else min(fac["from"], fy0)
        if ty0 is not None:
            fac["to"] = ty0 if fac.get("to") is None else max(fac["to"], ty0)
        area = sum(shoelace(poly[0]) for poly in geom)
        feats.append((fid, nm, geom, area))
    return feats


def to_feature(fid, geom_polys):
    fac = FACTIONS[fid]
    coords = geom_polys
    gtype = "MultiPolygon" if len(coords) != 1 else "Polygon"
    geometry = {"type": "MultiPolygon", "coordinates": coords} if gtype == "MultiPolygon" \
        else {"type": "Polygon", "coordinates": coords[0]}
    props = {"factionId": fid, "name": fac["name"], "color": fac["color"]}
    if fac.get("foreign"):
        props["foreign"] = True
    return {"type": "Feature", "properties": props, "geometry": geometry}


# ---------------------------------------------------------------------------
# historical-basemaps (GPL): europaweite Hauptquelle für alle Epochen.
# Namen werden auf bestehende (kuratierte) Fraktionen abgebildet; alles
# Übrige bekommt automatisch eine Fraktion mit stabiler Farbe.
# ---------------------------------------------------------------------------
WARM = ["#8a6d3b","#6e7d4a","#9c5a52","#7c8456","#94794e","#5f7a5a","#8c6d4a",
        "#a8724a","#7a5230","#8a7b5a","#6e6240","#9a7a3b","#b06a4e","#7c6a4a"]
COOL = ["#8a98a8","#9aa48a","#a89a78","#7a98a0","#9a8a8a","#a094a8","#9aa090",
        "#8a9aa0","#a0a890","#9a9a92","#aab0b8","#9a8a6a","#a89888","#8a9a9a"]

# HB-Name -> deutsche Anzeige (für automatisch erzeugte Fraktionen).
DE_NAMES = {
  "England":"England","Kingdom of England":"England","Scotland":"Schottland",
  "Ireland":"Irland","Great Britain":"Großbritannien","United Kingdom":"Vereinigtes Königreich",
  "Wales":"Wales","Portugal":"Portugal","Kingdom of Portugal":"Portugal",
  "Spain":"Spanien","Castile":"Kastilien","Aragon":"Aragón","Granada":"Granada",
  "Papal States":"Kirchenstaat","Naples":"Neapel","Kingdom of Naples":"Königreich Neapel",
  "Sicily":"Sizilien","Kingdom of Sicily":"Königreich Sizilien","Tuscany":"Toskana",
  "Florence":"Florenz","Byzantine Empire":"Byzantinisches Reich","Eastern Roman Empire":"Oströmisches Reich",
  "Bulgaria":"Bulgarien","Serbia":"Serbien","Bosnia":"Bosnien","Wallachia":"Walachei",
  "Moldavia":"Moldau","Greece":"Griechenland","Kievan Rus":"Kiewer Rus","Kievan Rus'":"Kiewer Rus",
  "Novgorod":"Nowgorod","Lithuania":"Litauen","Grand Duchy of Lithuania":"Großfürstentum Litauen",
  "Ukraine":"Ukraine","Belarus":"Belarus","Finland":"Finnland","Norway":"Norwegen",
  "Kingdom of Norway":"Norwegen","Iceland":"Island","Hanover":"Hannover","Hannover":"Hannover",
  "Brunswick":"Braunschweig","Mecklenburg":"Mecklenburg","Mecklenburg-Schwerin":"Mecklenburg-Schwerin",
  "Mecklenburg-Strelitz":"Mecklenburg-Strelitz","Oldenburg":"Oldenburg","Nassau":"Nassau",
  "Holstein":"Holstein","Schleswig":"Schleswig","Thuringia":"Thüringen","Anhalt":"Anhalt",
  "Lippe-Detmold":"Lippe-Detmold","Schaumburg-Lippe":"Schaumburg-Lippe","Waldeck":"Waldeck",
  "Electoral Hesse":"Kurhessen","Grand Duchy of Hesse":"Großherzogtum Hessen","Hesse":"Hessen",
  "Hohenzollern":"Hohenzollern","Bremen":"Bremen","Hamburg":"Hamburg","Lübeck":"Lübeck",
  "Frankfurt":"Frankfurt","Vandals":"Vandalen","Lombards":"Langobarden","Huns":"Hunnen",
  "Avars":"Awaren","Gepids":"Gepiden","Suebi":"Sueben","Visigoths":"Westgoten",
  "Magyars":"Magyaren","Crimean Khanate":"Krim-Khanat","Golden Horde":"Goldene Horde",
  "Croatia":"Kroatien","Czechoslovakia":"Tschechoslowakei","Yugoslavia":"Jugoslawien",
  "Czech Republic":"Tschechien","Czechia":"Tschechien","Slovakia":"Slowakei","Slovenia":"Slowenien","Austria":"Österreich","Turkey":"Türkei","Russia":"Russland","Spain":"Spanien",
  "Romania":"Rumänien","Estonia":"Estland","Latvia":"Lettland","Free City of Danzig":"Freie Stadt Danzig",
  "Marcomanni":"Markomannen","Cherusci":"Cherusker","Celts":"Kelten","Gauls":"Gallier",
  "Franche-Comté":"Freigrafschaft Burgund","Cuxhaven":"Cuxhaven","Wetzlar":"Wetzlar",
}

# Als „deutsche Lande“ (warm, hervorgehoben) behandelte HB-Namen.
GERMAN_SET = {
  "Holy Roman Empire","Prussia","Kingdom of Prussia","Bavaria","Kingdom of Bavaria",
  "Duchy of Bavaria","Saxony","Kingdom of Saxony","Electorate of Saxony","Baden",
  "Grand Duchy of Baden","Württemberg","Kingdom of Württemberg","Hanover","Hannover",
  "Brunswick","Mecklenburg","Mecklenburg-Schwerin","Mecklenburg-Strelitz","Oldenburg",
  "Nassau","Holstein","Schleswig","Thuringia","Anhalt","Lippe-Detmold","Schaumburg-Lippe",
  "Waldeck","Electoral Hesse","Grand Duchy of Hesse","Hesse","Hohenzollern","Bremen",
  "Hamburg","Lübeck","Frankfurt","Palatinate","Brandenburg","Electorate of Brandenburg",
  "Mainz","Cologne","Trier","Teutonic Order","German Empire","German Confederation",
  "Weimar Republic","Nazi Germany","West Germany","East Germany","Germany",
  "Federal Republic of Germany","German Democratic Republic","Cuxhaven","Wetzlar",
  "Franks","Saxons","Alamans","Alemanni","Burgunds","Burgundians","Ostrogoths",
  "Turingians","Thuringians","Suebi","Marcomanni","Cherusci","Lombards",
}

SKIP_NAMES = {"", "?", "Arctic marine mammal hunters"}

# Zusätzliche Namen, die durch die europaweite Cliopatria-Abdeckung auftauchen.
DE_NAMES.update({
  "East Franks":"Ostfrankenreich","West Franks":"Westfrankenreich",
  "Middle Francia":"Mittelfränkisches Reich","Kingdom of Germany":"Königreich Deutschland",
  "Frankish Kingdom":"Fränkisches Reich","Carolingian Empire":"Karolingerreich",
  "Mongol Empire":"Mongolisches Reich","Golden Horde":"Goldene Horde","Blue Horde":"Blaue Horde",
  "Spanish Empire":"Spanisches Reich","Tsardom of Russia":"Zarentum Russland",
  "Abbasid Caliphate":"Abbasiden-Kalifat","Great Seljuk Empire":"Seldschukenreich",
  "First Bulgarian Empire":"Bulgarisches Reich","Second Bulgarian Empire":"Bulgarisches Reich",
  "Novgorod Republic":"Republik Nowgorod","Crown of Castile":"Krone Kastilien",
  "Crown of Aragon":"Krone Aragón","Portuguese Empire":"Portugiesisches Reich",
  "Mamluk Sultanate":"Mamluken-Sultanat","Nicaean Empire":"Kaiserreich Nikaia",
  "House of Oldenburg":"Haus Oldenburg","House of Jagiellon":"Haus Jagiellonen",
  "House of Habsburg":"Haus Habsburg","House of Savoy":"Haus Savoyen",
  "Scandinavian minor kingdoms":"Skandinavische Kleinreiche","Khazaria":"Chasaren",
})
GERMAN_SET.update({"East Franks", "Kingdom of Germany", "Frankish Kingdom", "Carolingian Empire"})

# HB-Name -> bestehende (kuratierte) Fraktions-ID.
HB_MAP = {
  "Holy Roman Empire":"hre",
  "Kingdom of Bohemia":"boehmen","Bohemia":"boehmen","Duchy of Bohemia":"boehmen",
  "Prussia":"preussen","Kingdom of Prussia":"preussen",
  "Bavaria":"bayern_kgr","Kingdom of Bavaria":"bayern_kgr","Duchy of Bavaria":"bayern",
  "Saxony":"sachsen_kur","Electorate of Saxony":"sachsen_kur","Kingdom of Saxony":"sachsen_kur",
  "Baden":"baden","Grand Duchy of Baden":"baden",
  "Württemberg":"wuerttemberg_kgr","Kingdom of Württemberg":"wuerttemberg_kgr",
  "Austrian Empire":"oesterreich_kaisertum","Austria-Hungary":"oesterreich_ungarn",
  "Austria":"oesterreich_rep","Habsburg Monarchy":"habsburg",
  "German Empire":"deutsches_reich","German Confederation":"deutscher_bund",
  "Nazi Germany":"ns_reich","Weimar Republic":"deutsches_reich",
  "West Germany":"brd","Federal Republic of Germany":"brd",
  "East Germany":"ddr","German Democratic Republic":"ddr",
  "Teutonic Order":"deutschorden","Palatinate":"pfalz","Brandenburg":"brandenburg",
  "Electorate of Brandenburg":"brandenburg","Mainz":"mainz","Cologne":"koeln","Trier":"trier",
  "Franks":"franken_v","Saxons":"sachsen_v","Alamans":"alemannen_v","Alemanni":"alemannen_v",
  "Burgunds":"burgunden","Burgundians":"burgunden","Ostrogoths":"ostgoten",
  "Turingians":"thueringer_v","Thuringians":"thueringer_v",
  "Roman Empire":"roemer","Roman Republic":"roemer","Western Roman Empire":"weibrom",
  "France":"frankreich","Kingdom of France":"frankreich",
  "Kingdom of Hungary":"ungarn","Hungary":"ungarn",
  "Kingdom of Poland":"polen","Poland":"polen","Poland-Lithuania":"polen_litauen",
  "Polish-Lithuanian Commonwealth":"polen_litauen",
  "Denmark":"daenemark","Denmark-Norway":"daenemark","Kingdom of Denmark":"daenemark",
  "Sweden":"schweden","Kingdom of Sweden":"schweden","Swedish Empire":"schweden",
  "Kalmar Union":"kalmar","Ottoman Empire":"osmanen",
  "Venice":"venedig","Republic of Venice":"venedig","Genoa":"genua","Republic of Genoa":"genua",
  "Milan":"mailand","Duchy of Milan":"mailand","Dutch Republic":"niederlande",
  "Netherlands":"niederlande","United Provinces":"niederlande",
  "Switzerland":"eidgenossenschaft","Swiss Confederation":"eidgenossenschaft",
  "Russia":"russland","Russian Empire":"russland","Soviet Union":"sowjetunion","USSR":"sowjetunion",
  "Spain":"spanien","Kingdom of Spain":"spanien","Italy":"italien","Kingdom of Italy":"italien",
  "Lorraine":"lothringen_hzm","Duchy of Lorraine":"lothringen_hzm",
  "Savoy":"savoyen","Duchy of Savoy":"savoyen","County of Savoy":"savoyen",
  "Franche-Comté":"burgund_frei","Luxembourg":"luxemburg_staat",
  "Kingdom of Croatia":"kroatien","Belgium":"belgien","Kingdom of Belgium":"belgien",
}


def _slug(name):
    s = name.lower().replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "x"


def hb_faction(name):
    fid = HB_MAP.get(name)
    if fid:
        return fid
    fid = "hb_" + _slug(name)
    if fid not in FACTIONS:
        german = name in GERMAN_SET
        pal = WARM if german else COOL
        col = pal[zlib.crc32(name.encode("utf-8")) % len(pal)]
        # "en" = englischer Quellname für einen Wikipedia-Fallback-Link.
        FACTIONS[fid] = {"name": DE_NAMES.get(name, name), "color": col,
                         "foreign": (not german), "en": name}
    return fid


def load_ne(url, fname):
    path = os.path.join(NE_DIR, fname)
    if not os.path.exists(path):
        print(f"  downloading {fname} (Natural Earth) …")
        os.makedirs(NE_DIR, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(urllib.request.urlopen(url, timeout=180).read())
    return json.load(open(path))


def build_geo():
    print("  building Europe land base (Natural Earth 50m) …")
    for url, cache, out, eps in [(NE_LAND_URL, "land.json", "geo/land.geojson", 0.05),
                                 (NE_LAKES_URL, "lakes.json", "geo/lakes.geojson", 0.05)]:
        gj = load_ne(url, cache)
        feats = []
        for f in gj["features"]:
            g = process_geometry(f.get("geometry"), EUROPE_CLIP, eps)
            if not g:
                continue
            geom = ({"type": "MultiPolygon", "coordinates": g} if len(g) != 1
                    else {"type": "Polygon", "coordinates": g[0]})
            feats.append({"type": "Feature", "properties": {}, "geometry": geom})
        sz = write(out, {"type": "FeatureCollection", "features": feats})
        print(f"    {out}: {len(feats)} features ({sz} bytes)")


def load_hb(key):
    path = os.path.join(HB_DIR, f"world_{key}.geojson")
    if not os.path.exists(path):
        os.makedirs(HB_DIR, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(urllib.request.urlopen(HB_URL % key, timeout=180).read())
    return json.load(open(path))


def hb_features_for(hb, skip):
    out = []
    for f in hb["features"]:
        nm = (f["properties"].get("NAME") or "").strip()
        if nm in SKIP_NAMES or nm in skip:
            continue
        geom = process_geometry(f.get("geometry"), EUROPE_CLIP, EPS)
        if not geom:
            continue
        fid = hb_faction(nm)
        area = sum(shoelace(poly[0]) for poly in geom)
        out.append((fid, nm, geom, area))
    return out


def build():
    print("Building ChronoMap data v3 (Europe-wide, multi-source) …")
    build_geo()
    clio = load_clio()

    index = {"schemaVersion": 3, "title": "ChronoMap Deutschland",
             "yearRange": {"min": ERAS[0][0], "max": ERAS[-1][0]},
             "snapshots": []}

    for year, label, src, view, blurb in ERAS:
        byfac, order = {}, {}

        def add(fid, geom, area):
            byfac.setdefault(fid, []).extend(geom)
            order[fid] = max(order.get(fid, 0), area)

        if src.startswith("hb:"):
            for fid, nm, geom, area in hb_features_for(load_hb(src[3:]), set()):
                add(fid, geom, area)
        else:  # "clio" oder "clio+laender": kontinuierliche europaweite Quelle
            laender = src.endswith("+laender")
            # In der Gegenwart das gesamtdeutsche Polity weglassen (Bundesländer).
            skip = ({"Federated Republic of Germany", "Federal Republic of Germany",
                     "Germany", "German Democratic Republic"} if laender else None)
            for fid, nm, geom, area in clio_features_for(clio, year, EUROPE_CLIP,
                                                         auto=True, skip=skip):
                add(fid, geom, area)
            if laender:
                for fid, geom, area in load_laender():
                    add(fid, geom, area)

        # Große Flächen zuerst (z-Reihenfolge), kleine Detail-Territorien oben.
        fids_sorted = sorted(byfac.keys(), key=lambda k: order.get(k, 0), reverse=True)
        features = [to_feature(fid, byfac[fid]) for fid in fids_sorted]

        # Liste: deutsche Lande zuerst, dann Nachbarn (je nach Fläche).
        def sort_key(fid):
            return (1 if FACTIONS[fid].get("foreign") else 0, -order.get(fid, 0))
        faction_ids = sorted(byfac.keys(), key=sort_key)

        layers = {}
        if features:
            p = f"layers/territories/{year}.geojson"
            write(p, {"type": "FeatureCollection", "features": features})
            layers["territories"] = p
        if year in SETTLEMENTS:
            p = f"layers/settlements/{year}.json"
            write(p, {"schemaVersion": 1, "settlements": SETTLEMENTS[year]})
            layers["settlements"] = p
        if year in (1000, 1200, 1350, 1500):
            feats = [{"type": "Feature",
                      "properties": {k: z[k] for k in ("cultureId", "name", "color", "pattern", "note")},
                      "geometry": {"type": "Polygon", "coordinates": [z["ring"]]}} for z in LANG_ZONES]
            p = f"layers/cultures/{year}.geojson"
            write(p, {"type": "FeatureCollection", "features": feats})
            layers["cultures"] = p

        write(f"eras/{year}.json", {"schemaVersion": 3, "year": year, "label": label,
              "blurb": blurb, "view": {"bounds": view, "minZoom": 3, "maxZoom": 9},
              "layers": layers, "factionIds": faction_ids})
        index["snapshots"].append({"year": year, "file": f"eras/{year}.json", "label": label})
        print(f"  era {year:>5} [{src:>13}]: {len(features):>3} territories, "
              f"{len(faction_ids):>3} factions")

    sz = write("factions/factions.json", {"schemaVersion": 3, "factions": FACTIONS})
    write("eras/index.json", index)
    print(f"  factions.json: {len(FACTIONS)} factions ({sz} bytes)")
    print("Done.")


if __name__ == "__main__":
    build()
