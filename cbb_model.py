#!/usr/bin/env python3
"""
College Basketball Prediction Model
====================================
A comprehensive statistical model for predicting NCAA basketball game outcomes.
Uses KenPom-style advanced metrics, tempo-adjusted efficiency, and multiple
predictive factors to generate spread and moneyline predictions.

Requirements:
    pip install requests beautifulsoup4 pandas numpy scipy scikit-learn

Data Sources:
    - ESPN API for schedules and scores
    - barttorvik.com for advanced team stats (T-Rank)
    - Sports Reference for supplementary stats

Usage:
    python cbb_model.py              # Generate today's picks
    python cbb_model.py --date 2026-02-25  # Generate picks for a specific date
    python cbb_model.py --output json      # Output as JSON for the website
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
import argparse
import math
import random

# ============================================================================
# CONFIGURATION
# ============================================================================

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
BARTTORVIK_URL = "https://barttorvik.com/trank.php"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picks")

# The Odds API
ODDS_API_KEY = "f1c651a894f64fafcdda0ef0c250aba7"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds"

# Model weights for each factor (tuned via backtesting)
WEIGHTS = {
    "adj_efficiency_margin": 0.30,    # KenPom-style adjusted efficiency margin
    "tempo_adjusted_scoring": 0.12,   # Tempo-adjusted offensive/defensive ratings
    "strength_of_schedule": 0.08,     # SOS impact
    "recent_form": 0.12,              # Last 10 games performance trend
    "home_court_advantage": 0.08,     # Home court bump (~3.5 pts historically)
    "turnover_margin": 0.06,          # TO margin differential
    "rebounding_margin": 0.06,        # Rebounding differential
    "free_throw_rate": 0.04,          # FT rate and FT%
    "three_point_shooting": 0.05,     # 3PT% offense vs opponent 3PT% defense
    "experience_factor": 0.03,        # Roster experience / continuity
    "rest_advantage": 0.03,           # Days of rest differential
    "travel_fatigue": 0.03,           # Travel distance / timezone changes
}

HOME_COURT_ADVANTAGE_PTS = 3.5  # NCAA average home court advantage in points
NEUTRAL_SITE_ADVANTAGE = 0.0


# ============================================================================
# ESPN → BARTTORVIK TEAM NAME ALIAS TABLE
# Add entries here whenever a team fails to match.
# ============================================================================

# Maps ESPN display names (lowercased) to exact barttorvik keys (lowercased).
# Add entries here whenever a team fails to match.
ESPN_TO_BARTTORVIK = {
    "western michigan broncos":         "w. michigan",
    "central michigan chippewas":       "c. michigan",
    "eastern michigan eagles":          "e. michigan",
    "northern illinois huskies":        "n. illinois",
    "southern illinois salukis":        "s. illinois",
    "middle tennessee blue raiders":    "mid tenn",
    "miami (oh) redhawks":              "miami oh",
    "miami (fl) hurricanes":            "miami fl",
    "miami hurricanes":                 "miami fl",
    "georgia state panthers":           "ga. st.",
    "georgia southern eagles":          "ga. southern",
    "san josé state spartans":          "san jose st.",
    "san jose state spartans":          "san jose st.",
    "louisiana ragin' cajuns":         "louisiana",
    "louisiana lafayette ragin' cajuns": "louisiana",
    "unc wilmington seahawks":          "unc wilmington",
    "umass minutemen":                  "massachusetts",
    "massachusetts minutemen":          "massachusetts",
    "uconn huskies":                    "connecticut",
    "utep miners":                      "utep",
    "utsa roadrunners":                 "utsa",
    "ut arlington mavericks":           "ut arlington",
    "texas-arlington mavericks":        "ut arlington",
    "lsu tigers":                       "lsu",
    "vcu rams":                         "vcu",
    "ucf knights":                      "ucf",
    "uic flames":                       "uic",
    "umkc roos":                        "umkc",
    "siu edwardsville cougars":         "siue",
    "southern indiana screaming eagles": "southern indiana",
    "pfw mastodons":                    "purdue ft. wayne",
    "purdue fort wayne mastodons":      "purdue ft. wayne",
    "uc davis aggies":                  "uc davis",
    "uc irvine anteaters":              "uc irvine",
    "uc riverside highlanders":         "uc riverside",
    "uc santa barbara gauchos":         "uc santa barbara",
    "cal poly mustangs":                "cal poly",
    "cal state bakersfield roadrunners": "cs bakersfield",
    "cal state fullerton titans":       "cs fullerton",
    "cal state northridge matadors":    "cs northridge",
    "long beach state beach":           "long beach st.",
    "hawaii rainbow warriors":          "hawaii",
    "south florida bulls":              "usf",
    "fiu panthers":                     "fiu",
    "fau owls":                         "fau",
    "florida atlantic owls":            "fau",
    "florida international panthers":   "fiu",
    "bowling green falcons":            "bowling green",
    "kent state golden flashes":        "kent st.",
    "coastal carolina chanticleers":    "coastal carolina",
    "morehead state eagles":            "morehead st.",
    "air force falcons":                "air force",
    "army black knights":               "army",
    "navy midshipmen":                  "navy",
    "loyola chicago ramblers":          "loyola chicago",
    "loyola marymount lions":           "lmu",
    "st. john's red storm":            "st. john's",
    "saint john's red storm":          "st. john's",
    "mount st. mary's mountaineers":   "mt. st. mary's",
    "mount st. mary's":                "mt. st. mary's",
    "southern miss golden eagles":      "southern miss",
    "south dakota state jackrabbits":   "s. dakota st.",
    "north dakota state bison":         "n. dakota st.",
    "south dakota coyotes":             "s. dakota",
    "north dakota fighting hawks":      "n. dakota",
    "southeast missouri state redhawks": "se missouri st.",
    "southeast missouri redhawks":      "se missouri st.",
    "western kentucky hilltoppers":     "w. kentucky",
    "eastern kentucky colonels":        "e. kentucky",
    "western illinois leathernecks":    "w. illinois",
    "eastern illinois panthers":        "e. illinois",
    "northern iowa panthers":           "n. iowa",
    "southern utah thunderbirds":       "s. utah",
    "northern colorado bears":          "n. colorado",
    "western carolina catamounts":      "w. carolina",
    "eastern washington eagles":        "e. washington",
    "northern arizona lumberjacks":     "n. arizona",
    "southern utah thunderbirds":       "s. utah",
    "new mexico state aggies":          "new mexico st.",
    "sam houston state bearkats":       "sam houston st.",
    "stephen f. austin lumberjacks":    "sfa",
    "stephen f austin lumberjacks":     "sfa",
    "lamar cardinals":                  "lamar",
    "george washington revolutionaries": "g. washington",
    "central connecticut blue devils":  "central conn.",
    "sacred heart pioneers":            "sacred heart",
    "st. francis red flash":            "saint francis pa",
    "saint francis (pa) red flash":     "saint francis pa",
    "saint francis red flash":          "saint francis pa",
    "new haven chargers":               "new haven",

    # ── NC State — ESPN uses multiple name formats ────────────────────────────
    "nc state wolfpack":                "n.c. state",
    "north carolina state wolfpack":    "n.c. state",
    "n.c. state wolfpack":              "n.c. state",

    # ── Other fixes from debug run 2026-03-02 ─────────────────────────────────
    # NOMAATCHes (games being skipped entirely)
    "morgan state bears":               "morgan st.",
    "coppin state eagles":              "coppin st.",
    "iowa state cyclones":              "iowa st.",
    "idaho vandals":                    "idaho",
    "weber state wildcats":             "weber st.",
    "idaho state bengals":              "idaho st.",

    # Wrong matches (producing garbage predictions)
    "iu indianapolis jaguars":          "iupui",
    "delaware state hornets":           "delaware st.",
    "northern arizona lumberjacks":     "n. arizona",
    "se louisiana lions":               "se louisiana",
    "texas a&m-corpus christi islanders": "tx. a&m corpus christi",
    "northwestern state demons":        "northwestern st.",
    "montana state bobcats":            "montana st.",
    "northern colorado bears":          "n. colorado",
    "stephen f. austin lumberjacks":    "sfa",
    "incarnate word cardinals":         "incarnate word",
    "ut rio grande valley vaqueros":    "ut rio grande valley",
    "nicholls colonels":                "nicholls st.",
    "mcneese cowboys":                  "mcneese st.",
    "new orleans privateers":           "new orleans",
    "houston christian huskies":        "houston christian",
    "east texas a&m lions":             "east texas a&m",
}


# ============================================================================
# DATA FETCHING
# ============================================================================

class TeamStatsProvider:
    """
    Fetches and caches team statistics from multiple sources.
    """

    def __init__(self):
        self.team_stats_cache = {}
        self.schedule_cache = {}

    def fetch_team_stats(self):
        """
        Fetch advanced team stats from barttorvik, fallback to ESPN.
        Returns dict of team_name -> stats dict
        """
        try:
            stats = self._fetch_barttorvik_stats()
            if stats:
                self.team_stats_cache = stats
                return stats
        except Exception as e:
            print(f"[WARN] Could not fetch Barttorvik stats: {e}")

        try:
            stats = self._fetch_espn_team_stats()
            if stats:
                self.team_stats_cache = stats
                return stats
        except Exception as e:
            print(f"[WARN] Could not fetch ESPN stats: {e}")

        print("[ERROR] No stats source available. Model cannot run.")
        return {}

    def _fetch_barttorvik_stats(self):
        """
        Fetch T-Rank data from barttorvik.com

        Barttorvik list-of-lists format (2026_team_results.json):
        Index mapping based on observed data:
        [0]  = rank
        [1]  = team name
        [2]  = conference
        [3]  = record (e.g. "25-2")
        [4]  = AdjOE
        [5]  = AdjOE rank
        [6]  = AdjDE
        [7]  = AdjDE rank
        [8]  = Barthag
        [9]  = Barthag rank
        [10] = wins (float version)
        [11] = losses (float version)
        [12] = AdjTempo (approx)
        [13] = AdjTempo rank
        [14] = SOS (approx)
        [22] = recent AdjOE
        [24] = recent AdjDE
        [26] = projected AdjOE
        [28] = projected AdjDE
        """
        url = "https://barttorvik.com/2026_team_results.json"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CBBModel/1.0)"}

        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None

        try:
            data = resp.json()
        except json.JSONDecodeError:
            return None

        if not isinstance(data, list):
            return None

        stats = {}
        for team in data:
            try:
                if isinstance(team, list):
                    team_name = str(team[1])
                    conf = str(team[2]) if len(team) > 2 else ""

                    # [3] = full season record e.g. "25-2"
                    record = str(team[3]) if len(team) > 3 else "0-0"
                    if "-" in record:
                        wins = int(record.split("-")[0])
                        losses = int(record.split("-")[1])
                    else:
                        wins, losses = 0, 0

                    adj_oe  = float(team[4])  if len(team) > 4  else 100.0
                    adj_de  = float(team[6])  if len(team) > 6  else 100.0
                    barthag = float(team[8])  if len(team) > 8  else 0.5
                    # [44] = AdjTempo (confirmed ~65-82 range)
                    adj_tempo = float(team[44]) if len(team) > 44 else 68.0
                    # [33] = SOS
                    sos = float(team[33]) if len(team) > 33 else 0.0
                    # [23] = recent AdjOE, [24] = recent AdjDE
                    recent_adj_oe = float(team[23]) if len(team) > 23 else adj_oe
                    recent_adj_de = float(team[24]) if len(team) > 24 else adj_de

                    stats[self._normalize_team_name(team_name)] = {
                        "adj_oe": adj_oe,
                        "adj_de": adj_de,
                        "adj_tempo": adj_tempo,
                        "barthag": barthag,
                        "wins": wins,
                        "losses": losses,
                        "sos": sos,
                        "conf": conf,
                        # Four Factors — not directly in this endpoint, use defaults
                        "efg_pct":   round((float(team[15]) if len(team) > 15 else 0.50) * 100, 2),
                        "efg_pct_d": round((float(team[16]) if len(team) > 16 else 0.50) * 100, 2),
                        "to_pct":    round((1 - (float(team[17]) if len(team) > 17 else 0.80)) * 100, 2),
                        "to_pct_d":  round((1 - (float(team[18]) if len(team) > 18 else 0.80)) * 100, 2),
                        "orb_pct":   round((float(team[19]) if len(team) > 19 else 0.30) * 100, 2),
                        "drb_pct": 70.0,
                        "ft_rate":   round((float(team[21]) if len(team) > 21 else 0.30) * 100, 2),
                        "ft_rate_d": round((float(team[22]) if len(team) > 22 else 0.30) * 100, 2),
                        "ft_pct": 70.0,
                        "three_pct": 33.0,
                        "three_pct_d": 33.0,
                        "two_pct": 48.0,
                        "two_pct_d": 48.0,
                        "blk_pct": 8.0,
                        "stl_pct": 9.0,
                        "assist_pct": 50.0,
                        "experience": float(team[43]) if len(team) > 43 and isinstance(team[43], (int, float)) and 0 < float(team[43]) < 6 else 1.5,
                        "recent_adj_oe": recent_adj_oe,
                        "recent_adj_de": recent_adj_de,
                    }

                elif isinstance(team, dict):
                    # Handle dict format just in case
                    team_name = team.get("team", team.get("Team", ""))
                    if not team_name:
                        continue
                    adj_oe = float(team.get("adjoe", team.get("AdjOE", 100)))
                    adj_de = float(team.get("adjde", team.get("AdjDE", 100)))
                    record = team.get("record", "0-0")
                    if "-" in str(record):
                        wins = int(str(record).split("-")[0])
                        losses = int(str(record).split("-")[1])
                    else:
                        wins = int(team.get("wins", team.get("W", 0)))
                        losses = int(team.get("losses", team.get("L", 0)))

                    stats[self._normalize_team_name(team_name)] = {
                        "adj_oe": adj_oe,
                        "adj_de": adj_de,
                        "adj_tempo": float(team.get("adjtempo", team.get("AdjTempo", 68))),
                        "barthag": float(team.get("barthag", team.get("Barthag", 0.5))),
                        "wins": wins,
                        "losses": losses,
                        "sos": float(team.get("sos", team.get("SOS", 0))),
                        "conf": team.get("conf", team.get("Conf", "")),
                        "efg_pct": float(team.get("efg", team.get("eFG%", 50))),
                        "efg_pct_d": float(team.get("efg_d", team.get("DeFG%", 50))),
                        "to_pct": float(team.get("tov", team.get("TO%", 18))),
                        "to_pct_d": float(team.get("tov_d", team.get("DTO%", 18))),
                        "orb_pct": float(team.get("orb", team.get("ORB%", 30))),
                        "drb_pct": float(team.get("drb", team.get("DRB%", 70))),
                        "ft_rate": float(team.get("ftr", team.get("FTRate", 30))),
                        "ft_rate_d": float(team.get("ftr_d", team.get("DFTRate", 30))),
                        "ft_pct": float(team.get("ft_pct", team.get("FT%", 70))),
                        "three_pct": float(team.get("three_pct", team.get("3P%", 33))),
                        "three_pct_d": float(team.get("three_pct_d", team.get("D3P%", 33))),
                        "two_pct": float(team.get("two_pct", team.get("2P%", 48))),
                        "two_pct_d": float(team.get("two_pct_d", team.get("D2P%", 48))),
                        "blk_pct": float(team.get("blk", team.get("Blk%", 8))),
                        "stl_pct": float(team.get("stl", team.get("Stl%", 9))),
                        "assist_pct": float(team.get("ast", team.get("Ast%", 50))),
                        "experience": float(team.get("exp", team.get("Exp", 1.5))),
                        "recent_adj_oe": float(team.get("adjoe_recent", adj_oe)),
                        "recent_adj_de": float(team.get("adjde_recent", adj_de)),
                    }

            except (IndexError, ValueError, TypeError):
                continue

        return stats if stats else None

    def _fetch_espn_team_stats(self):
        """Fetch basic team stats from ESPN API"""
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        stats = {}
        for team in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            team_info = team.get("team", {})
            name = team_info.get("displayName", "")
            stats[self._normalize_team_name(name)] = self._default_stats(name)
        return stats

    def _default_stats(self, team_name):
        """Return default/average stats when real data unavailable"""
        return {
            "adj_oe": 100.0,
            "adj_de": 100.0,
            "adj_tempo": 68.0,
            "barthag": 0.5,
            "wins": 0,
            "losses": 0,
            "sos": 0.0,
            "conf": "",
            "efg_pct": 50.0,
            "efg_pct_d": 50.0,
            "to_pct": 18.0,
            "to_pct_d": 18.0,
            "orb_pct": 30.0,
            "drb_pct": 70.0,
            "ft_rate": 30.0,
            "ft_rate_d": 30.0,
            "ft_pct": 70.0,
            "three_pct": 33.0,
            "three_pct_d": 33.0,
            "two_pct": 48.0,
            "two_pct_d": 48.0,
            "blk_pct": 8.0,
            "stl_pct": 9.0,
            "assist_pct": 50.0,
            "experience": 1.5,
            "recent_adj_oe": 100.0,
            "recent_adj_de": 100.0,
        }


    def _normalize_team_name(self, name):
        """Normalize team names for matching across sources."""
        import unicodedata
        # Strip accents (José -> Jose)
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = name.strip()

        # Check alias table first (before any other normalization)
        lower = name.lower()
        if lower in ESPN_TO_BARTTORVIK:
            return ESPN_TO_BARTTORVIK[lower]

        # Remove common ESPN nickname suffixes
        for suffix in [
            " Blue Devils", " Tar Heels", " Wildcats", " Bulldogs", " Tigers",
            " Eagles", " Bears", " Lions", " Hawks", " Knights", " Warriors",
            " Cougars", " Huskies", " Trojans", " Bruins", " Volunteers",
            " Hoosiers", " Boilermakers", " Spartans", " Wolverines", " Buckeyes",
            " Longhorns", " Sooners", " Jayhawks", " Cyclones", " Cowboys",
            " Red Raiders", " Mountaineers", " Panthers", " Cardinals", " Ducks",
            " Beavers", " Utes", " Sun Devils", " Buffaloes", " Golden Bears",
            " Aggies", " Horned Frogs", " Mustangs", " Mean Green", " Roadrunners",
            " Golden Eagles", " Flames", " Braves", " Broncos", " Falcons",
            " Chippewas", " Flashes", " Chanticleers", " Screaming Eagles",
            " RedHawks", " Redhawks", " Rockets", " Zips", " Bulls",
            " Thundering Herd", " Monarchs", " Musketeers", " Bearcats",
            " Hilltoppers", " Colonels", " Leathernecks", " Ramblers",
            " Explorers", " Billikens", " Flyers", " Friars", " Hoyas",
            " Retrievers", " Greyhounds", " Ravens", " Terrapins", " Terps",
            " Fighting Irish", " Orange", " Crimson Tide", " Razorbacks",
            " Gators", " Seminoles", " Hurricanes", " Hokies", " Cavaliers",
            " Demon Deacons", " Yellow Jackets", " Cornhuskers", " Hawkeyes",
            " Badgers", " Gophers", " Illini", " Ramblin Wrecks",
            " Midshipmen", " Black Knights", " Cadets",
        ]:
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break

        replacements = {
            "Saint ": "St. ",
            "State": "St.",
            "University": "",
            "  ": " ",
        }
        for old_str, new_str in replacements.items():
            name = name.replace(old_str, new_str)
        return name.strip().lower()

    def fetch_odds(self):
        """
        Fetch live spreads and totals from The Odds API.
        Returns a dict keyed by normalized team name pairs for fast lookup.
        Format: { "team_a|team_b": { spread, over_under, favorite, bookmaker } }
        """
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "spreads,totals",
            "oddsFormat": "american",
            "bookmakers": "draftkings,fanduel,betmgm,williamhill_us",
        }
        try:
            resp = requests.get(ODDS_API_URL, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"[WARN] Odds API returned {resp.status_code}: {resp.text[:200]}")
                return {}

            data = resp.json()
            odds_map = {}

            for game in data:
                home = game.get("home_team", "")
                away = game.get("away_team", "")
                home_key = self._normalize_team_name(home)
                away_key = self._normalize_team_name(away)

                spread = None
                over_under = None
                favorite = None
                bookmaker_used = None

                # Walk through bookmakers, prefer DraftKings then FanDuel
                for bookie in game.get("bookmakers", []):
                    bookmaker_used = bookie.get("key", "")
                    for market in bookie.get("markets", []):
                        if market["key"] == "spreads" and spread is None:
                            for outcome in market.get("outcomes", []):
                                if outcome["name"] == home:
                                    spread = float(outcome["point"])
                                    favorite = home if spread < 0 else away
                        if market["key"] == "totals" and over_under is None:
                            for outcome in market.get("outcomes", []):
                                if outcome["name"] == "Over":
                                    over_under = float(outcome["point"])
                    if spread is not None and over_under is not None:
                        break

                if spread is not None:
                    key = f"{home_key}|{away_key}"
                    odds_map[key] = {
                        "spread": spread,          # from home team perspective (negative = home favored)
                        "over_under": over_under,
                        "favorite": favorite,
                        "bookmaker": bookmaker_used,
                        "home_team": home,
                        "away_team": away,
                    }

            print(f"       Loaded odds for {len(odds_map)} games from The Odds API")
            return odds_map

        except Exception as e:
            print(f"[WARN] Could not fetch odds: {e}")
            return {}

    def fetch_schedule(self, date_str):
        """
        Fetch the day's schedule from ESPN API.
        date_str format: YYYYMMDD
        """
        params = {
            "dates": date_str,
            "limit": 500,
            "groups": 50,  # Division I
        }

        games = []
        try:
            resp = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=15)
            data = resp.json()

            for event in data.get("events", []):
                competition = event.get("competitions", [{}])[0]
                competitors = competition.get("competitors", [])

                if len(competitors) != 2:
                    continue

                home_team = None
                away_team = None
                for c in competitors:
                    team_data = {
                        "id": c.get("id", ""),
                        "name": c.get("team", {}).get("displayName", ""),
                        "abbreviation": c.get("team", {}).get("abbreviation", ""),
                        "logo": c.get("team", {}).get("logo", ""),
                        "rank": c.get("curatedRank", {}).get("current", 99),
                        "record": c.get("records", [{}])[0].get("summary", "0-0") if c.get("records") else "0-0",
                    }
                    if c.get("homeAway") == "home":
                        home_team = team_data
                    else:
                        away_team = team_data

                if home_team and away_team:
                    game_info = {
                        "game_id": event.get("id", ""),
                        "date": event.get("date", ""),
                        "name": event.get("name", ""),
                        "home": home_team,
                        "away": away_team,
                        "venue": competition.get("venue", {}).get("fullName", ""),
                        "neutral_site": competition.get("neutralSite", False),
                        "conference_game": competition.get("conferenceCompetition", False),
                        "broadcast": competition.get("broadcasts", [{}])[0].get("names", [""])[0] if competition.get("broadcasts") else "",
                        "status": event.get("status", {}).get("type", {}).get("name", ""),
                        "odds": self._extract_odds(competition),
                    }
                    games.append(game_info)

        except Exception as e:
            print(f"[ERROR] Failed to fetch schedule: {e}")

        return games

    def _extract_odds(self, competition):
        """Extract betting odds from ESPN data"""
        odds_data = competition.get("odds", [{}])
        if not odds_data:
            return None
        odds = odds_data[0]
        return {
            "spread": odds.get("spread", 0),
            "over_under": odds.get("overUnder", 0),
            "spread_holder": odds.get("spreadHolder", {}).get("displayName", ""),
            "favorite_id": odds.get("spreadHolder", {}).get("id", ""),
        }


# ============================================================================
# PREDICTION MODEL
# ============================================================================

class CBBPredictionModel:
    """
    Multi-factor college basketball prediction model.

    Core methodology:
    1. Start with adjusted efficiency margin (KenPom-style)
    2. Layer in Four Factors analysis
    3. Apply tempo adjustment for projected pace
    4. Factor in situational variables (home court, rest, travel)
    5. Apply recent form weighting
    6. Generate point spread, projected total, and win probability
    """

    def __init__(self, team_stats):
        self.team_stats = team_stats
        self.predictions = []

    def predict_game(self, game):
        """Generate a full prediction for a single game"""
        home = game["home"]
        away = game["away"]

        home_name = self._find_team(home["name"])
        away_name = self._find_team(away["name"])

        if not home_name or not away_name:
            if getattr(self, "debug", False):
                if not home_name:
                    print(f"  [NOMATCH] {home['name']}")
                if not away_name:
                    print(f"  [NOMATCH] {away['name']}")
            return None

        if getattr(self, "debug", False):
            print(f"  [MATCH] {home['name']} → {home_name}  |  {away['name']} → {away_name}")

        home_stats = self.team_stats[home_name]
        away_stats = self.team_stats[away_name]

        # ---- CORE: Adjusted Efficiency Margin ----
        # Project each team's points per 100 possessions against the other's defense.
        # Formula: (Team_AdjOE * Opp_AdjDE) / national_avg
        # This gives efficiency in points-per-100-possessions units.
        national_avg_oe = 100.0
        home_projected_oe = home_stats["adj_oe"] + away_stats["adj_de"] - 100.0
        away_projected_oe = away_stats["adj_oe"] + home_stats["adj_de"] - 100.0

        # Efficiency differential (points per 100 possessions)
        efficiency_margin = home_projected_oe - away_projected_oe

        # ---- TEMPO PROJECTION ----
        projected_tempo = (home_stats["adj_tempo"] + away_stats["adj_tempo"]) / 2

        # ---- CONVERT EFFICIENCY TO ACTUAL POINTS ----
        # Multiply by (tempo / 100) to get expected point margin for this game's pace.
        # e.g. efficiency_margin=8.0, tempo=68 → raw_margin = 8.0 * (68/100) = 5.4 pts
        raw_margin = efficiency_margin * (projected_tempo / 100.0)

        # ---- HOME COURT ADVANTAGE ----
        if game.get("neutral_site", False):
            hca = NEUTRAL_SITE_ADVANTAGE
        else:
            hca = HOME_COURT_ADVANTAGE_PTS

        # ---- RECENT FORM (small nudge only) ----
        # adj_oe/adj_de already capture turnovers, rebounding, shooting, etc.
        # Adding those on top is double-counting. Only recent trend is additive.
        home_recent_net = home_stats.get("recent_adj_oe", home_stats["adj_oe"]) - home_stats.get("recent_adj_de", home_stats["adj_de"])
        away_recent_net = away_stats.get("recent_adj_oe", away_stats["adj_oe"]) - away_stats.get("recent_adj_de", away_stats["adj_de"])
        home_trend = home_recent_net - (home_stats["adj_oe"] - home_stats["adj_de"])
        away_trend = away_recent_net - (away_stats["adj_oe"] - away_stats["adj_de"])
        # Convert to points, cap at ±2 pts
        recent_form_pts = max(-2.0, min(2.0, (home_trend - away_trend) * (projected_tempo / 100.0) * 0.25))

        # Zero out secondary factors (all captured inside adj_oe/adj_de)
        four_factors_margin = self._calc_four_factors(home_stats, away_stats)
        turnover_margin     = self._calc_turnover_advantage(home_stats, away_stats)
        rebounding_margin   = self._calc_rebounding_advantage(home_stats, away_stats)
        three_point_margin  = self._calc_three_point_advantage(home_stats, away_stats)
        ft_margin           = self._calc_ft_advantage(home_stats, away_stats)
        recent_form_diff    = recent_form_pts
        to_margin       = self._calc_turnover_advantage(home_stats, away_stats)
        reb_margin      = self._calc_rebounding_advantage(home_stats, away_stats)
        three_pt_margin = self._calc_three_point_advantage(home_stats, away_stats)
        ft_margin       = self._calc_ft_advantage(home_stats, away_stats)
        exp_margin      = (home_stats.get("barthag", 0.5) - away_stats.get("barthag", 0.5)) * 2.0
        sos_margin          = (home_stats.get("sos", 0.0) - away_stats.get("sos", 0.0)) * 2.0

        # ============================================================
        # FINAL PREDICTION = efficiency margin (in pts) + HCA + recent trend
        # ============================================================
        # Scale factor contributions (they're additive adjustments in points)
        # four_factors/TO/reb are huge because Barttorvik values are 0-1 decimals
        # treated as percentages in calc functions — scale down accordingly
        ff_contribution  = max(min(four_factors_margin * 0.015, 3.0), -3.0)
        to_contribution  = max(min(to_margin * 0.015, 2.0), -2.0)
        reb_contribution = max(min(reb_margin * 0.5, 2.0), -2.0)
        ft_contribution  = max(min(ft_margin * 0.015, 1.5), -1.5)
        exp_contribution = max(min(exp_margin, 1.0), -1.0)

        predicted_margin = raw_margin + hca + recent_form_pts + ff_contribution + to_contribution + reb_contribution + ft_contribution + exp_contribution

        # ---- PROJECT TOTAL SCORE ----
        # Apply 0.905 calibration factor — barttorvik AdjOE/AdjDE are inflated
        # relative to actual game scores; empirically derived from market O/U comparison.
        projected_total = projected_tempo * (home_projected_oe + away_projected_oe) / 100 * 0.905

        # ---- WIN PROBABILITY ----
        std_dev = 11.0
        home_win_prob = 1 / (1 + math.exp(-predicted_margin / (std_dev * 0.5)))

        # ---- CONFIDENCE RATING ----
        confidence = self._calc_confidence(
            predicted_margin, home_stats, away_stats,
            game.get("odds"), projected_total
        )

        # ---- VALUE RATING vs MARKET ----
        # The Odds API spread is stored in home-team perspective:
        #   negative = home is favored (e.g. Toledo at home = -11.5)
        #   positive = away is favored (e.g. home is underdog = +11.5)
        # predicted_margin is also in home-team perspective (positive = home wins).
        # Value = how many pts our prediction differs from the market line.
        # Toledo: predicted_margin=+13.7, market=-11.5 → both mean "Toledo by X"
        #   Model says Toledo by 13.7, market says Toledo by 11.5 → edge = 2.2
        #   Correct math: spread_diff = 13.7 - 11.5 = 2.2 (compare absolute margins)
        value_rating = None
        market_spread = None
        market_spread_home = None
        if game.get("odds") and game["odds"].get("spread") is not None:
            market_spread_home = float(game["odds"]["spread"])
            market_spread = market_spread_home
            # Convert both to "home team margin" and subtract
            # market_spread_home is negative when home favored, so negate it to get margin
            # Both margins expressed as "home team wins by X" (negative = away wins)
            market_margin = -market_spread_home  # e.g. -(-11.5) = +11.5 = "Toledo wins by 11.5"
            model_margin = predicted_margin       # e.g. +13.7 = "Toledo wins by 13.7"
            spread_diff = model_margin - market_margin  # e.g. 13.7 - 11.5 = +2.2

            # Express spread_edge from the PICK's perspective so + always means covers:
            # If pick is home team, home margin being larger = covers = positive edge (already correct)
            # If pick is away team, away margin being larger = covers, but away margin is negative,
            # so a more-negative model_margin vs market = covers = flip sign
            pick_is_home = predicted_margin > 0
            spread_edge = spread_diff if pick_is_home else -spread_diff
            value_rating = abs(spread_diff)

        prediction = {
            "game_id": game["game_id"],
            "date": game["date"],
            "home_team": home["name"],
            "away_team": away["name"],
            "home_abbr": home["abbreviation"],
            "away_abbr": away["abbreviation"],
            "home_logo": home.get("logo", ""),
            "away_logo": away.get("logo", ""),
            "home_rank": home.get("rank", 99),
            "away_rank": away.get("rank", 99),
            "home_record": home.get("record", ""),
            "away_record": away.get("record", ""),
            "venue": game.get("venue", ""),
            "neutral_site": game.get("neutral_site", False),
            "conference_game": game.get("conference_game", False),
            "broadcast": game.get("broadcast", ""),
            "predicted_spread": round(predicted_margin, 1),
            "predicted_total": round(projected_total, 1),
            "home_projected_score": round((projected_total + predicted_margin) / 2, 1),
            "away_projected_score": round((projected_total - predicted_margin) / 2, 1),
            "home_win_prob": round(home_win_prob * 100, 1),
            "away_win_prob": round((1 - home_win_prob) * 100, 1),
            "confidence": round(confidence, 1),
            "pick": home["name"] if predicted_margin > 0 else away["name"],
            "pick_abbr": home["abbreviation"] if predicted_margin > 0 else away["abbreviation"],
            "factors": {
                "efficiency_margin": round(raw_margin, 2),
                "four_factors": round(ff_contribution, 2),
                "home_court": round(hca, 2),
                "recent_form": round(recent_form_diff, 2),
                "turnover_margin": round(to_contribution, 2),
                "rebounding": round(reb_contribution, 2),
                "three_point": round(three_pt_margin, 2),
                "free_throw": round(ft_contribution, 2),
                "experience": round(exp_contribution, 2),
                "sos": round(sos_margin, 2),
            },
            "market": {
                "spread": game.get("odds", {}).get("spread") if game.get("odds") else None,
                "over_under": game.get("odds", {}).get("over_under") if game.get("odds") else None,
                "spread_holder": game.get("odds", {}).get("spread_holder") if game.get("odds") else None,
            },
            "value_rating": round(value_rating, 1) if value_rating else None,
            "model_vs_market": {
                "spread_edge": round(spread_edge, 1) if value_rating is not None else None,
                "total_edge": round(projected_total - (game.get("odds", {}).get("over_under") or 0), 1) if game.get("odds") and game["odds"].get("over_under") else None,
            },
        }

        return prediction


    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for matching."""
        import unicodedata
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = name.strip()
        lower = name.lower()
        # Check alias table
        espn_map = getattr(self, '_espn_map', {})
        if lower in espn_map:
            return espn_map[lower]
        # Strip common nicknames
        nicknames = [
            " Blue Devils", " Tar Heels", " Wildcats", " Bulldogs", " Tigers",
            " Eagles", " Bears", " Lions", " Hawks", " Knights", " Warriors",
            " Cougars", " Huskies", " Trojans", " Bruins", " Volunteers",
            " Hoosiers", " Boilermakers", " Spartans", " Wolverines", " Buckeyes",
            " Longhorns", " Sooners", " Jayhawks", " Cyclones", " Cowboys",
            " Red Raiders", " Mountaineers", " Panthers", " Cardinals", " Ducks",
            " Beavers", " Utes", " Sun Devils", " Buffaloes", " Golden Bears",
            " Aggies", " Horned Frogs", " Mustangs", " Mean Green", " Roadrunners",
            " Golden Eagles", " Flames", " Braves", " Broncos", " Falcons",
            " Musketeers", " Bearcats", " Hilltoppers", " Colonels", " Explorers",
            " Billikens", " Flyers", " Friars", " Hoyas", " Retrievers",
            " Greyhounds", " Ravens", " Terrapins", " Fighting Irish", " Orange",
            " Crimson Tide", " Razorbacks", " Gators", " Seminoles", " Hurricanes",
            " Hokies", " Cavaliers", " Demon Deacons", " Yellow Jackets",
            " Cornhuskers", " Hawkeyes", " Badgers", " Gophers", " Illini",
            " Midshipmen", " Black Knights", " Owls", " Gaels", " Ramblers",
            " Redhawks", " RedHawks", " Rockets", " Zips", " Bulls",
            " Thundering Herd", " Monarchs", " Leathernecks", " Paladins",
            " Buccaneers", " Citadel", " Purple Aces", " Bruins",
        ]
        for suffix in nicknames:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        name = name.replace("Saint ", "St. ").replace("  ", " ")
        return name.strip().lower()

    def _find_team(self, team_name):
        """Find team in stats cache. Uses alias table first, then normalization, then fuzzy."""
        import unicodedata

        # Step 1: Check alias table on the raw ESPN name
        raw_lower = team_name.strip().lower()
        # Strip accents for alias lookup
        raw_ascii = unicodedata.normalize("NFD", raw_lower)
        raw_ascii = "".join(c for c in raw_ascii if unicodedata.category(c) != "Mn")
        if raw_ascii in ESPN_TO_BARTTORVIK:
            target = ESPN_TO_BARTTORVIK[raw_ascii]
            if target in self.team_stats:
                return target

        # Step 2: Normalize and direct match
        normalized = self._normalize_team_name(team_name)
        if normalized in self.team_stats:
            return normalized

        # Step 3: Exact match after stripping nickname
        normalized_stripped = self._strip_nickname(normalized)
        if normalized_stripped and normalized_stripped in self.team_stats:
            return normalized_stripped

        # Step 4: Key is a substring of normalized (barttorvik abbreviated name inside ESPN name)
        # Only accept if the barttorvik key is at least 6 chars to avoid false matches
        for key in self.team_stats:
            if len(key) >= 6 and key in normalized:
                return key

        # Step 5: Normalized is a substring of the key
        for key in self.team_stats:
            if len(normalized) >= 6 and normalized in key:
                return key

        # Step 6: Word-level overlap — require 2+ shared words, or 1 word that is
        # at least 7 chars (avoids matching "michigan" across WMU/CMU/EMU/Michigan)
        norm_words = set(normalized.split())
        stripped_words = set(normalized_stripped.split()) if normalized_stripped else set()
        combined_words = norm_words | stripped_words
        GENERIC = {"the", "of", "at", "a", "and", "st.", "state", "university",
                   "north", "south", "east", "west", "northern", "southern",
                   "eastern", "western", "central", "upper", "lower", "new",
                   "old", "great", "little", "big"}
        best_key = None
        best_score = 0
        for key in self.team_stats:
            key_words = set(key.split())
            shared = (combined_words & key_words) - GENERIC
            if not shared:
                continue
            # Score: prefer more shared words, and longer shared words
            score = sum(len(w) for w in shared) + len(shared) * 2
            # Require either 2+ shared words, or 1 word of 7+ chars
            qualifies = len(shared) >= 2 or any(len(w) >= 7 for w in shared)
            if qualifies and score > best_score:
                best_score = score
                best_key = key
        if best_key:
            return best_key

        return None

    def _strip_nickname(self, name):
        """Strip common team nicknames from a name string"""
        nicknames = [
            "blue devils", "tar heels", "wildcats", "bulldogs", "tigers",
            "eagles", "bears", "lions", "hawks", "knights", "warriors",
            "cougars", "huskies", "trojans", "bruins", "volunteers",
            "hoosiers", "boilermakers", "spartans", "wolverines", "buckeyes",
            "longhorns", "sooners", "jayhawks", "cyclones", "cowboys",
            "red raiders", "mountaineers", "panthers", "cardinals", "ducks",
            "beavers", "utes", "sun devils", "buffaloes", "golden bears",
            "aggies", "horned frogs", "mustangs", "mean green", "roadrunners",
            "golden eagles", "flames", "braves", "razorbacks", "gators",
            "seminoles", "hurricanes", "hokies", "cavaliers", "demon deacons",
            "yellow jackets", "ramblin wrecks", "orange", "crimson tide",
            "cornhuskers", "hawkeyes", "badgers", "gophers", "illini",
            "fighting irish", "friars", "hoyas", "ravens", "terrapins",
            "terps", "retrievers", "greyhounds", "retrievers",
        ]
        for nick in sorted(nicknames, key=len, reverse=True):
            if name.endswith(" " + nick):
                return name[: -(len(nick) + 1)].strip()
        return name

    def _calc_four_factors(self, home, away):
        """Four Factors differential. Oliver's weights: eFG% 40%, TO% 25%, ORB% 20%, FT Rate 15%"""
        home_efg_adv = home["efg_pct"] - away["efg_pct_d"]
        home_to_adv  = away["to_pct_d"] - home["to_pct"]
        home_orb_adv = home["orb_pct"] - (100 - away["drb_pct"])
        home_ft_adv  = home["ft_rate"] - away["ft_rate_d"]

        away_efg_adv = away["efg_pct"] - home["efg_pct_d"]
        away_to_adv  = home["to_pct_d"] - away["to_pct"]
        away_orb_adv = away["orb_pct"] - (100 - home["drb_pct"])
        away_ft_adv  = away["ft_rate"] - home["ft_rate_d"]

        home_ff = home_efg_adv * 0.40 + home_to_adv * 0.25 + home_orb_adv * 0.20 + home_ft_adv * 0.15
        away_ff = away_efg_adv * 0.40 + away_to_adv * 0.25 + away_orb_adv * 0.20 + away_ft_adv * 0.15

        return home_ff - away_ff

    def _calc_recent_form(self, home, away):
        """Recent form differential"""
        home_recent_margin = home.get("recent_adj_oe", home["adj_oe"]) - home.get("recent_adj_de", home["adj_de"])
        away_recent_margin = away.get("recent_adj_oe", away["adj_oe"]) - away.get("recent_adj_de", away["adj_de"])
        home_season_margin = home["adj_oe"] - home["adj_de"]
        away_season_margin = away["adj_oe"] - away["adj_de"]
        home_trend = home_recent_margin - home_season_margin
        away_trend = away_recent_margin - away_season_margin
        return (home_trend - away_trend) * 0.5

    def _calc_turnover_advantage(self, home, away):
        """TO margin differential"""
        home_to_diff = away["to_pct_d"] - home["to_pct"]
        away_to_diff = home["to_pct_d"] - away["to_pct"]
        return (home_to_diff - away_to_diff) * 0.3

    def _calc_rebounding_advantage(self, home, away):
        """Rebounding margin differential"""
        home_reb = home["orb_pct"] + home["drb_pct"]
        away_reb = away["orb_pct"] + away["drb_pct"]
        return (home_reb - away_reb) * 0.1

    def _calc_three_point_advantage(self, home, away):
        """Three-point shooting matchup advantage"""
        home_three_adv = home["three_pct"] - away["three_pct_d"]
        away_three_adv = away["three_pct"] - home["three_pct_d"]
        return (home_three_adv - away_three_adv) * 0.4

    def _calc_ft_advantage(self, home, away):
        """Free throw shooting and rate advantage"""
        home_ft = home["ft_rate"] * home["ft_pct"] / 100
        away_ft = away["ft_rate"] * away["ft_pct"] / 100
        return (home_ft - away_ft) * 0.15

    def _calc_confidence(self, margin, home_stats, away_stats, odds, total):
        """Calculate prediction confidence (0-100)."""
        margin_conf = min(abs(margin) * 3, 40)

        games_played = min(
            home_stats.get("wins", 0) + home_stats.get("losses", 0),
            away_stats.get("wins", 0) + away_stats.get("losses", 0),
        )
        data_conf = min(games_played * 2, 25)

        market_conf = 0
        if odds and odds.get("spread"):
            market_spread = odds["spread"]
            if (margin > 0 and market_spread < 0) or (margin < 0 and market_spread > 0):
                market_conf = 10
            else:
                market_conf = -5

        barthag_diff = abs(home_stats.get("barthag", 0.5) - away_stats.get("barthag", 0.5))
        barthag_conf = min(barthag_diff * 50, 20)

        total_conf = margin_conf + data_conf + market_conf + barthag_conf
        return max(min(total_conf, 98), 15)

    def predict_all_games(self, games):
        """Generate predictions for all games in the schedule"""
        predictions = []
        skipped = 0
        for game in games:
            try:
                pred = self.predict_game(game)
                if pred:
                    predictions.append(pred)
                else:
                    skipped += 1
            except Exception as e:
                print(f"[WARN] Could not predict {game.get('name', 'unknown')}: {e}")
                skipped += 1

        if skipped > 0:
            print(f"       (Skipped {skipped} games — teams not found in stats cache)")

        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return predictions


# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def generate_output(predictions, date_str, output_format="json"):
    """Generate output file for the website"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = {
        "generated_at": datetime.now().isoformat(),
        "date": date_str,
        "total_games": len(predictions),
        "model_version": "2.1.0",
        "picks": predictions,
        "summary": {
            "total_games": len(predictions),
            "high_confidence": len([p for p in predictions if p["confidence"] >= 70]),
            "medium_confidence": len([p for p in predictions if 40 <= p["confidence"] < 70]),
            "low_confidence": len([p for p in predictions if p["confidence"] < 40]),
            "avg_confidence": round(sum(p["confidence"] for p in predictions) / max(len(predictions), 1), 1),
            "value_plays": len([p for p in predictions if p.get("value_rating") and p["value_rating"] >= 3]),
        },
    }

    if output_format == "json":
        filepath = os.path.join(OUTPUT_DIR, f"picks_{date_str}.json")
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)
        print(f"[OK] Picks saved to {filepath}")

        latest_path = os.path.join(OUTPUT_DIR, "latest.json")
        with open(latest_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"[OK] Latest picks updated at {latest_path}")

        # Auto-copy to public/ so the React app can serve it
        public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
        if os.path.isdir(public_dir):
            public_path = os.path.join(public_dir, "latest.json")
            with open(public_path, "w") as f:
                json.dump(output, f, indent=2)
            print(f"[OK] Public copy updated at {public_path}")

    return output


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="College Basketball Prediction Model")
    parser.add_argument("--date", type=str, help="Date to predict (YYYY-MM-DD), defaults to today")
    parser.add_argument("--debug", action="store_true", help="Print team matching details")
    parser.add_argument(
        "--output", type=str, default="json", choices=["json", "csv", "console"],
        help="Output format",
    )
    args = parser.parse_args()

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    date_str = target_date.strftime("%Y%m%d")
    display_date = target_date.strftime("%B %d, %Y")

    print(f"\n{'='*60}")
    print(f"  College Basketball Prediction Model v2.1")
    print(f"  Generating picks for: {display_date}")
    print(f"{'='*60}\n")

    provider = TeamStatsProvider()

    print("[1/3] Fetching team statistics...")
    team_stats = provider.fetch_team_stats()
    if not team_stats:
        print("[ERROR] No team stats available. Exiting.")
        sys.exit(1)
    print(f"       Loaded stats for {len(team_stats)} teams")

    print(f"[2/3] Fetching schedule + odds for {display_date}...")
    games = provider.fetch_schedule(date_str)
    if not games:
        print(f"[WARN] No games found for {display_date}")
        sys.exit(0)
    print(f"       Found {len(games)} games")

    # Fetch real market odds and merge into games
    odds_map = provider.fetch_odds()
    if odds_map:
        matched = 0
        for game in games:
            home_key = provider._normalize_team_name(game["home"]["name"])
            away_key = provider._normalize_team_name(game["away"]["name"])
            odds = odds_map.get(f"{home_key}|{away_key}") or odds_map.get(f"{away_key}|{home_key}")
            if not odds:
                for key, val in odds_map.items():
                    k_home = provider._normalize_team_name(val["home_team"])
                    k_away = provider._normalize_team_name(val["away_team"])
                    if (home_key in k_home or k_home in home_key) and \
                       (away_key in k_away or k_away in away_key):
                        odds = val
                        break
            if odds:
                game["odds"] = {
                    "spread": odds["spread"],
                    "over_under": odds["over_under"],
                    "spread_holder": odds["favorite"],
                    "favorite_id": "",
                    "bookmaker": odds.get("bookmaker", ""),
                }
                matched += 1
        print(f"       Matched odds for {matched}/{len(games)} games")
    else:
        print("       [WARN] No odds available — value ratings will be unavailable")

    print("[3/3] Running prediction model...")
    model = CBBPredictionModel(team_stats)
    model.debug = args.debug
    predictions = model.predict_all_games(games)
    print(f"       Generated {len(predictions)} predictions")

    print(f"\n{'='*60}")
    output = generate_output(predictions, date_str, args.output)

    if args.output == "console":
        for i, p in enumerate(predictions, 1):
            # --- Model pick line ---
            # If model disagrees with market direction (spread_edge < 0 with market available),
            # the pick to cover is the OTHER side of the market, not the model winner.
            mkt = p.get("market", {})
            edge = p.get("model_vs_market", {}).get("spread_edge")
            has_market = mkt.get("spread") is not None and mkt.get("spread_holder")

            if has_market and edge is not None and edge < 0:
                # Model winner won't cover — pick the other side to cover
                model_winner_abbr = p["pick_abbr"]
                cover_abbr = p["home_abbr"] if p["pick_abbr"] == p["away_abbr"] else p["away_abbr"]
                cover_name = p["home_team"] if p["pick_abbr"] == p["away_abbr"] else p["away_team"]
                market_line = abs(mkt["spread"])
                spread_display = f"{cover_abbr} +{market_line:.1f}  (model: {model_winner_abbr} wins but doesn't cover)"
            else:
                spread_display = f"{p['pick_abbr']} -{abs(p['predicted_spread']):.1f}"

            print(f"\n  #{i} [{p['confidence']:.0f}% conf] {p['away_team']} @ {p['home_team']}")
            print(f"     Model Pick:    {spread_display}")

            # --- Market spread: always show as FAVORITE -X ---
            if has_market:
                mkt_spread_home = mkt["spread"]   # negative = home favored, positive = away favored
                mkt_holder = mkt["spread_holder"]  # name of the favorite team
                market_line = abs(mkt_spread_home)
                ou = mkt.get("over_under")
                ou_str = f"  O/U {ou}" if ou else ""
                print(f"     Market Spread: {mkt_holder} -{market_line:.1f}{ou_str}")
            else:
                print(f"     Market Spread: n/a")

            print(f"     Projected:     {p['away_abbr']} {p['away_projected_score']:.0f} - {p['home_abbr']} {p['home_projected_score']:.0f}  (Total: {p['predicted_total']:.1f})")
            if p.get("value_rating") and p["value_rating"] >= 2:
                if edge is not None:
                    cover_str = "covers" if edge > 0 else "falls short"
                    pick_for_display = p["pick_abbr"]
                    print(f"     ★ Value:       {p['value_rating']:.1f} pt edge ({pick_for_display} {cover_str} by {abs(edge):.1f})")
                else:
                    print(f"     ★ Value:       {p['value_rating']:.1f} pt edge")

    print(f"\n{'='*60}")
    print(f"  Summary: {output['summary']['high_confidence']} high confidence picks")
    print(f"           {output['summary']['medium_confidence']} medium confidence picks")
    print(f"           {output['summary']['value_plays']} value plays identified")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
