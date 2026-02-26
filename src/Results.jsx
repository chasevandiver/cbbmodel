import { useState, useEffect } from "react";

const SAMPLE_RESULTS = {
  generated_at: "2026-02-24T08:00:00",
  summary: {
    total_graded: 47,
    ats: { w: 27, l: 18, p: 2, pct: 60.0 },
    su: { correct: 31, total: 47, pct: 66.0 },
    ou: {
      over: 22, under: 23, push: 2,
      model_correct: 28, model_gradeable: 45, model_pct: 62.2,
    },
    by_confidence: {
      high: { w: 12, l: 5, p: 1, pct: 70.6 },
      medium: { w: 11, l: 9, p: 1, pct: 55.0 },
      low: { w: 4, l: 4, p: 0, pct: 50.0 },
    },
    value_plays: { w: 8, l: 3, p: 0, pct: 72.7 },
  },
  games: [
    {
      game_id: "101", graded: true,
      home_team: "Duke Blue Devils", away_team: "North Carolina Tar Heels",
      home_abbr: "DUKE", away_abbr: "UNC",
      predicted_spread: -6.2, predicted_total: 151.4,
      actual_home_score: 81, actual_away_score: 74,
      actual_margin: 7, actual_total: 155,
      ats_result: "W", ou_result: "O",
      confidence: 82.3, value_rating: 0.7,
      model_correct_winner: true,
      market: { spread: -5.5, over_under: 149.5 },
      date: "2026-02-23T19:00:00Z",
    },
    {
      game_id: "102", graded: true,
      home_team: "Houston Cougars", away_team: "Kansas Jayhawks",
      home_abbr: "HOU", away_abbr: "KU",
      predicted_spread: -8.7, predicted_total: 133.2,
      actual_home_score: 71, actual_away_score: 65,
      actual_margin: 6, actual_total: 136,
      ats_result: "L", ou_result: "O",
      confidence: 88.1, value_rating: 1.7,
      model_correct_winner: true,
      market: { spread: -7, over_under: 131.5 },
      date: "2026-02-23T21:00:00Z",
    },
    {
      game_id: "103", graded: true,
      home_team: "Gonzaga Bulldogs", away_team: "Saint Mary's Gaels",
      home_abbr: "GONZ", away_abbr: "SMC",
      predicted_spread: -9.1, predicted_total: 146.8,
      actual_home_score: 78, actual_away_score: 66,
      actual_margin: 12, actual_total: 144,
      ats_result: "W", ou_result: "U",
      confidence: 76.5, value_rating: 0.6,
      model_correct_winner: true,
      market: { spread: -8.5, over_under: 145.5 },
      date: "2026-02-22T20:00:00Z",
    },
    {
      game_id: "104", graded: true,
      home_team: "Iowa State Cyclones", away_team: "Texas Tech Red Raiders",
      home_abbr: "ISU", away_abbr: "TTU",
      predicted_spread: -11.3, predicted_total: 128.6,
      actual_home_score: 68, actual_away_score: 61,
      actual_margin: 7, actual_total: 129,
      ats_result: "L", ou_result: "O",
      confidence: 71.4, value_rating: 1.3,
      model_correct_winner: true,
      market: { spread: -10, over_under: 127.5 },
      date: "2026-02-22T18:00:00Z",
    },
    {
      game_id: "105", graded: true,
      home_team: "Auburn Tigers", away_team: "Alabama Crimson Tide",
      home_abbr: "AUB", away_abbr: "BAMA",
      predicted_spread: -4.8, predicted_total: 158.2,
      actual_home_score: 84, actual_away_score: 79,
      actual_margin: 5, actual_total: 163,
      ats_result: "W", ou_result: "O",
      confidence: 61.8, value_rating: 1.3,
      model_correct_winner: true,
      market: { spread: -3.5, over_under: 156.5 },
      date: "2026-02-21T21:00:00Z",
    },
    {
      game_id: "106", graded: true,
      home_team: "Purdue Boilermakers", away_team: "Michigan State Spartans",
      home_abbr: "PUR", away_abbr: "MSU",
      predicted_spread: 1.4, predicted_total: 142.8,
      actual_home_score: 69, actual_away_score: 74,
      actual_margin: -5, actual_total: 143,
      ats_result: "L", ou_result: "O",
      confidence: 32.6, value_rating: 3.9,
      model_correct_winner: false,
      market: { spread: 2.5, over_under: 141.5 },
      date: "2026-02-21T19:00:00Z",
    },
  ],
};

