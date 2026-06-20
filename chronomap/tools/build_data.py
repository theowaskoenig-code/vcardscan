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
import json, os, math, urllib.request, zipfile, io

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
CLIO_LOCAL = "/tmp/clio_out/cliopatria_polities_only.geojson"
CLIO_URL = "https://raw.githubusercontent.com/Seshat-Global-History-Databank/cliopatria/main/cliopatria.geojson.zip"

# Anzeige-/Clip-Fenster (Mitteleuropa).
CLIP = (-1.0, 43.0, 23.0, 57.5)   # minx,miny,maxx,maxy
VIEW_MED = [[46.0, 4.0], [56.0, 19.5]]
VIEW_ANCIENT = [[43.5, 2.0], [56.0, 20.0]]
VIEW_MODERN = [[46.5, 4.0], [56.0, 21.0]]


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
  "eidgenossenschaft": F("Alte Eidgenossenschaft", "#8a8d92", "confederation",
    origin="1291 als Bund der Waldstätte entstanden.",
    house="Bund autonomer Orte", capital=None,
    eras={
      "1356": {"keyFacts": ["Um 1353 zum „Bund der acht Orte“ gewachsen (u. a. Zürich, Luzern, Bern).",
                            "Formal Teil des Reiches, faktisch zunehmend eigenständig."]},
      "1500": {"keyFacts": ["Nach dem Schwabenkrieg 1499 faktisch vom Reich unabhängig.",
                            "Im Frieden von Basel von der Reichsgerichtsbarkeit gelöst."]},
      "1648": {"foreign": True, "keyFacts": ["Im Westfälischen Frieden 1648 formell aus dem Reichsverband entlassen."]},
    }),
  "deutschorden": F("Deutschordensstaat", "#9aa0a8", "theocracy",
    origin="Ordensstaat des Deutschen Ordens an der Ostsee (ab 1226).",
    house="Deutscher Orden (Hochmeister)", capital="Marienburg",
    eras={"1356": {"foreign": True, "keyFacts": ["Kreuzritterstaat in Preußen und im Baltikum.",
                                                 "Wirtschaftlich über die Hanse mit dem Reich verbunden."]}}),

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
                                "Österreich bleibt außerhalb (kleindeutsche Lösung)."]}}),

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
}

