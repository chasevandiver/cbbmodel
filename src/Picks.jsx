import { useMemo, useState } from "react";
import {
  VALUE_EDGE, betFor, totalLean, lineMove, confTier, tipTime, dayKey, formatDay, favoriteLine,
  teamName, isRanked, num, signed, line, record, recordText, pctText, seasonOf,
} from "./lib.js";

const FILTERS = [
  { key: "all", label: "All", test: () => true },
  { key: "best", label: "Best bets", test: (p) => p.is_best_bet },
  { key: "value", label: `Edge ${VALUE_EDGE}+`, test: (p) => (p.value_rating || 0) >= VALUE_EDGE },
  { key: "ranked", label: "Top 25", test: (p) => isRanked(p.home_rank) || isRanked(p.away_rank) },
  { key: "upcoming", label: "Not started", test: (p, now) => new Date(p.date) > now },
];

const SORTS = {
  tipoff: { label: "Tip time", fn: (a, b) => new Date(a.date) - new Date(b.date) },
  edge: { label: "Biggest edge", fn: (a, b) => (b.value_rating || 0) - (a.value_rating || 0) },
  confidence: { label: "Confidence", fn: (a, b) => b.confidence - a.confidence },
  spread: { label: "Closest game", fn: (a, b) => Math.abs(a.predicted_spread) - Math.abs(b.predicted_spread) },
  total: { label: "Highest total", fn: (a, b) => b.predicted_total - a.predicted_total },
};

export function Logo({ src, small }) {
  const [bad, setBad] = useState(false);
  const cls = `logo${small ? " sm" : ""}`;
  if (!src || bad) return <span className={`${cls} logo-blank`} aria-hidden="true" />;
  return <img className={cls} src={src} alt="" loading="lazy" onError={() => setBad(true)} />;
}

