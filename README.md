# Courtside Edge

College basketball spread and total projections, published daily to a React dashboard.

## How the model works

For each Division I game the model takes Barttorvik's adjusted offensive and
defensive efficiencies and tempo (`{season}_team_results.json`) and projects:

```
home_proj_oe = home.AdjOE + away.AdjDE - national_avg
away_proj_oe = away.AdjOE + home.AdjDE - national_avg
spread       = (home_proj_oe - away_proj_oe) * tempo / 100 + home_court   (3.5 pts, 0 on neutral floors)
total        = (home_proj_oe + away_proj_oe) * tempo / 100
win prob     = Phi(spread / 11)
```

Adjusted efficiencies already capture shooting, turnovers, rebounding and free
throws, so nothing else is layered on. Market lines (The Odds API, with ESPN's
line as fallback) are used only to report the model-vs-market edge and to rank
the slate by confidence; they never move the projection.

Home court is team-specific (`team_hca.json`, built by `estimate_hca.py` from
four seasons of Barttorvik game logs, shrunk toward the league mean of 3.4).
The true spread between teams is only about 0.7 points and the validated
out-of-sample gain is small, so expect values between roughly 2.8 and 4.5.

Each pick also records both teams' days of rest. It is stored for later
analysis and does not move the projection.

## Measuring whether the model has an edge

Win rate against the spread is nearly useless over a season: 600 games has a
noise band of about 4 points. Two better tests are computed in
`results_tracker.py` and shown on the Results page:

- **Calibration.** Regress actual margins on the model's margin and the
  market's. If the model's weight is near zero, the line already contains
  everything the model knows and nothing you add has mattered yet.
- **Closing-line value.** `cbb_model.py --snapshot-lines` runs five times a day
  (`.github/workflows/lines.yml`) and stamps the current line on every pick
  that has not tipped. The last snapshot before tip is the closing line. A
  model with an edge beats the close more often than not.

Add one factor at a time and keep only what moves the model weight.

Team names are matched exactly: ESPN's team `location` is normalized and looked
up in the Barttorvik table, with an explicit alias table for the handful of
names that differ. A game with a team that has no rating (non-D-I opponents) is
skipped, never guessed.

## Setup

```bash
pip install requests
npm install
export ODDS_API_KEY=...        # optional; without it only ESPN lines are used
```

## Commands

```bash
python3 cbb_model.py                          # today's picks -> picks/latest.json + public/latest.json
python3 cbb_model.py --date 2026-11-05        # a specific date (Eastern)
python3 cbb_model.py --output console --debug # readable output with team matching, writes nothing
python3 cbb_model.py --check-teams            # audit ESPN <-> Barttorvik names (run each new season)
python3 cbb_model.py --snapshot-lines         # stamp current lines on today's untipped picks

python3 results_tracker.py                    # grade yesterday's picks -> public/results/results.json
python3 results_tracker.py --date 2026-11-04  # grade a specific date
python3 results_tracker.py --regrade          # reapply grading rules to the stored history
python3 results_tracker.py --rebuild          # regrade from pick files (refetches scores)

python3 estimate_hca.py                       # rebuild team_hca.json (run each summer)
python3 automate.py                           # grade yesterday, generate today, commit + push
```

If Barttorvik is unreachable the model uses a cached copy under `data/` only if
it is less than 3 days old; otherwise it exits non-zero and publishes nothing.

## Daily automation

`.github/workflows/daily.yml` runs `automate.py` every morning and commits
`picks/`, `public/latest.json` and `public/results/results.json`. Set the
`ODDS_API_KEY` repository secret. Vercel redeploys on push to `main`.

Vercel deduplicates by commit SHA. If a commit was already built as a branch
preview, fast-forwarding `main` to it does not create a production
deployment. Push `main` before the feature branch, or merge with a merge
commit, so `main` always gets a SHA Vercel has not seen.

## Project structure

```
cbb_model.py          projections
results_tracker.py    grading
automate.py           daily driver
picks/                one JSON per date + latest.json
public/latest.json    served to the dashboard
public/results/       graded history
src/App.jsx           picks dashboard
src/Results.jsx       results dashboard
```

## Grading

ATS is graded only on picks that carried a real market line, using the same
rule as the dashboard: bet the home side if the model beats the line by more
than 0.5, the away side if it trails by more than 0.5, otherwise no bet.
Games without a line count only toward straight-up accuracy.

The results history before November 2026 was produced by an earlier version of
the model with a looser team matcher; treat it as a baseline, not a
validation of the current model.
