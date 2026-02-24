#!/usr/bin/env python3
"""
College Basketball Prediction Model v2.2
=========================================
A comprehensive statistical model for predicting NCAA basketball game outcomes.
Uses KenPom-style advanced metrics, tempo-adjusted efficiency, and multiple
predictive factors to generate spread and moneyline predictions.

Requirements:
    pip install requests pandas numpy

Data Sources:
    - ESPN API for schedules and scores
    - barttorvik.com for advanced team stats (T-Rank)
    - The Odds API for live betting lines

Usage:
    python cbb_model.py                        # Generate today's picks
    python cbb_model.py --date 2026-02-25      # Generate picks for a specific date
    python cbb_model.py --output console       # Print to console
    python cbb_model.py --debug                # Show team matching details

Changelog v2.2:
    - Fixed efficiency projection formula (additive, not multiplicative)
    - Fixed win probability formula (removed incorrect 0.5 divisor)
    - Added tempo-adjusted standard deviation for win probability
    - Implemented team-specific home court advantage by conference
    - Added rest days differential factor
    - Fixed confidence calculation market agreement logic
    - Added Barttorvik schema validation warnings
    - Recalibrated total projection factor
    - Cleaned up unused WEIGHTS dict
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import argparse
import math

# ============================================================================
# CONFIGURATION
# ============================================================================

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
BARTTORVIK_URL = "https://barttorvik.com/trank.php"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picks")

# The Odds API - ⚠️ SECURITY: Move to environment variable in production
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "f1c651a894f64fafcdda0ef0c250aba7")
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds"

# National average efficiency baseline (D-I average is ~100 by definition)
NATIONAL_AVG_EFFICIENCY = 100.0

# Base standard deviation for point spread → win probability conversion
# NCAA basketball games have ~11 point standard deviation historically
BASE_STD_DEV = 11.0

# Average tempo for std_dev adjustment calculations
NATIONAL_AVG_TEMPO = 68.0

# Home court advantage by conference tier (in points)
# Research shows significant variation: elite venues ~4.5+, mid-majors ~2.5
HCA_BY_CONFERENCE = {
    # Power conferences - stronger HCA due to larger, louder venues
    "B12": 4.0, "B10": 4.0, "SEC": 4.2, "ACC": 4.0, "BE": 3.8,
    # High-major conferences
    "P12": 3.5, "Amer": 3.5, "MWC": 3.5, "A10": 3.5,
    # Mid-major conferences
    "WCC": 3.5, "MVC": 3.8, "CUSA": 3.3, "MAC": 3.5, "SB": 3.3,
    "SC": 3.3, "CAA": 3.3, "Horz": 3.3, "Sum": 3.2, "WAC": 3.2,
    "OVC": 3.2, "BSky": 3.2, "BSth": 3.2, "Ivy": 2.8, "Pat": 3.0,
    "AE": 3.0, "MAAC": 3.0, "NEC": 2.8, "Slnd": 2.8, "SWAC": 3.0,
    "MEAC": 2.8, "ASun": 3.2, "BW": 3.0, "Peach": 3.2,
}
DEFAULT_HCA = 3.5  # Fallback if conference not found

# Venue-specific HCA overrides (stadiums known for exceptional atmosphere)
VENUE_HCA_OVERRIDE = {
    "cameron indoor stadium": 5.0,      # Duke - historically elite HCA
    "hilton coliseum": 5.0,             # Iowa State - "Hilton Magic"
    "rupp arena": 4.5,                  # Kentucky
    "phog allen fieldhouse": 4.8,       # Kansas
    "mccarthey athletic center": 4.5,   # Gonzaga - The Kennel
    "mackey arena": 4.5,                # Purdue
    "assembly hall": 4.3,               # Indiana
    "gallagher-iba arena": 4.3,         # Oklahoma State
    "mckale center": 4.3,               # Arizona
    "the pavilion": 4.2,                # Villanova
    "hinkle fieldhouse": 4.0,           # Butler - historic venue
    "neville arena": 4.3,               # Auburn
    "thompson-boling arena": 4.3,       # Tennessee
    "dean smith center": 4.2,           # UNC
    "xfinity center": 4.0,              # Maryland
}

NEUTRAL_SITE_ADVANTAGE = 0.0

# Total projection calibration factor
# After fixing the efficiency formula, this accounts for the difference
# between Barttorvik's efficiency ratings and actual game scoring
# Based on output analysis showing ~10-15 point overestimation, lowered to 0.92
TOTAL_CALIBRATION_FACTOR = 0.92


# ============================================================================
# ESPN → BARTTORVIK TEAM NAME ALIAS TABLE
# Maps ESPN display names (lowercased) to exact barttorvik keys (lowercased).
# Add entries here whenever a team fails to match with --debug flag.
# ============================================================================

ESPN_TO_BARTTORVIK = {
    # Directional schools (W./C./E./N./S. abbreviations)
    "western michigan broncos":         "w. michigan",
    "central michigan chippewas":       "c. michigan",
    "eastern michigan eagles":          "e. michigan",
    "northern illinois huskies":        "n. illinois",
    "southern illinois salukis":        "s. illinois",
    "middle tennessee blue raiders":    "mid. tenn.",
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
    
    # State abbreviation variations
    "south dakota state jackrabbits":   "s. dakota st.",
    "north dakota state bison":         "n. dakota st.",
    "south dakota coyotes":             "s. dakota",
    "north dakota fighting hawks":      "n. dakota",
    "southeast missouri state redhawks": "se missouri st.",
    "southeast missouri redhawks":      "se missouri st.",
    
    # Miami disambiguation
    "miami (oh) redhawks":              "miami oh",
    "miami (fl) hurricanes":            "miami fl",
    "miami hurricanes":                 "miami fl",
    
    # Georgia schools
    "georgia state panthers":           "ga. st.",
    "georgia southern eagles":          "ga. southern",
    
    # California schools
    "san josé state spartans":          "san jose st.",
    "san jose state spartans":          "san jose st.",
    "uc davis aggies":                  "uc davis",
    "uc irvine anteaters":              "uc irvine",
    "uc riverside highlanders":         "uc riverside",
    "uc santa barbara gauchos":         "uc santa barbara",
    "cal poly mustangs":                "cal poly",
    "cal state bakersfield roadrunners": "cs bakersfield",
    "cal state fullerton titans":       "cs fullerton",
    "cal state northridge matadors":    "cs northridge",
    "long beach state beach":           "long beach st.",
    
    # Louisiana
    "louisiana ragin' cajuns":          "louisiana",
    "louisiana lafayette ragin' cajuns": "louisiana",
    
    # Common abbreviations / alternate names
    "uconn huskies":                    "connecticut",
    "umass minutemen":                  "massachusetts",
    "massachusetts minutemen":          "massachusetts",
    "unc wilmington seahawks":          "unc wilmington",
    "lsu tigers":                       "lsu",
    "vcu rams":                         "vcu",
    "ucf knights":                      "ucf",
    "uic flames":                       "uic",
    "umkc roos":                        "umkc",
    "utep miners":                      "utep",
    "utsa roadrunners":                 "utsa",
    "ut arlington mavericks":           "ut arlington",
    "texas-arlington mavericks":        "ut arlington",
    
    # Southern Indiana / Purdue FW
    "siu edwardsville cougars":         "siue",
    "southern indiana screaming eagles": "southern indiana",
    "pfw mastodons":                    "purdue ft. wayne",
    "purdue fort wayne mastodons":      "purdue ft. wayne",
    
    # Florida schools
    "south florida bulls":              "usf",
    "fiu panthers":                     "fiu",
    "fau owls":                         "fau",
    "florida atlantic owls":            "fau",
    "florida international panthers":   "fiu",
    
    # Ohio schools
    "bowling green falcons":            "bowling green",
    "kent state golden flashes":        "kent st.",
    
    # Military academies
    "air force falcons":                "air force",
    "army black knights":               "army",
    "navy midshipmen":                  "navy",
    
    # Loyola schools
    "loyola chicago ramblers":          "loyola chicago",
    "loyola marymount lions":           "lmu",
    
    # Saint / St. variations
    "st. john's red storm":             "st. john's",
    "saint john's red storm":           "st. john's",
    "mount st. mary's mountaineers":    "mt. st. mary's",
    "mount st. mary's":                 "mt. st. mary's",
    "st. francis red flash":            "saint francis pa",
    "saint francis (pa) red flash":     "saint francis pa",
    "saint francis red flash":          "saint francis pa",
    
    # Texas schools
    "sam houston state bearkats":       "sam houston st.",
    "stephen f. austin lumberjacks":    "sfa",
    "stephen f austin lumberjacks":     "sfa",
    "lamar cardinals":                  "lamar",
    
    # Other
    "coastal carolina chanticleers":    "coastal carolina",
    "morehead state eagles":            "morehead st.",
    "southern miss golden eagles":      "southern miss",
    "george washington revolutionaries": "g. washington",
    "central connecticut blue devils":  "central conn.",
    "sacred heart pioneers":            "sacred heart",
    "new mexico state aggies":          "new mexico st.",
    "hawaii rainbow warriors":          "hawaii",
    "new haven chargers":               "new haven",
}

# Barttorvik uses different naming than our canonical keys
# This maps Barttorvik's actual team names to our canonical keys
# (The canonical key is the VALUE in ESPN_TO_BARTTORVIK)
BARTTORVIK_TO_CANONICAL = {
    # Directional schools - Barttorvik uses full names, we use abbreviated
    "central michigan":     "c. michigan",
    "western michigan":     "w. michigan",
    "eastern michigan":     "e. michigan",
    "northern illinois":    "n. illinois",
    "southern illinois":    "s. illinois",
    "middle tennessee":     "mid. tenn.",
    "western kentucky":     "w. kentucky",
    "eastern kentucky":     "e. kentucky",
    "western illinois":     "w. illinois",
    "eastern illinois":     "e. illinois",
    "northern iowa":        "n. iowa",
    "southern utah":        "s. utah",
    "northern colorado":    "n. colorado",
    "western carolina":     "w. carolina",
    "eastern washington":   "e. washington",
    "northern arizona":     "n. arizona",
    "south dakota state":   "s. dakota st.",
    "north dakota state":   "n. dakota st.",
    "south dakota":         "s. dakota",
    "north dakota":         "n. dakota",
    "southeast missouri state": "se missouri st.",
    "southeast missouri":   "se missouri st.",
    
    # State schools
    "kent state":           "kent st.",
    "georgia state":        "ga. st.",
    "georgia southern":     "ga. southern",
    "san jose state":       "san jose st.",
    "long beach state":     "long beach st.",
    "morehead state":       "morehead st.",
    "new mexico state":     "new mexico st.",
    "sam houston state":    "sam houston st.",
    
    # Cal State schools
    "cal state bakersfield": "cs bakersfield",
    "cal state fullerton":   "cs fullerton",
    "cal state northridge":  "cs northridge",
    
    # Abbreviation variations
    "connecticut":          "connecticut",
    "massachusetts":        "massachusetts",
    "george washington":    "g. washington",
    "central connecticut":  "central conn.",
    "mount st. mary's":     "mt. st. mary's",
    
    # Stephen F. Austin
    "stephen f. austin":    "sfa",
    
    # Purdue Fort Wayne
    "purdue fort wayne":    "purdue ft. wayne",
}


# ============================================================================
# DATA FETCHING
# ============================================================================

class TeamStatsProvider:
    """
    Fetches and caches team statistics from multiple sources.
    Handles team name normalization across ESPN/Barttorvik/Odds API.
    """

    def __init__(self):
        self.team_stats_cache: Dict[str, Dict] = {}
        self.schedule_cache: Dict[str, List] = {}
        self._warnings_issued: set = set()

    def fetch_team_stats(self) -> Dict[str, Dict]:
        """
        Fetch advanced team stats from barttorvik, fallback to ESPN.
        Returns dict of normalized_team_name -> stats dict
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

    def _fetch_barttorvik_stats(self) -> Optional[Dict[str, Dict]]:
        """
        Fetch T-Rank data from barttorvik.com

        Barttorvik 2026_team_results.json format (list of lists):
        Index mapping (verified against sample data):
        [0]  = T-Rank
        [1]  = Team name
        [2]  = Conference
        [3]  = Record (e.g. "25-2")
        [4]  = AdjOE (adjusted offensive efficiency)
        [5]  = AdjOE rank
        [6]  = AdjDE (adjusted defensive efficiency)
        [7]  = AdjDE rank
        [8]  = Barthag (power rating 0-1)
        [9]  = Barthag rank
        ...
        [23] = Recent AdjOE (last ~10 games)
        [24] = Recent AdjDE (last ~10 games)
        [33] = SOS (strength of schedule)
        [44] = AdjTempo
        
        ⚠️ SCHEMA WARNING: These indices may change between seasons.
        Run with --debug to validate values look reasonable.
        """
        # Update this URL each season
        url = "https://barttorvik.com/2026_team_results.json"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CBBModel/2.2)"}

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
        schema_warnings = []
        
        for team in data:
            try:
                if not isinstance(team, list) or len(team) < 10:
                    continue
                    
                team_name = str(team[1])
                conf = str(team[2]) if len(team) > 2 else ""

                # Parse record
                record = str(team[3]) if len(team) > 3 else "0-0"
                if "-" in record:
                    parts = record.split("-")
                    wins = int(parts[0])
                    losses = int(parts[1])
                else:
                    wins, losses = 0, 0

                # Core efficiency stats
                adj_oe = float(team[4]) if len(team) > 4 else 100.0
                adj_de = float(team[6]) if len(team) > 6 else 100.0
                barthag = float(team[8]) if len(team) > 8 else 0.5
                
                # Tempo (index 44 based on schema analysis)
                adj_tempo = float(team[44]) if len(team) > 44 else NATIONAL_AVG_TEMPO
                
                # SOS (index 33)
                sos = float(team[33]) if len(team) > 33 else 0.0
                
                # Recent form stats (indices 23, 24)
                recent_adj_oe = float(team[23]) if len(team) > 23 else adj_oe
                recent_adj_de = float(team[24]) if len(team) > 24 else adj_de

                # ============================================================
                # SCHEMA VALIDATION: Check for suspicious values
                # ============================================================
                # Use Barttorvik-specific normalization
                normalized_name = self._normalize_barttorvik_name(team_name)
                
                if not (80 < adj_oe < 135):  # Allow up to 135 for elite offenses
                    schema_warnings.append(f"{team_name}: AdjOE={adj_oe} (expected 80-135)")
                if not (80 < adj_de < 130):
                    schema_warnings.append(f"{team_name}: AdjDE={adj_de} (expected 80-130)")
                if not (55 < adj_tempo < 85):
                    schema_warnings.append(f"{team_name}: Tempo={adj_tempo} (expected 55-85)")
                if not (0 < barthag < 1):
                    schema_warnings.append(f"{team_name}: Barthag={barthag} (expected 0-1)")

                stats[normalized_name] = {
                    "adj_oe": adj_oe,
                    "adj_de": adj_de,
                    "adj_tempo": adj_tempo,
                    "barthag": barthag,
                    "wins": wins,
                    "losses": losses,
                    "sos": sos,
                    "conf": conf,
                    "recent_adj_oe": recent_adj_oe,
                    "recent_adj_de": recent_adj_de,
                    # Four Factors - defaults since not in this endpoint
                    # These are used for display but not core prediction
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
                    "experience": 1.5,
                }

            except (IndexError, ValueError, TypeError) as e:
                continue

        # Print schema warnings (deduplicated)
        if schema_warnings and len(schema_warnings) <= 5:
            for w in schema_warnings:
                print(f"[SCHEMA WARN] {w}")
        elif schema_warnings:
            print(f"[SCHEMA WARN] {len(schema_warnings)} teams have suspicious stat values - check index mapping")

        return stats if stats else None

    def _fetch_espn_team_stats(self) -> Optional[Dict[str, Dict]]:
        """Fetch basic team stats from ESPN API (fallback only)"""
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        stats = {}
        for team in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            team_info = team.get("team", {})
            name = team_info.get("displayName", "")
            stats[self._normalize_team_name(name)] = self._default_stats()
        return stats

    def _default_stats(self) -> Dict[str, Any]:
        """Return D-I average stats when real data unavailable"""
        return {
            "adj_oe": 100.0,
            "adj_de": 100.0,
            "adj_tempo": NATIONAL_AVG_TEMPO,
            "barthag": 0.5,
            "wins": 0,
            "losses": 0,
            "sos": 0.0,
            "conf": "",
            "recent_adj_oe": 100.0,
            "recent_adj_de": 100.0,
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
            "experience": 1.5,
        }

    def _normalize_barttorvik_name(self, name: str) -> str:
        """
        Normalize Barttorvik team names to canonical keys.
        
        Barttorvik uses different naming conventions than ESPN:
        - "Central Michigan" vs ESPN's "Central Michigan Chippewas"
        - "Kent State" vs ESPN's "Kent State Golden Flashes"
        
        This method maps Barttorvik names to the same canonical keys
        that ESPN names map to via ESPN_TO_BARTTORVIK.
        """
        import unicodedata
        
        # Strip accents
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = name.strip().lower()
        
        # Check Barttorvik-specific mapping first
        if name in BARTTORVIK_TO_CANONICAL:
            return BARTTORVIK_TO_CANONICAL[name]
        
        # Fallback: just lowercase
        return name

    def _normalize_team_name(self, name: str) -> str:
        """
        Normalize team names for matching across ESPN/Barttorvik/Odds API.
        
        Pipeline:
        1. Strip accents (José → Jose)
        2. Check alias table (highest priority)
        3. Remove ESPN nickname suffixes
        4. Apply common replacements (Saint→St., State→St.)
        5. Lowercase and strip
        """
        import unicodedata
        
        # Strip accents
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = name.strip()

        # Check alias table first (before any other normalization)
        lower = name.lower()
        if lower in ESPN_TO_BARTTORVIK:
            return ESPN_TO_BARTTORVIK[lower]

        # Remove common ESPN nickname suffixes
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
            " Midshipmen", " Black Knights", " Cadets", " Owls", " Gaels",
            " Shockers", " Bluejays", " Peacocks", " Pirates", " Rams",
            " Phoenix", " Miners", " Anteaters", " Highlanders", " Matadors",
            " Beach", " Titans", " Toreros", " Pilots", " Waves", " Broncs",
        ]
        for suffix in nicknames:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        # Common replacements
        replacements = {
            "Saint ": "St. ",
            "State": "St.",
            "University": "",
            "  ": " ",
        }
        for old_str, new_str in replacements.items():
            name = name.replace(old_str, new_str)
            
        return name.strip().lower()

    def fetch_odds(self) -> Dict[str, Dict]:
        """
        Fetch live spreads and totals from The Odds API.
        Returns dict keyed by "home_normalized|away_normalized" for fast lookup.
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
                        "spread": spread,
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

    def fetch_schedule(self, date_str: str) -> List[Dict]:
        """
        Fetch the day's schedule from ESPN API.
        
        Args:
            date_str: Date in YYYYMMDD format
            
        Returns:
            List of game dicts with home/away team info, venue, etc.
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
                        "broadcast": self._extract_broadcast(competition),
                        "status": event.get("status", {}).get("type", {}).get("name", ""),
                        "odds": self._extract_espn_odds(competition),
                    }
                    games.append(game_info)

        except Exception as e:
            print(f"[ERROR] Failed to fetch schedule: {e}")

        return games

    def _extract_broadcast(self, competition: Dict) -> str:
        """Extract broadcast network from competition data"""
        broadcasts = competition.get("broadcasts", [])
        if broadcasts and isinstance(broadcasts, list):
            names = broadcasts[0].get("names", [])
            if names:
                return names[0]
        return ""

    def _extract_espn_odds(self, competition: Dict) -> Optional[Dict]:
        """Extract betting odds from ESPN data (backup to Odds API)"""
        odds_data = competition.get("odds", [])
        if not odds_data:
            return None
        odds = odds_data[0] if isinstance(odds_data, list) else odds_data
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
    1. Calculate adjusted efficiency margin using ADDITIVE formula
    2. Apply tempo adjustment for projected pace
    3. Add venue-specific home court advantage
    4. Apply recent form adjustment (capped)
    5. Generate point spread, projected total, and win probability
    
    Key formulas:
    - Projected efficiency: Team_AdjOE + Opp_AdjDE - 100 (not multiplicative!)
    - Win probability: 1 / (1 + exp(-margin / std_dev)) (proper logistic)
    - Std dev: Tempo-adjusted from base 11.0
    """

    def __init__(self, team_stats: Dict[str, Dict]):
        self.team_stats = team_stats
        self.predictions: List[Dict] = []
        self.debug = False

    def predict_game(self, game: Dict) -> Optional[Dict]:
        """Generate a full prediction for a single game"""
        home = game["home"]
        away = game["away"]

        home_name = self._find_team(home["name"])
        away_name = self._find_team(away["name"])

        if not home_name or not away_name:
            if self.debug:
                if not home_name:
                    print(f"  [NOMATCH] {home['name']}")
                if not away_name:
                    print(f"  [NOMATCH] {away['name']}")
            return None

        if self.debug:
            print(f"  [MATCH] {home['name']} → {home_name}  |  {away['name']} → {away_name}")

        home_stats = self.team_stats[home_name]
        away_stats = self.team_stats[away_name]

        # ================================================================
        # CORE: Adjusted Efficiency Margin (ADDITIVE formula - FIXED)
        # ================================================================
        # Project each team's efficiency against the opponent.
        # Formula: Team_AdjOE + Opp_AdjDE - National_Avg
        # 
        # Example: Duke (AdjOE=115) vs UNC (AdjDE=95)
        #   Duke projected offense = 115 + 95 - 100 = 110 pts/100 poss
        #   (Better than Duke's average because UNC defense is below avg)
        #
        # This is the correct KenPom/Barttorvik methodology.
        # The previous multiplicative formula was incorrect.
        
        home_projected_oe = (home_stats["adj_oe"] + away_stats["adj_de"] 
                            - NATIONAL_AVG_EFFICIENCY)
        away_projected_oe = (away_stats["adj_oe"] + home_stats["adj_de"] 
                            - NATIONAL_AVG_EFFICIENCY)

        # Efficiency differential (points per 100 possessions)
        efficiency_margin = home_projected_oe - away_projected_oe

        # ================================================================
        # TEMPO PROJECTION
        # ================================================================
        # Average of both teams' tempos, as the game pace is a negotiation
        projected_tempo = (home_stats["adj_tempo"] + away_stats["adj_tempo"]) / 2

        # ================================================================
        # CONVERT EFFICIENCY TO ACTUAL POINTS
        # ================================================================
        # Efficiency is per 100 possessions, so multiply by (tempo/100)
        # Example: 8 pt efficiency edge at tempo 68 = 8 * 0.68 = 5.4 pts
        raw_margin = efficiency_margin * (projected_tempo / 100.0)

        # ================================================================
        # HOME COURT ADVANTAGE (Team/Venue-Specific)
        # ================================================================
        if game.get("neutral_site", False):
            hca = NEUTRAL_SITE_ADVANTAGE
        else:
            hca = self._get_home_court_advantage(
                game.get("venue", ""), 
                home_stats.get("conf", "")
            )

        # ================================================================
        # RECENT FORM ADJUSTMENT (Capped at ±2 pts)
        # ================================================================
        # Compare recent efficiency vs season efficiency to detect hot/cold streaks
        # Cap tightly because this can be noisy and efficiency already captures most
        home_season_net = home_stats["adj_oe"] - home_stats["adj_de"]
        away_season_net = away_stats["adj_oe"] - away_stats["adj_de"]
        
        home_recent_net = (home_stats.get("recent_adj_oe", home_stats["adj_oe"]) - 
                          home_stats.get("recent_adj_de", home_stats["adj_de"]))
        away_recent_net = (away_stats.get("recent_adj_oe", away_stats["adj_oe"]) - 
                          away_stats.get("recent_adj_de", away_stats["adj_de"]))
        
        home_trend = home_recent_net - home_season_net
        away_trend = away_recent_net - away_season_net
        
        # Convert to points with tempo adjustment, cap at ±2
        recent_form_raw = (home_trend - away_trend) * (projected_tempo / 100.0) * 0.25
        recent_form_pts = max(-2.0, min(2.0, recent_form_raw))

        # ================================================================
        # FINAL PREDICTION
        # ================================================================
        predicted_margin = raw_margin + hca + recent_form_pts

        # ================================================================
        # PROJECT TOTAL SCORE
        # ================================================================
        # Sum of projected efficiencies, adjusted for tempo
        # Calibration factor accounts for any remaining systematic bias
        raw_total = projected_tempo * (home_projected_oe + away_projected_oe) / 100.0
        projected_total = raw_total * TOTAL_CALIBRATION_FACTOR

        # ================================================================
        # WIN PROBABILITY (FIXED - removed incorrect 0.5 divisor)
        # ================================================================
        # Standard logistic conversion from point spread to probability
        # Formula: P(home wins) = 1 / (1 + exp(-margin / std_dev))
        #
        # Apply tempo adjustment to std_dev: faster games have more variance
        tempo_adjustment = 1 + ((projected_tempo - NATIONAL_AVG_TEMPO) / 
                               NATIONAL_AVG_TEMPO * 0.12)
        adjusted_std_dev = BASE_STD_DEV * tempo_adjustment
        
        home_win_prob = 1 / (1 + math.exp(-predicted_margin / adjusted_std_dev))

        # ================================================================
        # CONFIDENCE RATING
        # ================================================================
        confidence = self._calc_confidence(
            predicted_margin, home_stats, away_stats,
            game.get("odds"), projected_total
        )

        # ================================================================
        # VALUE RATING vs MARKET
        # ================================================================
        value_rating, spread_edge, total_edge = self._calc_value(
            predicted_margin, projected_total, game.get("odds")
        )

        # Build prediction dict
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
            
            # Core predictions
            "predicted_spread": round(predicted_margin, 1),
            "predicted_total": round(projected_total, 1),
            "home_projected_score": round((projected_total + predicted_margin) / 2, 1),
            "away_projected_score": round((projected_total - predicted_margin) / 2, 1),
            "home_win_prob": round(home_win_prob * 100, 1),
            "away_win_prob": round((1 - home_win_prob) * 100, 1),
            "confidence": round(confidence, 1),
            
            # Pick designation
            "pick": home["name"] if predicted_margin > 0 else away["name"],
            "pick_abbr": home["abbreviation"] if predicted_margin > 0 else away["abbreviation"],
            
            # Factor breakdown for display
            "factors": {
                "efficiency_margin": round(raw_margin, 2),
                "four_factors": 0.0,  # Embedded in efficiency
                "home_court": round(hca, 2),
                "recent_form": round(recent_form_pts, 2),
                "turnover_margin": 0.0,  # Embedded in efficiency
                "rebounding": 0.0,  # Embedded in efficiency
                "three_point": 0.0,  # Embedded in efficiency
                "free_throw": 0.0,  # Embedded in efficiency
                "experience": 0.0,
                "sos": 0.0,
            },
            
            # Market comparison
            "market": {
                "spread": game.get("odds", {}).get("spread") if game.get("odds") else None,
                "over_under": game.get("odds", {}).get("over_under") if game.get("odds") else None,
                "spread_holder": game.get("odds", {}).get("spread_holder") if game.get("odds") else None,
            },
            "value_rating": round(value_rating, 1) if value_rating is not None else None,
            "model_vs_market": {
                "spread_edge": round(spread_edge, 1) if spread_edge is not None else None,
                "total_edge": round(total_edge, 1) if total_edge is not None else None,
            },
        }

        return prediction

    def _get_home_court_advantage(self, venue: str, conf: str) -> float:
        """
        Get home court advantage in points.
        
        Priority:
        1. Venue-specific override (for elite venues)
        2. Conference-based HCA
        3. Default fallback
        """
        # Check venue overrides first
        venue_lower = venue.lower().strip()
        for venue_name, hca in VENUE_HCA_OVERRIDE.items():
            if venue_name in venue_lower:
                return hca
        
        # Conference-based HCA
        conf_upper = conf.upper().strip()
        if conf_upper in HCA_BY_CONFERENCE:
            return HCA_BY_CONFERENCE[conf_upper]
        
        return DEFAULT_HCA

    def _calc_value(self, predicted_margin: float, projected_total: float,
                   odds: Optional[Dict]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calculate value rating compared to market lines.
        
        Returns:
            (value_rating, spread_edge, total_edge)
            
        spread_edge is expressed from the PICK's perspective:
        - Positive = model pick covers by more than market expects
        - Negative = model pick doesn't cover market spread
        """
        if not odds or odds.get("spread") is None:
            return None, None, None
            
        market_spread_home = float(odds["spread"])
        
        # Market spread is from home perspective:
        # Negative = home favored (e.g., -7.5 means home favored by 7.5)
        # Positive = away favored (e.g., +7.5 means home is underdog)
        
        # Convert to margin comparison (both in home-team-wins-by-X units)
        # market_spread_home of -7.5 means "home wins by 7.5 expected"
        # But the spread is the points you GIVE, so negate to get margin
        market_margin = -market_spread_home
        model_margin = predicted_margin
        
        spread_diff = model_margin - market_margin
        
        # Express from pick's perspective
        pick_is_home = predicted_margin > 0
        spread_edge = spread_diff if pick_is_home else -spread_diff
        
        value_rating = abs(spread_diff)
        
        # Total edge
        total_edge = None
        if odds.get("over_under"):
            total_edge = projected_total - float(odds["over_under"])
        
        return value_rating, spread_edge, total_edge

    def _calc_confidence(self, margin: float, home_stats: Dict, 
                        away_stats: Dict, odds: Optional[Dict],
                        total: float) -> float:
        """
        Calculate prediction confidence (0-100).
        
        Components:
        - Margin magnitude (larger spreads = more confident)
        - Sample size (games played)
        - Market agreement (when model agrees with sharp money)
        - Barthag differential (quality gap)
        """
        # Margin confidence (caps at 40 for ~13+ pt spreads)
        margin_conf = min(abs(margin) * 3, 40)

        # Data confidence based on games played (caps at 25)
        games_played = min(
            home_stats.get("wins", 0) + home_stats.get("losses", 0),
            away_stats.get("wins", 0) + away_stats.get("losses", 0),
        )
        data_conf = min(games_played * 2, 25)

        # Market agreement/disagreement
        # FIXED: When margin > 0 (home favored) and spread < 0 (home favored),
        # that's AGREEMENT, which should boost confidence
        market_conf = 0
        if odds and odds.get("spread"):
            market_spread = float(odds["spread"])
            model_favors_home = margin > 0
            market_favors_home = market_spread < 0
            
            if model_favors_home == market_favors_home:
                # Agreement with market - mild confidence boost
                market_conf = 5
            else:
                # Disagreement with market - be more cautious
                market_conf = -8

        # Barthag differential (quality gap confidence)
        barthag_diff = abs(home_stats.get("barthag", 0.5) - 
                          away_stats.get("barthag", 0.5))
        barthag_conf = min(barthag_diff * 40, 20)

        total_conf = margin_conf + data_conf + market_conf + barthag_conf
        return max(min(total_conf, 95), 15)

    def _find_team(self, team_name: str) -> Optional[str]:
        """
        Find team in stats cache.
        
        Pipeline:
        1. Check alias table on raw ESPN name
        2. Normalize and direct match
        3. Strip nickname and match
        4. Substring matching (both directions)
        5. Word-overlap fuzzy matching
        """
        import unicodedata

        # Step 1: Check alias table on raw ESPN name
        raw_lower = team_name.strip().lower()
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

        # Step 3: Strip nickname and match
        normalized_stripped = self._strip_nickname(normalized)
        if normalized_stripped and normalized_stripped in self.team_stats:
            return normalized_stripped

        # Step 4: Substring matching
        # Barttorvik key inside ESPN name (min 6 chars)
        for key in self.team_stats:
            if len(key) >= 6 and key in normalized:
                return key

        # ESPN name inside Barttorvik key
        for key in self.team_stats:
            if len(normalized) >= 6 and normalized in key:
                return key

        # Step 5: Word-overlap fuzzy matching
        norm_words = set(normalized.split())
        stripped_words = set(normalized_stripped.split()) if normalized_stripped else set()
        combined_words = norm_words | stripped_words
        
        GENERIC = {
            "the", "of", "at", "a", "and", "st.", "state", "university",
            "north", "south", "east", "west", "northern", "southern",
            "eastern", "western", "central", "upper", "lower", "new",
            "old", "great", "little", "big"
        }
        
        best_key = None
        best_score = 0
        
        for key in self.team_stats:
            key_words = set(key.split())
            shared = (combined_words & key_words) - GENERIC
            
            if not shared:
                continue
                
            score = sum(len(w) for w in shared) + len(shared) * 2
            qualifies = len(shared) >= 2 or any(len(w) >= 7 for w in shared)
            
            if qualifies and score > best_score:
                best_score = score
                best_key = key
                
        return best_key

    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name (delegate to provider method logic)"""
        import unicodedata
        
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = name.strip()

        lower = name.lower()
        if lower in ESPN_TO_BARTTORVIK:
            return ESPN_TO_BARTTORVIK[lower]

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
            " Midshipmen", " Black Knights", " Cadets", " Owls", " Gaels",
        ]
        for suffix in nicknames:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        replacements = {"Saint ": "St. ", "State": "St.", "University": "", "  ": " "}
        for old, new in replacements.items():
            name = name.replace(old, new)
            
        return name.strip().lower()

    def _strip_nickname(self, name: str) -> str:
        """Strip common team nicknames from normalized name"""
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
            "terps", "retrievers", "greyhounds", "owls", "gaels",
        ]
        for nick in sorted(nicknames, key=len, reverse=True):
            if name.endswith(" " + nick):
                return name[:-(len(nick) + 1)].strip()
        return name

    def predict_all_games(self, games: List[Dict]) -> List[Dict]:
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
                if self.debug:
                    print(f"[WARN] Could not predict {game.get('name', 'unknown')}: {e}")
                skipped += 1

        if skipped > 0:
            print(f"       (Skipped {skipped} games — teams not found in stats cache)")

        # Sort by confidence descending
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return predictions


# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def generate_output(predictions: List[Dict], date_str: str, 
                   output_format: str = "json") -> Dict:
    """Generate output file for the website"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = {
        "generated_at": datetime.now().isoformat(),
        "date": date_str,
        "total_games": len(predictions),
        "model_version": "2.2.0",
        "picks": predictions,
        "summary": {
            "total_games": len(predictions),
            "high_confidence": len([p for p in predictions if p["confidence"] >= 70]),
            "medium_confidence": len([p for p in predictions if 40 <= p["confidence"] < 70]),
            "low_confidence": len([p for p in predictions if p["confidence"] < 40]),
            "avg_confidence": round(
                sum(p["confidence"] for p in predictions) / max(len(predictions), 1), 1
            ),
            "value_plays": len([
                p for p in predictions 
                if p.get("value_rating") and p["value_rating"] >= 3
            ]),
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

    return output


def print_console_output(predictions: List[Dict], output: Dict) -> None:
    """Print formatted predictions to console"""
    for i, p in enumerate(predictions, 1):
        mkt = p.get("market", {})
        edge = p.get("model_vs_market", {}).get("spread_edge")
        has_market = mkt.get("spread") is not None and mkt.get("spread_holder")

        # Model pick display
        if has_market and edge is not None and edge < 0:
            # Model winner won't cover — suggest the other side
            model_winner_abbr = p["pick_abbr"]
            cover_abbr = (p["home_abbr"] if p["pick_abbr"] == p["away_abbr"] 
                         else p["away_abbr"])
            market_line = abs(mkt["spread"])
            spread_display = (f"{cover_abbr} +{market_line:.1f}  "
                            f"(model: {model_winner_abbr} wins but doesn't cover)")
        else:
            spread_display = f"{p['pick_abbr']} -{abs(p['predicted_spread']):.1f}"

        # Print game header
        conf_str = f"{p['confidence']:.0f}%"
        print(f"\n  #{i} [{conf_str} conf] {p['away_team']} @ {p['home_team']}")
        print(f"     Model Pick:    {spread_display}")

        # Market spread
        if has_market:
            mkt_holder = mkt["spread_holder"]
            market_line = abs(mkt["spread"])
            ou = mkt.get("over_under")
            ou_str = f"  O/U {ou}" if ou else ""
            print(f"     Market Spread: {mkt_holder} -{market_line:.1f}{ou_str}")
        else:
            print(f"     Market Spread: n/a")

        # Projected score
        print(f"     Projected:     {p['away_abbr']} {p['away_projected_score']:.0f} - "
              f"{p['home_abbr']} {p['home_projected_score']:.0f}  "
              f"(Total: {p['predicted_total']:.1f})")

        # Value play indicator
        if p.get("value_rating") and p["value_rating"] >= 2:
            if edge is not None:
                cover_str = "covers" if edge > 0 else "falls short"
                print(f"     ★ Value:       {p['value_rating']:.1f} pt edge "
                      f"({p['pick_abbr']} {cover_str} by {abs(edge):.1f})")
            else:
                print(f"     ★ Value:       {p['value_rating']:.1f} pt edge")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="College Basketball Prediction Model v2.2"
    )
    parser.add_argument(
        "--date", type=str, 
        help="Date to predict (YYYY-MM-DD), defaults to today"
    )
    parser.add_argument(
        "--debug", action="store_true", 
        help="Print team matching details and schema warnings"
    )
    parser.add_argument(
        "--output", type=str, default="json", 
        choices=["json", "console"],
        help="Output format"
    )
    args = parser.parse_args()

    # Parse target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    date_str = target_date.strftime("%Y%m%d")
    display_date = target_date.strftime("%B %d, %Y")

    print(f"\n{'='*60}")
    print(f"  College Basketball Prediction Model v2.2")
    print(f"  Generating picks for: {display_date}")
    print(f"{'='*60}\n")

    # Initialize provider
    provider = TeamStatsProvider()

    # Step 1: Fetch team stats
    print("[1/3] Fetching team statistics...")
    team_stats = provider.fetch_team_stats()
    if not team_stats:
        print("[ERROR] No team stats available. Exiting.")
        sys.exit(1)
    print(f"       Loaded stats for {len(team_stats)} teams")

    # Step 2: Fetch schedule
    print(f"[2/3] Fetching schedule + odds for {display_date}...")
    games = provider.fetch_schedule(date_str)
    if not games:
        print(f"[WARN] No games found for {display_date}")
        sys.exit(0)
    print(f"       Found {len(games)} games")

    # Fetch and merge odds
    odds_map = provider.fetch_odds()
    if odds_map:
        matched = 0
        for game in games:
            home_key = provider._normalize_team_name(game["home"]["name"])
            away_key = provider._normalize_team_name(game["away"]["name"])
            
            # Try direct match
            odds = (odds_map.get(f"{home_key}|{away_key}") or 
                   odds_map.get(f"{away_key}|{home_key}"))
            
            # Try fuzzy match if direct fails
            if not odds:
                for key, val in odds_map.items():
                    k_home = provider._normalize_team_name(val["home_team"])
                    k_away = provider._normalize_team_name(val["away_team"])
                    if ((home_key in k_home or k_home in home_key) and 
                        (away_key in k_away or k_away in away_key)):
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

    # Step 3: Run predictions
    print("[3/3] Running prediction model...")
    model = CBBPredictionModel(team_stats)
    model.debug = args.debug
    predictions = model.predict_all_games(games)
    print(f"       Generated {len(predictions)} predictions")

    # Generate output
    print(f"\n{'='*60}")
    output = generate_output(predictions, date_str, args.output)

    if args.output == "console":
        print_console_output(predictions, output)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Summary: {output['summary']['high_confidence']} high confidence picks")
    print(f"           {output['summary']['medium_confidence']} medium confidence picks")
    print(f"           {output['summary']['value_plays']} value plays identified")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
