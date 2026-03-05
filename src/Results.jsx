import { useState, useEffect, useMemo } from "react";

// ─── Team → Conference lookup (2025-26 season) ────────────────────────────
const TEAM_CONFERENCE = {
  // ACC
  "Boston College Eagles": "ACC", "California Golden Bears": "ACC",
  "Clemson Tigers": "ACC", "Duke Blue Devils": "ACC",
  "Florida State Seminoles": "ACC", "Georgia Tech Yellow Jackets": "ACC",
  "Louisville Cardinals": "ACC", "Miami Hurricanes": "ACC",
  "North Carolina Tar Heels": "ACC", "Pittsburgh Panthers": "ACC",
  "SMU Mustangs": "ACC", "Stanford Cardinal": "ACC",
  "Syracuse Orange": "ACC", "Virginia Cavaliers": "ACC",
  "Virginia Tech Hokies": "ACC", "Wake Forest Demon Deacons": "ACC",
  // Big 12
  "Arizona State Sun Devils": "Big 12", "Arizona Wildcats": "Big 12",
  "BYU Cougars": "Big 12", "Baylor Bears": "Big 12",
  "Colorado Buffaloes": "Big 12", "Houston Cougars": "Big 12",
  "Iowa State Cyclones": "Big 12", "Kansas Jayhawks": "Big 12",
  "Kansas State Wildcats": "Big 12", "Oklahoma State Cowboys": "Big 12",
  "TCU Horned Frogs": "Big 12", "Texas Tech Red Raiders": "Big 12",
  "UCF Knights": "Big 12", "Utah Utes": "Big 12",
  "West Virginia Mountaineers": "Big 12",
  // Big Ten
  "Illinois Fighting Illini": "Big Ten", "Indiana Hoosiers": "Big Ten",
  "Maryland Terrapins": "Big Ten", "Michigan State Spartans": "Big Ten",
  "Michigan Wolverines": "Big Ten", "Minnesota Golden Gophers": "Big Ten",
  "Nebraska Cornhuskers": "Big Ten", "Northwestern Wildcats": "Big Ten",
  "Oregon Ducks": "Big Ten", "Purdue Boilermakers": "Big Ten",
  "Rutgers Scarlet Knights": "Big Ten", "UCLA Bruins": "Big Ten",
  "USC Trojans": "Big Ten", "Washington Huskies": "Big Ten",
  "Wisconsin Badgers": "Big Ten",
  // SEC
  "Alabama Crimson Tide": "SEC", "Arkansas Razorbacks": "SEC",
  "Auburn Tigers": "SEC", "Florida Gators": "SEC",
  "Georgia Bulldogs": "SEC", "Kentucky Wildcats": "SEC",
  "LSU Tigers": "SEC", "Mississippi State Bulldogs": "SEC",
  "Missouri Tigers": "SEC", "Oklahoma Sooners": "SEC",
  "South Carolina Gamecocks": "SEC", "Tennessee Volunteers": "SEC",
  "Texas Longhorns": "SEC", "Texas A&M Aggies": "SEC",
  "Vanderbilt Commodores": "SEC",
  // Big East
  "Butler Bulldogs": "Big East", "Creighton Bluejays": "Big East",
  "DePaul Blue Demons": "Big East", "Georgetown Hoyas": "Big East",
  "Marquette Golden Eagles": "Big East", "Providence Friars": "Big East",
  "Seton Hall Pirates": "Big East", "St. John's Red Storm": "Big East",
  "UConn Huskies": "Big East", "Villanova Wildcats": "Big East",
  "Xavier Musketeers": "Big East",
  // Mountain West
  "Air Force Falcons": "Mountain West", "Colorado State Rams": "Mountain West",
  "Nevada Wolf Pack": "Mountain West", "New Mexico Lobos": "Mountain West",
  "San Diego State Aztecs": "Mountain West", "San José State Spartans": "Mountain West",
  "Wyoming Cowboys": "Mountain West", "Fresno State Bulldogs": "Mountain West",
  "Boise State Broncos": "Mountain West", "UNLV Rebels": "Mountain West",
  "Utah State Aggies": "Mountain West", "New Mexico State Aggies": "Mountain West",
  // American (AAC)
  "Charlotte 49ers": "AAC", "East Carolina Pirates": "AAC",
  "Florida Atlantic Owls": "AAC", "Memphis Tigers": "AAC",
  "North Texas Mean Green": "AAC", "Rice Owls": "AAC",
  "South Florida Bulls": "AAC", "Temple Owls": "AAC",
  "Tulane Green Wave": "AAC", "UTSA Roadrunners": "AAC",
  "Wichita State Shockers": "AAC",
  // Atlantic 10
  "Dayton Flyers": "Atlantic 10", "Davidson Wildcats": "Atlantic 10",
  "Duquesne Dukes": "Atlantic 10", "Fordham Rams": "Atlantic 10",
  "George Mason Patriots": "Atlantic 10", "George Washington Revolutionaries": "Atlantic 10",
  "La Salle Explorers": "Atlantic 10", "Loyola Chicago Ramblers": "Atlantic 10",
  "Massachusetts Minutemen": "Atlantic 10", "Rhode Island Rams": "Atlantic 10",
  "Richmond Spiders": "Atlantic 10", "Saint Joseph's Hawks": "Atlantic 10",
  "Saint Louis Billikens": "Atlantic 10", "St. Bonaventure Bonnies": "Atlantic 10",
  "VCU Rams": "Atlantic 10",
  // WCC
  "Gonzaga Bulldogs": "WCC", "Loyola Marymount Lions": "WCC",
  "Pacific Tigers": "WCC", "Pepperdine Waves": "WCC",
  "Portland Pilots": "WCC", "Saint Mary's Gaels": "WCC",
  "San Diego Toreros": "WCC", "San Francisco Dons": "WCC",
  "Santa Clara Broncos": "WCC", "Seattle U Redhawks": "WCC",
  // Missouri Valley
  "Drake Bulldogs": "Missouri Valley", "Evansville Purple Aces": "Missouri Valley",
  "Illinois State Redbirds": "Missouri Valley", "Indiana State Sycamores": "Missouri Valley",
  "Missouri State Bears": "Missouri Valley", "Northern Iowa Panthers": "Missouri Valley",
  "Southern Illinois Salukis": "Missouri Valley", "Valparaiso Beacons": "Missouri Valley",
  "Western Illinois Leathernecks": "Missouri Valley",
  // CAA
  "Charleston Cougars": "CAA", "Delaware Blue Hens": "CAA",
  "Drexel Dragons": "CAA", "Hofstra Pride": "CAA",
  "James Madison Dukes": "CAA", "Monmouth Hawks": "CAA",
  "Northeastern Huskies": "CAA", "Stony Brook Seawolves": "CAA",
  "Towson Tigers": "CAA", "UNC Wilmington Seahawks": "CAA",
  "William & Mary Tribe": "CAA",
  // MAC
  "Akron Zips": "MAC", "Bowling Green Falcons": "MAC",
  "Buffalo Bulls": "MAC", "Central Michigan Chippewas": "MAC",
  "Eastern Michigan Eagles": "MAC", "Kent State Golden Flashes": "MAC",
  "Miami (OH) RedHawks": "MAC", "Northern Illinois Huskies": "MAC",
  "Toledo Rockets": "MAC", "Western Michigan Broncos": "MAC",
  // ASUN
  "Austin Peay Governors": "ASUN", "Bellarmine Knights": "ASUN",
  "Central Arkansas Bears": "ASUN", "Eastern Kentucky Colonels": "ASUN",
  "Florida Gulf Coast Eagles": "ASUN", "Jacksonville Dolphins": "ASUN",
  "Liberty Flames": "ASUN", "Lindenwood Lions": "ASUN",
  "Lipscomb Bisons": "ASUN", "North Alabama Lions": "ASUN",
  "North Florida Ospreys": "ASUN", "Queens University Royals": "ASUN",
  "Stetson Hatters": "ASUN", "West Georgia Wolves": "ASUN",
  // Big South
  "Campbell Fighting Camels": "Big South", "Charleston Southern Buccaneers": "Big South",
  "High Point Panthers": "Big South", "Longwood Lancers": "Big South",
  "Presbyterian Blue Hose": "Big South", "Radford Highlanders": "Big South",
  "Robert Morris Colonials": "Big South", "South Carolina Upstate Spartans": "Big South",
  "Winthrop Eagles": "Big South",
  // Sun Belt
  "Arkansas State Red Wolves": "Sun Belt", "Coastal Carolina Chanticleers": "Sun Belt",
  "Georgia Southern Eagles": "Sun Belt", "Georgia State Panthers": "Sun Belt",
  "Louisiana Ragin' Cajuns": "Sun Belt", "Marshall Thundering Herd": "Sun Belt",
  "Old Dominion Monarchs": "Sun Belt", "South Alabama Jaguars": "Sun Belt",
  "UT Arlington Mavericks": "Sun Belt",
  // CUSA
  "Florida International Panthers": "CUSA", "Jacksonville State Gamecocks": "CUSA",
  "Kennesaw State Owls": "CUSA", "Louisiana Tech Bulldogs": "CUSA",
  "Middle Tennessee Blue Raiders": "CUSA", "Sam Houston Bearkats": "CUSA",
  "UTEP Miners": "CUSA", "Western Kentucky Hilltoppers": "CUSA",
  // Horizon
  "Cleveland State Vikings": "Horizon", "Detroit Mercy Titans": "Horizon",
  "Green Bay Phoenix": "Horizon", "IU Indianapolis Jaguars": "Horizon",
  "Milwaukee Panthers": "Horizon", "Northern Kentucky Norse": "Horizon",
  "Oakland Golden Grizzlies": "Horizon", "Purdue Fort Wayne Mastodons": "Horizon",
  "Youngstown State Penguins": "Horizon",
  // Ivy League
  "Brown Bears": "Ivy League", "Columbia Lions": "Ivy League",
  "Cornell Big Red": "Ivy League", "Dartmouth Big Green": "Ivy League",
  "Harvard Crimson": "Ivy League", "Princeton Tigers": "Ivy League",
  "Yale Bulldogs": "Ivy League",
  // Patriot
  "American University Eagles": "Patriot", "Army Black Knights": "Patriot",
  "Boston University Terriers": "Patriot", "Bucknell Bison": "Patriot",
  "Colgate Raiders": "Patriot", "Holy Cross Crusaders": "Patriot",
  "Lafayette Leopards": "Patriot", "Lehigh Mountain Hawks": "Patriot",
  "Loyola Maryland Greyhounds": "Patriot", "Navy Midshipmen": "Patriot",
  // Southern
  "Chattanooga Mocs": "Southern", "East Tennessee State Buccaneers": "Southern",
  "Furman Paladins": "Southern", "Mercer Bears": "Southern",
  "Samford Bulldogs": "Southern", "The Citadel Bulldogs": "Southern",
  "UNC Greensboro Spartans": "Southern", "Western Carolina Catamounts": "Southern",
  "Wofford Terriers": "Southern",
  // OVC
  "Belmont Bruins": "OVC", "Eastern Illinois Panthers": "OVC",
  "Little Rock Trojans": "OVC", "Morehead State Eagles": "OVC",
  "SE Louisiana Lions": "OVC", "Southeast Missouri State Redhawks": "OVC",
  "Tennessee State Tigers": "OVC", "Tennessee Tech Golden Eagles": "OVC",
  "Southern Indiana Screaming Eagles": "OVC",
  // Big West
  "Cal Poly Mustangs": "Big West", "Cal State Bakersfield Roadrunners": "Big West",
  "Cal State Northridge Matadors": "Big West", "California Baptist Lancers": "Big West",
  "Long Beach State Beach": "Big West", "UC Irvine Anteaters": "Big West",
  "UC Riverside Highlanders": "Big West", "UC San Diego Tritons": "Big West",
  "UC Santa Barbara Gauchos": "Big West", "Utah Valley Wolverines": "Big West",
  // Summit
  "Denver Pioneers": "Summit", "Kansas City Roos": "Summit",
  "North Dakota Fighting Hawks": "Summit", "North Dakota State Bison": "Summit",
  "Oral Roberts Golden Eagles": "Summit", "South Dakota Coyotes": "Summit",
  "South Dakota State Jackrabbits": "Summit", "St. Thomas-Minnesota Tommies": "Summit",
  // WAC
  "Abilene Christian Wildcats": "WAC", "Chicago State Cougars": "WAC",
  "Grand Canyon Lopes": "WAC", "Houston Christian Huskies": "WAC",
  "Lamar Cardinals": "WAC", "Nicholls Colonels": "WAC",
  "Tarleton State Texans": "WAC", "Texas A&M-Corpus Christi Islanders": "WAC",
  "UT Rio Grande Valley Vaqueros": "WAC", "Utah Tech Trailblazers": "WAC",
  "East Texas A&M Lions": "WAC",
  // Big Sky
  "Eastern Washington Eagles": "Big Sky", "Idaho State Bengals": "Big Sky",
  "Idaho Vandals": "Big Sky", "Montana Grizzlies": "Big Sky",
  "Montana State Bobcats": "Big Sky", "Northern Arizona Lumberjacks": "Big Sky",
  "Northern Colorado Bears": "Big Sky", "Portland State Vikings": "Big Sky",
  "Sacramento State Hornets": "Big Sky", "Weber State Wildcats": "Big Sky",
  // MEAC
  "Coppin State Eagles": "MEAC", "Delaware State Hornets": "MEAC",
  "Florida A&M Rattlers": "MEAC", "Hampton Pirates": "MEAC",
  "Howard Bison": "MEAC", "Maryland Eastern Shore Hawks": "MEAC",
  "Morgan State Bears": "MEAC", "Norfolk State Spartans": "MEAC",
  "North Carolina A&T Aggies": "MEAC", "North Carolina Central Eagles": "MEAC",
  "South Carolina State Bulldogs": "MEAC",
  // SWAC
  "Alabama A&M Bulldogs": "SWAC", "Alabama State Hornets": "SWAC",
  "Arkansas-Pine Bluff Golden Lions": "SWAC", "Grambling Tigers": "SWAC",
  "Jackson State Tigers": "SWAC", "Mississippi Valley State Delta Devils": "SWAC",
  "Prairie View A&M Panthers": "SWAC", "Southern Jaguars": "SWAC",
  "Texas Southern Tigers": "SWAC",
  // America East
  "Binghamton Bearcats": "America East", "Bryant Bulldogs": "America East",
  "UAlbany Great Danes": "America East", "UMBC Retrievers": "America East",
  "UMass Lowell River Hawks": "America East", "New Hampshire Wildcats": "America East",
  "Vermont Catamounts": "America East", "New Haven Chargers": "America East",
  // NEC
  "Central Connecticut Blue Devils": "NEC", "Fairleigh Dickinson Knights": "NEC",
  "Le Moyne Dolphins": "NEC", "Merrimack Warriors": "NEC",
  "Mount St. Mary's Mountaineers": "NEC", "Sacred Heart Pioneers": "NEC",
  "Saint Francis Red Flash": "NEC", "Stonehill Skyhawks": "NEC",
  "Wagner Seahawks": "NEC",
  // MAAC
  "Canisius Golden Griffins": "MAAC", "Fairfield Stags": "MAAC",
  "Iona Gaels": "MAAC", "Marist Red Foxes": "MAAC",
  "Manhattan Jaspers": "MAAC", "Niagara Purple Eagles": "MAAC",
  "Quinnipiac Bobcats": "MAAC", "Saint Peter's Peacocks": "MAAC",
  // Southland
  "Incarnate Word Cardinals": "Southland", "New Orleans Privateers": "Southland",
  "Northwestern State Demons": "Southland", "Stephen F. Austin Lumberjacks": "Southland",
};

