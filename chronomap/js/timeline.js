// Schieberegler über die definierten Epochen. Da die Epochen sehr ungleich
// über die Zeit verteilt sind (von 100 v. Chr. bis heute), arbeitet der Regler
// index-basiert: jede Epoche bekommt gleich viel Platz und ist gut anwählbar.
import { T } from "./i18n.js";

export class Timeline {
  // snapshots: [{year, file, label}], onChange(entry) bei Epochenwechsel.
  constructor(index, els, onChange) {
    this.snapshots = index.snapshots.slice().sort((a, b) => a.year - b.year);
    this.onChange = onChange;
    this.slider = els.slider;
    this.yearOut = els.yearOut;
    this.labelOut = els.labelOut;
    this.ticks = els.ticks;
    this.idx = -1;
    this.tickEls = [];

    this.slider.min = "0";
    this.slider.max = String(this.snapshots.length - 1);
    this.slider.step = "1";

    this.renderTicks();
    this.slider.addEventListener("input", () =>
      this.updateIndex(parseInt(this.slider.value, 10)));
  }

  renderTicks() {
    if (!this.ticks) return;
    const n = this.snapshots.length;
    this.ticks.innerHTML = "";
    this.tickEls = this.snapshots.map((s, i) => {
      const tick = document.createElement("button");
      tick.type = "button";
      tick.className = "tl-tick";
      tick.style.left = (n <= 1 ? 0 : (i / (n - 1)) * 100) + "%";
      tick.title = s.label;
      tick.addEventListener("click", () => this.setIndex(i));
      this.ticks.appendChild(tick);
      return tick;
    });
  }

  setIndex(i) {
    this.slider.value = String(i);
    this.updateIndex(i);
  }

  updateIndex(i) {
    const s = this.snapshots[i];
    if (!s) return;
    this.yearOut.textContent = T.yearLabel(s.year);
    this.labelOut.textContent = s.label;
    this.tickEls.forEach((t, k) => t.classList.toggle("is-active", k === i));
    if (this.idx === i) return; // gleicher Snapshot – nichts neu zeichnen
    this.idx = i;
    this.onChange(s);
  }

  nearestIndex(year) {
    let best = 0, bestDist = Infinity;
    this.snapshots.forEach((s, i) => {
      const d = Math.abs(s.year - year);
      if (d < bestDist) { bestDist = d; best = i; }
    });
    return best;
  }

  // Öffentliche API: nach Jahr starten/springen (auf nächste Epoche gerundet).
  start(year) {
    this.setIndex(typeof year === "number" ? this.nearestIndex(year) : 0);
  }

  setYear(year) {
    this.setIndex(this.nearestIndex(year));
  }
}
