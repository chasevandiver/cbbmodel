#!/usr/bin/env python3
"""
Results Tracker v1.0
=====================
Fetches actual game scores from ESPN and grades yesterday's model picks.
Run this each morning AFTER games have completed (before generating new picks).

Usage:
    python3 results_tracker.py                    # Grade yesterday's picks
    python3 results_tracker.py --date 2026-02-24  # Grade a specific date
    python3 results_tracker.py --rebuild          # Rebuild full results from all dated pick files

Output:
    public/results/results.json  — full graded history for the dashboard
"""

import requests
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, List

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
PICKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "picks")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "results")


def fetch_scores(date_str: str) -> Dict[str, Dict]:
    """
    Fetch completed game scores from ESPN for a given date (YYYYMMDD).
    Returns dict keyed by normalized "home|away" for matching.
    """
    params = {"dates": date_str, "limit": 500, "groups": 50}
    try:
        resp = requests.get(ESPN_SCOREBOARD_URL, params=params, timeout=15)
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] Could not fetch scores for {date_str}: {e}")
        return {}

    scores = {}
    for event in data.get("events", []):
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", {}).get("type", {}).get("completed", False)
        if not status:
            continue  # Skip games not yet completed

        competitors = competition.get("competitors", [])
        if len(competitors) != 2:
            continue

        home_team = away_team = None
        home_score = away_score = 0

        for c in competitors:
            name = c.get("team", {}).get("displayName", "")
            score = int(c.get("score", 0) or 0)
            if c.get("homeAway") == "home":
                home_team = name
                home_score = score
            else:
                away_team = name
                away_score = score

        if home_team and away_team:
            key = f"{home_team.lower()}|{away_team.lower()}"
            scores[key] = {
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "total": home_score + away_score,
                "margin": home_score - away_score,  # positive = home won
            }

    return scores


def fuzzy_match_game(pick: Dict, scores: Dict) -> Optional[Dict]:
    """
    Match a pick to an actual score result.
    Tries exact match first, then partial name matching.
    """
    home = pick["home_team"].lower()
    away = pick["away_team"].lower()

    # Direct key match
    key = f"{home}|{away}"
    if key in scores:
        return scores[key]

    # Try fuzzy: find score where both team names are substrings
    for score_key, score in scores.items():
        sh = score["home_team"].lower()
        sa = score["away_team"].lower()
        # Check if 6+ char substring of pick name appears in score name
        home_match = any(w in sh or sh in home for w in home.split() if len(w) >= 5)
        away_match = any(w in sa or sa in away for w in away.split() if len(w) >= 5)
        if home_match and away_match:
            return score

    return None


def grade_pick(pick: Dict, result: Dict) -> Dict:
    """
    Grade a single pick against the actual result.

    Returns graded pick with:
    - ats_result: "W" / "L" / "P" (push)
    - ou_result: "O" / "U" / "P"
    - actual_home_score, actual_away_score
    - actual_margin, actual_total
    """
    actual_margin = result["margin"]   # positive = home won
    actual_total = result["total"]
    model_margin = pick["predicted_spread"]  # positive = model favors home
    market_spread = pick.get("market", {}).get("spread")  # home perspective (negative = home fav)
    market_ou = pick.get("market", {}).get("over_under")

    # ---- ATS grading ----
    # We grade against the market spread if available, otherwise model spread
    if market_spread is not None:
        # Market spread is from home perspective: -7 = home favored by 7
        # Home covers if: actual_margin > -market_spread (i.e. home wins by more than spread)
        # Away covers if: actual_margin < -market_spread
        cover_line = -float(market_spread)  # convert to margin threshold
    else:
        cover_line = 0  # just grade straight up if no market line

    if abs(actual_margin - cover_line) < 0.5:
        ats_result = "P"  # push (within 0.5)
    elif actual_margin > cover_line:
        # Home covered
        if model_margin > 0:
            ats_result = "W"  # model picked home, home covered
        else:
            ats_result = "L"  # model picked away, home covered (away didn't cover)
    else:
        # Away covered
        if model_margin < 0:
            ats_result = "W"  # model picked away, away covered
        else:
            ats_result = "L"  # model picked home, away covered

    # ---- O/U grading ----
    ou_line = float(market_ou) if market_ou else pick["predicted_total"]
    if abs(actual_total - ou_line) < 0.5:
        ou_result = "P"
    elif actual_total > ou_line:
        ou_result = "O"
    else:
        ou_result = "U"

    # Model's O/U call: did model correctly call over or under?
    model_ou_call = "O" if pick["predicted_total"] > ou_line else "U"
    ou_correct = (model_ou_call == ou_result) if ou_result != "P" else None

    return {
        **pick,
        "graded": True,
        "actual_home_score": result["home_score"],
        "actual_away_score": result["away_score"],
        "actual_margin": actual_margin,
        "actual_total": actual_total,
        "actual_winner": pick["home_team"] if actual_margin > 0 else pick["away_team"],
        "model_correct_winner": (actual_margin > 0) == (model_margin > 0),
        "ats_result": ats_result,
        "ou_result": ou_result,
        "ou_model_correct": ou_correct,
        "cover_line": round(cover_line, 1),
    }


