#!/usr/bin/env python3
"""
Shared pick feed exporter
=========================
Writes the sport-agnostic feed described in FEED_SCHEMA.md so one slate/tracking
app can load picks from the CBB, CFB and NBA model repos with a single loader.

Usage:
    python3 export_feed.py              # write public/feed/cbb/{index,slate,season-<yyyy>}.json
    python3 export_feed.py --validate   # also validate every file against feed_schema.json
                                        # (needs `pip install jsonschema`)

Reads picks/picks_*.json, picks/latest.json and public/results/results.json.
Never modifies them. Runs after grading and pick generation in automate.py.

To publish another sport from its own repo: copy this file, change SPORT and
season_for(), and remap the fields in to_record(). Keep every key; use None
for anything your model does not produce.
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICKS_DIR = os.path.join(BASE_DIR, "picks")
RESULTS_PATH = os.path.join(BASE_DIR, "public", "results", "results.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "feed_schema.json")
EASTERN = ZoneInfo("America/New_York")

SCHEMA_VERSION = "1.0"
SPORT = {
    "sport": "cbb",
    "league": "NCAAM",
    "sport_name": "College Basketball",
    "model_name": "courtside-edge",
    "game_id_source": "espn",
}
FEED_DIR = os.path.join(BASE_DIR, "public", "feed", SPORT["sport"])
PENDING_GRACE = timedelta(hours=24)   # an ungraded pick older than this is "no_result"
PUSH_TOLERANCE = 0.5                  # same rule as results_tracker.py


def season_for(date_str):
    """Barttorvik labels a season by the year it ends: Nov 2026 - Apr 2027 -> 2027."""
    d = datetime.strptime(date_str[:10], "%Y-%m-%d")
    return d.year + 1 if d.month >= 10 else d.year


def season_label(season):
    return f"{season - 1}-{str(season)[-2:]}"


def confidence_tier(conf):
    if conf is None:
        return None
    return "high" if conf >= 70 else "medium" if conf >= 40 else "low"


def parse_utc(s):
    """ESPN-style '2026-11-11T18:00Z' or a full ISO timestamp -> aware UTC datetime."""
    s = s.replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def market_block(mk):
    """Normalize a pick-time or closing line. Spreads are already home-relative in this repo."""
    if not mk:
        return None
    spread, total = mk.get("spread"), mk.get("over_under")
    if spread == 0 and not mk.get("spread_holder"):   # pre-v4 files stored a phantom 0 when ESPN had no line
        spread, total = None, None
    if total == 0:
        total = None
    if spread is None and total is None:
        return None
    return {
        "spread_home": spread,
        "total": total,
        "favorite": mk.get("spread_holder"),
        "bookmaker": mk.get("bookmaker"),
        "captured_at": mk.get("captured_at"),
    }


def team_block(pick, side):
    rank = pick.get(f"{side}_rank")
    return {
        "name": pick[f"{side}_team"],
        "abbr": pick.get(f"{side}_abbr"),
        "logo": pick.get(f"{side}_logo"),
        "record": pick.get(f"{side}_record"),
        "rank": rank if isinstance(rank, int) and 0 < rank < 99 else None,
    }


def to_record(pick, slate_date, model_version, now):
    """One feed record from a pick (graded or not). This is the only sport-specific mapping."""
    season = season_for(pick["date"])
    market = market_block(pick.get("market"))
    closing = market_block(pick.get("closing_line"))
    model_margin = pick.get("predicted_spread")        # projected home margin, + = home favored
    model_total = pick.get("predicted_total")

    spread_home = market["spread_home"] if market else None
    edge_spread = round(model_margin + spread_home, 1) if model_margin is not None and spread_home is not None else None
    edge_total = round(model_total - market["total"], 1) if model_total is not None and market and market["total"] is not None else None

    graded = bool(pick.get("graded"))
    if graded:
        status = "final"
    else:
        status = "pending" if parse_utc(pick["date"]) >= now - PENDING_GRACE else "no_result"

    bet_side = pick.get("bet_side")
    if bet_side is None:   # not graded yet: apply the tracker's rule to the pick-time line
        if edge_spread is None:
            bet_side = "none"
        else:
            bet_side = "home" if edge_spread > PUSH_TOLERANCE else "away" if edge_spread < -PUSH_TOLERANCE else "none"

    pick_team = pick.get("pick")
    if pick.get("is_home_pick") is not None:
        pick_side = "home" if pick["is_home_pick"] else "away"
    else:
        pick_side = "home" if pick_team == pick["home_team"] else "away" if pick_team == pick["away_team"] else None

    result = None
    if graded:
        result = {
            "home_score": pick["actual_home_score"],
            "away_score": pick["actual_away_score"],
            "margin_home": pick["actual_margin"],
            "total": pick["actual_total"],
            "winner": pick.get("actual_winner"),
            "su_correct": pick.get("model_correct_winner"),
            "ats": pick.get("ats_result"),
            "ou_call": pick.get("model_ou_call"),
            "ou_result": pick.get("ou_result"),
            "ou_correct": pick.get("ou_model_correct"),
            "clv": pick.get("clv"),
        }

    value_rating = pick.get("value_rating")
    tags = []
    if pick.get("is_best_bet"):
        tags.append("best_bet")
    if (value_rating or 0) >= 3:
        tags.append("value")
    if (pick.get("confidence") or 0) >= 70:
        tags.append("high_confidence")
    if pick.get("is_tournament_game"):
        tags.append("tournament")
    if pick.get("conference_game"):
        tags.append("conference")

    return {
        "id": f"{SPORT['sport']}:{pick['game_id']}",
        "sport": SPORT["sport"],
        "league": SPORT["league"],
        "season": season,
        "season_label": season_label(season),
        "slate_date": slate_date,
        "game_id": str(pick["game_id"]),
        "game_id_source": SPORT["game_id_source"],
        "start_time": pick["date"],
        "status": status,
        "home": team_block(pick, "home"),
        "away": team_block(pick, "away"),
        "venue": pick.get("venue"),
        "neutral_site": pick.get("neutral_site"),
        "conference_game": pick.get("conference_game"),
        "broadcast": pick.get("broadcast"),
        "model": {
            "version": model_version,
            "spread_home": round(-model_margin, 1) if model_margin is not None else None,
            "total": model_total,
            "home_score": pick.get("home_projected_score"),
            "away_score": pick.get("away_projected_score"),
            "home_win_prob": pick.get("home_win_prob"),
            "confidence": pick.get("confidence"),
            "confidence_tier": confidence_tier(pick.get("confidence")),
            "pick": {"team": pick_team, "abbr": pick.get("pick_abbr"), "side": pick_side},
        },
        "market": market,
        "closing": closing,
        "edge": {
            "spread": edge_spread,
            "total": edge_total,
            "value_rating": value_rating,
            "is_best_bet": bool(pick.get("is_best_bet")),
        },
        "bet": {
            "side": bet_side,
            "cover_line": round(-spread_home, 1) if spread_home is not None else None,
        },
        "result": result,
        "tags": tags,
    }


# ---------------------------------------------------------------- sources

def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def slate_date_of(file_date):
    return f"{file_date[:4]}-{file_date[4:6]}-{file_date[6:]}"


def load_pick_files():
    """{file_date: picks_file_json} for every picks/picks_YYYYMMDD.json, oldest first."""
    files = {}
    for path in sorted(glob.glob(os.path.join(PICKS_DIR, "picks_*.json"))):
        m = re.search(r"picks_(\d{8})\.json$", os.path.basename(path))
        if m:
            files[m.group(1)] = load_json(path, {})
    return files


def build_season_records(pick_files, graded_by_id, now):
    """
    Every pick ever published, keyed by game id, overlaid with its grade. If a game was
    published on more than one slate (postponements), the latest publication wins.
    Returns {season: [records]}.
    """
    latest = {}
    for file_date, data in pick_files.items():
        version = data.get("model_version")
        for pick in data.get("picks", []):
            latest[str(pick["game_id"])] = (pick, slate_date_of(file_date), version)

    # Graded games whose pick file was regenerated or lost still count: fall back to the graded copy.
    for gid, g in graded_by_id.items():
        if gid not in latest:
            latest[gid] = (g, parse_utc(g["date"]).astimezone(EASTERN).strftime("%Y-%m-%d"), None)

    by_season = {}
    for gid, (pick, slate_date, version) in latest.items():
        source = graded_by_id.get(gid, pick)
        rec = to_record(source, slate_date, version, now)
        by_season.setdefault(rec["season"], []).append(rec)
    for recs in by_season.values():
        recs.sort(key=lambda r: (r["start_time"], r["game_id"]))
    return by_season


def header(kind, season, model_version, now):
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "sport": SPORT["sport"],
        "league": SPORT["league"],
        "sport_name": SPORT["sport_name"],
        "model": {"name": SPORT["model_name"], "version": model_version},
        "generated_at": now.astimezone(EASTERN).isoformat(),
        "season": season,
        "season_label": season_label(season),
    }


SUMMARY_KEYS = ("total_graded", "ats_graded", "ats", "su", "ou", "by_confidence",
                "value_plays", "best_bets", "clv", "calibration")


def summary_block(summary):
    return {k: summary[k] for k in SUMMARY_KEYS if k in summary}


def write(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"[OK] {os.path.relpath(path, BASE_DIR)}")


def validate(paths):
    try:
        import jsonschema
    except ImportError:
        print("[ERROR] --validate needs `pip install jsonschema`")
        return False
    schema = load_json(SCHEMA_PATH)
    ok = True
    for path in paths:
        errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(load_json(path)), key=lambda e: e.path)
        if errors:
            ok = False
            e = errors[0]
            print(f"[FAIL] {os.path.relpath(path, BASE_DIR)}: {len(errors)} error(s); first at "
                  f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message[:200]}")
        else:
            print(f"[VALID] {os.path.relpath(path, BASE_DIR)}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Export the shared pick feed")
    ap.add_argument("--validate", action="store_true", help="validate the written files against feed_schema.json")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    results = load_json(RESULTS_PATH, {"games": [], "summary": {}})
    graded_by_id = {str(g["game_id"]): g for g in results.get("games", []) if g.get("graded")}
    pick_files = load_pick_files()
    latest = load_json(os.path.join(PICKS_DIR, "latest.json"), {})

    by_season = build_season_records(pick_files, graded_by_id, now)
    if not by_season and not latest.get("picks"):
        print("[ERROR] nothing to export: no picks or results found")
        sys.exit(1)

    today_season = season_for(now.astimezone(EASTERN).strftime("%Y-%m-%d"))
    current = today_season if today_season in by_season else max(by_season) if by_season else today_season
    model_version = latest.get("model_version")

    written = []
    seasons_meta = []
    for season in sorted(by_season, reverse=True):
        recs = by_season[season]
        path = os.path.join(FEED_DIR, f"season-{season}.json")
        write(path, {**header("season", season, model_version, now), "records": recs})
        written.append(path)
        seasons_meta.append({
            "season": season, "label": season_label(season), "file": os.path.basename(path),
            "records": len(recs),
            "final": sum(r["status"] == "final" for r in recs),
            "pending": sum(r["status"] == "pending" for r in recs),
            "no_result": sum(r["status"] == "no_result" for r in recs),
        })

    slate_date = slate_date_of(latest["date"]) if latest.get("date") else now.astimezone(EASTERN).strftime("%Y-%m-%d")
    slate_records = [to_record(graded_by_id.get(str(p["game_id"]), p), slate_date, model_version, now)
                     for p in latest.get("picks", [])]
    slate_records.sort(key=lambda r: (r["start_time"], r["game_id"]))
    slate_path = os.path.join(FEED_DIR, "slate.json")
    write(slate_path, {**header("slate", season_for(slate_date), model_version, now),
                       "slate_date": slate_date, "records": slate_records})
    written.append(slate_path)

    summary = results.get("summary", {})
    index = {k: v for k, v in header("index", current, model_version, now).items() if k != "kind"}
    index.update({
        "files": {"slate": "slate.json", "season": f"season-{current}.json"},
        "seasons": seasons_meta,
        "slate": {
            "date": slate_date,
            "total_games": len(slate_records),
            "pending": sum(r["status"] == "pending" for r in slate_records),
        },
        "summary": summary_block(summary),
        "all_time": summary_block(summary.get("all_time", summary)),
    })
    index_path = os.path.join(FEED_DIR, "index.json")
    write(index_path, index)
    written.append(index_path)

    for m in seasons_meta:
        print(f"     {m['label']}: {m['records']} records, {m['final']} final, {m['pending']} pending, {m['no_result']} no result")
    print(f"     slate {slate_date}: {len(slate_records)} games")

    if args.validate and not validate(written):
        sys.exit(1)


if __name__ == "__main__":
    main()
