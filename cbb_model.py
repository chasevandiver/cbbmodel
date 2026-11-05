#!/usr/bin/env python3
"""
College Basketball Prediction Model
===================================
Projects a point spread and total for every Division I game on a date.

Method (KenPom / Barttorvik style):
    home_proj_oe = home.AdjOE + away.AdjDE - national_avg
    away_proj_oe = away.AdjOE + home.AdjDE - national_avg
    margin       = (home_proj_oe - away_proj_oe) * tempo / 100 + home_court
    total        = (home_proj_oe + away_proj_oe) * tempo / 100

Adjusted efficiencies already encapsulate shooting, turnovers, rebounding and
free throws, so nothing else is added on top. Market lines are used only to
report an edge and to score confidence, never to move the projection.

Data sources:
    - barttorvik.com   T-Rank adjusted efficiencies (cached under data/)
    - ESPN             schedule, team metadata, fallback spread/total
    - The Odds API     consensus spread/total (ODDS_API_KEY env var)

Usage:
    python3 cbb_model.py                         # today's picks -> picks/ + public/
    python3 cbb_model.py --date 2026-11-05       # a specific date (ET)
    python3 cbb_model.py --output console        # readable output, writes nothing
    python3 cbb_model.py --debug                 # show team matching
    python3 cbb_model.py --check-teams           # audit ESPN <-> Barttorvik names
"""

import argparse
import json
import math
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "picks")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_DIR = os.path.join(BASE_DIR, "data")

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams"
BARTTORVIK_URL = "https://barttorvik.com/{season}_team_results.json"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds"
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
ODDS_BOOKMAKERS = "draftkings,fanduel,betmgm,williamhill_us"

EASTERN = ZoneInfo("America/New_York")      # ESPN schedules are keyed by Eastern date

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}
HTTP_RETRIES = 3
STATS_CACHE_MAX_AGE_DAYS = 3                # refuse stale cached ratings beyond this

HOME_COURT_ADVANTAGE_PTS = 3.5              # D-I average; neutral sites get 0
SPREAD_STD_DEV = 11.0                       # std dev of (actual - projected) margin
MODEL_VERSION = "4.0.0"

# Edge-vs-market bands used for confidence and the best-bet flag. An edge larger
# than EDGE_MAX_TRUSTED almost always means stale ratings or a bad data point,
# not a genuine opportunity. Re-tune these once a clean season of results exists.
EDGE_BEST_BET_MIN = 3.0
EDGE_BEST_BET_MAX = 6.0
EDGE_MAX_TRUSTED = 10.0

# ESPN team "location" -> Barttorvik team name, for the names that differ after
# normalization. Run `--check-teams` at the start of each season to find drift.
ESPN_TO_BARTTORVIK = {
    "American University": "American",
    "App State": "Appalachian St.",
    "California Baptist": "Cal Baptist",
    "Florida International": "FIU",
    "Grambling": "Grambling St.",
    "Hawai'i": "Hawaii",
    "IU Indianapolis": "IU Indy",
    "Kansas City": "UMKC",
    "Long Island University": "LIU",
    "Loyola Maryland": "Loyola MD",
    "LSU New Orleans": "New Orleans",
    "McNeese": "McNeese St.",
    "Miami": "Miami FL",
    "NC State": "N.C. State",
    "Nicholls": "Nicholls St.",
    "Ole Miss": "Mississippi",
    "Omaha": "Nebraska Omaha",
    "Pennsylvania": "Penn",
    "Queens University": "Queens",
    "Sam Houston": "Sam Houston St.",
    "SE Louisiana": "Southeastern Louisiana",
    "Seattle U": "Seattle",
    "South Carolina Upstate": "USC Upstate",
    "Texas A&M-Corpus Christi": "Texas A&M Corpus Chris",
    "UAlbany": "Albany",
    "UConn": "Connecticut",
    "UIC": "Illinois Chicago",
    "UL Monroe": "Louisiana Monroe",
    "UT Martin": "Tennessee Martin",
}


# ============================================================================
# HELPERS
# ============================================================================