def compute_summary(graded_picks: List[Dict]) -> Dict:
    """Compute aggregate performance stats from all graded picks."""
    total = len(graded_picks)
    if total == 0:
        return {}

    ats_w = sum(1 for p in graded_picks if p.get("ats_result") == "W")
    ats_l = sum(1 for p in graded_picks if p.get("ats_result") == "L")
    ats_p = sum(1 for p in graded_picks if p.get("ats_result") == "P")

    ou_o = sum(1 for p in graded_picks if p.get("ou_result") == "O")
    ou_u = sum(1 for p in graded_picks if p.get("ou_result") == "U")
    ou_p = sum(1 for p in graded_picks if p.get("ou_result") == "P")
    ou_correct = sum(1 for p in graded_picks if p.get("ou_model_correct") is True)
    ou_gradeable = sum(1 for p in graded_picks if p.get("ou_model_correct") is not None)

    su_correct = sum(1 for p in graded_picks if p.get("model_correct_winner"))

    # Break down ATS by confidence tier
    high_conf = [p for p in graded_picks if p.get("confidence", 0) >= 70]
    med_conf = [p for p in graded_picks if 40 <= p.get("confidence", 0) < 70]
    low_conf = [p for p in graded_picks if p.get("confidence", 0) < 40]

    def tier_record(picks):
        w = sum(1 for p in picks if p.get("ats_result") == "W")
        l = sum(1 for p in picks if p.get("ats_result") == "L")
        p = sum(1 for p in picks if p.get("ats_result") == "P")
        pct = round(w / (w + l) * 100, 1) if (w + l) > 0 else 0
        return {"w": w, "l": l, "p": p, "pct": pct}

    ats_pct = round(ats_w / (ats_w + ats_l) * 100, 1) if (ats_w + ats_l) > 0 else 0

    # Value plays (value_rating >= 3)
    value_plays = [p for p in graded_picks if (p.get("value_rating") or 0) >= 3]
    value_record = tier_record(value_plays)

    return {
        "total_graded": total,
        "ats": {"w": ats_w, "l": ats_l, "p": ats_p, "pct": ats_pct},
        "su": {"correct": su_correct, "total": total, "pct": round(su_correct / total * 100, 1)},
        "ou": {
            "over": ou_o, "under": ou_u, "push": ou_p,
            "model_correct": ou_correct,
            "model_gradeable": ou_gradeable,
            "model_pct": round(ou_correct / ou_gradeable * 100, 1) if ou_gradeable > 0 else 0,
        },
        "by_confidence": {
            "high": tier_record(high_conf),
            "medium": tier_record(med_conf),
            "low": tier_record(low_conf),
        },
        "value_plays": value_record,
    }