function getConference(teamName) {
  return TEAM_CONFERENCE[teamName] || "Other";
}

function computeStats(games) {
  const atsW = games.filter(g => g.ats_result === "W").length;
  const atsL = games.filter(g => g.ats_result === "L").length;
  const atsP = games.filter(g => g.ats_result === "P").length;
  const atsPct = (atsW + atsL) > 0 ? Math.round(atsW / (atsW + atsL) * 1000) / 10 : 0;

  const suCorrect = games.filter(g => g.model_correct_winner).length;
  const suPct = games.length > 0 ? Math.round(suCorrect / games.length * 1000) / 10 : 0;

  const ouGradeable = games.filter(g => g.ou_result && g.ou_result !== "P").length;
  const ouCorrect = games.filter(g => g.ou_model_correct).length;
  const ouModelPct = ouGradeable > 0 ? Math.round(ouCorrect / ouGradeable * 1000) / 10 : 0;

  const tierStats = tier => {
    const w = tier.filter(g => g.ats_result === "W").length;
    const l = tier.filter(g => g.ats_result === "L").length;
    const p = tier.filter(g => g.ats_result === "P").length;
    return { w, l, p, pct: (w + l) > 0 ? Math.round(w / (w + l) * 1000) / 10 : 0 };
  };

  const vp = games.filter(g => (g.value_rating || 0) >= 3);
  const vpW = vp.filter(g => g.ats_result === "W").length;
  const vpL = vp.filter(g => g.ats_result === "L").length;
  const vpP = vp.filter(g => g.ats_result === "P").length;

  return {
    ats: { w: atsW, l: atsL, p: atsP, pct: atsPct },
    su: { correct: suCorrect, total: games.length, pct: suPct },
    ou: {
      over: games.filter(g => g.ou_result === "O").length,
      under: games.filter(g => g.ou_result === "U").length,
      push: games.filter(g => g.ou_result === "P").length,
      model_correct: ouCorrect, model_gradeable: ouGradeable, model_pct: ouModelPct,
    },
    by_confidence: {
      high: tierStats(games.filter(g => g.confidence >= 70)),
      medium: tierStats(games.filter(g => g.confidence >= 40 && g.confidence < 70)),
      low: tierStats(games.filter(g => g.confidence < 40)),
    },
    value_plays: { w: vpW, l: vpL, p: vpP, pct: (vpW + vpL) > 0 ? Math.round(vpW / (vpW + vpL) * 1000) / 10 : 0 },
  };
}

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
  const [dateFilter, setDateFilter] = useState("all");
  const [confFilter, setConfFilter] = useState("all");
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

  // Build sorted unique conference list from graded games (must be before early return)
  const availableConfs = useMemo(() => {
    if (!data) return ["all"];
    const graded = data.games.filter(g => g.graded);
    const confs = new Set();
    graded.forEach(g => {
      confs.add(getConference(g.home_team));
      confs.add(getConference(g.away_team));
    });
    return ["all", ...Array.from(confs).filter(c => c !== "Other").sort(), "Other"]
      .filter(c => c === "all" || graded.some(g =>
        getConference(g.home_team) === c || getConference(g.away_team) === c
      ));
  }, [data]);

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

  // Date boundary helpers
  const now = new Date();
  const startOfYesterday = new Date(now);
  startOfYesterday.setDate(now.getDate() - 1);
  startOfYesterday.setHours(0, 0, 0, 0);
  const endOfYesterday = new Date(startOfYesterday);
  endOfYesterday.setHours(23, 59, 59, 999);
  const last7Start = new Date(now);
  last7Start.setDate(now.getDate() - 7);
  last7Start.setHours(0, 0, 0, 0);
  const last30Start = new Date(now);
  last30Start.setDate(now.getDate() - 30);
  last30Start.setHours(0, 0, 0, 0);

  // Date + conference filter — used for computing live stats AND game log
  let dateConfFiltered = [...graded];
  if (dateFilter === "yesterday") {
    dateConfFiltered = dateConfFiltered.filter(g => {
      const d = new Date(g.date);
      return d >= startOfYesterday && d <= endOfYesterday;
    });
  } else if (dateFilter === "7days") {
    dateConfFiltered = dateConfFiltered.filter(g => new Date(g.date) >= last7Start);
  } else if (dateFilter === "30days") {
    dateConfFiltered = dateConfFiltered.filter(g => new Date(g.date) >= last30Start);
  }
  if (confFilter !== "all") {
    dateConfFiltered = dateConfFiltered.filter(g =>
      getConference(g.home_team) === confFilter ||
      getConference(g.away_team) === confFilter
    );
  }

  // Compute stats from the date/conference-filtered set
  const { ats, su, ou, by_confidence, value_plays } = computeStats(dateConfFiltered);

  // Additional result/confidence filter — only for the game log rows
  let filtered = [...dateConfFiltered];
  if (filter === "high") filtered = filtered.filter(g => g.confidence >= 70);
  if (filter === "value") filtered = filtered.filter(g => (g.value_rating || 0) >= 3);
  if (filter === "wins") filtered = filtered.filter(g => g.ats_result === "W");
  if (filter === "losses") filtered = filtered.filter(g => g.ats_result === "L");

  // Sort
  if (sortBy === "date") filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
  if (sortBy === "confidence") filtered.sort((a, b) => b.confidence - a.confidence);
  if (sortBy === "value") filtered.sort((a, b) => (b.value_rating || 0) - (a.value_rating || 0));

  const datePeriodLabel = dateFilter === "yesterday" ? "Yesterday"
    : dateFilter === "7days" ? "Last 7 Days"
    : dateFilter === "30days" ? "Last 30 Days"
    : "Season";
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
              {dateConfFiltered.length} games graded • {datePeriodLabel} record
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
              Against the spread · {datePeriodLabel}
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
            flexDirection: "column",
            gap: 10,
          }}>
            {/* Row 1: title + sort */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{
                fontSize: 9, fontWeight: 800, color: C.muted,
                letterSpacing: 2.5, textTransform: "uppercase",
                fontFamily: "'JetBrains Mono', monospace",
              }}>
                Game Log
              </span>
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

            {/* Row 2: date filters */}
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <span style={{ fontSize: 9, color: C.dim, fontFamily: "'JetBrains Mono', monospace", marginRight: 2 }}>DATE:</span>
              {[
                { key: "all", label: "All Time" },
                { key: "yesterday", label: "Yesterday" },
                { key: "7days", label: "Last 7 Days" },
                { key: "30days", label: "Last 30 Days" },
              ].map(f => (
                <button key={f.key} onClick={() => setDateFilter(f.key)} style={{
                  background: dateFilter === f.key ? `${C.indigo}30` : "transparent",
                  border: `1px solid ${dateFilter === f.key ? C.indigo : C.border}`,
                  borderRadius: 20, padding: "4px 12px",
                  color: dateFilter === f.key ? C.indigoDim : C.muted,
                  fontSize: 10, fontWeight: 700, cursor: "pointer",
                  fontFamily: "'JetBrains Mono', monospace",
                  transition: "all 0.2s",
                }}>
                  {f.label}
                </button>
              ))}
            </div>

            {/* Row 3: result filters + conference dropdown */}
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <span style={{ fontSize: 9, color: C.dim, fontFamily: "'JetBrains Mono', monospace", marginRight: 2 }}>FILTER:</span>
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
              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 9, color: C.dim, fontFamily: "'JetBrains Mono', monospace" }}>CONF:</span>
                <select value={confFilter} onChange={e => setConfFilter(e.target.value)} style={{
                  background: confFilter !== "all" ? `${C.indigo}20` : C.surface2,
                  border: `1px solid ${confFilter !== "all" ? C.indigo : C.border}`,
                  borderRadius: 6, padding: "4px 8px",
                  color: confFilter !== "all" ? C.indigoDim : C.muted,
                  fontSize: 10, outline: "none",
                  cursor: "pointer", fontFamily: "'JetBrains Mono', monospace",
                }}>
                  <option value="all">All Conferences</option>
                  {availableConfs.filter(c => c !== "all").map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
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
