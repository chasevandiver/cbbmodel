import { useState, useEffect, useRef } from "react";
import Results from "./Results.jsx";

// Sample data structure matching the Python model output
const SAMPLE_DATA = {
  generated_at: "2026-02-24T14:30:00",
  date: "20260224",
  total_games: 42,
  model_version: "2.2.0",
  summary: {
    total_games: 42,
    high_confidence: 8,
    medium_confidence: 22,
    low_confidence: 12,
    avg_confidence: 58.3,
    value_plays: 6,
  },
  picks: [
    {
      game_id: "1",
      home_team: "Duke Blue Devils",
      away_team: "North Carolina Tar Heels",
      home_abbr: "DUKE",
      away_abbr: "UNC",
      home_rank: 4,
      away_rank: 12,
      home_record: "23-4",
      away_record: "20-7",
      venue: "Cameron Indoor Stadium",
      neutral_site: false,
      conference_game: true,
      broadcast: "ESPN",
      predicted_spread: -6.2,
      predicted_total: 151.4,
      home_projected_score: 78.8,
      away_projected_score: 72.6,
      home_win_prob: 74.2,
      away_win_prob: 25.8,
      confidence: 82.3,
      pick: "Duke Blue Devils",
      pick_abbr: "DUKE",
      factors: {
        efficiency_margin: 8.4,
        four_factors: 3.2,
        home_court: 3.5,
        recent_form: 1.8,
        turnover_margin: 0.6,
        rebounding: -0.3,
        three_point: 1.1,
        free_throw: 0.4,
        experience: 0.2,
        sos: 0.5,
      },
      market: { spread: -5.5, over_under: 149.5, spread_holder: "Duke" },
      value_rating: 0.7,
      model_vs_market: { spread_edge: -0.7, total_edge: 1.9 },
    },
    {
      game_id: "2",
      home_team: "Houston Cougars",
      away_team: "Kansas Jayhawks",
      home_abbr: "HOU",
      away_abbr: "KU",
      home_rank: 2,
      away_rank: 7,
      home_record: "25-2",
      away_record: "21-6",
      venue: "Fertitta Center",
      neutral_site: false,
      conference_game: true,
      broadcast: "ESPN2",
      predicted_spread: -8.7,
      predicted_total: 133.2,
      home_projected_score: 70.9,
      away_projected_score: 62.3,
      home_win_prob: 81.5,
      away_win_prob: 18.5,
      confidence: 88.1,
      pick: "Houston Cougars",
      pick_abbr: "HOU",
      factors: {
        efficiency_margin: 11.2,
        four_factors: 5.1,
        home_court: 3.5,
        recent_form: 2.4,
        turnover_margin: 1.2,
        rebounding: 1.8,
        three_point: -0.6,
        free_throw: 0.3,
        experience: 0.4,
        sos: 1.1,
      },
      market: { spread: -7, over_under: 131.5, spread_holder: "Houston" },
      value_rating: 1.7,
      model_vs_market: { spread_edge: -1.7, total_edge: 1.7 },
    },
    {
      game_id: "3",
      home_team: "Gonzaga Bulldogs",
      away_team: "Saint Mary's Gaels",
      home_abbr: "GONZ",
      away_abbr: "SMC",
      home_rank: 6,
      away_rank: 22,
      home_record: "24-3",
      away_record: "22-5",
      venue: "McCarthey Athletic Center",
      neutral_site: false,
      conference_game: true,
      broadcast: "ESPN+",
      predicted_spread: -9.1,
      predicted_total: 146.8,
      home_projected_score: 78.0,
      away_projected_score: 68.9,
      home_win_prob: 83.7,
      away_win_prob: 16.3,
      confidence: 76.5,
      pick: "Gonzaga Bulldogs",
      pick_abbr: "GONZ",
      factors: {
        efficiency_margin: 9.8,
        four_factors: 4.3,
        home_court: 4.2,
        recent_form: 0.9,
        turnover_margin: 0.3,
        rebounding: 0.7,
        three_point: 2.1,
        free_throw: 0.6,
        experience: -0.1,
        sos: -0.4,
      },
      market: { spread: -8.5, over_under: 145.5, spread_holder: "Gonzaga" },
      value_rating: 0.6,
      model_vs_market: { spread_edge: -0.6, total_edge: 1.3 },
    },
    {
      game_id: "4",
      home_team: "Iowa State Cyclones",
      away_team: "Texas Tech Red Raiders",
      home_abbr: "ISU",
      away_abbr: "TTU",
      home_rank: 8,
      away_rank: 99,
      home_record: "22-5",
      away_record: "16-11",
      venue: "Hilton Coliseum",
      neutral_site: false,
      conference_game: true,
      broadcast: "ESPN+",
      predicted_spread: -11.3,
      predicted_total: 128.6,
      home_projected_score: 69.9,
      away_projected_score: 58.7,
      home_win_prob: 88.2,
      away_win_prob: 11.8,
      confidence: 71.4,
      pick: "Iowa State Cyclones",
      pick_abbr: "ISU",
      factors: {
        efficiency_margin: 12.1,
        four_factors: 4.8,
        home_court: 4.5,
        recent_form: 1.2,
        turnover_margin: 2.1,
        rebounding: 0.4,
        three_point: -0.2,
        free_throw: -0.1,
        experience: 0.3,
        sos: 0.8,
      },
      market: { spread: -10, over_under: 127.5, spread_holder: "Iowa State" },
      value_rating: 1.3,
      model_vs_market: { spread_edge: -1.3, total_edge: 1.1 },
    },
    {
      game_id: "5",
      home_team: "Auburn Tigers",
      away_team: "Alabama Crimson Tide",
      home_abbr: "AUB",
      away_abbr: "BAMA",
      home_rank: 1,
      away_rank: 5,
      home_record: "26-1",
      away_record: "21-6",
      venue: "Neville Arena",
      neutral_site: false,
      conference_game: true,
      broadcast: "CBS",
      predicted_spread: -4.8,
      predicted_total: 158.2,
      home_projected_score: 81.5,
      away_projected_score: 76.7,
      home_win_prob: 67.1,
      away_win_prob: 32.9,
      confidence: 61.8,
      pick: "Auburn Tigers",
      pick_abbr: "AUB",
      factors: {
        efficiency_margin: 5.3,
        four_factors: 2.1,
        home_court: 3.8,
        recent_form: -1.2,
        turnover_margin: -0.4,
        rebounding: 1.5,
        three_point: 0.8,
        free_throw: 0.7,
        experience: -0.3,
        sos: 1.2,
      },
      market: { spread: -3.5, over_under: 156.5, spread_holder: "Auburn" },
      value_rating: 1.3,
      model_vs_market: { spread_edge: -1.3, total_edge: 1.7 },
    },
    {
      game_id: "6",
      home_team: "Purdue Boilermakers",
      away_team: "Michigan State Spartans",
      home_abbr: "PUR",
      away_abbr: "MSU",
      home_rank: 15,
      away_rank: 10,
      home_record: "19-8",
      away_record: "20-7",
      venue: "Mackey Arena",
      neutral_site: false,
      conference_game: true,
      broadcast: "BTN",
      predicted_spread: 1.4,
      predicted_total: 142.8,
      home_projected_score: 72.1,
      away_projected_score: 70.7,
      home_win_prob: 53.2,
      away_win_prob: 46.8,
      confidence: 32.6,
      pick: "Purdue Boilermakers",
      pick_abbr: "PUR",
      factors: {
        efficiency_margin: -1.2,
        four_factors: 0.3,
        home_court: 3.5,
        recent_form: 0.6,
        turnover_margin: -0.8,
        rebounding: 2.1,
        three_point: -0.9,
        free_throw: 0.2,
        experience: -0.3,
        sos: -0.1,
      },
      market: { spread: 2.5, over_under: 141.5, spread_holder: "Michigan State" },
      value_rating: 3.9,
      model_vs_market: { spread_edge: -1.1, total_edge: 1.3 },
    },
    {
      game_id: "7",
      home_team: "UConn Huskies",
      away_team: "Marquette Golden Eagles",
      home_abbr: "CONN",
      away_abbr: "MARQ",
      home_rank: 3,
      away_rank: 9,
      home_record: "24-3",
      away_record: "21-6",
      venue: "Gampel Pavilion",
      neutral_site: false,
      conference_game: true,
      broadcast: "FOX",
      predicted_spread: -5.4,
      predicted_total: 148.6,
      home_projected_score: 77.0,
      away_projected_score: 71.6,
      home_win_prob: 71.8,
      away_win_prob: 28.2,
      confidence: 68.9,
      pick: "UConn Huskies",
      pick_abbr: "CONN",
      factors: {
        efficiency_margin: 6.7,
        four_factors: 3.8,
        home_court: 3.2,
        recent_form: 0.4,
        turnover_margin: 0.9,
        rebounding: -0.5,
        three_point: 1.6,
        free_throw: 0.8,
        experience: 0.6,
        sos: 0.3,
      },
      market: { spread: -4.5, over_under: 147.5, spread_holder: "UConn" },
      value_rating: 0.9,
      model_vs_market: { spread_edge: -0.9, total_edge: 1.1 },
    },
    {
      game_id: "8",
      home_team: "Tennessee Volunteers",
      away_team: "Kentucky Wildcats",
      home_abbr: "TENN",
      away_abbr: "UK",
      home_rank: 11,
      away_rank: 14,
      home_record: "21-6",
      away_record: "19-8",
      venue: "Thompson-Boling Arena",
      neutral_site: false,
      conference_game: true,
      broadcast: "SEC Network",
      predicted_spread: -7.2,
      predicted_total: 136.4,
      home_projected_score: 71.8,
      away_projected_score: 64.6,
      home_win_prob: 77.3,
      away_win_prob: 22.7,
      confidence: 73.4,
      pick: "Tennessee Volunteers",
      pick_abbr: "TENN",
      factors: {
        efficiency_margin: 7.9,
        four_factors: 3.1,
        home_court: 4.1,
        recent_form: 1.5,
        turnover_margin: 1.8,
        rebounding: 0.9,
        three_point: -1.2,
        free_throw: -0.4,
        experience: 0.5,
        sos: 0.7,
      },
      market: { spread: -6, over_under: 134.5, spread_holder: "Tennessee" },
      value_rating: 1.2,
      model_vs_market: { spread_edge: -1.2, total_edge: 1.9 },
    },
  ],
};

