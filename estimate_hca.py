#!/usr/bin/env python3
"""
Estimate home-court advantage from Barttorvik game logs and write team_hca.json.

For every home game between two rated teams in each season:
    residual = actual home margin - (AdjEM_home - AdjEM_away) * tempo / 100
The league value is the mean residual. Each team's value is its mean residual
shrunk toward the league mean (empirical Bayes), so a team with few home games
or a noisy record stays near the average.

Validated once on 2023-25 -> 2026: true between-team spread is only ~0.7 pts
and the out-of-sample gain over a flat value is small but positive. Re-run
each summer with the just-finished season added.

Usage:
    python3 estimate_hca.py                 # seasons 2023-2026 -> team_hca.json
    python3 estimate_hca.py 2024 2025 2026  # explicit seasons
"""

import csv
import io
import json
import math
import statistics as st
import sys
from collections import defaultdict

from cbb_model import BARTTORVIK_GAMES_URL, BARTTORVIK_URL, TEAM_HCA_PATH, http_get


def season_residuals(season):
    ratings = {r[1]: (float(r[4]) - float(r[6]), float(r[44])) for r in http_get(BARTTORVIK_URL.format(season=season)).json()}
    rows = csv.reader(io.StringIO(http_get(BARTTORVIK_GAMES_URL.format(season=season)).text))
    out = []
    for r in rows:
        if len(r) < 7 or r[5] != "H" or r[2] not in ratings or r[4] not in ratings:
            continue
        won, score = r[6].split(", ")
        a, b = (int(x) for x in score.split("-"))
        margin = (a - b) if won == "W" else -(a - b)
        (em_t, tp_t), (em_o, tp_o) = ratings[r[2]], ratings[r[4]]
        out.append((r[2], margin - (em_t - em_o) * (tp_t + tp_o) / 2 / 100))
    return out


def main():
    seasons = [int(s) for s in sys.argv[1:]] or [2023, 2024, 2025, 2026]
    residuals = []
    for s in seasons:
        rows = season_residuals(s)
        print(f"{s}: {len(rows)} home games, mean HCA {st.mean(r for _, r in rows):.2f}")
        residuals += rows

    league = st.mean(r for _, r in residuals)
    game_var = st.pvariance([r for _, r in residuals])
    by_team = defaultdict(list)
    for team, r in residuals:
        by_team[team].append(r)
    means = {t: st.mean(v) for t, v in by_team.items()}
    tau2 = max(1e-6, st.pvariance(list(means.values())) - st.mean(game_var / len(v) for v in by_team.values()))
    team_hca = {t: (len(v) * means[t] / game_var + league / tau2) / (len(v) / game_var + 1 / tau2)
                for t, v in by_team.items()}

    with open(TEAM_HCA_PATH, "w") as f:
        json.dump({"seasons": seasons, "league_hca": round(league, 2), "between_team_sd": round(math.sqrt(tau2), 2),
                   "team_hca": {t: round(v, 2) for t, v in sorted(team_hca.items())}}, f, indent=1)
    ranked = sorted(team_hca.items(), key=lambda kv: -kv[1])
    print(f"league {league:.2f}, between-team sd {math.sqrt(tau2):.2f}, {len(team_hca)} teams -> {TEAM_HCA_PATH}")
    print("highest:", ", ".join(f"{t} {v:.1f}" for t, v in ranked[:5]))
    print("lowest: ", ", ".join(f"{t} {v:.1f}" for t, v in ranked[-5:]))


if __name__ == "__main__":
    main()