def canon(name):
    """Canonical key for a team name: accent-free, lowercase, 'State'/'Saint' -> 'st'."""
    name = unicodedata.normalize("NFD", name or "")
    name = "".join(c for c in name if unicodedata.category(c) != "Mn").lower().strip()
    name = name.replace("&", " and ")
    name = re.sub(r"\bsaint\b", "st", name)
    name = re.sub(r"\bstate\b", "st", name)
    name = re.sub(r"\bst\.", "st", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def season_for(date):
    """Barttorvik labels a season by the year it ends: Nov 2026 - Apr 2027 -> 2027."""
    return date.year + 1 if date.month >= 10 else date.year


def http_get(url, **kwargs):
    """GET with retries and a browser-like UA. Returns the Response or raises."""
    kwargs.setdefault("timeout", 20)
    headers = dict(HTTP_HEADERS)
    headers.update(kwargs.pop("headers", {}))
    last_err = None
    for attempt in range(HTTP_RETRIES):
        try:
            resp = requests.get(url, headers=headers, **kwargs)
            if resp.status_code == 200:
                return resp
            last_err = f"HTTP {resp.status_code}: {resp.text[:120]!r}"
        except requests.RequestException as e:
            last_err = str(e)
        time.sleep(2 ** attempt)
    raise RuntimeError(f"{url} failed after {HTTP_RETRIES} attempts: {last_err}")


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ============================================================================
# TEAM RATINGS
# ============================================================================

class TeamRatings:
    """
    Barttorvik team_results.json, list-of-lists. Columns used:
        [1] team  [2] conf  [3] record "W-L"  [4] AdjOE  [6] AdjDE  [8] Barthag  [44] AdjTempo
    The file carries no four-factor or recent-form columns; do not read others.
    """

    def __init__(self, season):
        self.season = season
        self.by_key = {}            # canon(team name) -> stats
        self.avg_oe = 0.0
        self.source = None

    # ---- loading --------------------------------------------------------
    def load(self):
        rows = self._fetch_live()
        if rows is None:
            rows = self._load_cache()
        if rows is None:
            raise SystemExit(
                f"[FATAL] No team ratings for season {self.season}: Barttorvik is unreachable "
                f"and no cache younger than {STATS_CACHE_MAX_AGE_DAYS} days exists under data/. "
                "Refusing to generate picks from placeholder data."
            )
        self._index(rows)
        return self

    def _fetch_live(self):
        url = BARTTORVIK_URL.format(season=self.season)
        try:
            rows = http_get(url).json()
        except (RuntimeError, ValueError) as e:
            print(f"[WARN] Barttorvik fetch failed: {e}")
            return None
        if not isinstance(rows, list) or len(rows) < 300:
            print(f"[WARN] Barttorvik returned an unexpected payload ({type(rows).__name__}, "
                  f"{len(rows) if isinstance(rows, list) else 'n/a'} rows)")
            return None
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self._cache_path(), "w") as f:
            json.dump({"fetched_at": datetime.now(EASTERN).isoformat(), "rows": rows}, f)
        self.source = "barttorvik (live)"
        return rows

    def _cache_path(self):
        return os.path.join(DATA_DIR, f"barttorvik_{self.season}.json")

    def _load_cache(self):
        path = self._cache_path()
        if not os.path.exists(path):
            return None
        with open(path) as f:
            blob = json.load(f)
        fetched = datetime.fromisoformat(blob["fetched_at"])
        age = datetime.now(EASTERN) - fetched
        if age > timedelta(days=STATS_CACHE_MAX_AGE_DAYS):
            print(f"[WARN] Cached ratings are {age.days} days old — too stale to use")
            return None
        print(f"[WARN] Using cached ratings fetched {fetched:%Y-%m-%d %H:%M} ET")
        self.source = f"barttorvik (cache {fetched:%Y-%m-%d})"
        return blob["rows"]

    def _index(self, rows):
        for t in rows:
            try:
                wins, losses = (int(x) for x in str(t[3]).split("-")[:2])
            except (ValueError, IndexError):
                wins, losses = 0, 0
            self.by_key[canon(t[1])] = {
                "team": t[1],
                "conf": t[2],
                "adj_oe": float(t[4]),
                "adj_de": float(t[6]),
                "barthag": float(t[8]),
                "adj_tempo": float(t[44]),
                "wins": wins,
                "losses": losses,
                "games": wins + losses,
            }
        self.avg_oe = sum(s["adj_oe"] for s in self.by_key.values()) / len(self.by_key)

    # ---- lookup ---------------------------------------------------------
    def find(self, location):
        """Exact lookup by ESPN team location via the alias table, then canonical key."""
        alias = ESPN_TO_BARTTORVIK.get(location)
        if alias and canon(alias) in self.by_key:
            return self.by_key[canon(alias)]
        return self.by_key.get(canon(location))


