// Pure scan logic (runs in the browser; also unit-tested in node).
function runScan(stocks, kind, o) {
  const days = (a, b) => Math.round((Date.parse(a) - Date.parse(b)) / 864e5);
  let latest = ""; for (const k in stocks) if (stocks[k].last_date > latest) latest = stocks[k].last_date;
  const rows = [];
  for (const sym in stocks) {
    const v = stocks[sym];
    if (days(latest, v.last_date) > 7) continue;               // suspended / stale
    if (kind === "listing") {
      const ever = o.basis === "high" ? v.ath : v.max_close;
      const pct = (v.listing - v.last) / v.listing * 100;
      if (ever <= v.listing && pct >= o.min && pct <= o.max) rows.push({ symbol: sym, ...v, pct });
    } else {
      const pct = (v.ath - v.last) / v.ath * 100, age = days(latest, v.ath_date);
      if (pct < o.min || pct > o.max) continue;
      if (o.excl && (v.last >= v.ath || age < 364)) continue;  // must be below an ATH set >=52 weeks ago
      rows.push({ symbol: sym, ...v, pct, ath_age_days: age });
    }
  }
  return rows.sort((a, b) => a.pct - b.pct);
}
if (typeof module !== "undefined") module.exports = { runScan };
