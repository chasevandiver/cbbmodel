import { useState, useEffect, useRef } from "react";
import Results from "./Results.jsx";

const SAMPLE_DATA = {
  generated_at: "2026-02-24T14:30:00",
  date: "20260224",
  total_games: 3,
  model_version: "2.3.0",
  summary: { total_games: 3, high_confidence: 1, medium_confidence: 2, low_confidence: 0, avg_confidence: 71.2, value_plays: 1 },
  picks: [
    {
      game_id: "1", date: "2026-02-24T19:00:00Z",
      home_team: "Duke Blue Devils", away_team: "North Carolina Tar Heels",
      home_abbr: "DUKE", away_abbr: "UNC", home_rank: 4, away_rank: 12,
      home_record: "23-4", away_record: "20-7", venue: "Cameron Indoor Stadium",
      neutral_site: false, conference_game: true, broadcast: "ESPN",
      predicted_spread: -6.2, predicted_total: 151.4,
      home_projected_score: 78.8, away_projected_score: 72.6,
      home_win_prob: 74.2, away_win_prob: 25.8, confidence: 82.3,
      pick: "Duke Blue Devils", pick_abbr: "DUKE",
      factors: { efficiency_margin: 3.8, four_factors: 1.6, home_court: 5.0, recent_form: 1.2, turnover_margin: 0.4, rebounding: -0.2, three_point: 0.7, free_throw: 0.3, experience: 0.2, sos: 0.4 },
      market: { spread: -5.5, over_under: 149.5, spread_holder: "Duke Blue Devils" },
      value_rating: 0.7, model_vs_market: { spread_edge: -0.7, total_edge: 1.9 },
    },
    {
      game_id: "2", date: "2026-02-24T21:00:00Z",
      home_team: "Houston Cougars", away_team: "Kansas Jayhawks",
      home_abbr: "HOU", away_abbr: "KU", home_rank: 2, away_rank: 7,
      home_record: "25-2", away_record: "21-6", venue: "Fertitta Center",
      neutral_site: false, conference_game: true, broadcast: "ESPN2",
      predicted_spread: -8.7, predicted_total: 133.2,
      home_projected_score: 70.9, away_projected_score: 62.3,
      home_win_prob: 81.5, away_win_prob: 18.5, confidence: 88.1,
      pick: "Houston Cougars", pick_abbr: "HOU",
      factors: { efficiency_margin: 5.2, four_factors: 2.1, home_court: 4.5, recent_form: 0.8, turnover_margin: 0.9, rebounding: 0.6, three_point: -0.3, free_throw: 0.5, experience: -0.1, sos: 0.8 },
      market: { spread: -7, over_under: 131.5, spread_holder: "Houston Cougars" },
      value_rating: 3.2, model_vs_market: { spread_edge: -1.7, total_edge: 1.7 },
    },
    {
      game_id: "3", date: "2026-02-24T23:00:00Z",
      home_team: "Iowa State Cyclones", away_team: "Texas Tech Red Raiders",
      home_abbr: "ISU", away_abbr: "TTU", home_rank: 8, away_rank: 99,
      home_record: "22-5", away_record: "16-11", venue: "Hilton Coliseum",
      neutral_site: false, conference_game: true, broadcast: "ESPN+",
      predicted_spread: -11.3, predicted_total: 128.6,
      home_projected_score: 69.9, away_projected_score: 58.7,
      home_win_prob: 88.2, away_win_prob: 11.8, confidence: 63.4,
      pick: "Iowa State Cyclones", pick_abbr: "ISU",
      factors: { efficiency_margin: 8.1, four_factors: 1.4, home_court: 3.5, recent_form: -1.2, turnover_margin: 0.3, rebounding: 1.5, three_point: 0.8, free_throw: 0.7, experience: -0.3, sos: 1.2 },
      market: { spread: -10, over_under: 126.5, spread_holder: "Iowa State Cyclones" },
      value_rating: 1.3, model_vs_market: { spread_edge: -1.3, total_edge: 2.1 },
    },
  ],
};