# ============================================================================
# SCHEDULE + ODDS
# ============================================================================

def fetch_schedule(date_str):
    """All D-I games on an Eastern date (YYYYMMDD). Includes non-D-I opponents; those won't match ratings."""
    data = http_get(ESPN_SCOREBOARD_URL, params={"dates": date_str, "limit": 500, "groups": 50}).json()
    games = []
    for event in data.get("events", []):
        comp = (event.get("competitions") or [{}])[0]
        sides = {}
        for c in comp.get("competitors", []):
            team = c.get("team", {})
            sides[c.get("homeAway")] = {
                "id": team.get("id", ""),
                "location": team.get("location") or team.get("displayName", ""),
                "name": team.get("displayName", ""),
                "abbreviation": team.get("abbreviation", ""),
                "logo": team.get("logo", ""),
                "rank": (c.get("curatedRank") or {}).get("current", 99),
                "record": (c.get("records") or [{}])[0].get("summary", "0-0"),
            }
        if "home" not in sides or "away" not in sides:
            continue
        broadcasts = comp.get("broadcasts") or []
        games.append({
            "game_id": event.get("id", ""),
            "date": event.get("date", ""),
            "name": event.get("name", ""),
            "home": sides["home"],
            "away": sides["away"],
            "venue": (comp.get("venue") or {}).get("fullName", ""),
            "neutral_site": bool(comp.get("neutralSite", False)),
            "conference_game": bool(comp.get("conferenceCompetition", False)),
            "broadcast": (broadcasts[0].get("names") or [""])[0] if broadcasts else "",
            "status": (event.get("status") or {}).get("type", {}).get("name", ""),
            "odds": _espn_odds(comp),
        })
    return games


def _espn_odds(comp):
    """ESPN's line, home-team perspective (negative = home favored). None when absent."""
    odds = (comp.get("odds") or [None])[0]
    if not odds or odds.get("spread") is None:
        return None
    return {
        "spread": float(odds["spread"]),
        "over_under": float(odds["overUnder"]) if odds.get("overUnder") is not None else None,
        "spread_holder": (odds.get("spreadHolder") or {}).get("displayName") or odds.get("details", ""),
        "bookmaker": "espn",
    }


def fetch_market_odds():
    """The Odds API spreads/totals; empty list if no key or the call fails."""
    if not ODDS_API_KEY:
        print("       [WARN] ODDS_API_KEY not set — using ESPN lines only")
        return []
    params = {"apiKey": ODDS_API_KEY, "regions": "us", "markets": "spreads,totals",
              "oddsFormat": "american", "bookmakers": ODDS_BOOKMAKERS}
    try:
        data = http_get(ODDS_API_URL, params=params).json()
    except (RuntimeError, ValueError) as e:
        print(f"       [WARN] Odds API unavailable: {e}")
        return []
    out = []
    for g in data:
        home, away = g.get("home_team", ""), g.get("away_team", "")
        spread = total = book = None
        for bookie in g.get("bookmakers", []):
            for market in bookie.get("markets", []):
                if market["key"] == "spreads" and spread is None:
                    for o in market.get("outcomes", []):
                        if o["name"] == home and o.get("point") is not None:
                            spread, book = float(o["point"]), bookie.get("key")
                elif market["key"] == "totals" and total is None:
                    for o in market.get("outcomes", []):
                        if o["name"] == "Over" and o.get("point") is not None:
                            total = float(o["point"])
            if spread is not None and total is not None:
                break
        if spread is None:
            continue
        try:
            commence = datetime.fromisoformat(g["commence_time"].replace("Z", "+00:00")).astimezone(EASTERN)
        except (KeyError, ValueError):
            continue
        out.append({"home": home, "away": away, "spread": spread, "over_under": total,
                    "bookmaker": book, "date": commence.strftime("%Y%m%d"),
                    "home_key": canon(home), "away_key": canon(away)})
    return out


