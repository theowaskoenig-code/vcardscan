// Fraktionsliste + Detailbereich. Auflösung der Anzeige-Infos:
// Basisdaten der Fraktion, überschrieben mit dem epochenspezifischen Block.
import { T } from "./i18n.js";
import { FALLBACK_COLOR } from "./config.js";

// Basis + eras[year] flach zusammenführen (era gewinnt).
export function resolveFaction(factions, fid, year) {
  const base = factions[fid] || { name: fid };
  const eraBlock = (base.eras && base.eras[String(year)]) || {};
  const merged = Object.assign({}, base, eraBlock);
  delete merged.eras;
  return merged;
}

export class FactionPanel {
  constructor(els, factions, onSelect) {
    this.listEl = els.list;
    this.infoEl = els.info;
    this.factions = factions;
    this.onSelect = onSelect;
    this.year = null;
    this.selectedId = null;
  }

  render(factionIds, year) {
    this.year = year;
    this.selectedId = null;
    this.listEl.innerHTML = "";
    this.clearInfo();

    for (const fid of factionIds) {
      const f = resolveFaction(this.factions, fid, year);
      const item = document.createElement("button");
      item.type = "button";
      item.className = "faction-item";
      item.dataset.fid = fid;

      const sw = document.createElement("span");
      sw.className = "swatch";
      sw.style.background = (this.factions[fid] && this.factions[fid].color) || FALLBACK_COLOR;

      const txt = document.createElement("span");
      txt.className = "faction-name";
      txt.textContent = f.name;

      const rank = f.rank ? (T.rank[f.rank] || "") : "";
      if (rank) {
        const r = document.createElement("span");
        r.className = "faction-rank";
        r.textContent = rank;
        txt.appendChild(r);
      }

      item.appendChild(sw);
      item.appendChild(txt);
      item.addEventListener("click", () => this.onSelect(fid));
      this.listEl.appendChild(item);
    }
  }

  // Auswahl optisch markieren + Detailbereich füllen.
  select(fid, hasTerritory) {
    this.selectedId = fid;
    for (const el of this.listEl.querySelectorAll(".faction-item")) {
      el.classList.toggle("active", el.dataset.fid === fid);
    }
    this.renderInfo(fid, hasTerritory);
  }

  renderInfo(fid, hasTerritory) {
    const f = resolveFaction(this.factions, fid, this.year);
    const rows = [];
    const addRow = (label, val) => {
      if (val == null || val === "") return;
      rows.push(`<div class="info-row"><dt>${label}</dt><dd>${val}</dd></div>`);
    };

    const hasRich = f.origin || (Array.isArray(f.keyFacts) && f.keyFacts.length)
      || f.rulingHouse || f.capital;
    const fmtYear = (y) => (y == null ? "?" : (y < 0 ? `${-y} v. Chr.` : `${y} n. Chr.`));

    addRow(T.field.rank, f.rank ? (T.rank[f.rank] || f.rank) : "");
    addRow(T.field.rulingHouse, f.rulingHouse);
    addRow(T.field.capital, f.capital);
    addRow(T.field.religion, f.religion);
    if (f.from != null || f.to != null) {
      addRow(T.field.span, `${fmtYear(f.from)} – ${fmtYear(f.to)}`);
    }
    // Jede Macht zeigt mindestens etwas: kuratierter Ursprung oder generischer Text.
    addRow(T.field.origin, f.origin || (hasRich ? "" : T.genericAbout));

    let facts = "";
    if (Array.isArray(f.keyFacts) && f.keyFacts.length) {
      facts = `<div class="info-facts"><h4>${T.field.keyFacts}</h4><ul>` +
        f.keyFacts.map((x) => `<li>${x}</li>`).join("") + "</ul></div>";
    }

    let wiki = "";
    const wikiTitle = f.wiki || f.en;
    if (wikiTitle) {
      const url = "https://en.wikipedia.org/wiki/" +
        encodeURIComponent(String(wikiTitle).replace(/ /g, "_"));
      wiki = `<p class="info-wiki"><a href="${url}" target="_blank" rel="noopener">${T.wikipedia} ↗</a></p>`;
    }

    const note = hasTerritory ? "" : `<p class="info-note">${T.noTerritory}</p>`;

    this.infoEl.innerHTML =
      `<div class="info-head">
         <h3>${f.name}</h3>
         <button type="button" class="info-close" aria-label="${T.close}">&times;</button>
       </div>
       ${note}
       <dl class="info-grid">${rows.join("")}</dl>
       ${facts}
       ${wiki}`;
    this.infoEl.classList.add("open");
    this.infoEl.querySelector(".info-close").addEventListener("click", () => this.onSelect(fid));
  }

  clearInfo() {
    this.selectedId = null;
    this.infoEl.classList.remove("open");
    this.infoEl.innerHTML = "";
    for (const el of this.listEl.querySelectorAll(".faction-item")) el.classList.remove("active");
  }
}
