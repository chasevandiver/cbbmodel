#!/usr/bin/env python3
"""
Results Tracker
===============
Grades the model's picks against ESPN final scores, matched by ESPN game id.

Usage:
    python3 results_tracker.py                    # grade yesterday (Eastern)
    python3 results_tracker.py --date 2026-11-04  # grade a specific date
    python3 results_tracker.py --rebuild          # regrade every picks/picks_*.json from scratch

Output:
    public/results/results.json  — graded history + summary for the dashboard

Grading rules:
    ATS   only when the pick carried a real market line. bet_side follows the
          dashboard: home if model margin beats the line by > 0.5, away if it
          trails by > 0.5, otherwise no bet. Games with no line get ats_result
          null and count only toward straight-up accuracy.
    O/U   model call is Over if projected total > market total, graded on the
          market total. No market total -> null.
"""

import argparse
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICKS_DIR = os.path.join(BASE_DIR, "picks")
RESULTS_PATH = os.path.join(BASE_DIR, "public", "results", "results.json")
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
EASTERN = ZoneInfo("America/New_York")
PUSH_TOLERANCE = 0.5


def fetch_scores(date_str):
    """Completed games on an Eastern date, keyed by ESPN game id."""
    for attempt in range(3):
        try:
            resp = requests.get(ESPN_SCOREBOARD_URL, params={"dates": date_str, "limit": 500, "groups": 50}, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            break
        except (requests.RequestException, ValueError) as e:
            print(f"[WARN] score fetch {date_str} attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)
    else:
        return {}

    scores = {}
    for event in data.get("events", []):
        comp = (event.get("competitions") or [{}])[0]
        if not (comp.get("status") or {}).get("type", {}).get("completed"):
            continue
        sides = {}
        for c in comp.get("competitors", []):
            try:
                sides[c.get("homeAway")] = int(c.get("score") or 0)
            except ValueError:
                sides[c.get("homeAway")] = 0
        if "home" not in sides or "away" not in sides:
            continue
        scores[event["id"]] = {
            "home_score": sides["home"],
            "away_score": sides["away"],
            "total": sides["home"] + sides["away"],
            "margin": sides["home"] - sides["away"],
        }
    return scores


def market_line(pick):
    """Market spread/total for a pick, or None. Pre-v4 files stored a phantom 0 spread when ESPN had no line."""
    mk = pick.get("market") or {}
    spread, total = mk.get("spread"), mk.get("over_under")
    if spread == 0 and not mk.get("spread_holder"):
        spread, total = None, None
    if total == 0:
        total = None
    return spread, total


def grade_pick(pick, result):
    actual_margin, actual_total = result["margin"], result["total"]
    model_margin = pick["predicted_spread"]
    spread, total = market_line(pick)

    ats_result, bet_side, cover_line = None, "none", None
    if spread is not None:
        cover_line = -float(spread)                     # home must win by more than this
        edge = model_margin - cover_line
        if edge > PUSH_TOLERANCE:
            bet_side = "home"
        elif edge < -PUSH_TOLERANCE:
            bet_side = "away"
        if bet_side != "none":
            if abs(actual_margin - cover_line) < PUSH_TOLERANCE:
                ats_result = "P"
            else:
                home_covered = actual_margin > cover_line
                ats_result = "W" if home_covered == (bet_side == "home") else "L"

    ou_result, ou_correct, model_ou_call = None, None, None
    if total is not None:
        model_ou_call = "O" if pick["predicted_total"] > total else "U"
        if abs(actual_total - total) < PUSH_TOLERANCE:
            ou_result = "P"
        else:
            ou_result = "O" if actual_total > total else "U"
            ou_correct = model_ou_call == ou_result

    # Closing-line value: points of line movement in the bet's favor between pick time and close.
    clv = None
    closing = (pick.get("closing_line") or {}).get("spread")
    if closing is not None and spread is not None and bet_side != "none":
        clv = round((float(spread) - closing) if bet_side == "home" else (closing - float(spread)), 1)

    return {
        **pick,
        "graded": True,
        "bet_side": bet_side,
        "cover_line": cover_line,
        "clv": clv,
        "actual_home_score": result["home_score"],
        "actual_away_score": result["away_score"],
        "actual_margin": actual_margin,
        "actual_total": actual_total,
        "actual_winner": pick["home_team"] if actual_margin > 0 else pick["away_team"],
        "model_correct_winner": (actual_margin > 0) == (model_margin > 0),
        "ats_result": ats_result,
        "ou_result": ou_result,
        "model_ou_call": model_ou_call,
        "ou_model_correct": ou_correct,
    }


def record(picks):
    w = sum(p.get("ats_result") == "W" for p in picks)
    l = sum(p.get("ats_result") == "L" for p in picks)
    push = sum(p.get("ats_result") == "P" for p in picks)
    return {"w": w, "l": l, "p": push, "pct": round(w / (w + l) * 100, 1) if w + l else 0}


def calibration(games):
    """
    How much information the model carries beyond the market, on games with a real line:
    OLS of actual margin on model margin and market margin. A model weight near zero means
    the market already contains everything the model knows.
    """
    rows = [(g["predicted_spread"], -float(market_line(g)[0]), g["actual_margin"])
            for g in games if market_line(g)[0] is not None]
    n = len(rows)
    if n < 50:
        return {"n": n}
    mae = lambda i: round(sum(abs(r[i] - r[2]) for r in rows) / n, 2)
    X = [[1.0, m, k] for m, k, _ in rows]
    y = [r[2] for r in rows]
    A = [[sum(r[i] * r[j] for r in X) for j in range(3)] + [sum(r[i] * yy for r, yy in zip(X, y))] for i in range(3)]
    for i in range(3):
        p = max(range(i, 3), key=lambda r: abs(A[r][i]))
        A[i], A[p] = A[p], A[i]
        for r in range(3):
            if r != i and A[i][i]:
                f = A[r][i] / A[i][i]
                A[r] = [a - f * b for a, b in zip(A[r], A[i])]
    a, b, c = (A[i][3] / A[i][i] if A[i][i] else 0.0 for i in range(3))
    buckets = {}
    for g in games:
        s = market_line(g)[0]
        if s is None or g.get("ats_result") not in ("W", "L"):
            continue
        e = abs(g["predicted_spread"] + float(s))
        k = "0-2" if e < 2 else "2-4" if e < 4 else "4-7" if e < 7 else "7+"
        buckets.setdefault(k, {"w": 0, "l": 0})
        buckets[k]["w" if g["ats_result"] == "W" else "l"] += 1
    for v in buckets.values():
        v["pct"] = round(v["w"] / (v["w"] + v["l"]) * 100, 1) if v["w"] + v["l"] else 0
    return {"n": n, "model_mae": mae(0), "market_mae": mae(1), "intercept": round(a, 2),
            "model_weight": round(b, 3), "market_weight": round(c, 3),
            "ats_by_edge": {k: buckets[k] for k in ("0-2", "2-4", "4-7", "7+") if k in buckets}}


def closing_line_value(games):
    vals = [g["clv"] for g in games if g.get("clv") is not None]
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "avg": round(sum(vals) / len(vals), 2),
            "beat_close_pct": round(sum(v > 0 for v in vals) / len(vals) * 100, 1),
            "beat_or_matched_pct": round(sum(v >= 0 for v in vals) / len(vals) * 100, 1)}


def compute_summary(games):
    if not games:
        return {}
    ou_gradeable = [g for g in games if g.get("ou_model_correct") is not None]
    tiers = {"high": [g for g in games if g.get("confidence", 0) >= 70],
             "medium": [g for g in games if 40 <= g.get("confidence", 0) < 70],
             "low": [g for g in games if g.get("confidence", 0) < 40]}
    return {
        "calibration": calibration(games),
        "clv": closing_line_value(games),
        "clv_by_confidence": {k: closing_line_value(v) for k, v in tiers.items()},
        "total_graded": len(games),
        "ats_graded": sum(g.get("ats_result") in ("W", "L", "P") for g in games),
        "ats": record(games),
        "su": {"correct": sum(bool(g.get("model_correct_winner")) for g in games), "total": len(games),
               "pct": round(sum(bool(g.get("model_correct_winner")) for g in games) / len(games) * 100, 1)},
        "ou": {
            "over": sum(g.get("ou_result") == "O" for g in games),
            "under": sum(g.get("ou_result") == "U" for g in games),
            "push": sum(g.get("ou_result") == "P" for g in games),
            "model_correct": sum(bool(g.get("ou_model_correct")) for g in ou_gradeable),
            "model_gradeable": len(ou_gradeable),
            "model_pct": round(sum(bool(g.get("ou_model_correct")) for g in ou_gradeable) / len(ou_gradeable) * 100, 1)
            if ou_gradeable else 0,
        },
        "by_confidence": {
            "high": record([g for g in games if g.get("confidence", 0) >= 70]),
            "medium": record([g for g in games if 40 <= g.get("confidence", 0) < 70]),
            "low": record([g for g in games if g.get("confidence", 0) < 40]),
        },
        "value_plays": record([g for g in games if (g.get("value_rating") or 0) >= 3]),
        "best_bets": record([g for g in games if g.get("is_best_bet")]),
    }


def load_results():
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            return json.load(f)
    return {"generated_at": None, "games": [], "summary": {}}


def save_results(results):
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    results["summary"] = compute_summary(results["games"])
    results["generated_at"] = datetime.now(EASTERN).isoformat()
    results["games"].sort(key=lambda g: (g.get("date", ""), g.get("game_id", "")))
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    s = results["summary"]
    print(f"[OK] {RESULTS_PATH}: {s.get('total_graded', 0)} graded, ATS {s.get('ats', {}).get('w', 0)}-"
          f"{s.get('ats', {}).get('l', 0)}-{s.get('ats', {}).get('p', 0)}, SU {s.get('su', {}).get('pct', 0)}%")


def grade_date(date_str, games):
    """Grade ungraded picks from picks/picks_<date>.json. Returns the number graded."""
    path = os.path.join(PICKS_DIR, f"picks_{date_str}.json")
    if not os.path.exists(path):
        print(f"[WARN] no picks file for {date_str}")
        return 0
    with open(path) as f:
        picks = json.load(f).get("picks", [])
    done = {g["game_id"] for g in games}
    pending = [p for p in picks if p["game_id"] not in done]
    if not pending:
        print(f"[INFO] {date_str}: nothing to grade")
        return 0

    scores = fetch_scores(date_str)
    graded = 0
    for pick in pending:
        result = scores.get(pick["game_id"])
        if not result:
            print(f"  [PENDING] {pick['away_team']} @ {pick['home_team']} — no final score")
            continue
        g = grade_pick(pick, result)
        games.append(g)
        graded += 1
        tag = g["ats_result"] or ("SU " + ("W" if g["model_correct_winner"] else "L"))
        print(f"  {tag:<4} {pick['away_team']} @ {pick['home_team']}  ({result['away_score']}-{result['home_score']})")
    print(f"[OK] graded {graded}/{len(pending)} picks for {date_str}")
    return graded


def main():
    ap = argparse.ArgumentParser(description="CBB Results Tracker")
    ap.add_argument("--date", help="Eastern date to grade (YYYY-MM-DD), default yesterday")
    ap.add_argument("--rebuild", action="store_true",
                    help="regrade every picks file from scratch (refetches scores; loses lines for any pick file "
                         "that was regenerated after the fact)")
    ap.add_argument("--regrade", action="store_true",
                    help="reapply the grading rules to the existing history using its stored final scores")
    args = ap.parse_args()

    if args.regrade:
        results = load_results()
        results["games"] = [
            grade_pick(g, {"home_score": g["actual_home_score"], "away_score": g["actual_away_score"],
                           "total": g["actual_home_score"] + g["actual_away_score"],
                           "margin": g["actual_home_score"] - g["actual_away_score"]})
            for g in results["games"]
        ]
        print(f"[OK] regraded {len(results['games'])} games")
    elif args.rebuild:
        results = {"generated_at": None, "games": [], "summary": {}}
        dates = sorted(re.findall(r"picks_(\d{8})\.json$", os.path.basename(p))[0]
                       for p in glob.glob(os.path.join(PICKS_DIR, "picks_*.json")))
        for d in dates:
            print(f"--- {d}")
            grade_date(d, results["games"])
            time.sleep(0.5)
    else:
        results = load_results()
        if args.date:
            date_str = datetime.strptime(args.date, "%Y-%m-%d").strftime("%Y%m%d")
        else:
            date_str = (datetime.now(EASTERN) - timedelta(days=1)).strftime("%Y%m%d")
        grade_date(date_str, results["games"])

    save_results(results)


if __name__ == "__main__":
    main()
