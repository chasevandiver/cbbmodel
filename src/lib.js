// Shared formatting + betting helpers for the picks and results pages.

export const TZ = "America/Chicago";
export const VALUE_EDGE = 3;       // "value play" threshold, same as cbb_model.py / results_tracker.py
export const WIN_UNITS = 100 / 110; // profit on a 1-unit bet at -110
export const BREAK_EVEN = 52.4;     // win % needed at -110

const dayFmt = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" });
const timeFmt = new Intl.DateTimeFormat("en-US", { timeZone: TZ, hour: "numeric", minute: "2-digit" });

/** YYYY-MM-DD of the slate day a game belongs to (Central time). */
export function dayKey(dateStr) {
  return dayFmt.format(new Date(dateStr));
}

export function tipTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return Number.isNaN(d.getTime()) ? "" : `${timeFmt.format(d)} CT`;
}

/** "2026-11-10" -> "Tue, Nov 10" */
export function formatDay(key, opts = { weekday: "short", month: "short", day: "numeric" }) {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", opts);
}

// Barttorvik labels a season by the year it ends: Nov 2026 - Apr 2027 -> 2027.
export function seasonOf(dateStr) {
  const d = new Date(dateStr);
  return d.getUTCMonth() >= 9 ? d.getUTCFullYear() + 1 : d.getUTCFullYear();
}

export const seasonLabel = (s) => `${s - 1}-${String(s).slice(-2)}`;

export function num(n, digits = 1) {
  const s = Number(n).toFixed(digits);
  return digits > 0 ? s.replace(/\.0+$/, "") : s;
}

export function signed(n, digits = 1) {
  const v = Number(n);
  if (Math.abs(v) < 0.05) return "0";
  return `${v > 0 ? "+" : "−"}${num(Math.abs(v), digits)}`;
}

/** A point spread from one team's side: -3.5, +7, PK. */
export function line(n) {
  const v = Number(n);
  if (Math.abs(v) < 0.05) return "PK";
  return `${v > 0 ? "+" : "−"}${num(Math.abs(v))}`;
}

/** A home-perspective spread written from the favorite's side: "DUKE −5.5". */
export function favoriteLine(g, homeSpread) {
  const v = Number(homeSpread);
  if (Math.abs(v) < 0.05) return "Pick’em";
  return v < 0 ? `${g.home_abbr} ${line(v)}` : `${g.away_abbr} ${line(-v)}`;
}

export const teamName = (g, side) => g[`${side}_location`] || g[`${side}_team`];
export const isRanked = (r) => r != null && r <= 25;

/**
 * The bet the model implies, using the same rule as results_tracker.py:
 * predicted_spread is the projected home margin, market.spread is the home line.
 * Back the home side if the model beats the line by more than 0.5, the away
 * side if it trails by more than 0.5, otherwise there is no bet.
 */
export function betFor(g) {
  const raw = g.market?.spread;
  if (raw == null || raw === "") {
    const home = g.predicted_spread > 0;
    return { kind: "su", side: home ? "home" : "away", abbr: home ? g.home_abbr : g.away_abbr, label: `${home ? g.home_abbr : g.away_abbr} to win`, edge: null };
  }
  const mkt = parseFloat(raw);
  const diff = g.predicted_spread + mkt;
  const edge = Math.abs(diff);
  if (diff > 0.5) return { kind: "ats", side: "home", abbr: g.home_abbr, lineValue: mkt, label: `${g.home_abbr} ${line(mkt)}`, edge };
  if (diff < -0.5) return { kind: "ats", side: "away", abbr: g.away_abbr, lineValue: -mkt, label: `${g.away_abbr} ${line(-mkt)}`, edge };
  return { kind: "none", side: "none", abbr: null, label: "No bet", edge };
}

/** Model's lean on the total, or null when there is no market total. */
export function totalLean(g) {
  const ou = g.market?.over_under;
  if (ou == null || g.predicted_total == null) return null;
  const diff = g.predicted_total - parseFloat(ou);
  if (Math.abs(diff) < 0.05) return { call: null, diff: 0, ou: parseFloat(ou) };
  return { call: diff > 0 ? "Over" : "Under", diff, ou: parseFloat(ou) };
}

/** How far the line has moved since the pick was made, from the bet's point of view. */
export function lineMove(g, bet) {
  const open = g.market?.spread;
  const now = g.closing_line?.spread;
  if (open == null || now == null || bet.kind !== "ats") return null;
  const o = parseFloat(open);
  const c = parseFloat(now);
  // Positive = the number we took is now better than what the market offers.
  const value = bet.side === "home" ? o - c : c - o;
  return { current: c, value, capturedAt: g.closing_line.captured_at };
}

export function confTier(c) {
  return c >= 70 ? "high" : c >= 40 ? "medium" : "low";
}

export function record(games) {
  let w = 0, l = 0, p = 0;
  for (const g of games) {
    if (g.ats_result === "W") w++;
    else if (g.ats_result === "L") l++;
    else if (g.ats_result === "P") p++;
  }
  const n = w + l;
  return { w, l, p, n, pct: n ? Math.round((w / n) * 1000) / 10 : null, units: w * WIN_UNITS - l };
}

export const recordText = (r) => `${r.w}-${r.l}${r.p ? `-${r.p}` : ""}`;
export const pctText = (p) => (p == null ? "—" : `${num(p)}%`);
export const unitsText = (u) => `${signed(u, 1)}u`;