# Zusätzliche (meist ausländische) Fraktionen, knapp gehalten.
FOREIGN = {
  "frankreich": ("Königreich Frankreich", "#8a98a8"),
  "frankreich_rep": ("Französische Republik", "#8a98a8"),
  "polen": ("Königreich Polen", "#9aa48a"),
  "polen_litauen": ("Polen-Litauen", "#9aa48a"),
  "schlesien": ("Schlesische Herzogtümer", "#9a8a6a"),
  "ungarn": ("Königreich Ungarn", "#a89a78"),
  "daenemark": ("Königreich Dänemark", "#7a98a0"),
  "kalmar": ("Kalmarer Union", "#7a98a0"),
  "schweden": ("Schwedisches Reich", "#8aa0a8"),
  "schweden_norwegen": ("Schweden-Norwegen", "#8aa0a8"),
  "norwegen": ("Königreich Norwegen", "#8aa0a8"),
  "osmanen": ("Osmanisches Reich", "#a88a7a"),
  "venedig": ("Republik Venedig", "#a094a8"),
  "genua": ("Republik Genua", "#a094a8"),
  "mailand": ("Herzogtum Mailand", "#a094a8"),
  "italien": ("Königreich Italien", "#a094a8"),
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
  "spanien": ("Königreich Spanien", "#a89888"),
  "russland": ("Russisches Reich", "#9aa0a8"),
  "oesterreich_ungarn": ("Österreich-Ungarn", "#a8554a"),
  "luxemburg": ("Haus Luxemburg", "#b59a5a"),
}
for fid, (nm, col) in FOREIGN.items():
    if fid not in FACTIONS:
        FACTIONS[fid] = F(nm, col, foreign=(fid not in ("luxemburg",)))


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
  1356:[C("prag","Prag",50.09,14.42,"residenz",3,"boehmen"),
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
  1648:[C("wien","Wien",48.21,16.37,"residenz",3,"habsburg"),
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
  1871:[C("berlin","Berlin",52.52,13.40,"residenz",3,"deutsches_reich"),
        C("wien","Wien",48.21,16.37,"residenz",3,"oesterreich_ungarn"),
        C("muenchen","München",48.14,11.58,"residenz",2,"deutsches_reich"),
        C("hamburg","Hamburg",53.55,9.99,"hansestadt",3,"deutsches_reich"),
        C("koeln","Köln",50.94,6.96,"stadt",2,"deutsches_reich"),
        C("frankfurt","Frankfurt am Main",50.11,8.68,"stadt",2,"deutsches_reich"),
        C("leipzig","Leipzig",51.34,12.37,"stadt",2,"deutsches_reich"),
        C("dresden","Dresden",51.05,13.74,"residenz",2,"deutsches_reich")],
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

# Epochen-Definitionen.
ERAS = [
  (-100,"Um 100 v. Chr. — Kelten & Germanen", "ancient",
   "Vor der römischen Expansion: keltische Stämme der La-Tène-Kultur im Süden und Westen, germanische Stämme im Norden. Die Boier geben Böhmen seinen Namen.", VIEW_ANCIENT),
  (100,"Um 100 n. Chr. — Römisches Reich & Limes", "ancient",
   "Rom sichert die Grenze entlang von Rhein und Donau (Limes). Westlich und südlich liegen die Provinzen mit Städten wie Köln und Trier; östlich beginnt das freie Germanien.", VIEW_ANCIENT),
  (500,"Um 500 — Völkerwanderung", "ancient",
   "Nach dem Untergang Westroms entstehen germanische Reiche: die Franken unter Chlodwig, dazu Sachsen, Thüringer, Alemannen, Burgunden und das Ostgotenreich Theoderichs.", VIEW_ANCIENT),
  (1000,"Um 1000 — Ottonisches Reich", "clio",
   "Das ottonische Reich gliedert sich in die großen Stammesherzogtümer. Kaiser Otto III. träumt von der Erneuerung des Römischen Reiches.", VIEW_MED),
  (1200,"Um 1200 — Stauferzeit", "clio",
   "Unter den Staufern erreicht das Reich seine größte Ausdehnung. Neue Mächte wie das Königreich Böhmen treten hervor.", VIEW_MED),
  (1356,"Goldene Bulle (1356)", "clio",
   "Karl IV. erlässt die Goldene Bulle: Sieben Kurfürsten wählen fortan den König. Das Reich ist ein Flickenteppich aus Hunderten Territorien.", VIEW_MED),
  (1500,"Um 1500 — Reichsreform", "clio",
   "An der Schwelle zur Neuzeit: Reichsreform unter Maximilian I., Aufstieg der Habsburger, faktische Unabhängigkeit der Eidgenossenschaft.", VIEW_MED),
  (1648,"1648 — Westfälischer Friede", "clio",
   "Das Ende des Dreißigjährigen Krieges. Die Reichsstände werden faktisch souverän; Brandenburg-Preußen und das wettinische Sachsen steigen auf.", VIEW_MED),
  (1815,"1815 — Deutscher Bund", "clio",
   "Nach Napoleon ordnet der Wiener Kongress Mitteleuropa neu: 39 Staaten bilden den Deutschen Bund unter österreichischem Vorsitz, mit Preußen als Rivalen.", VIEW_MODERN),
  (1871,"1871 — Deutsches Kaiserreich", "clio",
   "Reichsgründung unter preußischer Führung (kleindeutsche Lösung). Österreich bleibt außen vor; Bismarck wird Reichskanzler.", VIEW_MODERN),
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


def clio_features_for(clio, year):
    feats = []
    for f in clio["features"]:
        p = f["properties"]
        if p.get("Type") != "POLITY":
            continue
        nm = p.get("Name", "")
        if nm.startswith("("):
            continue
        fy, ty = p.get("FromYear"), p.get("ToYear")
        if fy is None or ty is None or not (fy <= year <= ty):
            continue
        geom = process_geometry(f.get("geometry"), CLIP, EPS)
        if not geom:
            continue
        fid = NAME_MAP.get(nm)
        if fid is None:
            continue  # Unkartierte (meist ferne) Polities überspringen
        feats.append((fid, nm, geom, p.get("Area", 0)))
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


def build():
    print("Building ChronoMap data v2 …")
    clio = load_clio()

    index = {"schemaVersion": 2, "title": "ChronoMap Deutschland",
             "yearRange": {"min": ERAS[0][0], "max": ERAS[-1][0]},
             "snapshots": []}
    used_factions = set()

    for year, label, src, blurb, view in ERAS:
        # Territorien sammeln (fid -> Liste von Polygonen)
        byfac = {}
        order = {}  # fid -> Sortierfläche
        if src == "clio":
            for fid, nm, geom, area in clio_features_for(clio, year):
                byfac.setdefault(fid, []).extend(geom)
                order[fid] = max(order.get(fid, 0), area)
        else:  # ancient
            for fid, ring in ANCIENT[year]:
                g = process_geometry({"type": "Polygon", "coordinates": [ring]}, CLIP, EPS)
                if g:
                    byfac.setdefault(fid, []).extend(g)
                    order[fid] = max(order.get(fid, 0), shoelace(simplify_ring(clip_ring(ring, CLIP), EPS)))

        # Features in Reihenfolge große -> kleine Fläche (z-Reihenfolge)
        fids_sorted = sorted(byfac.keys(), key=lambda k: order.get(k, 0), reverse=True)
        features = [to_feature(fid, byfac[fid]) for fid in fids_sorted]
        used_factions.update(byfac.keys())

        # factionIds für die Liste: deutsche Lande zuerst, dann Nachbarn,
        # jeweils nach Fläche absteigend.
        def sort_key(fid):
            foreign = 1 if FACTIONS[fid].get("foreign") else 0
            return (foreign, -order.get(fid, 0))
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

        if src == "clio" and year in (1000, 1200, 1356, 1500):
            feats = [{"type": "Feature",
                      "properties": {k: z[k] for k in ("cultureId", "name", "color", "pattern", "note")},
                      "geometry": {"type": "Polygon", "coordinates": [z["ring"]]}} for z in LANG_ZONES]
            p = f"layers/cultures/{year}.geojson"
            write(p, {"type": "FeatureCollection", "features": feats})
            layers["cultures"] = p

        write(f"eras/{year}.json", {"schemaVersion": 2, "year": year, "label": label,
              "blurb": blurb, "view": {"bounds": view, "minZoom": 4, "maxZoom": 9},
              "layers": layers, "factionIds": faction_ids})
        index["snapshots"].append({"year": year, "file": f"eras/{year}.json", "label": label})
        print(f"  era {year}: {len(features)} territories, factions={len(faction_ids)}")

    # Alle Fraktionen ausgeben (auch solche, die nur von Städten referenziert
    # werden, z. B. Mainz/Kurpfalz, die in Cliopatria im „Minor States“-Block
    # aufgehen, aber als Stadt-Zuordnung gebraucht werden).
    sz = write("factions/factions.json", {"schemaVersion": 2, "factions": FACTIONS})
    _ = used_factions
    write("eras/index.json", index)
    print(f"  factions.json: {len(FACTIONS)} factions ({sz} bytes)")
    print("Done.")


if __name__ == "__main__":
    build()