const FACTOR_LABELS = {
  efficiency_margin: "Efficiency",
  four_factors: "Four Factors",
  home_court: "Home Court",
  recent_form: "Recent Form",
  turnover_margin: "Turnovers",
  rebounding: "Rebounding",
  three_point: "3PT Shooting",
  free_throw: "Free Throws",
  experience: "Experience",
  sos: "Strength of Schedule",
};

function ConfidenceMeter({ value }) {
  const color =
    value >= 75
      ? "#22c55e"
      : value >= 55
      ? "#eab308"
      : value >= 40
      ? "#f97316"
      : "#ef4444";
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = (value / 100) * circumference;

  return (
    <div style={{ position: "relative", width: 76, height: 76 }}>
      <svg width="76" height="76" viewBox="0 0 76 76">
        <circle
          cx="38"
          cy="38"
          r={radius}
          fill="none"
          stroke="#1a1a2e"
          strokeWidth="5"
        />
        <circle
          cx="38"
          cy="38"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeDasharray={`${strokeDash} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 38 38)"
          style={{
            transition: "stroke-dasharray 1s ease-out",
            filter: `drop-shadow(0 0 4px ${color}80)`,
          }}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontSize: 18,
            fontWeight: 800,
            color,
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {Math.round(value)}
        </span>
        <span style={{ fontSize: 8, color: "#6b7280", letterSpacing: 1, textTransform: "uppercase" }}>
          conf
        </span>
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
      <span
        style={{
          fontSize: 10,
          color: "#9ca3af",
          width: 90,
          textAlign: "right",
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        {label}
      </span>
      <div
        style={{
          flex: 1,
          height: 6,
          background: "#0d0d1a",
          borderRadius: 3,
          overflow: "hidden",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: isPositive ? "50%" : `${50 - pct / 2}%`,
            width: `${pct / 2}%`,
            height: "100%",
            background: isPositive
              ? "linear-gradient(90deg, #22c55e, #4ade80)"
              : "linear-gradient(90deg, #ef4444, #f87171)",
            borderRadius: 3,
            transition: "all 0.6s ease-out",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: "50%",
            width: 1,
            height: "100%",
            background: "#374151",
          }}
        />
      </div>
      <span
        style={{
          fontSize: 10,
          fontWeight: 700,
          color: isPositive ? "#4ade80" : "#f87171",
          width: 36,
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        {value > 0 ? "+" : ""}
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function formatCT(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      timeZone: "America/Chicago",
      hour12: true,
    }).replace(":00", "").toLowerCase() + " CT";
  } catch {
    return "";
  }
}

function GameCard({ pick, expanded, onToggle, index }) {
  const isHomePick = pick.predicted_spread < 0;
  const spreadAbs = Math.abs(pick.predicted_spread).toFixed(1);

  // Spread display from the PICK's perspective
  // If model picks home (predicted_spread < 0), home is favored: show "DUKE -6.2"
  // If model picks away (predicted_spread > 0), away is favored: show "UNC -6.2"
  // (the away team is covering as favorite, so it's still shown as -X)
  const pickSpreadDisplay = `${pick.pick_abbr} -${spreadAbs}`;

  // Market spread display — from the market favorite's perspective
  const mktSpread = pick.market?.spread;
  const mktHolder = pick.market?.spread_holder;
  const mktOU = pick.market?.over_under;
  let marketDisplay = null;
  if (mktSpread != null && mktHolder) {
    const mktAbs = Math.abs(mktSpread).toFixed(1);
    marketDisplay = `${mktHolder} -${mktAbs}`;
  }

  // Game time in CT
  const gameTime = formatCT(pick.date);

  const confLevel =
    pick.confidence >= 75
      ? "STRONG"
      : pick.confidence >= 55
      ? "LEAN"
      : pick.confidence >= 40
      ? "SLIGHT"
      : "TOSS-UP";
  const confColor =
    pick.confidence >= 75
      ? "#22c55e"
      : pick.confidence >= 55
      ? "#eab308"
      : pick.confidence >= 40
      ? "#f97316"
      : "#ef4444";

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%)",
        border: "1px solid #1e293b",
        borderRadius: 12,
        overflow: "hidden",
        transition: "all 0.3s ease",
        animationDelay: `${index * 60}ms`,
        animation: "fadeSlideIn 0.5s ease-out both",
      }}
    >
      {/* Main row */}
      <div
        onClick={onToggle}
        style={{
          padding: "16px 20px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 16,
          position: "relative",
        }}
      >
        {/* Confidence */}
        <ConfidenceMeter value={pick.confidence} />

        {/* Teams */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            {pick.away_rank <= 25 && (
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  color: "#818cf8",
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                #{pick.away_rank}
              </span>
            )}
            <span
              style={{
                fontSize: 14,
                fontWeight: !isHomePick ? 800 : 500,
                color: !isHomePick ? "#f8fafc" : "#94a3b8",
                textDecoration: !isHomePick ? `underline 2px ${confColor}` : "none",
                textUnderlineOffset: 4,
              }}
            >
              {pick.away_team}
            </span>
            <span style={{ fontSize: 11, color: "#4b5563", fontFamily: "'JetBrains Mono', monospace" }}>
              {pick.away_record}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 10, color: "#6b7280" }}>@</span>
            {pick.home_rank <= 25 && (
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  color: "#818cf8",
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                #{pick.home_rank}
              </span>
            )}
            <span
              style={{
                fontSize: 14,
                fontWeight: isHomePick ? 800 : 500,
                color: isHomePick ? "#f8fafc" : "#94a3b8",
                textDecoration: isHomePick ? `underline 2px ${confColor}` : "none",
                textUnderlineOffset: 4,
              }}
            >
              {pick.home_team}
            </span>
            <span style={{ fontSize: 11, color: "#4b5563", fontFamily: "'JetBrains Mono', monospace" }}>
              {pick.home_record}
            </span>
          </div>
          {/* Time + Market spread at a glance */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            {gameTime && (
              <span style={{
                fontSize: 10,
                color: "#4b5563",
                fontFamily: "'JetBrains Mono', monospace",
              }}>
                🕐 {gameTime}
              </span>
            )}
            {marketDisplay && (
              <span style={{
                fontSize: 10,
                color: "#6b7280",
                fontFamily: "'JetBrains Mono', monospace",
                background: "#0d0d1a",
                padding: "2px 8px",
                borderRadius: 4,
                border: "1px solid #1e293b",
              }}>
                MKT: {marketDisplay}{mktOU ? ` · O/U ${mktOU}` : ""}
              </span>
            )}
          </div>
        </div>

        {/* Pick & Spread */}
        <div style={{ textAlign: "right", minWidth: 110 }}>
          <div
            style={{
              fontSize: 10,
              fontWeight: 800,
              color: confColor,
              letterSpacing: 2,
              marginBottom: 4,
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {confLevel}
          </div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 900,
              color: "#f8fafc",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {pickSpreadDisplay}
          </div>
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>
            O/U {pick.predicted_total}
          </div>
        </div>

        {/* Expand icon */}
        <div
          style={{
            color: "#4b5563",
            transform: expanded ? "rotate(180deg)" : "rotate(0)",
            transition: "transform 0.3s ease",
            fontSize: 18,
          }}
        >
          ▾
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div
          style={{
            borderTop: "1px solid #1e293b",
            padding: "16px 20px",
            background: "#080816",
            animation: "fadeIn 0.3s ease-out",
          }}
        >
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {/* Left: Score projection & market */}
            <div>
              <h4
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  color: "#6b7280",
                  letterSpacing: 2,
                  marginBottom: 12,
                  textTransform: "uppercase",
                }}
              >
                Projection
              </h4>
              <div
                style={{
                  background: "#0d0d1a",
                  borderRadius: 8,
                  padding: 12,
                  display: "flex",
                  justifyContent: "space-around",
                  alignItems: "center",
                  marginBottom: 16,
                }}
              >
                <div style={{ textAlign: "center" }}>
                  <div
                    style={{
                      fontSize: 10,
                      color: "#6b7280",
                      marginBottom: 4,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {pick.away_abbr}
                  </div>
                  <div
                    style={{
                      fontSize: 24,
                      fontWeight: 900,
                      color: !isHomePick ? "#f8fafc" : "#94a3b8",
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {Math.round(pick.away_projected_score)}
                  </div>
                  <div style={{ fontSize: 10, color: "#4b5563" }}>
                    {pick.away_win_prob}%
                  </div>
                </div>
                <div style={{ fontSize: 12, color: "#374151", fontWeight: 600 }}>VS</div>
                <div style={{ textAlign: "center" }}>
                  <div
                    style={{
                      fontSize: 10,
                      color: "#6b7280",
                      marginBottom: 4,
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {pick.home_abbr}
                  </div>
                  <div
                    style={{
                      fontSize: 24,
                      fontWeight: 900,
                      color: isHomePick ? "#f8fafc" : "#94a3b8",
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {Math.round(pick.home_projected_score)}
                  </div>
                  <div style={{ fontSize: 10, color: "#4b5563" }}>
                    {pick.home_win_prob}%
                  </div>
                </div>
              </div>

              {/* Market comparison */}
              {pick.market.spread && (
                <div>
                  <h4
                    style={{
                      fontSize: 10,
                      fontWeight: 800,
                      color: "#6b7280",
                      letterSpacing: 2,
                      marginBottom: 8,
                      textTransform: "uppercase",
                    }}
                  >
                    vs Market
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    <div style={{ background: "#0d0d1a", borderRadius: 6, padding: 8 }}>
                      <div style={{ fontSize: 9, color: "#6b7280", marginBottom: 2 }}>
                        MARKET SPREAD
                      </div>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: "#94a3b8",
                          fontFamily: "'JetBrains Mono', monospace",
                        }}
                      >
                        {pick.market.spread_holder} {pick.market.spread}
                      </div>
                    </div>
                    <div style={{ background: "#0d0d1a", borderRadius: 6, padding: 8 }}>
                      <div style={{ fontSize: 9, color: "#6b7280", marginBottom: 2 }}>
                        MARKET O/U
                      </div>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: "#94a3b8",
                          fontFamily: "'JetBrains Mono', monospace",
                        }}
                      >
                        {pick.market.over_under}
                      </div>
                    </div>
                  </div>
                  {pick.value_rating >= 2 && (
                    <div
                      style={{
                        marginTop: 8,
                        padding: "6px 10px",
                        background: "rgba(34, 197, 94, 0.1)",
                        border: "1px solid rgba(34, 197, 94, 0.3)",
                        borderRadius: 6,
                        fontSize: 11,
                        color: "#4ade80",
                        fontWeight: 700,
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                    >
                      ★ VALUE PLAY — {pick.value_rating} pt edge
                    </div>
                  )}
                </div>
              )}

              {/* Game info */}
              <div style={{ marginTop: 12, fontSize: 10, color: "#4b5563" }}>
                <div>{pick.venue}</div>
                {pick.broadcast && <div>📺 {pick.broadcast}</div>}
                {pick.conference_game && <div>Conference Game</div>}
                {pick.neutral_site && <div>Neutral Site</div>}
              </div>
            </div>

            {/* Right: Factor breakdown */}
            <div>
              <h4
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  color: "#6b7280",
                  letterSpacing: 2,
                  marginBottom: 12,
                  textTransform: "uppercase",
                }}
              >
                Factor Breakdown (+ favors home)
              </h4>
              {Object.entries(pick.factors).map(([key, val]) => (
                <FactorBar
                  key={key}
                  label={FACTOR_LABELS[key] || key}
                  value={val}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState("picks");
  const [data, setData] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("confidence");

  // Route to Results page
  if (page === "results") {
    return <Results onNavigate={setPage} />;
  }

  useEffect(() => {
    fetch(`/picks/latest.json?v=${Date.now()}`)
      .then((r) => {
        if (!r.ok) throw new Error("No picks file yet");
        return r.json();
      })
      .then(setData)
      .catch(() => setData(SAMPLE_DATA)); // fallback to sample data if file missing
  }, []);

  if (!data)
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "#080816",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#6b7280",
        }}
      >
        Loading model...
      </div>
    );

  let filtered = [...data.picks];

  if (filter === "high")
    filtered = filtered.filter((p) => p.confidence >= 70);
  if (filter === "value")
    filtered = filtered.filter((p) => p.value_rating >= 2);
  if (filter === "ranked")
    filtered = filtered.filter(
      (p) => p.home_rank <= 25 || p.away_rank <= 25
    );
  if (filter === "upset")
    filtered = filtered.filter((p) => {
      const fav = p.predicted_spread < 0 ? "home" : "away";
      const marketFav = p.market?.spread < 0 ? "away" : "home"; // simplified
      return fav !== marketFav;
    });

  if (searchTerm) {
    const term = searchTerm.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.home_team.toLowerCase().includes(term) ||
        p.away_team.toLowerCase().includes(term) ||
        p.home_abbr.toLowerCase().includes(term) ||
        p.away_abbr.toLowerCase().includes(term)
    );
  }

  if (sortBy === "confidence")
    filtered.sort((a, b) => b.confidence - a.confidence);
  if (sortBy === "spread")
    filtered.sort(
      (a, b) => Math.abs(b.predicted_spread) - Math.abs(a.predicted_spread)
    );
  if (sortBy === "value")
    filtered.sort((a, b) => (b.value_rating || 0) - (a.value_rating || 0));
  if (sortBy === "total")
    filtered.sort((a, b) => b.predicted_total - a.predicted_total);
  if (sortBy === "time")
    filtered.sort((a, b) => new Date(a.date || 0) - new Date(b.date || 0));

  const displayDate = (() => {
    const d = data.date;
    if (!d) return new Date().toLocaleDateString("en-US", {
      weekday: "long", month: "long", day: "numeric", year: "numeric",
    });
    const year = d.slice(0, 4);
    const month = d.slice(4, 6);
    const day = d.slice(6, 8);
    const dt = new Date(year, month - 1, day);
    return dt.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  })();

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#080816",
        color: "#f8fafc",
        fontFamily:
          "'Satoshi', 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder { color: #4b5563; }
      `}</style>

      {/* Header */}
      <header
        style={{
          padding: "32px 24px 24px",
          maxWidth: 900,
          margin: "0 auto",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "#22c55e",
                animation: "pulse 2s ease-in-out infinite",
                boxShadow: "0 0 8px #22c55e80",
              }}
            />
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                color: "#22c55e",
                letterSpacing: 3,
                textTransform: "uppercase",
                fontFamily: "'JetBrains Mono', monospace",
              }}
            >
              MODEL v{data.model_version} • LIVE
            </span>
          </div>
          <button
            onClick={() => setPage("results")}
            style={{
              background: "transparent",
              border: "1px solid #1e293b",
              borderRadius: 20,
              padding: "6px 16px",
              color: "#6b7280",
              fontSize: 11,
              fontWeight: 700,
              cursor: "pointer",
              letterSpacing: 0.5,
              fontFamily: "'JetBrains Mono', monospace",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={e => { e.target.style.borderColor = "#818cf8"; e.target.style.color = "#a5b4fc"; }}
            onMouseLeave={e => { e.target.style.borderColor = "#1e293b"; e.target.style.color = "#6b7280"; }}
          >
            RESULTS →
          </button>
        </div>
        <h1
          style={{
            fontSize: 32,
            fontWeight: 900,
            letterSpacing: -1,
            marginBottom: 4,
            background: "linear-gradient(135deg, #f8fafc, #818cf8)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          COURTSIDE EDGE
        </h1>
        <p style={{ fontSize: 13, color: "#6b7280" }}>
          {displayDate} — {data.total_games} games analyzed
        </p>

        {/* Stats bar */}
        <div
          style={{
            display: "flex",
            gap: 16,
            marginTop: 20,
            flexWrap: "wrap",
          }}
        >
          {[
            { label: "GAMES", value: data.summary.total_games, color: "#818cf8" },
            { label: "HIGH CONF", value: data.summary.high_confidence, color: "#22c55e" },
            { label: "VALUE PLAYS", value: data.summary.value_plays, color: "#eab308" },
            {
              label: "AVG CONF",
              value: `${data.summary.avg_confidence}%`,
              color: "#f97316",
            },
          ].map((s, i) => (
            <div
              key={i}
              style={{
                background: "#0f0f23",
                border: "1px solid #1e293b",
                borderRadius: 8,
                padding: "10px 16px",
                minWidth: 100,
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  color: "#4b5563",
                  letterSpacing: 2,
                  fontFamily: "'JetBrains Mono', monospace",
                  marginBottom: 4,
                }}
              >
                {s.label}
              </div>
              <div
                style={{
                  fontSize: 22,
                  fontWeight: 900,
                  color: s.color,
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {s.value}
              </div>
            </div>
          ))}
        </div>
      </header>

      {/* Controls */}
      <div
        style={{
          maxWidth: 900,
          margin: "0 auto",
          padding: "0 24px 16px",
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {/* Search */}
        <input
          type="text"
          placeholder="Search teams..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            background: "#0f0f23",
            border: "1px solid #1e293b",
            borderRadius: 8,
            padding: "8px 14px",
            color: "#f8fafc",
            fontSize: 13,
            outline: "none",
            width: 180,
            fontFamily: "'DM Sans', sans-serif",
          }}
        />

        {/* Filter pills */}
        <div style={{ display: "flex", gap: 6 }}>
          {[
            { key: "all", label: "All" },
            { key: "high", label: "High Conf" },
            { key: "value", label: "Value" },
            { key: "ranked", label: "Ranked" },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              style={{
                background: filter === f.key ? "#818cf830" : "transparent",
                border: `1px solid ${filter === f.key ? "#818cf8" : "#1e293b"}`,
                borderRadius: 20,
                padding: "6px 14px",
                color: filter === f.key ? "#a5b4fc" : "#6b7280",
                fontSize: 11,
                fontWeight: 700,
                cursor: "pointer",
                letterSpacing: 0.5,
                fontFamily: "'JetBrains Mono', monospace",
                transition: "all 0.2s ease",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              fontSize: 10,
              color: "#4b5563",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            SORT:
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              background: "#0f0f23",
              border: "1px solid #1e293b",
              borderRadius: 6,
              padding: "6px 10px",
              color: "#94a3b8",
              fontSize: 11,
              outline: "none",
              cursor: "pointer",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            <option value="confidence">Confidence</option>
            <option value="time">Tip-off Time</option>
            <option value="spread">Spread</option>
            <option value="value">Value</option>
            <option value="total">Total</option>
          </select>
        </div>
      </div>

      {/* Game cards */}
      <div
        style={{
          maxWidth: 900,
          margin: "0 auto",
          padding: "0 24px 48px",
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        {filtered.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: 48,
              color: "#4b5563",
              fontSize: 14,
            }}
          >
            No games match your filters
          </div>
        ) : (
          filtered.map((pick, i) => (
            <GameCard
              key={pick.game_id}
              pick={pick}
              index={i}
              expanded={expandedId === pick.game_id}
              onToggle={() =>
                setExpandedId(expandedId === pick.game_id ? null : pick.game_id)
              }
            />
          ))
        )}
      </div>

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid #1e293b",
          padding: "20px 24px",
          textAlign: "center",
          maxWidth: 900,
          margin: "0 auto",
        }}
      >
        <p style={{ fontSize: 10, color: "#374151", lineHeight: 1.6 }}>
          Model predictions are for entertainment and informational purposes only.
          <br />
          Generated at{" "}
          {new Date(data.generated_at).toLocaleString()} • v{data.model_version}
        </p>
      </footer>
    </div>
  );
}
