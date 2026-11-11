import { useEffect, useMemo, useRef, useState } from "react";
import { getConference } from "./conferences.js";
import { Logo } from "./Picks.jsx";
import {
  VALUE_EDGE, BREAK_EVEN, betFor, dayKey, formatDay, seasonOf, seasonLabel, teamName,
  num, signed, record, recordText, pctText, unitsText,
} from "./lib.js";

const PERIODS = [
  { key: "all", label: "Full season" },
  { key: "30", label: "Last 30 days" },
  { key: "7", label: "Last 7 days" },
  { key: "latest", label: "Latest day" },
];
const LOG_FILTERS = [
  { key: "all", label: "All", test: () => true },
  { key: "W", label: "Wins", test: (g) => g.ats_result === "W" },
  { key: "L", label: "Losses", test: (g) => g.ats_result === "L" },
  { key: "best", label: "Best bets", test: (g) => g.is_best_bet },
  { key: "value", label: `Edge ${VALUE_EDGE}+`, test: (g) => (g.value_rating || 0) >= VALUE_EDGE },
];
const PAGE = 60;

const shiftDay = (key, days) => {
  const [y, m, d] = key.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d - days));
  return dt.toISOString().slice(0, 10);
};

function betLine(g) {
  if (g.market?.spread == null) return null;
  const s = parseFloat(g.market.spread);
  return g.bet_side === "home" ? s : g.bet_side === "away" ? -s : null;
}

function Tile({ label, value, sub, tone }) {
  return (
    <div className="tile">
      <div className="tile-label">{label}</div>
      <div className={`tile-value${tone ? ` ${tone}` : ""}`}>{value}</div>
      <div className="tile-sub">{sub}</div>
    </div>
  );
}

function Split({ label, rec }) {
  const tone = rec.n < 10 || rec.pct == null ? "" : rec.pct >= BREAK_EVEN ? " good" : " bad";
  return (
    <div className="split">
      <span className="split-label">{label}</span>
      <span className="split-rec">{rec.n ? recordText(rec) : "—"}</span>
      <span className={`meter${tone}`} role="img" aria-label={rec.n ? `${rec.pct}% wins` : "no games"}>
        <i style={{ width: `${rec.pct || 0}%` }} />
      </span>
      <span className="split-pct">{pctText(rec.pct)}</span>
    </div>
  );
}