// ─── Shared design tokens ──────────────────────────────────────────────────
const C = {
  bg: "#080816",
  surface: "#0f0f23",
  surface2: "#0d0d1a",
  border: "#1e293b",
  text: "#f8fafc",
  muted: "#6b7280",
  dim: "#4b5563",
  green: "#22c55e",
  greenDim: "#4ade80",
  red: "#ef4444",
  redDim: "#f87171",
  yellow: "#eab308",
  indigo: "#818cf8",
  indigoDim: "#a5b4fc",
  orange: "#f97316",
};

function StatCard({ label, value, sub, color = C.indigo, large = false }) {
  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 12,
      padding: large ? "20px 24px" : "14px 18px",
      display: "flex",
      flexDirection: "column",
      gap: 4,
    }}>
      <div style={{
        fontSize: 9,
        fontWeight: 800,
        color: C.muted,
        letterSpacing: 2.5,
        textTransform: "uppercase",
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        {label}
      </div>
      <div style={{
        fontSize: large ? 36 : 26,
        fontWeight: 900,
        color,
        fontFamily: "'JetBrains Mono', monospace",
        lineHeight: 1,
      }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{sub}</div>
      )}
    </div>
  );
}

function RecordBadge({ w, l, p, pct, color }) {
  const c = color || (pct >= 55 ? C.green : pct >= 50 ? C.yellow : C.red);
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
      <span style={{
        fontSize: 22,
        fontWeight: 900,
        color: c,
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        {w}-{l}{p > 0 ? `-${p}` : ""}
      </span>
      <span style={{
        fontSize: 13,
        fontWeight: 700,
        color: C.muted,
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        ({pct}%)
      </span>
    </div>
  );
}

function WinBar({ w, l, p }) {
  const total = w + l + (p || 0);
  if (total === 0) return null;
  const wPct = (w / total) * 100;
  const lPct = (l / total) * 100;
  const pPct = ((p || 0) / total) * 100;
  return (
    <div style={{
      display: "flex",
      height: 6,
      borderRadius: 3,
      overflow: "hidden",
      gap: 1,
    }}>
      <div style={{ width: `${wPct}%`, background: C.green, transition: "width 1s ease-out" }} />
      <div style={{ width: `${pPct}%`, background: C.yellow }} />
      <div style={{ width: `${lPct}%`, background: C.red, transition: "width 1s ease-out" }} />
    </div>
  );
}

function ConfTierRow({ label, record, highlight }) {
  const { w, l, p, pct } = record;
  const color = pct >= 60 ? C.green : pct >= 52 ? C.yellow : C.red;
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: "10px 0",
      borderBottom: `1px solid ${C.border}`,
    }}>
      <div style={{
        fontSize: 10,
        fontWeight: 800,
        color: highlight ? C.indigoDim : C.muted,
        width: 80,
        letterSpacing: 1,
        textTransform: "uppercase",
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        {label}
      </div>
      <div style={{ flex: 1 }}>
        <WinBar w={w} l={l} p={p} />
      </div>
      <div style={{
        fontSize: 13,
        fontWeight: 700,
        color: C.muted,
        fontFamily: "'JetBrains Mono', monospace",
        width: 60,
        textAlign: "right",
      }}>
        {w}-{l}{p > 0 ? `-${p}` : ""}
      </div>
      <div style={{
        fontSize: 14,
        fontWeight: 900,
        color,
        fontFamily: "'JetBrains Mono', monospace",
        width: 52,
        textAlign: "right",
      }}>
        {pct}%
      </div>
    </div>
  );
}

function GameResultRow({ game, index }) {
  const isWin = game.ats_result === "W";
  const isLoss = game.ats_result === "L";
  const isPush = game.ats_result === "P";
  const atsColor = isWin ? C.green : isLoss ? C.red : C.yellow;
  const ouColor = game.ou_result === "O" ? C.orange :
                  game.ou_result === "U" ? C.indigo : C.yellow;

  // Same coverCheck logic as App.jsx and results_tracker.py
  // predicted_spread and market.spread are both home-perspective
  const modelMargin = game.predicted_spread;
  const mktSpread = game.market?.spread != null ? parseFloat(game.market.spread) : null;

  let betAbbr, betLine;
  if (mktSpread != null) {
    const coverCheck = modelMargin + mktSpread;
    if (coverCheck > 0.5) {
      // Bet home
      betAbbr = game.home_abbr;
      betLine = mktSpread >= 0 ? `+${mktSpread}` : `${mktSpread}`;
    } else if (coverCheck < -0.5) {
      // Bet away
      betAbbr = game.away_abbr;
      const awayLine = -mktSpread;
      betLine = awayLine >= 0 ? `+${awayLine}` : `${awayLine}`;
    } else {
      betAbbr = "—";
      betLine = "";
    }
  } else {
    // No market line — straight up pick
    betAbbr = modelMargin > 0 ? game.home_abbr : game.away_abbr;
    betLine = "ML";
  }

  const gameDate = game.date
    ? new Date(game.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })
    : "";

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "60px 1fr 80px 60px 60px 60px",
      gap: 8,
      alignItems: "center",
      padding: "10px 16px",
      background: index % 2 === 0 ? C.surface2 : "transparent",
      borderRadius: 6,
      animation: "fadeSlideIn 0.4s ease-out both",
      animationDelay: `${index * 40}ms`,
    }}>
      {/* Date */}
      <div style={{ fontSize: 10, color: C.dim, fontFamily: "'JetBrains Mono', monospace" }}>
        {gameDate}
      </div>

      {/* Matchup */}
      <div>
        <div style={{ fontSize: 12, color: C.muted }}>
          <span style={{ color: C.text, fontWeight: 600 }}>{game.away_abbr}</span>
          {" "}@{" "}
          <span style={{ color: C.text, fontWeight: 600 }}>{game.home_abbr}</span>
        </div>
        <div style={{ fontSize: 10, color: C.dim, marginTop: 2, fontFamily: "'JetBrains Mono', monospace" }}>
          Pick: {betAbbr} {betLine} • Actual: {game.actual_away_score}-{game.actual_home_score}
        </div>
      </div>

      {/* Conf */}
      <div style={{
        fontSize: 11,
        fontWeight: 700,
        color: game.confidence >= 70 ? C.green : game.confidence >= 40 ? C.yellow : C.muted,
        fontFamily: "'JetBrains Mono', monospace",
        textAlign: "center",
      }}>
        {Math.round(game.confidence)}%
      </div>

      {/* ATS */}
      <div style={{
        fontSize: 13,
        fontWeight: 900,
        color: atsColor,
        fontFamily: "'JetBrains Mono', monospace",
        textAlign: "center",
        background: `${atsColor}15`,
        borderRadius: 4,
        padding: "3px 6px",
      }}>
        {game.ats_result}
      </div>

      {/* O/U result */}
      <div style={{
        fontSize: 11,
        fontWeight: 700,
        color: ouColor,
        fontFamily: "'JetBrains Mono', monospace",
        textAlign: "center",
      }}>
        {game.ou_result}
      </div>

      {/* Total */}
      <div style={{
        fontSize: 10,
        color: C.dim,
        fontFamily: "'JetBrains Mono', monospace",
        textAlign: "right",
      }}>
        {game.actual_total}
      </div>
    </div>
  );
}

