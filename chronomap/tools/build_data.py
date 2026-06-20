#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChronoMap Deutschland — Daten-Autorenwerkzeug (one-off authoring helper).

Dies ist KEINE Laufzeit-Abhängigkeit. Es erzeugt die statischen JSON/GeoJSON-
Dateien unter chronomap/data/ aus von Hand recherchierten Angaben. Einmal
ausführen, Ergebnis wird committet; die App lädt nur die fertigen Dateien.

Quellenlage: Grenzverläufe sind bewusst vereinfacht ("Zonen", keine exakten
Linien). Sachangaben (Herrscherhäuser, Kurfürsten, Städte) nach gängiger
Geschichtsliteratur (u. a. Goldene Bulle 1356). Geometrie ist Eigenarbeit,
grob an realer Geographie ausgerichtet, ausdrücklich näherungsweise.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))


def w(path, obj):
    full = os.path.join(DATA, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  wrote {path} ({os.path.getsize(full)} bytes)")


# ---------------------------------------------------------------------------
# Polygon-Bibliothek (Koordinaten [lon, lat], stark vereinfacht).
# ---------------------------------------------------------------------------
P = {
    # Stammesherzogtümer (um 1000) -------------------------------------------
    "sachsen_stamm": [[6.8,51.3],[6.6,52.5],[7.5,53.6],[9.5,54.0],[11.5,53.9],
                      [12.3,52.8],[11.8,51.5],[10.0,51.0],[8.0,51.0],[6.8,51.3]],
    "bayern_stamm":  [[10.9,47.4],[10.9,49.0],[12.5,49.2],[14.5,48.9],[16.5,48.5],
                      [15.5,46.7],[12.5,47.0],[11.0,47.0],[10.9,47.4]],
    "schwaben_stamm":[[7.4,47.0],[7.3,48.6],[9.0,48.9],[10.8,48.7],[10.8,47.4],
                      [9.5,47.2],[8.0,46.9],[7.4,47.0]],
    "franken_stamm": [[8.4,49.0],[8.3,50.4],[9.5,50.6],[11.5,50.3],[12.0,49.4],
                      [10.8,48.9],[9.3,48.9],[8.4,49.0]],
    "lothringen_stamm":[[4.5,47.8],[4.3,49.5],[5.0,50.9],[6.5,51.2],[7.2,50.0],
                        [7.0,48.5],[6.0,47.7],[4.5,47.8]],

    # Kernregionen (mittelalterlich) -----------------------------------------
    "boehmen": [[12.1,50.3],[13.0,51.05],[14.4,51.05],[15.3,50.7],[16.6,50.6],
                [18.6,49.6],[17.2,48.6],[15.1,48.7],[13.5,48.9],[12.4,49.3],[12.1,50.3]],
    "bayern":  [[10.9,48.0],[10.9,48.9],[11.8,49.3],[12.9,49.2],[13.8,48.6],
                [13.4,47.7],[12.2,47.4],[11.0,47.5],[10.9,48.0]],
    "oesterreich":[[13.0,47.5],[13.0,48.3],[14.5,48.8],[16.5,48.7],[17.0,48.0],
                   [16.0,46.7],[14.0,46.7],[13.1,47.0],[13.0,47.5]],
    "brandenburg":[[11.6,52.0],[11.7,53.0],[12.6,53.4],[14.2,53.3],[14.6,52.6],
                   [14.0,51.8],[12.8,51.7],[11.6,52.0]],
    "sachsen_wittenberg":[[12.0,51.7],[12.2,52.1],[13.0,52.1],[13.4,51.7],
                          [13.0,51.4],[12.2,51.45],[12.0,51.7]],
    "pfalz":[[7.7,49.1],[7.7,49.7],[8.4,49.9],[9.1,49.7],[9.0,49.1],[8.3,48.95],[7.7,49.1]],
    "mainz":[[7.9,49.9],[7.9,50.4],[8.6,50.6],[9.6,50.3],[9.4,49.8],[8.5,49.75],[7.9,49.9]],
    "koeln":[[6.1,50.7],[6.0,51.3],[6.6,51.6],[7.4,51.4],[7.5,50.8],[6.9,50.55],[6.1,50.7]],
    "trier":[[6.3,49.7],[6.4,50.3],[7.1,50.5],[7.8,50.1],[7.5,49.6],[6.8,49.5],[6.3,49.7]],
    "wuerttemberg":[[8.7,48.5],[8.7,49.1],[9.3,49.2],[10.0,48.9],[9.8,48.4],[9.0,48.35],[8.7,48.5]],
    "hessen":[[8.5,50.6],[8.4,51.1],[9.0,51.4],[9.8,51.2],[9.7,50.5],[9.0,50.35],[8.5,50.6]],
    "thueringen":[[10.0,50.6],[9.9,51.3],[11.0,51.5],[12.2,51.2],[12.0,50.5],[11.0,50.4],[10.0,50.6]],
    "braunschweig_lueneburg":[[9.6,52.2],[9.6,53.0],[10.4,53.4],[11.4,53.2],[11.6,52.3],
                              [10.7,51.75],[9.7,51.9],[9.6,52.2]],
    "eidgenossenschaft":[[7.5,47.0],[7.5,47.6],[8.4,47.7],[9.4,47.4],[9.0,46.8],[8.0,46.75],[7.5,47.0]],
    "zaehringen":[[7.3,47.4],[7.2,48.3],[8.2,48.5],[9.0,48.0],[8.7,47.3],[7.9,47.1],[7.3,47.4]],
    # Sachsen unter den Welfen / Askaniern (um 1200, kleiner als Stammesherzogtum)
    "sachsen_welf":[[9.5,51.6],[9.4,52.6],[10.6,53.2],[11.8,52.8],[11.6,51.7],
                    [10.6,51.3],[9.5,51.6]],
    # Habsburgische Erblande um 1500 (Österreich + Tirol grob)
    "habsburg_1500":[[10.4,46.6],[10.5,47.6],[12.0,48.1],[13.0,48.4],[14.5,48.8],
                     [16.6,48.7],[17.0,47.8],[15.8,46.6],[12.5,46.6],[10.4,46.6]],
    # Sachsen unter den Wettinern um 1500 (Thüringen + Meißen grob)
    "sachsen_wettin":[[10.2,50.5],[10.0,51.5],[11.5,51.6],[13.4,51.5],[13.2,50.6],
                      [12.0,50.3],[10.8,50.4],[10.2,50.5]],
}


def feat(fid, name, ring, **extra):
    props = {"factionId": fid, "name": name}
    props.update(extra)
    return {"type": "Feature", "properties": props,
            "geometry": {"type": "Polygon", "coordinates": [ring]}}


def fc(features):
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# Fraktionen (Stammdaten + epochenspezifische Ergänzungen)
# ---------------------------------------------------------------------------
FACTIONS = {
  "hre": {
    "name": "Heiliges Römisches Reich", "color": "#6b4f2a", "rank": "empire",
    "origin": "Aus dem Ostfränkischen Reich hervorgegangen; Kaiserkrönung Ottos I. 962.",
    "rulingHouse": "Wahlmonarchie (wechselnde Dynastien)",
    "religion": "Römisch-katholisch", "capital": "keine feste Hauptstadt",
    "eras": {
      "1000": {"rulingHouse": "Liudolfinger (Ottonen)", "capital": "Pfalzen u. a. Aachen, Magdeburg",
               "keyFacts": ["Kaiser Otto III. strebt eine „Erneuerung des Römischen Reiches“ an.",
                            "Herrschaft über die Stammesherzogtümer Sachsen, Bayern, Schwaben, Franken, Lothringen."]},
      "1200": {"rulingHouse": "Staufer", "capital": "Reisekönigtum (u. a. Hagenau, Goslar)",
               "keyFacts": ["Höhepunkt der Stauferzeit; Thronstreit nach 1198 zwischen Staufern und Welfen.",
                            "Reich reicht von der Nordsee bis nach Mittelitalien."]},
      "1356": {"rulingHouse": "Haus Luxemburg (Karl IV.)", "capital": "Prag als Residenz Karls IV.",
               "keyFacts": ["Die Goldene Bulle von 1356 regelt die Königswahl durch sieben Kurfürsten.",
                            "Drei geistliche (Mainz, Köln, Trier) und vier weltliche Kurfürsten (Böhmen, Pfalz, Sachsen-Wittenberg, Brandenburg).",
                            "Das Reich ist als Wahlmonarchie ohne feste Hauptstadt gefestigt."]},
      "1500": {"rulingHouse": "Haus Habsburg (Maximilian I.)", "capital": "Wien/Innsbruck als habsburgische Zentren",
               "keyFacts": ["Reichsreform: Ewiger Landfriede (1495) und Einrichtung des Reichskammergerichts.",
                            "Einteilung in Reichskreise; das Reich heißt nun „Heiliges Römisches Reich Deutscher Nation“."]},
    },
  },
  # Stammesherzogtümer ------------------------------------------------------
  "sachsen": {"name":"Herzogtum Sachsen","color":"#7d6b4a","rank":"duchy",
    "origin":"Altes sächsisches Stammesgebiet, nach 804 ins Frankenreich eingegliedert.",
    "rulingHouse":"wechselnd","religion":"Römisch-katholisch","capital":None,
    "eras":{"1000":{"rulingHouse":"Billunger (Herzöge); Königshaus der Ottonen entstammt Sachsen",
                    "keyFacts":["Kernland der ottonischen Königsdynastie.","Reicht von Rhein/Westfalen bis zur Elbe."]},
            "1200":{"rulingHouse":"Askanier (seit 1180)","capital":"u. a. Lauenburg/Wittenberg",
                    "keyFacts":["1180 nach dem Sturz Heinrichs des Löwen stark verkleinert.","Aufteilung der welfischen Macht."]}}},
  "bayern": {"name":"Herzogtum Bayern","color":"#5f7a5a","rank":"duchy",
    "origin":"Bajuwarisches Stammesherzogtum, seit dem Frühmittelalter bestehend.",
    "rulingHouse":"Haus Wittelsbach (seit 1180)","religion":"Römisch-katholisch","capital":"München",
    "eras":{"1000":{"rulingHouse":"wechselnde Herzöge, eng an die Ottonen gebunden",
                    "keyFacts":["Umfasst auch die Marken im Südosten (spätere Ostmark/Österreich)."]},
            "1200":{"rulingHouse":"Haus Wittelsbach","capital":"Landshut/München",
                    "keyFacts":["Seit 1180 unter den Wittelsbachern, die Bayern bis 1918 regieren."]},
            "1356":{"rulingHouse":"Haus Wittelsbach","capital":"München/Landshut",
                    "keyFacts":["Mehrfach geteilt; die Wittelsbacher halten zeitweise auch Brandenburg und die Pfalz."]},
            "1500":{"rulingHouse":"Haus Wittelsbach","capital":"München",
                    "keyFacts":["Nach dem Landshuter Erbfolgekrieg (1504/05) weitgehend wiedervereinigt.","Primogenitur sichert künftig die Einheit des Herzogtums."]}}},
  "schwaben": {"name":"Herzogtum Schwaben","color":"#8a8d62","rank":"duchy",
    "origin":"Alemannisches Stammesherzogtum am Oberrhein und an der oberen Donau.",
    "rulingHouse":"Staufer (ab 1079)","religion":"Römisch-katholisch","capital":None,
    "eras":{"1000":{"keyFacts":["Stammesherzogtum zwischen Rhein, Alpen und Lech."]},
            "1200":{"rulingHouse":"Staufer","keyFacts":["Hausmacht der staufischen Kaiser."]}}},
  "franken": {"name":"Herzogtum Franken","color":"#9c7b4f","rank":"duchy",
    "origin":"Ostfränkisches Kernland am Main.","rulingHouse":"wechselnd",
    "religion":"Römisch-katholisch","capital":None,
    "eras":{"1000":{"keyFacts":["Mainfränkisches Gebiet mit den Bischofssitzen Würzburg und Bamberg."]}}},
  "lothringen": {"name":"Herzogtum Lothringen","color":"#7a6e8c","rank":"duchy",
    "origin":"Aus dem Mittelreich Lothars hervorgegangen, 925 zum Ostreich.",
    "rulingHouse":"wechselnd","religion":"Römisch-katholisch","capital":None,
    "eras":{"1000":{"keyFacts":["Grenzland zum Westfrankenreich, oft in Ober- und Niederlothringen geteilt."]}}},
  "boehmen": {"name":"Königreich Böhmen","color":"#7a5230","rank":"kingdom",
    "origin":"Slawisches Herzogtum, ab 1198 erbliches Königreich im Reichsverband.",
    "rulingHouse":"Haus Luxemburg","religion":"Römisch-katholisch","capital":"Prag",
    "eras":{"1000":{"rulingHouse":"Přemysliden","capital":"Prag","rank":"duchy",
                    "keyFacts":["Herzogtum der Přemysliden, dem Reich locker verbunden."]},
            "1200":{"rulingHouse":"Přemysliden","keyFacts":["1198 zum erblichen Königreich erhoben (Ottokar I.)."]},
            "1356":{"rulingHouse":"Haus Luxemburg (Karl IV.)","capital":"Prag",
                    "keyFacts":["Kurstimme als eines der sieben Kurfürstentümer bestätigt.","Wirtschaftliches und kulturelles Zentrum des Reiches unter Karl IV.","Universität Prag 1348 gegründet."]},
            "1500":{"rulingHouse":"Jagiellonen","capital":"Prag",
                    "keyFacts":["Seit 1471 unter den Jagiellonen, in Personalunion mit Ungarn."]}}},
  "oesterreich": {"name":"Herzogtum Österreich","color":"#a8554a","rank":"duchy",
    "origin":"845 erstmals als „Ostarrîchi“ erwähnt; 1156 zum eigenen Herzogtum erhoben.",
    "rulingHouse":"Haus Habsburg","religion":"Römisch-katholisch","capital":"Wien",
    "eras":{"1200":{"rulingHouse":"Babenberger","keyFacts":["1156 durch das Privilegium Minus zum Herzogtum erhoben."]},
            "1356":{"rulingHouse":"Haus Habsburg","capital":"Wien",
                    "keyFacts":["Habsburgisch seit 1278; mit dem (gefälschten) Privilegium Maius beanspruchen die Habsburger Sonderrechte.","Nicht unter den sieben Kurfürsten der Goldenen Bulle."]}}},
  "habsburg": {"name":"Habsburgische Erblande","color":"#a8554a","rank":"archduchy",
    "origin":"Hausmacht der Habsburger um Österreich, Steiermark und Tirol.",
    "rulingHouse":"Haus Habsburg","religion":"Römisch-katholisch","capital":"Wien/Innsbruck",
    "eras":{"1500":{"rulingHouse":"Haus Habsburg (Maximilian I.)",
                    "keyFacts":["Maximilian I. ist römisch-deutscher König und Erzherzog von Österreich.","Durch die Heiratspolitik (Burgund, Spanien) entsteht die habsburgische Großmacht.","„Bella gerant alii, tu felix Austria nube.“"]}}},
  "thueringen": {"name":"Landgrafschaft Thüringen","color":"#8c6d4a","rank":"landgraviate",
    "origin":"Landgrafschaft im mitteldeutschen Raum.","rulingHouse":"Ludowinger",
    "religion":"Römisch-katholisch","capital":"u. a. Eisenach (Wartburg)",
    "eras":{"1200":{"keyFacts":["Blütezeit unter den Ludowingern; Sängerkrieg auf der Wartburg (Sage)."]}}},
  "zaehringen": {"name":"Herzogtum der Zähringer","color":"#6e8a8d","rank":"duchy",
    "origin":"Mächtiges Adelsgeschlecht im Südwesten, Städtegründer (u. a. Freiburg, Bern).",
    "rulingHouse":"Zähringer","religion":"Römisch-katholisch","capital":None,
    "eras":{"1200":{"keyFacts":["Gründen zahlreiche Städte; sterben 1218 im Mannesstamm aus."]}}},
  # Kurfürstentümer 1356 ----------------------------------------------------
  "mainz": {"name":"Kurmainz (Erzbistum Mainz)","color":"#9c5a52","rank":"electorate",
    "origin":"Erzbistum seit dem 8. Jh.; der Erzbischof ist Erzkanzler für Deutschland.",
    "rulingHouse":"geistliches Fürstentum (Erzbischof)","religion":"Römisch-katholisch","capital":"Mainz",
    "eras":{"1356":{"keyFacts":["Geistlicher Kurfürst; der Mainzer Erzbischof leitet als Erzkanzler die Königswahl.","Erste Stimme im Kurkolleg."]}}},
  "koeln": {"name":"Kurköln (Erzbistum Köln)","color":"#7d4a44","rank":"electorate",
    "origin":"Erzbistum seit der Spätantike; einer der reichsten Kirchenfürsten.",
    "rulingHouse":"geistliches Fürstentum (Erzbischof)","religion":"Römisch-katholisch","capital":"Köln (Residenz Bonn)",
    "eras":{"1356":{"keyFacts":["Geistlicher Kurfürst und Erzkanzler für Italien.","Die Stadt Köln selbst ist faktisch Freie Reichsstadt."]}}},
  "trier": {"name":"Kurtrier (Erzbistum Trier)","color":"#b06a4e","rank":"electorate",
    "origin":"Ältestes Bistum nördlich der Alpen.","rulingHouse":"geistliches Fürstentum (Erzbischof)",
    "religion":"Römisch-katholisch","capital":"Trier (später Koblenz)",
    "eras":{"1356":{"keyFacts":["Geistlicher Kurfürst und Erzkanzler für Burgund.","Territorium entlang der Mosel."]}}},
  "pfalz": {"name":"Kurpfalz (Pfalzgrafschaft bei Rhein)","color":"#8c5a3c","rank":"electorate",
    "origin":"Pfalzgrafschaft am Rhein, seit 1214 wittelsbachisch.","rulingHouse":"Haus Wittelsbach",
    "religion":"Römisch-katholisch","capital":"Heidelberg",
    "eras":{"1356":{"keyFacts":["Weltlicher Kurfürst; der Pfalzgraf ist Reichsvikar.","Wittelsbachische Linie mit Residenz Heidelberg."]}}},
  "sachsen_wittenberg": {"name":"Kursachsen (Sachsen-Wittenberg)","color":"#8a6d3b","rank":"electorate",
    "origin":"Askanisches Teilherzogtum an der Elbe.","rulingHouse":"Askanier",
    "religion":"Römisch-katholisch","capital":"Wittenberg",
    "eras":{"1356":{"keyFacts":["Die Goldene Bulle weist die sächsische Kurstimme Sachsen-Wittenberg zu (nicht Sachsen-Lauenburg).","Weltlicher Kurfürst, Erzmarschall des Reiches."]}}},
  "wuerttemberg": {"name":"Grafschaft Württemberg","color":"#6e6240","rank":"county",
    "origin":"Schwäbisches Grafengeschlecht, von Stuttgart aus expandierend.",
    "rulingHouse":"Haus Württemberg","religion":"Römisch-katholisch","capital":"Stuttgart",
    "eras":{"1356":{"keyFacts":["Aufstrebende Grafschaft im ehemaligen Herzogtum Schwaben."]},
            "1500":{"rank":"duchy","keyFacts":["1495 von König Maximilian I. zum Herzogtum erhoben."]}}},
  "hessen": {"name":"Landgrafschaft Hessen","color":"#7c8456","rank":"landgraviate",
    "origin":"1264 aus dem thüringischen Erbe als eigene Landgrafschaft entstanden.",
    "rulingHouse":"Haus Hessen (Brabanter Linie)","religion":"Römisch-katholisch","capital":"Kassel/Marburg",
    "eras":{"1356":{"keyFacts":["Eigenständige Landgrafschaft zwischen Rhein, Main und Weser."]}}},
  "braunschweig_lueneburg": {"name":"Herzogtum Braunschweig-Lüneburg","color":"#94794e","rank":"duchy",
    "origin":"Welfischer Restbesitz nach dem Sturz Heinrichs des Löwen, 1235 Reichsherzogtum.",
    "rulingHouse":"Welfen","religion":"Römisch-katholisch","capital":"Braunschweig/Lüneburg",
    "eras":{"1356":{"keyFacts":["Welfisches Herzogtum, vielfach unter den Linien geteilt."]}}},
  "brandenburg": {"name":"Markgrafschaft Brandenburg","color":"#9a7b4f","rank":"electorate",
    "origin":"1157 von Albrecht dem Bären gegründet (Eroberung der Mark).","rulingHouse":"Haus Wittelsbach (um 1356)",
    "religion":"Römisch-katholisch","capital":"Brandenburg/Tangermünde",
    "eras":{"1200":{"rulingHouse":"Askanier","rank":"margraviate","keyFacts":["Unter den Askaniern im Zuge der Ostsiedlung ausgebaut."]},
            "1356":{"rulingHouse":"Haus Wittelsbach","keyFacts":["Inhaber der brandenburgischen Kurstimme (Erzkämmerer).","1373 an die Luxemburger übergegangen."]},
            "1500":{"rulingHouse":"Haus Hohenzollern (seit 1415)","keyFacts":["Seit 1415 unter den Hohenzollern, die das Land bis 1918 regieren."]}}},
  "eidgenossenschaft": {"name":"Alte Eidgenossenschaft","color":"#8a8d92","rank":"confederation",
    "origin":"1291 als Bund der Waldstätte entstanden, im Reichsverband.","rulingHouse":"Bund autonomer Orte",
    "religion":"Römisch-katholisch","capital":None,
    "eras":{"1356":{"keyFacts":["Um 1353 zum „Bund der acht Orte“ angewachsen (u. a. Zürich, Luzern, Bern).","Formal Teil des Reiches, faktisch zunehmend eigenständig."]},
            "1500":{"keyFacts":["Nach dem Schwabenkrieg 1499 faktisch vom Reich unabhängig.","Im Frieden von Basel von der Reichsgerichtsbarkeit gelöst."]}}},
  "sachsen_wettin": {"name":"Kursachsen (Wettiner)","color":"#8a6d3b","rank":"electorate",
    "origin":"Die Wettiner erben 1423 das sächsische Kurfürstentum.","rulingHouse":"Haus Wettin",
    "religion":"Römisch-katholisch","capital":"Wittenberg/Dresden",
    "eras":{"1500":{"keyFacts":["1485 Leipziger Teilung in eine ernestinische (Kur) und albertinische Linie.","Bald darauf Ausgangspunkt der Reformation (Wittenberg)."]}}},
}


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------
BOUNDS_FULL = [[46.0, 4.5], [55.0, 18.5]]

SNAPSHOTS = [
  {"year":1000,"label":"Um 1000 — Ottonisches Reich",
   "blurb":"Das ottonische Reich gliedert sich in die großen Stammesherzogtümer. Kaiser Otto III. träumt von der Erneuerung des Römischen Reiches.",
   "bounds":BOUNDS_FULL,
   "territories":[
       feat("sachsen","Herzogtum Sachsen",P["sachsen_stamm"]),
       feat("franken","Herzogtum Franken",P["franken_stamm"]),
       feat("bayern","Herzogtum Bayern",P["bayern_stamm"]),
       feat("schwaben","Herzogtum Schwaben",P["schwaben_stamm"]),
       feat("lothringen","Herzogtum Lothringen",P["lothringen_stamm"]),
       feat("boehmen","Herzogtum Böhmen",P["boehmen"]),
   ],
   "factionIds":["hre","sachsen","franken","bayern","schwaben","lothringen","boehmen"],
   "settlements":[
       {"id":"aachen","name":"Aachen","lat":50.78,"lon":6.08,"kind":"residenz","importance":3,"factionId":"lothringen"},
       {"id":"magdeburg","name":"Magdeburg","lat":52.13,"lon":11.63,"kind":"bischofssitz","importance":3,"factionId":"sachsen"},
       {"id":"regensburg","name":"Regensburg","lat":49.02,"lon":12.10,"kind":"residenz","importance":2,"factionId":"bayern"},
       {"id":"mainz","name":"Mainz","lat":50.00,"lon":8.27,"kind":"bischofssitz","importance":2,"factionId":"franken"},
       {"id":"prag","name":"Prag","lat":50.09,"lon":14.42,"kind":"residenz","importance":2,"factionId":"boehmen"},
   ],
   "cultures":[]},

  {"year":1200,"label":"Um 1200 — Stauferzeit",
   "blurb":"Unter den Staufern erreicht das Reich seine größte Ausdehnung. Nach 1180 zerfällt die welfische Macht; neue Territorien wie Österreich und Böhmen treten hervor.",
   "bounds":BOUNDS_FULL,
   "territories":[
       feat("sachsen","Herzogtum Sachsen",P["sachsen_welf"]),
       feat("brandenburg","Markgrafschaft Brandenburg",P["brandenburg"]),
       feat("thueringen","Landgrafschaft Thüringen",P["thueringen"]),
       feat("franken","Herzogtum Franken",P["franken_stamm"]),
       feat("schwaben","Herzogtum Schwaben (Staufer)",P["schwaben_stamm"]),
       feat("zaehringen","Zähringer",P["zaehringen"]),
       feat("bayern","Herzogtum Bayern",P["bayern"]),
       feat("oesterreich","Herzogtum Österreich",P["oesterreich"]),
       feat("boehmen","Königreich Böhmen",P["boehmen"]),
   ],
   "factionIds":["hre","sachsen","brandenburg","thueringen","franken","schwaben","zaehringen","bayern","oesterreich","boehmen"],
   "settlements":[
       {"id":"goslar","name":"Goslar","lat":51.91,"lon":10.43,"kind":"residenz","importance":2,"factionId":"sachsen"},
       {"id":"nuernberg","name":"Nürnberg","lat":49.45,"lon":11.08,"kind":"reichsstadt","importance":2,"factionId":"hre"},
       {"id":"wien","name":"Wien","lat":48.21,"lon":16.37,"kind":"residenz","importance":2,"factionId":"oesterreich"},
       {"id":"prag","name":"Prag","lat":50.09,"lon":14.42,"kind":"residenz","importance":3,"factionId":"boehmen"},
       {"id":"koeln","name":"Köln","lat":50.94,"lon":6.96,"kind":"stadt","importance":3,"factionId":"hre"},
   ],
   "cultures":[]},

  {"year":1356,"label":"Goldene Bulle (1356)",
   "blurb":"Karl IV. erlässt die Goldene Bulle: Sieben Kurfürsten — drei geistliche und vier weltliche — wählen fortan den römisch-deutschen König. Das Reich ist ein Flickenteppich aus Hunderten Territorien.",
   "bounds":[[46.2,5.0],[55.0,18.7]],
   "territories":[
       feat("mainz","Kurmainz",P["mainz"]),
       feat("koeln","Kurköln",P["koeln"]),
       feat("trier","Kurtrier",P["trier"]),
       feat("pfalz","Kurpfalz",P["pfalz"]),
       feat("sachsen_wittenberg","Kursachsen (Wittenberg)",P["sachsen_wittenberg"]),
       feat("brandenburg","Mark Brandenburg",P["brandenburg"]),
       feat("boehmen","Königreich Böhmen",P["boehmen"]),
       feat("bayern","Herzogtum Bayern",P["bayern"]),
       feat("oesterreich","Herzogtum Österreich",P["oesterreich"]),
       feat("wuerttemberg","Grafschaft Württemberg",P["wuerttemberg"]),
       feat("hessen","Landgrafschaft Hessen",P["hessen"]),
       feat("braunschweig_lueneburg","Braunschweig-Lüneburg",P["braunschweig_lueneburg"]),
       feat("eidgenossenschaft","Eidgenossenschaft",P["eidgenossenschaft"]),
   ],
   "factionIds":["hre","mainz","koeln","trier","boehmen","pfalz","sachsen_wittenberg","brandenburg",
                 "bayern","oesterreich","wuerttemberg","hessen","braunschweig_lueneburg","eidgenossenschaft"],
   "settlements":[
       {"id":"prag","name":"Prag","lat":50.09,"lon":14.42,"kind":"residenz","importance":3,"factionId":"boehmen"},
       {"id":"frankfurt","name":"Frankfurt am Main","lat":50.11,"lon":8.68,"kind":"reichsstadt","importance":3,"factionId":"hre"},
       {"id":"nuernberg","name":"Nürnberg","lat":49.45,"lon":11.08,"kind":"reichsstadt","importance":3,"factionId":"hre"},
       {"id":"koeln","name":"Köln","lat":50.94,"lon":6.96,"kind":"reichsstadt","importance":3,"factionId":"hre"},
       {"id":"luebeck","name":"Lübeck","lat":53.87,"lon":10.69,"kind":"hansestadt","importance":3,"factionId":"hre"},
       {"id":"wien","name":"Wien","lat":48.21,"lon":16.37,"kind":"residenz","importance":3,"factionId":"oesterreich"},
       {"id":"muenchen","name":"München","lat":48.14,"lon":11.58,"kind":"residenz","importance":2,"factionId":"bayern"},
       {"id":"hamburg","name":"Hamburg","lat":53.55,"lon":9.99,"kind":"hansestadt","importance":2,"factionId":"hre"},
       {"id":"mainz","name":"Mainz","lat":50.00,"lon":8.27,"kind":"bischofssitz","importance":2,"factionId":"mainz"},
       {"id":"trier","name":"Trier","lat":49.76,"lon":6.64,"kind":"bischofssitz","importance":2,"factionId":"trier"},
       {"id":"augsburg","name":"Augsburg","lat":48.37,"lon":10.90,"kind":"reichsstadt","importance":2,"factionId":"hre"},
       {"id":"strassburg","name":"Straßburg","lat":48.58,"lon":7.75,"kind":"reichsstadt","importance":2,"factionId":"hre"},
       {"id":"heidelberg","name":"Heidelberg","lat":49.40,"lon":8.69,"kind":"residenz","importance":2,"factionId":"pfalz"},
       {"id":"wittenberg","name":"Wittenberg","lat":51.87,"lon":12.65,"kind":"residenz","importance":1,"factionId":"sachsen_wittenberg"},
       {"id":"zuerich","name":"Zürich","lat":47.37,"lon":8.54,"kind":"stadt","importance":2,"factionId":"eidgenossenschaft"},
       {"id":"stuttgart","name":"Stuttgart","lat":48.78,"lon":9.18,"kind":"residenz","importance":1,"factionId":"wuerttemberg"},
   ],
   "cultures":[
       {"type":"Feature","properties":{"cultureId":"niederdeutsch","name":"Niederdeutsche Mundarten","color":"#5a6b7a","pattern":"hatch","note":"Sprachgrenzen fließend, kein scharfer Verlauf."},
        "geometry":{"type":"Polygon","coordinates":[[[6.5,51.4],[6.5,53.6],[9.5,54.0],[12.5,54.3],[14.2,53.6],[13.5,51.8],[11.0,51.5],[8.0,51.3],[6.5,51.4]]]}},
       {"type":"Feature","properties":{"cultureId":"hochdeutsch","name":"Hochdeutsche Mundarten","color":"#8a6b3a","pattern":"hatch","note":"Ober- und mitteldeutsches Sprachgebiet."},
        "geometry":{"type":"Polygon","coordinates":[[[6.0,47.0],[6.0,51.4],[9.0,51.4],[12.0,51.6],[15.5,51.0],[17.0,48.5],[13.0,46.6],[9.0,46.7],[6.5,46.9],[6.0,47.0]]]}},
       {"type":"Feature","properties":{"cultureId":"sorbisch","name":"Sorbisch/Wendisches Gebiet","color":"#6a8a5a","pattern":"hatch","note":"Westslawische Restbevölkerung in der Lausitz."},
        "geometry":{"type":"Polygon","coordinates":[[[13.4,50.9],[13.3,51.9],[14.0,52.0],[14.8,51.4],[14.5,50.9],[13.4,50.9]]]}},
   ]},

  {"year":1500,"label":"Um 1500 — Reichsreform",
   "blurb":"An der Schwelle zur Neuzeit: Maximilian I. und die Reichsreform (Ewiger Landfriede 1495, Reichskreise). Die Habsburger steigen zur Großmacht auf, die Eidgenossenschaft löst sich faktisch vom Reich.",
   "bounds":BOUNDS_FULL,
   "territories":[
       feat("habsburg","Habsburgische Erblande",P["habsburg_1500"]),
       feat("bayern","Herzogtum Bayern",P["bayern"]),
       feat("sachsen_wettin","Kursachsen (Wettiner)",P["sachsen_wettin"]),
       feat("brandenburg","Kurbrandenburg (Hohenzollern)",P["brandenburg"]),
       feat("boehmen","Königreich Böhmen",P["boehmen"]),
       feat("pfalz","Kurpfalz",P["pfalz"]),
       feat("mainz","Kurmainz",P["mainz"]),
       feat("koeln","Kurköln",P["koeln"]),
       feat("trier","Kurtrier",P["trier"]),
       feat("wuerttemberg","Herzogtum Württemberg",P["wuerttemberg"]),
       feat("hessen","Landgrafschaft Hessen",P["hessen"]),
       feat("eidgenossenschaft","Eidgenossenschaft",P["eidgenossenschaft"]),
   ],
   "factionIds":["hre","habsburg","boehmen","brandenburg","sachsen_wettin","pfalz","mainz","koeln","trier",
                 "bayern","wuerttemberg","hessen","eidgenossenschaft"],
   "settlements":[
       {"id":"wien","name":"Wien","lat":48.21,"lon":16.37,"kind":"residenz","importance":3,"factionId":"habsburg"},
       {"id":"innsbruck","name":"Innsbruck","lat":47.27,"lon":11.39,"kind":"residenz","importance":2,"factionId":"habsburg"},
       {"id":"augsburg","name":"Augsburg","lat":48.37,"lon":10.90,"kind":"reichsstadt","importance":3,"factionId":"hre"},
       {"id":"nuernberg","name":"Nürnberg","lat":49.45,"lon":11.08,"kind":"reichsstadt","importance":3,"factionId":"hre"},
       {"id":"koeln","name":"Köln","lat":50.94,"lon":6.96,"kind":"reichsstadt","importance":3,"factionId":"hre"},
       {"id":"prag","name":"Prag","lat":50.09,"lon":14.42,"kind":"residenz","importance":2,"factionId":"boehmen"},
       {"id":"wittenberg","name":"Wittenberg","lat":51.87,"lon":12.65,"kind":"residenz","importance":2,"factionId":"sachsen_wettin"},
       {"id":"luebeck","name":"Lübeck","lat":53.87,"lon":10.69,"kind":"hansestadt","importance":2,"factionId":"hre"},
   ],
   "cultures":[]},
]


def build():
    print("Building ChronoMap data ...")
    # factions
    w("factions/factions.json", {"schemaVersion": 1, "factions": FACTIONS})

    # eras index
    index = {"schemaVersion": 1, "title": "ChronoMap Deutschland",
             "yearRange": {"min": SNAPSHOTS[0]["year"], "max": SNAPSHOTS[-1]["year"]},
             "snapshots": []}
    for s in SNAPSHOTS:
        y = s["year"]
        index["snapshots"].append({"year": y, "file": f"eras/{y}.json", "label": s["label"]})

        layers = {}
        if s["territories"]:
            p = f"layers/territories/{y}.geojson"; w(p, fc(s["territories"])); layers["territories"] = p
        if s.get("cultures"):
            p = f"layers/cultures/{y}.geojson"; w(p, fc(s["cultures"])); layers["cultures"] = p
        if s.get("settlements"):
            p = f"layers/settlements/{y}.json"
            w(p, {"schemaVersion": 1, "settlements": s["settlements"]}); layers["settlements"] = p

        w(f"eras/{y}.json", {"schemaVersion": 1, "year": y, "label": s["label"],
                             "blurb": s["blurb"],
                             "view": {"bounds": s["bounds"], "minZoom": 5, "maxZoom": 9},
                             "layers": layers, "factionIds": s["factionIds"]})

    w("eras/index.json", index)
    print("Done.")


if __name__ == "__main__":
    build()