/** Cumulative units by slate day, with a crosshair tooltip. */
function UnitsChart({ days }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);
  const [hover, setHover] = useState(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const H = 230;
  const m = { l: 38, r: 56, t: 14, b: 26 };
  const iw = Math.max(width - m.l - m.r, 10);
  const ih = H - m.t - m.b;
  const vals = days.map((d) => d.cum);
  const lo = Math.min(0, ...vals);
  const hi = Math.max(0, ...vals);
  const span = hi - lo || 1;
  const step = [1, 2, 5, 10, 20, 50, 100].find((s) => span / s <= 5) || 200;
  const y0 = Math.floor(lo / step) * step;
  const y1 = Math.ceil(hi / step) * step || step;
  const ticks = [];
  for (let t = y0; t <= y1 + 1e-9; t += step) ticks.push(t);
  const x = (i) => m.l + (days.length === 1 ? iw / 2 : (i / (days.length - 1)) * iw);
  const y = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * ih;
  const path = days.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d.cum).toFixed(1)}`).join("");
  const area = `${path}L${x(days.length - 1).toFixed(1)},${y(0)}L${x(0).toFixed(1)},${y(0)}Z`;
  const labelEvery = Math.max(1, Math.ceil(days.length / Math.max(2, Math.floor(iw / 90))));
  const last = days[days.length - 1];

  const onMove = (e) => {
    const box = ref.current.getBoundingClientRect();
    const px = e.clientX - box.left;
    const i = Math.round(((px - m.l) / iw) * (days.length - 1));
    setHover(Math.max(0, Math.min(days.length - 1, i)));
  };
  const h = hover != null ? days[hover] : null;

  return (
    <div className="chart" ref={ref} onPointerMove={onMove} onPointerDown={onMove} onPointerLeave={() => setHover(null)}>
      {width > 0 && (
        <svg height={H} role="img" aria-label={`Cumulative units against the spread, ending at ${unitsText(last.cum)}`}>
          {ticks.map((t) => (
            <g key={t}>
              <line className={t === 0 ? "zero" : "grid"} x1={m.l} x2={m.l + iw} y1={y(t)} y2={y(t)} />
              <text className="axis" x={m.l - 8} y={y(t) + 4} textAnchor="end">{t > 0 ? `+${t}` : t}</text>
            </g>
          ))}
          {days.map((d, i) => (i % labelEvery === 0 && (days.length - 1 - i >= labelEvery / 2 || i === days.length - 1)) && (
            <text key={d.key} className="axis" x={x(i)} y={H - 6} textAnchor={i === 0 ? "start" : "middle"}>
              {formatDay(d.key, { month: "short", day: "numeric" })}
            </text>
          ))}
          <path className="area" d={area} />
          <path className="series" d={path} />
          {h && <line className="cross" x1={x(hover)} x2={x(hover)} y1={m.t} y2={m.t + ih} />}
          <circle className="dot" cx={x(h ? hover : days.length - 1)} cy={y((h || last).cum)} r="5" />
          {!h && <text className="endlabel" x={x(days.length - 1) + 10} y={y(last.cum) + 4}>{unitsText(last.cum)}</text>}
        </svg>
      )}
      {h && (
        <div className="tip" style={x(hover) > width / 2 ? { right: width - x(hover) + 12 } : { left: x(hover) + 12 }}>
          <b>{formatDay(h.key)}</b><br />
          {recordText(h.rec)} that day ({unitsText(h.rec.units)})<br />
          Running total {unitsText(h.cum)}
        </div>
      )}
    </div>
  );
}

function LogRow({ g }) {
  const bet = betFor(g);
  const res = g.ats_result || "–";
  const mktTotal = g.market?.over_under;
  return (
    <li className="row">
      <span className={`res ${g.ats_result || ""}`} title={{ W: "Covered", L: "Did not cover", P: "Push" }[g.ats_result] || "No spread bet"}>{res}</span>
      <span className="row-game">
        <b>{teamName(g, "away")}</b> at <b>{teamName(g, "home")}</b>
      </span>
      <span className="row-score">{g.actual_away_score}–{g.actual_home_score}</span>
      <span className="row-bet">
        {bet.kind === "ats" && <>Pick <b>{bet.label}</b> · {num(g.value_rating || bet.edge)} pt edge</>}
        {bet.kind === "none" && "No bet — model matched the line"}
        {bet.kind === "su" && <>No line · picked <b>{bet.abbr}</b> to win {g.model_correct_winner ? "✓" : "✗"}</>}
        {g.is_best_bet && <> · <b>Best bet</b></>}
      </span>
      <span className="row-extra">
        {mktTotal != null && g.model_ou_call && (
          <span className={g.ou_model_correct ? "ok" : g.ou_result === "P" ? "" : "no"}>
            {g.model_ou_call === "O" ? "Over" : "Under"} {num(mktTotal)} {g.ou_model_correct ? "✓" : g.ou_result === "P" ? "push" : "✗"}
          </span>
        )}
        {g.clv != null && <span><span className="sep"> · </span>CLV {signed(g.clv)}</span>}
      </span>
    </li>
  );
}

export default function Results({ state }) {
  const [seasonSel, setSeasonSel] = useState(null);
  const [period, setPeriod] = useState("all");
  const [conf, setConf] = useState("all");
  const [logFilter, setLogFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [shown, setShown] = useState(PAGE);

  const all = useMemo(
    () => (state.data?.games || []).filter((g) => g.graded && g.date).map((g) => ({ ...g, _day: dayKey(g.date), _season: seasonOf(g.date) })),
    [state.data],
  );
  const seasons = useMemo(() => [...new Set(all.map((g) => g._season))].sort((a, b) => b - a), [all]);
  const currentSeason = state.data?.summary?.season ?? seasons[0];
  const season = seasonSel ?? currentSeason;

  const seasonGames = useMemo(() => (season === "all" ? all : all.filter((g) => g._season === season)), [all, season]);
  const confs = useMemo(() => {
    const s = new Set();
    seasonGames.forEach((g) => { s.add(getConference(g.home_team)); s.add(getConference(g.away_team)); });
    const hasOther = s.delete("Other");
    return [...[...s].sort(), ...(hasOther ? ["Other"] : [])];
  }, [seasonGames]);

  const games = useMemo(() => {
    let list = seasonGames;
    if (period !== "all" && list.length) {
      const latest = list.reduce((mx, g) => (g._day > mx ? g._day : mx), "");
      const from = period === "latest" ? latest : shiftDay(latest, Number(period) - 1);
      list = list.filter((g) => g._day >= from);
    }
    if (conf !== "all") list = list.filter((g) => getConference(g.home_team) === conf || getConference(g.away_team) === conf);
    return list;
  }, [seasonGames, period, conf]);

  const stats = useMemo(() => {
    const ats = record(games);
    const su = games.filter((g) => g.model_correct_winner).length;
    const ouGames = games.filter((g) => g.ou_result && g.ou_result !== "P" && g.model_ou_call);
    const ouRight = ouGames.filter((g) => g.ou_model_correct).length;
    const bets = games.filter((g) => g.ats_result === "W" || g.ats_result === "L" || g.ats_result === "P");
    const edge = (lo, hi) => record(bets.filter((g) => (g.value_rating || 0) >= lo && (g.value_rating || 0) < hi));
    const byDay = new Map();
    bets.forEach((g) => { if (!byDay.has(g._day)) byDay.set(g._day, []); byDay.get(g._day).push(g); });
    let cum = 0;
    const days = [...byDay.keys()].sort().map((key) => {
      const rec = record(byDay.get(key));
      cum += rec.units;
      return { key, rec, cum };
    });
    return {
      ats, su, ouGames: ouGames.length, ouRight, days,
      best: record(bets.filter((g) => g.is_best_bet)),
      value: record(bets.filter((g) => (g.value_rating || 0) >= VALUE_EDGE)),
      tiers: [
        ["High (70+)", record(bets.filter((g) => g.confidence >= 70))],
        ["Medium (40–69)", record(bets.filter((g) => g.confidence >= 40 && g.confidence < 70))],
        ["Low (under 40)", record(bets.filter((g) => g.confidence < 40))],
      ],
      edges: [["Under 2 pts", edge(0, 2)], ["2–4 pts", edge(2, 4)], ["4–7 pts", edge(4, 7)], ["7+ pts", edge(7, Infinity)]],
      sides: [
        ["Home teams", record(bets.filter((g) => g.bet_side === "home"))],
        ["Road teams", record(bets.filter((g) => g.bet_side === "away"))],
        ["Favorites", record(bets.filter((g) => betLine(g) < 0))],
        ["Underdogs", record(bets.filter((g) => betLine(g) > 0))],
      ],
    };
  }, [games]);

  const logGames = useMemo(() => {
    const term = search.trim().toLowerCase();
    const test = LOG_FILTERS.find((f) => f.key === logFilter).test;
    return games
      .filter(test)
      .filter((g) => !term || [g.home_team, g.away_team, g.home_abbr, g.away_abbr].some((s) => (s || "").toLowerCase().includes(term)))
      .sort((a, b) => new Date(b.date) - new Date(a.date));
  }, [games, logFilter, search]);

  useEffect(() => { setShown(PAGE); }, [season, period, conf, logFilter, search]);

  if (state.status === "loading") return <div className="loading">Loading results…</div>;
  if (state.status === "error" || !all.length) {
    return <div className="empty"><b>No graded results yet.</b><br />Results appear here the morning after the first slate is played.</div>;
  }

  const summary = state.data.summary || {};
  const calScope = season === "all" ? summary.all_time : season === currentSeason ? summary : null;
  const cal = calScope?.calibration;
  const clv = calScope?.clv;
  const scopeLabel = season === "all" ? "All seasons" : `${seasonLabel(season)} season`;
  const { ats } = stats;
  const roi = ats.n ? (ats.units / (ats.n + ats.p)) * 100 : null;

  const visibleLog = logGames.slice(0, shown);
  const groups = [];
  visibleLog.forEach((g) => {
    const lastGroup = groups[groups.length - 1];
    if (lastGroup && lastGroup.key === g._day) lastGroup.games.push(g);
    else groups.push({ key: g._day, games: [g] });
  });
  const dayRecords = new Map(stats.days.map((d) => [d.key, d.rec]));

  return (
    <>
      <div className="page-head">
        <h1>Results</h1>
        <p className="page-sub">
          {games.length} games graded · {scopeLabel}{conf !== "all" ? ` · ${conf}` : ""} · 1 unit per pick at −110
        </p>
      </div>

      <div className="controls" style={{ paddingTop: 0 }}>
        <div className="seg" role="group" aria-label="Time period">
          {PERIODS.map((p) => (
            <button key={p.key} aria-pressed={period === p.key} onClick={() => setPeriod(p.key)}>{p.label}</button>
          ))}
        </div>
        <span className="spacer" />
        <label className="control-label grow-sm">
          <span>Season</span>
          <select className="field" value={season} onChange={(e) => setSeasonSel(e.target.value === "all" ? "all" : Number(e.target.value))}>
            {seasons.map((s) => <option key={s} value={s}>{seasonLabel(s)}</option>)}
            {seasons.length > 1 && <option value="all">All seasons</option>}
          </select>
        </label>
        <label className="control-label grow-sm">
          <span>Conference</span>
          <select className="field" value={conf} onChange={(e) => setConf(e.target.value)}>
            <option value="all">All</option>
            {confs.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>

      <div className="tiles six">
        <Tile label="Against the spread" value={ats.n ? recordText(ats) : "—"} sub={`${pctText(ats.pct)} · break-even ${BREAK_EVEN}%`} />
        <Tile label="Units won" value={ats.n ? unitsText(ats.units) : "—"} tone={ats.units > 0.05 ? "pos" : ats.units < -0.05 ? "neg" : ""}
          sub={roi == null ? "No bets" : `${signed(roi)}% return per bet`} />
        <Tile label="Best bets" value={stats.best.n ? recordText(stats.best) : "—"} sub={`${pctText(stats.best.pct)} · ${stats.best.n ? unitsText(stats.best.units) : "none yet"}`} />
        <Tile label={`Edge ${VALUE_EDGE}+ points`} value={stats.value.n ? recordText(stats.value) : "—"} sub={`${pctText(stats.value.pct)} · ${stats.value.n ? unitsText(stats.value.units) : "none yet"}`} />
        <Tile label="Winners picked" value={games.length ? pctText((stats.su / games.length) * 100) : "—"} sub={`${stats.su} of ${games.length} straight up`} />
        <Tile label="Totals" value={stats.ouGames ? pctText((stats.ouRight / stats.ouGames) * 100) : "—"} sub={`${stats.ouRight} of ${stats.ouGames} over/unders`} />
      </div>

      <div className="stack">
        <section className="card">
          <h2>Running profit against the spread</h2>
          <p className="card-sub">Units won or lost betting every pick, day by day.</p>
          {stats.days.length >= 2
            ? <UnitsChart days={stats.days} />
            : <p className="hint">Needs at least two days of graded picks in this view.</p>}
        </section>
      </div>

      <div className="grid-2">
        <section className="card">
          <h2>Where the picks win and lose</h2>
          <p className="card-sub">Record against the spread. The tick marks the {BREAK_EVEN}% needed to break even.</p>
          <div className="split-h">By edge vs market</div>
          {stats.edges.map(([label, rec]) => <Split key={label} label={label} rec={rec} />)}
          <div className="split-h">By confidence</div>
          {stats.tiers.map(([label, rec]) => <Split key={label} label={label} rec={rec} />)}
          <div className="split-h">By side</div>
          {stats.sides.map(([label, rec]) => <Split key={label} label={label} rec={rec} />)}
        </section>

        <section className="card">
          <h2>Model vs the market</h2>
          {cal && cal.n >= 50 ? (
            <>
              <p className="card-sub">{scopeLabel}, {cal.n} games with a line. Not affected by the filters above.</p>
              <dl className="facts" style={{ marginTop: 10 }}>
                <div><dt>Model’s average miss</dt><dd>{num(cal.model_mae, 2)} pts</dd></div>
                <div><dt>Market’s average miss</dt><dd>{num(cal.market_mae, 2)} pts</dd></div>
                <div>
                  <dt>Model weight</dt>
                  <dd>{cal.model_weight.toFixed(2)}<small>market {cal.market_weight.toFixed(2)}</small></dd>
                </div>
                <div>
                  <dt>Closing line value</dt>
                  <dd>
                    {clv?.n ? `${signed(clv.avg, 2)} pts` : "n/a"}
                    <small>{clv?.n ? `${clv.beat_close_pct}% beat the close · ${clv.n} bets` : "Needs closing-line snapshots"}</small>
                  </dd>
                </div>
              </dl>
              <p className="hint">
                <b>Model weight</b> is how much the model adds once the market line is known: near 0 means the line already
                contains what the model knows; higher is a real edge. <b>Closing line value</b> is how many points better
                the pick’s number was than the final line — positive over many bets is the best sign of a lasting edge.
              </p>
            </>
          ) : (
            <p className="card-sub" style={{ marginTop: 8 }}>
              {season !== "all" && season !== currentSeason
                ? "Calibration is only tracked for the current season and all seasons combined."
                : "Needs at least 50 graded games with a market line."}
            </p>
          )}
        </section>
      </div>

      <div className="stack">
        <section className="card">
          <div className="log-head">
            <h2>Game log</h2>
            <input className="field search" type="search" placeholder="Search teams" aria-label="Search game log"
              value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <div className="chips" role="group" aria-label="Filter game log" style={{ marginTop: 10 }}>
            {LOG_FILTERS.map((f) => (
              <button key={f.key} className="chip" aria-pressed={logFilter === f.key} onClick={() => setLogFilter(f.key)}>{f.label}</button>
            ))}
          </div>

          {logGames.length === 0 && <div className="empty">No games match your filters.</div>}
          {groups.map((grp) => {
            const rec = dayRecords.get(grp.key);
            return (
              <div key={grp.key}>
                <div className="day-head">
                  <span>{formatDay(grp.key, { weekday: "long", month: "short", day: "numeric" })}</span>
                  {rec && <span>{recordText(rec)} · {unitsText(rec.units)}</span>}
                </div>
                <ul>{grp.games.map((g) => <LogRow key={g.game_id} g={g} />)}</ul>
              </div>
            );
          })}
          {shown < logGames.length && (
            <button className="more" onClick={() => setShown(shown + PAGE)}>
              Show more ({logGames.length - shown} remaining)
            </button>
          )}
        </section>
      </div>

      <footer className="footer">
        <div className="glossary">
          <span><b>W / L / P</b> — the pick covered, didn’t cover, or pushed against the spread at the time of the pick.</span>
          <span><b>CLV</b> — closing line value: points the line moved in the pick’s favor before tip-off.</span>
        </div>
        Games without a market line count only toward straight-up accuracy. For entertainment and informational purposes only.
      </footer>
    </>
  );
}