const FACTOR_LABELS = {
  efficiency_margin: "Efficiency",
  four_factors:      "Four Factors",
  home_court:        "Home Court",
  recent_form:       "Recent Form",
  turnover_margin:   "Turnovers",
  rebounding:        "Rebounding",
  three_point:       "3PT Shooting",
  free_throw:        "Free Throws",
  experience:        "Experience",
  sos:               "SOS Diff",
};

function ConfidenceMeter({ value }) {
  const color = value >= 75 ? "#22c55e" : value >= 55 ? "#eab308" : value >= 40 ? "#f97316" : "#ef4444";
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = (value / 100) * circumference;
  return (
    <div style={{ position: "relative", width: 76, height: 76 }}>
      <svg width="76" height="76" viewBox="0 0 76 76">
        <circle cx="38" cy="38" r={radius} fill="none" stroke="#1a1a2e" strokeWidth="5" />
        <circle cx="38" cy="38" r={radius} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={`${strokeDash} ${circumference}`} strokeLinecap="round"
          transform="rotate(-90 38 38)"
          style={{ transition: "stroke-dasharray 1s ease-out", filter: `drop-shadow(0 0 4px ${color}80)` }}
        />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontSize: 18, fontWeight: 800, color, fontFamily: "'JetBrains Mono', monospace" }}>{Math.round(value)}</span>
        <span style={{ fontSize: 8, color: "#6b7280", letterSpacing: 1, textTransform: "uppercase" }}>conf</span>
      </div>
    </div>
  );
}

function FactorBar({ label, value }) {
  const maxVal = 12;
  const pct = Math.min(Math.abs(value) / maxVal, 1) * 100;
  const isPositive = value >= 0;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
      <span style={{ fontSize: 10, color: "#9ca3af", width: 90, textAlign: "right", fontFamily: "'JetBrains Mono', monospace" }}>{label}</span>
      <div style={{ flex: 1, height: 6, background: "#0d0d1a", borderRadius: 3, overflow: "hidden", position: "relative" }}>
        <div style={{
          position: "absolute", left: isPositive ? "50%" : `${50 - pct / 2}%`,
          width: `${pct / 2}%`, height: "100%",
          background: isPositive ? "linear-gradient(90deg, #22c55e, #4ade80)" : "linear-gradient(90deg, #ef4444, #f87171)",
          borderRadius: 3, transition: "all 0.6s ease-out",
        }} />
        <div style={{ position: "absolute", left: "50%", width: 1, height: "100%", background: "#374151" }} />
      </div>
      <span style={{ fontSize: 10, fontWeight: 700, color: isPositive ? "#4ade80" : "#f87171", width: 36, fontFamily: "'JetBrains Mono', monospace" }}>
        {value > 0 ? "+" : ""}{value.toFixed(1)}
      </span>
    </div>
  );
}