def load_existing_results() -> Dict:
    """Load existing results.json if it exists."""
    path = os.path.join(RESULTS_DIR, "results.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"generated_at": None, "games": [], "summary": {}}


def save_results(results: Dict):
    """Save results.json to public/results/."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results["generated_at"] = datetime.now().isoformat()
    path = os.path.join(RESULTS_DIR, "results.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[OK] Results saved to {path}")


def grade_date(date_str: str, existing_games: List[Dict]) -> List[Dict]:
    """
    Fetch scores for date_str and grade any matching ungraded picks.
    Returns updated games list.
    """
    picks_path = os.path.join(PICKS_DIR, f"picks_{date_str}.json")
    if not os.path.exists(picks_path):
        print(f"[WARN] No picks file found for {date_str}")
        return existing_games

    with open(picks_path) as f:
        picks_data = json.load(f)

    picks = picks_data.get("picks", [])
    if not picks:
        print(f"[WARN] No picks in file for {date_str}")
        return existing_games

    # Skip if already fully graded for this date
    already_graded_ids = {g["game_id"] for g in existing_games if g.get("graded")}
    ungraded = [p for p in picks if p["game_id"] not in already_graded_ids]

    if not ungraded:
        print(f"[INFO] All picks for {date_str} already graded")
        return existing_games

    print(f"[INFO] Fetching scores for {date_str} ({len(ungraded)} picks to grade)...")
    scores = fetch_scores(date_str)

    if not scores:
        print(f"[WARN] No completed scores found for {date_str}")
        return existing_games

    graded_count = 0
    for pick in ungraded:
        result = fuzzy_match_game(pick, scores)
        if result:
            graded = grade_pick(pick, result)
            existing_games.append(graded)
            graded_count += 1
            status = graded["ats_result"]
            print(f"  {pick['away_team']} @ {pick['home_team']}: ATS {status} "
                  f"(actual: {result['away_score']}-{result['home_score']})")
        else:
            print(f"  [NOMATCH] {pick['away_team']} @ {pick['home_team']}")

    print(f"[OK] Graded {graded_count}/{len(ungraded)} picks for {date_str}")
    return existing_games


def main():
    parser = argparse.ArgumentParser(description="CBB Results Tracker v1.0")
    parser.add_argument("--date", type=str, help="Date to grade (YYYY-MM-DD), defaults to yesterday")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild all results from all pick files")
    args = parser.parse_args()

    existing = load_existing_results()
    games = existing.get("games", [])

    if args.rebuild:
        print("[INFO] Rebuilding results from all pick files...")
        games = []
        pick_files = sorted([f for f in os.listdir(PICKS_DIR) if f.startswith("picks_") and f.endswith(".json")])
        for fname in pick_files:
            date_str = fname.replace("picks_", "").replace(".json", "")
            if date_str == "latest":
                continue
            games = grade_date(date_str, games)
    else:
        if args.date:
            target = datetime.strptime(args.date, "%Y-%m-%d")
        else:
            target = datetime.now() - timedelta(days=1)
        date_str = target.strftime("%Y%m%d")
        print(f"[INFO] Grading picks for {target.strftime('%B %d, %Y')}...")
        games = grade_date(date_str, games)

    summary = compute_summary([g for g in games if g.get("graded")])
    save_results({"games": games, "summary": summary})

    if summary:
        ats = summary["ats"]
        print(f"\n{'='*50}")
        print(f"  Overall ATS: {ats['w']}-{ats['l']}-{ats['p']} ({ats['pct']}%)")
        print(f"  High Conf:   {summary['by_confidence']['high']['w']}-"
              f"{summary['by_confidence']['high']['l']} "
              f"({summary['by_confidence']['high']['pct']}%)")
        print(f"  Value Plays: {summary['value_plays']['w']}-"
              f"{summary['value_plays']['l']} "
              f"({summary['value_plays']['pct']}%)")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