export default function Results({ onNavigate }) {
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState("all");
  const [sortBy, setSortBy] = useState("date");

  useEffect(() => {
    fetch(`/results/results.json?v=${Date.now()}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => {
        // Use sample data if no real results yet
        if (!d || !d.summary || d.summary.total_graded === 0) {
          setData(SAMPLE_RESULTS);
        } else {
          setData(d);
        }
      })
      .catch(() => setData(SAMPLE_RESULTS));
  }, []);

  if (!data) return (
    <div style={{
      minHeight: "100vh", background: C.bg,
      display: "flex", alignItems: "center", justifyContent: "center",
      color: C.muted, fontFamily: "'DM Sans', sans-serif",
    }}>
      Loading results...
    </div>
  );

  const { summary, games } = data;
  const graded = games.filter(g => g.graded);

  // Filter
  let filtered = [...graded];
  if (filter === "high") filtered = filtered.filter(g => g.confidence >= 70);
  if (filter === "value") filtered = filtered.filter(g => (g.value_rating || 0) >= 3);
  if (filter === "wins") filtered = filtered.filter(g => g.ats_result === "W");
  if (filter === "losses") filtered = filtered.filter(g => g.ats_result === "L");

  // Sort
  if (sortBy === "date") filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
  if (sortBy === "confidence") filtered.sort((a, b) => b.confidence - a.confidence);
  if (sortBy === "value") filtered.sort((a, b) => (b.value_rating || 0) - (a.value_rating || 0));

  const { ats, su, ou, by_confidence, value_plays } = summary;
  const atsColor = ats.pct >= 55 ? C.green : ats.pct >= 50 ? C.yellow : C.red;

  return (
    <div style={{
      minHeight: "100vh",
      background: C.bg,
      color: C.text,
      fontFamily: "'Satoshi', 'DM Sans', -apple-system, sans-serif",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
        * { box-sizing: border-box; margin: 0; padding: 0; }
      `}</style>

      {/* Header */}
      <header style={{ padding: "32px 24px 0", maxWidth: 900, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: C.green,
            animation: "pulse 2s ease-in-out infinite",
            boxShadow: `0 0 8px ${C.green}80`,
          }} />
          <span style={{
            fontSize: 10, fontWeight: 700, color: C.green,
            letterSpacing: 3, textTransform: "uppercase",
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            MODEL PERFORMANCE
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h1 style={{
              fontSize: 32, fontWeight: 900, letterSpacing: -1,
              background: "linear-gradient(135deg, #f8fafc, #818cf8)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
              marginBottom: 4,
            }}>
              COURTSIDE EDGE
            </h1>
            <p style={{ fontSize: 13, color: C.muted }}>
              {graded.length} games graded • Season record
            </p>
          </div>

          {/* Nav */}
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => onNavigate("picks")} style={{
              background: "transparent",
              border: `1px solid ${C.border}`,
              borderRadius: 20, padding: "7px 16px",
              color: C.muted, fontSize: 11, fontWeight: 700,
              cursor: "pointer", letterSpacing: 0.5,
              fontFamily: "'JetBrains Mono', monospace",
              transition: "all 0.2s",
            }}>
              ← TODAY'S PICKS
            </button>
            <div style={{
              background: `${C.indigo}20`,
              border: `1px solid ${C.indigo}`,
              borderRadius: 20, padding: "7px 16px",
              color: C.indigoDim, fontSize: 11, fontWeight: 700,
              letterSpacing: 0.5,
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              RESULTS
            </div>
          </div>
        </div>
      </header>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 24px 48px" }}>

        {/* Hero stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24 }}>
          <div style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: 12, padding: "20px 24px",
            gridColumn: "1",
          }}>
            <div style={{
              fontSize: 9, fontWeight: 800, color: C.muted,
              letterSpacing: 2.5, textTransform: "uppercase",
              fontFamily: "'JetBrains Mono', monospace", marginBottom: 8,
            }}>
              ATS Record
            </div>
            <RecordBadge w={ats.w} l={ats.l} p={ats.p} pct={ats.pct} />
            <div style={{ marginTop: 10 }}>
              <WinBar w={ats.w} l={ats.l} p={ats.p} />
            </div>
            <div style={{ fontSize: 10, color: C.dim, marginTop: 6 }}>
              Against the spread
            </div>
          </div>

          <StatCard
            label="Straight Up"
            value={`${su.pct}%`}
            sub={`${su.correct}/${su.total} correct winner`}
            color={su.pct >= 60 ? C.green : C.yellow}
          />

          <StatCard
            label="O/U Model"
            value={`${ou.model_pct}%`}
            sub={`${ou.model_correct}/${ou.model_gradeable} correct calls`}
            color={ou.model_pct >= 55 ? C.green : C.yellow}
          />
        </div>

        {/* Confidence breakdown + Value plays */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 24 }}>
          <div style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: 12, padding: "18px 20px",
          }}>
            <div style={{
              fontSize: 9, fontWeight: 800, color: C.muted,
              letterSpacing: 2.5, textTransform: "uppercase",
              fontFamily: "'JetBrains Mono', monospace", marginBottom: 14,
            }}>
              ATS by Confidence Tier
            </div>
            <ConfTierRow label="High ≥70%" record={by_confidence.high} highlight />
            <ConfTierRow label="Med 40-70%" record={by_confidence.medium} />
            <ConfTierRow label="Low <40%" record={by_confidence.low} />
          </div>

          <div style={{
            background: C.surface,
            border: `1px solid ${C.border}`,
            borderRadius: 12, padding: "18px 20px",
          }}>
            <div style={{
              fontSize: 9, fontWeight: 800, color: C.muted,
              letterSpacing: 2.5, textTransform: "uppercase",
              fontFamily: "'JetBrains Mono', monospace", marginBottom: 14,
            }}>
              Value Plays (Edge ≥ 3pts)
            </div>
            <RecordBadge
              w={value_plays.w} l={value_plays.l}
              p={value_plays.p} pct={value_plays.pct}
            />
            <div style={{ marginTop: 10 }}>
              <WinBar w={value_plays.w} l={value_plays.l} p={value_plays.p} />
            </div>
            <div style={{ fontSize: 10, color: C.dim, marginTop: 6 }}>
              Games where model disagreed with market by 3+ pts
            </div>

            <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <div style={{ background: C.surface2, borderRadius: 8, padding: "10px 12px" }}>
                <div style={{ fontSize: 9, color: C.dim, marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>OVERS</div>
                <div style={{ fontSize: 18, fontWeight: 900, color: C.orange, fontFamily: "'JetBrains Mono', monospace" }}>{ou.over}</div>
              </div>
              <div style={{ background: C.surface2, borderRadius: 8, padding: "10px 12px" }}>
                <div style={{ fontSize: 9, color: C.dim, marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>UNDERS</div>
                <div style={{ fontSize: 18, fontWeight: 900, color: C.indigo, fontFamily: "'JetBrains Mono', monospace" }}>{ou.under}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Game log */}
        <div style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 12, overflow: "hidden",
        }}>
          {/* Table header + filters */}
          <div style={{
            padding: "16px 20px",
            borderBottom: `1px solid ${C.border}`,
            display: "flex",
            alignItems: "center",
            gap: 12,
            flexWrap: "wrap",
          }}>
            <span style={{
              fontSize: 9, fontWeight: 800, color: C.muted,
              letterSpacing: 2.5, textTransform: "uppercase",
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              Game Log
            </span>

            <div style={{ display: "flex", gap: 6, marginLeft: 8 }}>
              {[
                { key: "all", label: "All" },
                { key: "high", label: "High Conf" },
                { key: "value", label: "Value" },
                { key: "wins", label: "Wins" },
                { key: "losses", label: "Losses" },
              ].map(f => (
                <button key={f.key} onClick={() => setFilter(f.key)} style={{
                  background: filter === f.key ? `${C.indigo}30` : "transparent",
                  border: `1px solid ${filter === f.key ? C.indigo : C.border}`,
                  borderRadius: 20, padding: "4px 12px",
                  color: filter === f.key ? C.indigoDim : C.muted,
                  fontSize: 10, fontWeight: 700, cursor: "pointer",
                  fontFamily: "'JetBrains Mono', monospace",
                  transition: "all 0.2s",
                }}>
                  {f.label}
                </button>
              ))}
            </div>

            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 9, color: C.dim, fontFamily: "'JetBrains Mono', monospace" }}>SORT:</span>
              <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{
                background: C.surface2, border: `1px solid ${C.border}`,
                borderRadius: 6, padding: "4px 8px",
                color: C.muted, fontSize: 10, outline: "none",
                cursor: "pointer", fontFamily: "'JetBrains Mono', monospace",
              }}>
                <option value="date">Date</option>
                <option value="confidence">Confidence</option>
                <option value="value">Value</option>
              </select>
            </div>
          </div>

          {/* Column headers */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "60px 1fr 80px 60px 60px 60px",
            gap: 8,
            padding: "8px 16px",
            borderBottom: `1px solid ${C.border}`,
          }}>
            {["DATE", "MATCHUP", "CONF", "ATS", "O/U", "TOT"].map(h => (
              <div key={h} style={{
                fontSize: 8, fontWeight: 800, color: C.dim,
                letterSpacing: 1.5, textTransform: "uppercase",
                fontFamily: "'JetBrains Mono', monospace",
                textAlign: h === "CONF" || h === "ATS" || h === "O/U" ? "center" : h === "TOT" ? "right" : "left",
              }}>
                {h}
              </div>
            ))}
          </div>

          {/* Rows */}
          <div style={{ padding: "8px" }}>
            {filtered.length === 0 ? (
              <div style={{
                textAlign: "center", padding: 40,
                color: C.muted, fontSize: 13,
              }}>
                No games match your filters
              </div>
            ) : (
              filtered.map((game, i) => (
                <GameResultRow key={game.game_id} game={game} index={i} />
              ))
            )}
          </div>
        </div>

        {/* Legend */}
        <div style={{
          display: "flex", gap: 20, marginTop: 16, flexWrap: "wrap",
          fontSize: 10, color: C.dim, fontFamily: "'JetBrains Mono', monospace",
        }}>
          <span><span style={{ color: C.green }}>W</span> = Pick covered spread</span>
          <span><span style={{ color: C.red }}>L</span> = Pick didn't cover</span>
          <span><span style={{ color: C.yellow }}>P</span> = Push</span>
          <span><span style={{ color: C.orange }}>O</span> = Over hit</span>
          <span><span style={{ color: C.indigo }}>U</span> = Under hit</span>
        </div>
      </div>

      <footer style={{
        borderTop: `1px solid ${C.border}`,
        padding: "20px 24px", textAlign: "center",
        maxWidth: 900, margin: "0 auto",
      }}>
        <p style={{ fontSize: 10, color: C.dim, lineHeight: 1.6 }}>
          Results are graded against market closing spreads where available.<br />
          For entertainment and informational purposes only.
        </p>
      </footer>
    </div>
  );
}