def _name_matches(odds_name_key, team, rating):
    """Odds API names are 'Location Nickname' with abbreviations ('Chicago St Cougars').
    Accept when the ESPN location or Barttorvik name is a whole-word prefix of it.
    Returns the matched prefix length (0 = no match) so callers can prefer the tightest fit."""
    best = 0
    candidates = [canon(team["location"])]
    if rating:
        candidates.append(canon(rating["team"]))
    for cand in candidates:
        if cand and (odds_name_key == cand or odds_name_key.startswith(cand + " ")):
            best = max(best, len(cand))
    return best


def attach_market_odds(games, odds, date_str, ratings):
    """Overwrite ESPN lines with Odds API lines for games on the target date. Each odds entry is used once."""
    todays = [o for o in odds if o["date"] == date_str]
    matched = 0
    used = set()
    for game in games:
        best, best_i = 0, None
        hr, ar = ratings.find(game["home"]["location"]), ratings.find(game["away"]["location"])
        for i, o in enumerate(todays):
            if i in used:
                continue
            h = _name_matches(o["home_key"], game["home"], hr)
            a = _name_matches(o["away_key"], game["away"], ar)
            if h and a and h + a > best:
                best, best_i = h + a, i
        if best_i is None:
            continue
        o = todays[best_i]
        used.add(best_i)
        game["odds"] = {"spread": o["spread"], "over_under": o["over_under"],
                        "spread_holder": o["home"] if o["spread"] < 0 else o["away"],
                        "bookmaker": o["bookmaker"]}
        matched += 1
    return matched


# ============================================================================
# PREDICTION
# ============================================================================

class PredictionModel:
    def __init__(self, ratings, debug=False):
        self.ratings = ratings
        self.debug = debug
        self.skipped = []

    def predict_all(self, games):
        preds = []
        for g in games:
            p = self.predict(g)
            if p:
                preds.append(p)
        preds.sort(key=lambda p: p["confidence"], reverse=True)
        return preds

    def predict(self, game):
        home, away = game["home"], game["away"]
        hs, as_ = self.ratings.find(home["location"]), self.ratings.find(away["location"])
        if not hs or not as_:
            missing = [t["name"] for t, s in ((home, hs), (away, as_)) if not s]
            self.skipped.append(f"{away['name']} @ {home['name']}  (no ratings: {', '.join(missing)})")
            return None
        if self.debug:
            print(f"  [MATCH] {home['name']} -> {hs['team']}  |  {away['name']} -> {as_['team']}")

        avg = self.ratings.avg_oe
        home_oe = hs["adj_oe"] + as_["adj_de"] - avg         # pts per 100 poss vs this defense
        away_oe = as_["adj_oe"] + hs["adj_de"] - avg
        tempo = (hs["adj_tempo"] + as_["adj_tempo"]) / 2.0
        efficiency_margin = (home_oe - away_oe) * tempo / 100.0
        hca = 0.0 if game["neutral_site"] else HOME_COURT_ADVANTAGE_PTS
        margin = efficiency_margin + hca                      # + = home wins by
        total = (home_oe + away_oe) * tempo / 100.0
        home_win_prob = norm_cdf(margin / SPREAD_STD_DEV)

        odds = game.get("odds")
        market_spread = odds["spread"] if odds else None      # home perspective
        market_total = odds.get("over_under") if odds else None
        pick_is_home = margin > 0
        spread_diff = spread_edge = total_edge = None
        if market_spread is not None:
            spread_diff = margin - (-market_spread)           # + = model likes home more than market
            spread_edge = spread_diff if pick_is_home else -spread_diff
        if market_total is not None:
            total_edge = total - market_total

        confidence = self._confidence(margin, spread_diff, hs, as_)
        edge_abs = abs(spread_diff) if spread_diff is not None else None

        return {
            "game_id": game["game_id"],
            "date": game["date"],
            "home_team": home["name"],
            "away_team": away["name"],
            "home_abbr": home["abbreviation"],
            "away_abbr": away["abbreviation"],
            "home_logo": home["logo"],
            "away_logo": away["logo"],
            "home_rank": home["rank"],
            "away_rank": away["rank"],
            "home_record": home["record"],
            "away_record": away["record"],
            "home_rating_team": hs["team"],
            "away_rating_team": as_["team"],
            "home_adj_em": round(hs["adj_oe"] - hs["adj_de"], 2),
            "away_adj_em": round(as_["adj_oe"] - as_["adj_de"], 2),
            "venue": game["venue"],
            "neutral_site": game["neutral_site"],
            "conference_game": game["conference_game"],
            "broadcast": game["broadcast"],
            "predicted_spread": round(margin, 1),
            "predicted_total": round(total, 1),
            "home_projected_score": round((total + margin) / 2, 1),
            "away_projected_score": round((total - margin) / 2, 1),
            "home_win_prob": round(home_win_prob * 100, 1),
            "away_win_prob": round((1 - home_win_prob) * 100, 1),
            "confidence": round(confidence, 1),
            "pick": home["name"] if pick_is_home else away["name"],
            "pick_abbr": home["abbreviation"] if pick_is_home else away["abbreviation"],
            "is_home_pick": pick_is_home,
            "projected_tempo": round(tempo, 1),
            "factors": {
                "efficiency_margin": round(efficiency_margin, 2),
                "home_court": round(hca, 2),
            },
            "market": {
                "spread": market_spread,
                "over_under": market_total,
                "spread_holder": odds.get("spread_holder") if odds else None,
                "bookmaker": odds.get("bookmaker") if odds else None,
            },
            "value_rating": round(edge_abs, 1) if edge_abs is not None else None,
            "model_vs_market": {
                "spread_edge": round(spread_edge, 1) if spread_edge is not None else None,
                "total_edge": round(total_edge, 1) if total_edge is not None else None,
            },
            "is_best_bet": edge_abs is not None and EDGE_BEST_BET_MIN <= edge_abs <= EDGE_BEST_BET_MAX,
            "is_tournament_game": game["neutral_site"],
        }

    @staticmethod
    def _confidence(margin, spread_diff, hs, as_):
        """
        Heuristic 15-95 score for ranking a slate. Not a calibrated probability.
          + edge vs market, up to 6 pts (bigger edges are usually data problems)
          - no market line, or an edge too large to trust
          - very large projected margins (least reliable region)
          + ratings maturity (games played this season)
        """
        c = 50.0
        if spread_diff is None:
            c -= 10
        else:
            edge = abs(spread_diff)
            c += min(edge, EDGE_BEST_BET_MAX) * 4
            if edge > EDGE_MAX_TRUSTED:
                c -= 20
        m = abs(margin)
        if m >= 15:
            c -= 10
        elif m >= 10:
            c -= 5
        c += min(hs["games"], as_["games"], 10)
        return max(15.0, min(95.0, c))