function GameCard({ pick, expanded, onToggle, index }) {
  const spreadAbs = Math.abs(pick.predicted_spread).toFixed(1);
  const isHomePick = pick.pick === pick.home_team;
  const isAwayPick = pick.pick === pick.away_team;

  const confLevel = pick.confidence >= 75 ? "STRONG" : pick.confidence >= 55 ? "LEAN" : pick.confidence >= 40 ? "SLIGHT" : "TOSS-UP";
  const confColor = pick.confidence >= 75 ? "#22c55e" : pick.confidence >= 55 ? "#eab308" : pick.confidence >= 40 ? "#f97316" : "#ef4444";

  // Market spread is always stored from HOME team perspective:
  //   negative = home favored (e.g. -7 means home wins by 7)
  //   positive = away favored (e.g. +7 means away wins by 7, home is dog)
  // predicted_spread is also home-perspective (positive = home wins)
  const mkt = pick.market || {};
  let atsLabel = null;
  let marketDisplayStr = null;

  if (mkt.spread != null) {
    const mktHomeSpread = parseFloat(mkt.spread); // home perspective
    // Display: show as "{favorite} -{amount}"
    if (mktHomeSpread < 0) {
      // Home is favored
      marketDisplayStr = `${pick.home_team} ${mktHomeSpread.toFixed(1)}`;
    } else {
      // Away is favored
      marketDisplayStr = `${pick.away_team} -${mktHomeSpread.toFixed(1)}`;
    }

    // ATS: compare model (predicted_spread) vs market (mktHomeSpread), both home-perspective
    const edge = pick.predicted_spread - mktHomeSpread;
    if (edge > 0.5) {
      // Model likes home MORE than market → bet home
      const homeSpread = mktHomeSpread.toFixed(1);
      atsLabel = `${pick.home_abbr} ${mktHomeSpread >= 0 ? "+" : ""}${homeSpread}`;
    } else if (edge < -0.5) {
      // Model likes away MORE than market → bet away
      const awaySpread = (-mktHomeSpread).toFixed(1);
      atsLabel = `${pick.away_abbr} ${parseFloat(awaySpread) >= 0 ? "+" : ""}${awaySpread}`;
    }
  }

  // Tipoff time in CT
  let tipoff = "";
  if (pick.date) {
    try {
      tipoff = new Date(pick.date).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/Chicago", timeZoneName: "short" });
    } catch {}
  }

  return (
    <div style={{ background: "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)", border: "1px solid #1e293b", borderRadius: 12, overflow: "hidden", transition: "all 0.3s ease", animationDelay: `${index * 60}ms`, animation: "fadeSlideIn 0.5s ease-out both" }}>
      {/* Main row */}
      <div onClick={onToggle} style={{ padding: "16px 20px", cursor: "pointer", display: "flex", alignItems: "center", gap: 16 }}>
        <ConfidenceMeter value={pick.confidence} />

        {/* Teams */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Away */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            {pick.away_rank <= 25 && <span style={{ fontSize: 10, fontWeight: 800, color: "#818cf8", fontFamily: "'JetBrains Mono', monospace" }}>#{pick.away_rank}</span>}
            <span style={{ fontSize: 14, fontWeight: isAwayPick ? 800 : 500, color: isAwayPick ? "#f8fafc" : "#94a3b8", textDecoration: isAwayPick ? `underline 2px ${confColor}` : "none", textUnderlineOffset: 4 }}>
              {pick.away_team}
            </span>
            <span style={{ fontSize: 11, color: "#4b5563", fontFamily: "'JetBrains Mono', monospace" }}>{pick.away_record}</span>
          </div>
          {/* Home */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: "#6b7280" }}>@</span>
            {pick.home_rank <= 25 && <span style={{ fontSize: 10, fontWeight: 800, color: "#818cf8", fontFamily: "'JetBrains Mono', monospace" }}>#{pick.home_rank}</span>}
            <span style={{ fontSize: 14, fontWeight: isHomePick ? 800 : 500, color: isHomePick ? "#f8fafc" : "#94a3b8", textDecoration: isHomePick ? `underline 2px ${confColor}` : "none", textUnderlineOffset: 4 }}>
              {pick.home_team}
            </span>
            <span style={{ fontSize: 11, color: "#4b5563", fontFamily: "'JetBrains Mono', monospace" }}>{pick.home_record}</span>
          </div>
          {/* Tipoff + broadcast */}
          {(tipoff || pick.broadcast) && (
            <div style={{ fontSize: 10, color: "#4b5563", marginTop: 5, fontFamily: "'JetBrains Mono', monospace" }}>
              {tipoff}{pick.broadcast ? ` · ${pick.broadcast}` : ""}
            </div>
          )}
        </div>

        {/* Pick & spread */}
        <div style={{ textAlign: "right", minWidth: 120 }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: confColor, letterSpacing: 2, marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>{confLevel}</div>
          <div style={{ fontSize: 16, fontWeight: 900, color: "#f8fafc", fontFamily: "'JetBrains Mono', monospace" }}>
            {pick.pick_abbr} {isHomePick ? "-" : "+"}{spreadAbs}
          </div>
          {atsLabel && (
            <div style={{ fontSize: 11, color: "#818cf8", fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", marginTop: 1 }}>
              BET: {atsLabel}
            </div>
          )}
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>O/U {pick.predicted_total}</div>
        </div>

        <div style={{ color: "#4b5563", transform: expanded ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.3s ease", fontSize: 18 }}>▾</div>
      </div>

      {/* Expanded */}
      {expanded && (
        <div style={{ borderTop: "1px solid #1e293b", padding: "16px 20px", background: "#080816", animation: "fadeIn 0.3s ease-out" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {/* Left */}
            <div>
              <h4 style={{ fontSize: 10, fontWeight: 800, color: "#6b7280", letterSpacing: 2, marginBottom: 12, textTransform: "uppercase" }}>Projection</h4>
              <div style={{ background: "#0d0d1a", borderRadius: 8, padding: 12, display: "flex", justifyContent: "space-around", alignItems: "center", marginBottom: 16 }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: "#6b7280", marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>{pick.away_abbr}</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: isAwayPick ? "#f8fafc" : "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>{Math.round(pick.away_projected_score)}</div>
                  <div style={{ fontSize: 10, color: "#4b5563" }}>{pick.away_win_prob}%</div>
                </div>
                <div style={{ fontSize: 12, color: "#374151", fontWeight: 600 }}>VS</div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: "#6b7280", marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>{pick.home_abbr}</div>
                  <div style={{ fontSize: 24, fontWeight: 900, color: isHomePick ? "#f8fafc" : "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>{Math.round(pick.home_projected_score)}</div>
                  <div style={{ fontSize: 10, color: "#4b5563" }}>{pick.home_win_prob}%</div>
                </div>
              </div>

              {mkt.spread != null && (
                <div>
                  <h4 style={{ fontSize: 10, fontWeight: 800, color: "#6b7280", letterSpacing: 2, marginBottom: 8, textTransform: "uppercase" }}>vs Market</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    <div style={{ background: "#0d0d1a", borderRadius: 6, padding: 8 }}>
                      <div style={{ fontSize: 9, color: "#6b7280", marginBottom: 2 }}>MARKET SPREAD</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>
                        {marketDisplayStr}
                      </div>
                    </div>
                    <div style={{ background: "#0d0d1a", borderRadius: 6, padding: 8 }}>
                      <div style={{ fontSize: 9, color: "#6b7280", marginBottom: 2 }}>MARKET O/U</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>{mkt.over_under}</div>
                    </div>
                  </div>
                  {atsLabel && (
                    <div style={{ marginTop: 8, padding: "6px 10px", background: "rgba(129,140,248,0.1)", border: "1px solid rgba(129,140,248,0.3)", borderRadius: 6, fontSize: 11, color: "#a5b4fc", fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                      ★ BET: {atsLabel} (model {pick.predicted_spread > 0 ? "+" : ""}{pick.predicted_spread.toFixed(1)} vs market {parseFloat(mkt.spread) > 0 ? "+" : ""}{parseFloat(mkt.spread).toFixed(1)})
                    </div>
                  )}
                </div>
              )}

              <div style={{ marginTop: 12, fontSize: 10, color: "#4b5563" }}>
                <div>{pick.venue}</div>
                {pick.broadcast && <div>📺 {pick.broadcast}</div>}
                {pick.conference_game && <div>Conference Game</div>}
                {pick.neutral_site && <div>Neutral Site</div>}
              </div>
            </div>

            {/* Right: factors */}
            <div>
              <h4 style={{ fontSize: 10, fontWeight: 800, color: "#6b7280", letterSpacing: 2, marginBottom: 12, textTransform: "uppercase" }}>Factor Breakdown (+ favors home)</h4>
              {pick.factors && Object.entries(pick.factors).map(([key, val]) => (
                <FactorBar key={key} label={FACTOR_LABELS[key] || key} value={val} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState("picks");
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("tipoff");

  useEffect(() => {
    fetch("/latest.json")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setData)
      .catch(() => setData(SAMPLE_DATA));
  }, []);

  if (!data) return (
    <div style={{ minHeight: "100vh", background: "#080816", display: "flex", alignItems: "center", justifyContent: "center", color: "#6b7280" }}>
      Loading model...
    </div>
  );

  let filtered = [...data.picks];
  if (filter === "high") filtered = filtered.filter((p) => p.confidence >= 70);
  if (filter === "value") filtered = filtered.filter((p) => p.value_rating >= 2);
  if (filter === "ranked") filtered = filtered.filter((p) => p.home_rank <= 25 || p.away_rank <= 25);

  if (searchTerm) {
    const term = searchTerm.toLowerCase();
    filtered = filtered.filter((p) =>
      p.home_team.toLowerCase().includes(term) || p.away_team.toLowerCase().includes(term) ||
      p.home_abbr.toLowerCase().includes(term) || p.away_abbr.toLowerCase().includes(term)
    );
  }

  if (sortBy === "tipoff") filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
  if (sortBy === "confidence") filtered.sort((a, b) => b.confidence - a.confidence);
  if (sortBy === "spread") filtered.sort((a, b) => Math.abs(b.predicted_spread) - Math.abs(a.predicted_spread));
  if (sortBy === "value") filtered.sort((a, b) => (b.value_rating || 0) - (a.value_rating || 0));
  if (sortBy === "total") filtered.sort((a, b) => b.predicted_total - a.predicted_total);

  const displayDate = (() => {
    const d = data.date;
    const dt = new Date(d.slice(0,4), d.slice(4,6)-1, d.slice(6,8));
    return dt.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  })();

  return (
    <div style={{ minHeight: "100vh", background: "#080816", color: "#f8fafc", fontFamily: "'Satoshi', 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
        @keyframes fadeSlideIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder { color: #4b5563; }
      `}</style>

      {/* Header */}
      <header style={{ padding: "32px 24px 24px", maxWidth: 900, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", animation: "pulse 2s ease-in-out infinite", boxShadow: "0 0 8px #22c55e80" }} />
          <span style={{ fontSize: 10, fontWeight: 700, color: "#22c55e", letterSpacing: 3, textTransform: "uppercase", fontFamily: "'JetBrains Mono', monospace" }}>
            MODEL v{data.model_version} • LIVE
          </span>
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 900, letterSpacing: -1, marginBottom: 4, background: "linear-gradient(135deg, #f8fafc, #818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          COURTSIDE EDGE
        </h1>
        <p style={{ fontSize: 13, color: "#6b7280" }}>{displayDate} — {data.total_games} games analyzed</p>

        {/* Stats bar */}
        <div style={{ display: "flex", gap: 16, marginTop: 20, flexWrap: "wrap" }}>
          {[
            { label: "GAMES", value: data.summary?.total_games ?? data.total_games, color: "#818cf8" },
            { label: "HIGH CONF", value: data.summary?.high_confidence ?? 0, color: "#22c55e" },
            { label: "VALUE PLAYS", value: data.summary?.value_plays ?? 0, color: "#eab308" },
            { label: "AVG CONF", value: `${data.summary?.avg_confidence ?? 0}%`, color: "#f97316" },
          ].map((s, i) => (
            <div key={i} style={{ background: "#0f0f23", border: "1px solid #1e293b", borderRadius: 8, padding: "10px 16px", minWidth: 100 }}>
              <div style={{ fontSize: 9, color: "#4b5563", letterSpacing: 2, fontFamily: "'JetBrains Mono', monospace", marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 22, fontWeight: 900, color: s.color, fontFamily: "'JetBrains Mono', monospace" }}>{s.value}</div>
            </div>
          ))}
        </div>
      </header>

      {/* Tab Nav */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 24px 0", display: "flex", gap: 4, borderBottom: "1px solid #1e293b" }}>
        {[{ key: "picks", label: "Today's Picks" }, { key: "results", label: "Results" }].map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} style={{
            background: "none", border: "none", cursor: "pointer", padding: "10px 20px",
            fontSize: 11, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase",
            fontFamily: "'JetBrains Mono', monospace",
            color: activeTab === tab.key ? "#818cf8" : "#4b5563",
            borderBottom: activeTab === tab.key ? "2px solid #818cf8" : "2px solid transparent",
            marginBottom: -1, transition: "all 0.2s ease",
          }}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Results Tab */}
      {activeTab === "results" && <Results />}

      {/* Picks Tab */}
      {activeTab === "picks" && <>
        {/* Controls */}
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "16px 24px", display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <input type="text" placeholder="Search teams..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: "#0f0f23", border: "1px solid #1e293b", borderRadius: 8, padding: "8px 14px", color: "#f8fafc", fontSize: 13, outline: "none", width: 180, fontFamily: "'DM Sans', sans-serif" }}
          />
          <div style={{ display: "flex", gap: 6 }}>
            {[{ key: "all", label: "All" }, { key: "high", label: "High Conf" }, { key: "value", label: "Value" }, { key: "ranked", label: "Ranked" }].map((f) => (
              <button key={f.key} onClick={() => setFilter(f.key)} style={{
                background: filter === f.key ? "#818cf830" : "transparent",
                border: `1px solid ${filter === f.key ? "#818cf8" : "#1e293b"}`,
                borderRadius: 20, padding: "6px 14px",
                color: filter === f.key ? "#a5b4fc" : "#6b7280",
                fontSize: 11, fontWeight: 700, cursor: "pointer", letterSpacing: 0.5,
                fontFamily: "'JetBrains Mono', monospace", transition: "all 0.2s ease",
              }}>
                {f.label}
              </button>
            ))}
          </div>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: "#4b5563", fontFamily: "'JetBrains Mono', monospace" }}>SORT:</span>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={{ background: "#0f0f23", border: "1px solid #1e293b", borderRadius: 6, padding: "6px 10px", color: "#94a3b8", fontSize: 11, outline: "none", cursor: "pointer", fontFamily: "'JetBrains Mono', monospace" }}>
              <option value="tipoff">Tipoff Time</option>
              <option value="confidence">Confidence</option>
              <option value="spread">Spread</option>
              <option value="value">Value</option>
              <option value="total">Total</option>
            </select>
          </div>
        </div>

        {/* Game cards */}
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 24px 48px", display: "flex", flexDirection: "column", gap: 8 }}>
          {filtered.length === 0 ? (
            <div style={{ textAlign: "center", padding: 48, color: "#4b5563", fontSize: 14 }}>No games match your filters</div>
          ) : (
            filtered.map((pick, i) => (
              <GameCard key={pick.game_id} pick={pick} index={i} expanded={expandedId === pick.game_id}
                onToggle={() => setExpandedId(expandedId === pick.game_id ? null : pick.game_id)}
              />
            ))
          )}
        </div>

        <footer style={{ borderTop: "1px solid #1e293b", padding: "20px 24px", textAlign: "center", maxWidth: 900, margin: "0 auto" }}>
          <p style={{ fontSize: 10, color: "#374151", lineHeight: 1.6 }}>
            Model predictions are for entertainment and informational purposes only.<br />
            Generated at {new Date(data.generated_at).toLocaleString()} • v{data.model_version}
          </p>
        </footer>
      </>}
    </div>
  );
}
