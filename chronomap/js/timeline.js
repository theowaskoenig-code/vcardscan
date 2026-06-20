// Verbindet den durchgehenden Jahres-Schieberegler mit den definierten
// Snapshots: jedes Jahr wird auf den NÄCHSTGELEGENEN Snapshot abgebildet.
import { T } from "./i18n.js";

export class Timeline {
  // snapshots: [{year, file, label}], onChange(entry) wird gerufen, wenn
  // sich der aufgelöste Snapshot ändert.
  constructor(index, els, onChange) {
    this.snapshots = index.snapshots.slice().sort((a, b) => a.year - b.year);
    this.onChange = onChange;
    this.slider = els.slider;
    this.yearOut = els.yearOut;
    this.labelOut = els.labelOut;
    this.ticks = els.ticks;
    this.currentYear = null;

    const { min, max } = index.yearRange;
    this.slider.min = String(min);
    this.slider.max = String(max);
    this.slider.step = "1";

    this.renderTicks(min, max);
    this.slider.addEventListener("input", () => this.handleInput());
  }

  renderTicks(min, max) {
    if (!this.ticks) return;
    const span = Math.max(1, max - min);
    this.ticks.innerHTML = "";
    for (const s of this.snapshots) {
      const tick = document.createElement("button");
      tick.type = "button";
      tick.className = "tl-tick";
      tick.style.left = ((s.year - min) / span) * 100 + "%";
      tick.title = s.label;
      tick.addEventListener("click", () => this.setYear(s.year, true));
      this.ticks.appendChild(tick);
    }
  }

  nearest(year) {
    let best = this.snapshots[0];
    let bestDist = Infinity;
    for (const s of this.snapshots) {
      const d = Math.abs(s.year - year);
      if (d < bestDist) { bestDist = d; best = s; }
    }
    return best;
  }

  handleInput() {
    const year = parseInt(this.slider.value, 10);
    this.updateYear(year);
  }

  // Schieber programmatisch setzen (z. B. Klick auf eine Markierung).
  setYear(year, snapThumb) {
    if (snapThumb) this.slider.value = String(year);
    this.updateYear(year);
  }

  updateYear(year) {
    this.yearOut.textContent = T.yearLabel(year);
    const entry = this.nearest(year);
    this.labelOut.textContent = entry.label;
    if (this.currentYear === entry.year) return; // gleicher Snapshot – nichts neu zeichnen
    this.currentYear = entry.year;
    this.onChange(entry);
  }

  start(year) {
    const y = (typeof year === "number") ? year : this.snapshots[0].year;
    this.slider.value = String(y);
    this.updateYear(y);
  }
}