# ============================================================================
# OUTPUT
# ============================================================================

def build_output(predictions, date_str, ratings):
    return {
        "generated_at": datetime.now(EASTERN).isoformat(),
        "date": date_str,
        "total_games": len(predictions),
        "model_version": MODEL_VERSION,
        "ratings_source": ratings.source,
        "ratings_season": ratings.season,
        "picks": predictions,
        "summary": {
            "total_games": len(predictions),
            "high_confidence": sum(p["confidence"] >= 70 for p in predictions),
            "medium_confidence": sum(40 <= p["confidence"] < 70 for p in predictions),
            "low_confidence": sum(p["confidence"] < 40 for p in predictions),
            "avg_confidence": round(sum(p["confidence"] for p in predictions) / max(len(predictions), 1), 1),
            "value_plays": sum((p["value_rating"] or 0) >= 3 for p in predictions),
            "best_bets": sum(p["is_best_bet"] for p in predictions),
            "with_market_line": sum(p["market"]["spread"] is not None for p in predictions),
            "tournament_games": sum(p["is_tournament_game"] for p in predictions),
        },
    }


def write_output(output, date_str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paths = [os.path.join(OUTPUT_DIR, f"picks_{date_str}.json"), os.path.join(OUTPUT_DIR, "latest.json")]
    if os.path.isdir(PUBLIC_DIR):
        paths.append(os.path.join(PUBLIC_DIR, "latest.json"))
    for path in paths:
        with open(path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"[OK] wrote {os.path.relpath(path, BASE_DIR)}")


def print_console(predictions):
    for i, p in enumerate(predictions, 1):
        tags = []
        if p["is_tournament_game"]:
            tags.append("NEUTRAL")
        if p["is_best_bet"]:
            tags.append("BEST BET")
        tag = f"  [{', '.join(tags)}]" if tags else ""
        print(f"\n  #{i} [{p['confidence']:.0f}] {p['away_team']} @ {p['home_team']}{tag}")
        print(f"     Model: {p['pick_abbr']} by {abs(p['predicted_spread']):.1f}   "
              f"({p['away_abbr']} {p['away_projected_score']:.0f} - {p['home_abbr']} {p['home_projected_score']:.0f}, "
              f"total {p['predicted_total']:.1f}, home win {p['home_win_prob']:.0f}%)")
        mk = p["market"]
        if mk["spread"] is not None:
            side = p["home_abbr"] if mk["spread"] < 0 else p["away_abbr"]
            ou = f", O/U {mk['over_under']:.1f}" if mk["over_under"] is not None else ""
            print(f"     Market: {side} {-abs(mk['spread']):.1f}{ou} ({mk['bookmaker']})   "
                  f"edge {p['model_vs_market']['spread_edge']:+.1f} on {p['pick_abbr']}")
        else:
            print("     Market: n/a")


# ============================================================================
# TEAM NAME AUDIT
# ============================================================================

def check_teams(ratings):
    """Compare ESPN's D-I team list with Barttorvik's names and report anything unmatched."""
    data = http_get(ESPN_TEAMS_URL, params={"limit": 1000}).json()
    teams = data["sports"][0]["leagues"][0]["teams"]
    unmatched, used = [], set()
    for t in teams:
        loc = t["team"].get("location") or t["team"]["displayName"]
        r = ratings.find(loc)
        if r:
            used.add(r["team"])
        else:
            unmatched.append(f"{loc}  ({t['team']['displayName']})")
    print(f"ESPN D-I teams: {len(teams)}   matched: {len(teams) - len(unmatched)}   unmatched: {len(unmatched)}")
    for u in unmatched:
        print("  ESPN only:       ", u)
    for name in sorted(s["team"] for s in ratings.by_key.values() if s["team"] not in used):
        print("  Barttorvik only: ", name)
    stale = [k for k in ESPN_TO_BARTTORVIK if canon(ESPN_TO_BARTTORVIK[k]) not in ratings.by_key]
    for k in stale:
        print(f"  alias target missing: {k} -> {ESPN_TO_BARTTORVIK[k]}")
    return len(unmatched) + len(stale)


# ============================================================================
# MAIN
# ============================================================================

def main():
    ap = argparse.ArgumentParser(description="College Basketball Prediction Model")
    ap.add_argument("--date", help="Eastern date to predict (YYYY-MM-DD), default today")
    ap.add_argument("--output", choices=["json", "console"], default="json")
    ap.add_argument("--debug", action="store_true", help="print team matching")
    ap.add_argument("--check-teams", action="store_true", help="audit ESPN vs Barttorvik team names and exit")
    args = ap.parse_args()

    target = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=EASTERN) if args.date else datetime.now(EASTERN)
    date_str = target.strftime("%Y%m%d")
    season = season_for(target)

    print(f"\n{'=' * 60}\n  CBB Model v{MODEL_VERSION}  |  {target:%B %d, %Y}  |  season {season}\n{'=' * 60}\n")

    print("[1/3] Loading team ratings...")
    ratings = TeamRatings(season).load()
    print(f"       {len(ratings.by_key)} teams from {ratings.source}  (avg AdjOE {ratings.avg_oe:.1f})")

    if args.check_teams:
        sys.exit(1 if check_teams(ratings) else 0)

    print(f"[2/3] Fetching schedule and lines for {date_str}...")
    games = fetch_schedule(date_str)
    print(f"       {len(games)} games on ESPN")
    odds = fetch_market_odds()
    if odds:
        matched = attach_market_odds(games, odds, date_str, ratings)
        print(f"       Odds API lines matched for {matched}/{len(games)} games")
    espn_lines = sum(1 for g in games if g.get("odds"))
    print(f"       {espn_lines}/{len(games)} games have a market line")

    print("[3/3] Projecting...")
    model = PredictionModel(ratings, debug=args.debug)
    predictions = model.predict_all(games)
    print(f"       {len(predictions)} projections, {len(model.skipped)} games skipped")
    if args.debug:
        for s in model.skipped:
            print(f"  [SKIP] {s}")

    output = build_output(predictions, date_str, ratings)
    if args.output == "console":
        print_console(predictions)
    else:
        write_output(output, date_str)
    s = output["summary"]
    print(f"\n  {s['total_games']} games | {s['with_market_line']} with lines | "
          f"{s['value_plays']} value plays (3+ pt edge) | {s['best_bets']} best bets (3-6)\n")


if __name__ == "__main__":
    main()