function TeamRow({ pick, side, picked }) {
  const rank = pick[`${side}_rank`];
  return (
    <div className={`team${picked ? " picked" : ""}`}>
      <Logo src={pick[`${side}_logo`]} />
      <div className="team-name">
        {isRanked(rank) && <span className="rank">#{rank}</span>}
        <span className="nm">{teamName(pick, side)}</span>
        <span className="rec">{pick[`${side}_record`]}</span>
        {picked && <span className="pick-dot" title="Model's side" />}
      </div>
      <div className="proj" title="Projected score">{Math.round(pick[`${side}_projected_score`])}</div>
    </div>
  );
}

function Detail({ pick, bet, bigEdge }) {
  const mkt = pick.market || {};
  const lean = totalLean(pick);
  const move = lineMove(pick, bet);
  const hasLine = mkt.spread != null;
  const awayProb = pick.away_win_prob;
  const homeProb = pick.home_win_prob;
  const awayFav = awayProb > homeProb;

  return (
    <div className="game-detail">
      {bigEdge && bet.edge >= 7 && (
        <p className="caution">
          <b>Large edge — check the news first.</b> Picks with a 7+ point edge are {bigEdge.w}-{bigEdge.l} against the
          spread this season. A gap this big usually means the market knows something the ratings don’t (injuries, lineup changes).
        </p>
      )}

      <section>
        <h3 className="detail-h">Spread</h3>
        <dl className="facts">
          <div><dt>Model line</dt><dd>{favoriteLine(pick, -pick.predicted_spread)}</dd></div>
          {hasLine && (
            <div><dt>Market line{mkt.bookmaker && <span className="book"> ({mkt.bookmaker})</span>}</dt><dd>{favoriteLine(pick, mkt.spread)}</dd></div>
          )}
          {hasLine && (
            <div>
              <dt>Edge</dt>
              <dd>{num(bet.edge)} pts{bet.kind === "ats" ? ` on ${bet.abbr}` : ""}{bet.kind === "none" && <small>Inside half a point — no bet</small>}</dd>
            </div>
          )}
          {move && (
            <div>
              <dt>Latest line</dt>
              <dd>
                {favoriteLine(pick, move.current)}
                <small>
                  {Math.abs(move.value) < 0.05 ? "No movement since the pick"
                    : move.value > 0 ? `Moved ${num(Math.abs(move.value))} toward the model`
                    : `Moved ${num(Math.abs(move.value))} against the model`}
                </small>
              </dd>
            </div>
          )}
          {!hasLine && <div><dt>Market line</dt><dd>None posted</dd></div>}
        </dl>
      </section>

      <section>
        <h3 className="detail-h">Total</h3>
        <dl className="facts">
          <div><dt>Model total</dt><dd>{num(pick.predicted_total)}</dd></div>
          {lean && <div><dt>Market total</dt><dd>{num(lean.ou)}</dd></div>}
          {lean && (
            <div><dt>Lean</dt><dd>{lean.call ? `${lean.call} ${num(lean.ou)} (${signed(lean.diff)})` : "None"}</dd></div>
          )}
          {pick.projected_tempo != null && <div><dt>Projected pace</dt><dd>{num(pick.projected_tempo)} poss.</dd></div>}
        </dl>
      </section>

      <section>
        <h3 className="detail-h">Win probability</h3>
        <div className="prob">
          <div className="prob-row"><span>{pick.away_abbr} {num(awayProb)}%</span><span>{num(homeProb)}% {pick.home_abbr}</span></div>
          <div className="prob-bar" role="img" aria-label={`${pick.away_abbr} ${awayProb}%, ${pick.home_abbr} ${homeProb}%`}>
            <i className={awayFav ? "on" : ""} style={{ width: `${awayProb}%` }} />
            <i className={awayFav ? "" : "on"} style={{ width: `${homeProb}%` }} />
          </div>
        </div>
        <p className="venue">
          {[pick.venue, pick.neutral_site && "Neutral site", pick.conference_game && "Conference game", pick.is_tournament_game && "Tournament game"].filter(Boolean).join(" · ")}
        </p>
      </section>

      <section>
        <h3 className="detail-h">What drives the projection</h3>
        <dl className="facts">
          {pick.home_adj_em != null && pick.away_adj_em != null && (
            <div><dt>Adj. efficiency margin</dt><dd>{pick.away_abbr} {signed(pick.away_adj_em)} · {pick.home_abbr} {signed(pick.home_adj_em)}</dd></div>
          )}
          {pick.factors?.efficiency_margin != null && (
            <div><dt>Team quality</dt><dd>{factorText(pick, pick.factors.efficiency_margin)}</dd></div>
          )}
          {pick.factors?.home_court != null && (
            <div><dt>Home court</dt><dd>{pick.factors.home_court ? factorText(pick, pick.factors.home_court) : "None (neutral)"}</dd></div>
          )}
        </dl>
      </section>
    </div>
  );
}

const factorText = (pick, v) => (Math.abs(v) < 0.05 ? "Even" : `${v > 0 ? pick.home_abbr : pick.away_abbr} +${num(Math.abs(v))} pts`);

function GameCard({ pick, now, expanded, onToggle, bigEdge }) {
  const bet = betFor(pick);
  const tipped = new Date(pick.date) <= now;
  const edge = pick.value_rating;
  const tier = confTier(pick.confidence);
  const id = `detail-${pick.game_id}`;

  return (
    <article className={`game${pick.is_best_bet ? " best" : ""}${tipped ? " tipped" : ""}`}>
      <button className="game-main" onClick={onToggle} aria-expanded={expanded} aria-controls={id}>
        <div className="game-meta">
          <span className="time">{tipTime(pick.date)}</span>
          {pick.broadcast && <span>{pick.broadcast}</span>}
          {pick.neutral_site && <span>Neutral</span>}
          {tipped && <span className="badge plain">Started</span>}
          {pick.is_best_bet && <span className="badge best">Best bet</span>}
          {!pick.is_best_bet && (edge || 0) >= VALUE_EDGE && <span className="badge value">Edge {VALUE_EDGE}+</span>}
        </div>
        <span className="chev" aria-hidden="true">▼</span>

        <div className="game-teams">
          <span className="proj-h">Proj.</span>
          <TeamRow pick={pick} side="away" picked={bet.side === "away"} />
          <TeamRow pick={pick} side="home" picked={bet.side === "home"} />
        </div>

        <div className="game-pick">
          <div>
            <div className="pick-label">{bet.kind === "su" ? "Pick (no line)" : "Pick"}</div>
            <div className={`pick-bet${bet.kind === "none" ? " none" : ""}`}>{bet.label}</div>
            <div className="pick-edge">
              {bet.kind === "ats" && <><b>{num(bet.edge)} pt</b> edge vs market</>}
              {bet.kind === "none" && "Model agrees with the line"}
              {bet.kind === "su" && `Model: ${favoriteLine(pick, -pick.predicted_spread)}`}
            </div>
          </div>
          <div className={`conf ${tier}`} title="Confidence: a 15–95 ranking score, not a win probability">
            <div className="pick-label">Conf.</div>
            <div className="conf-num">{Math.round(pick.confidence)}</div>
            <div className="conf-bar"><i style={{ width: `${pick.confidence}%` }} /></div>
          </div>
        </div>
      </button>
      {expanded && <div id={id}><Detail pick={pick} bet={bet} bigEdge={bigEdge} /></div>}
    </article>
  );
}

function seasonSnapshot(results) {
  if (!results?.games?.length) return null;
  const season = results.summary?.season ?? Math.max(...results.games.map((g) => seasonOf(g.date)));
  const games = results.games.filter((g) => g.graded && seasonOf(g.date) === season);
  if (!games.length) return null;
  const lastDay = games.reduce((m, g) => { const k = dayKey(g.date); return k > m ? k : m; }, "");
  const big = results.summary?.calibration?.ats_by_edge?.["7+"];
  return {
    ats: record(games),
    best: record(games.filter((g) => g.is_best_bet)),
    lastDay,
    last: record(games.filter((g) => dayKey(g.date) === lastDay)),
    bigEdge: big && big.w + big.l >= 15 && big.pct < 50 ? big : null,
  };
}

export default function Picks({ state, results, onNavigate }) {
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("tipoff");
  const [now] = useState(() => new Date());
  const snap = useMemo(() => seasonSnapshot(results), [results]);

  if (state.status === "loading") return <div className="loading">Loading today’s slate…</div>;
  if (state.status === "error" || !state.data?.picks) {
    return <div className="empty"><b>Couldn’t load today’s picks.</b><br />The slate file is missing or unreachable — try refreshing.</div>;
  }

  const data = state.data;
  const picks = data.picks;
  const slateKey = `${data.date.slice(0, 4)}-${data.date.slice(4, 6)}-${data.date.slice(6, 8)}`;
  const todayKey = new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York" }).format(now);
  const stale = slateKey !== todayKey;

  const counts = Object.fromEntries(FILTERS.map((f) => [f.key, picks.filter((p) => f.test(p, now)).length]));
  const term = search.trim().toLowerCase();
  const visible = picks
    .filter((p) => FILTERS.find((f) => f.key === filter).test(p, now))
    .filter((p) => !term || [p.home_team, p.away_team, p.home_abbr, p.away_abbr].some((s) => (s || "").toLowerCase().includes(term)))
    .sort(SORTS[sortBy].fn);
  const upcoming = visible.filter((p) => new Date(p.date) > now);
  const started = visible.filter((p) => new Date(p.date) <= now);

  const renderCards = (list) => (
    <div className="games">
      {list.map((p) => (
        <GameCard key={p.game_id} pick={p} now={now} bigEdge={snap?.bigEdge}
          expanded={expandedId === p.game_id}
          onToggle={() => setExpandedId(expandedId === p.game_id ? null : p.game_id)} />
      ))}
    </div>
  );

  const updated = new Date(data.generated_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

  return (
    <>
      <div className="page-head">
        <h1>{formatDay(slateKey, { weekday: "long", month: "long", day: "numeric" })}</h1>
        <p className="page-sub">{picks.length} games · updated {updated} · model v{data.model_version}</p>
        {stale && (
          <p className="notice">
            These picks are for {formatDay(slateKey, { weekday: "long", month: "short", day: "numeric" })}. Today’s slate hasn’t been published yet.
          </p>
        )}
      </div>

      <div className="tiles">
        <div className="tile">
          <div className="tile-label">Games</div>
          <div className="tile-value">{picks.length}</div>
          <div className="tile-sub">{counts.upcoming} still to tip</div>
        </div>
        <button className="tile" onClick={() => setFilter("best")}>
          <div className="tile-label">Best bets</div>
          <div className="tile-value">{counts.best}</div>
          <div className="tile-sub">{snap?.best.n ? `${recordText(snap.best)} this season` : "Edge of 3–6 points"}</div>
        </button>
        <button className="tile" onClick={() => setFilter("value")}>
          <div className="tile-label">Edge {VALUE_EDGE}+ points</div>
          <div className="tile-value">{counts.value}</div>
          <div className="tile-sub">Model vs market spread</div>
        </button>
        {snap ? (
          <button className="tile" onClick={() => onNavigate("results")}>
            <div className="tile-label">Season vs spread</div>
            <div className="tile-value">{recordText(snap.ats)}</div>
            <div className="tile-sub">
              {pctText(snap.ats.pct)}{snap.last.n ? ` · ${recordText(snap.last)} on ${formatDay(snap.lastDay, { month: "short", day: "numeric" })}` : ""}
            </div>
          </button>
        ) : (
          <div className="tile">
            <div className="tile-label">With a market line</div>
            <div className="tile-value">{picks.filter((p) => p.market?.spread != null).length}</div>
            <div className="tile-sub">of {picks.length} games</div>
          </div>
        )}
      </div>

      <div className="controls">
        <input className="field search" type="search" placeholder="Search teams" aria-label="Search teams"
          value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="chips" role="group" aria-label="Filter games">
          {FILTERS.map((f) => (
            <button key={f.key} className="chip" aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}>
              {f.label}<span className="count">{counts[f.key]}</span>
            </button>
          ))}
        </div>
        <span className="spacer" />
        <label className="control-label grow-sm">
          Sort
          <select className="field" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            {Object.entries(SORTS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
          </select>
        </label>
      </div>

      {visible.length === 0 && <div className="empty">No games match your filters.</div>}
      {upcoming.length > 0 && renderCards(upcoming)}
      {started.length > 0 && (
        <>
          <h2 className="section-title">Already started <small>{started.length} {started.length === 1 ? "game" : "games"}</small></h2>
          {renderCards(started)}
        </>
      )}

      <footer className="footer">
        <div className="glossary">
          <span><b>Pick</b> — the side to take at the market spread. The number next to each team is its projected score.</span>
          <span><b>Edge</b> — points between the model’s line and the market’s. <b>Best bets</b> are edges of 3–6 points.</span>
          <span><b>Conf.</b> — a 15–95 score for ranking the slate, not a win probability.</span>
        </div>
        Ratings: {data.ratings_source || "Barttorvik"}. For entertainment and informational purposes only.
      </footer>
    </>
  );
}
