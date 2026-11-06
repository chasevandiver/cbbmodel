#!/usr/bin/env python3
"""
CBB Daily Automation
====================
  1. Grade yesterday's picks against final scores
  2. Generate today's picks
  3. Commit and push (skipped under GitHub Actions, where the workflow commits)

Exit code is non-zero if the model fails, so a CI run goes red instead of
publishing stale or placeholder picks.

Local cron example (9:00 AM):
  0 9 * * * cd /path/to/cbbmodel && ODDS_API_KEY=... /usr/bin/python3 automate.py >> logs/auto.log 2>&1
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EASTERN = ZoneInfo("America/New_York")
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"
TRACKED = ["picks/", "public/latest.json", "public/results/results.json", "data/"]


def log(msg):
    print(f"[{datetime.now(EASTERN):%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def run(cmd):
    log("$ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
    for stream, lines in (("", proc.stdout), ("[stderr] ", proc.stderr)):
        for line in lines.strip().splitlines():
            log(f"  {stream}{line}")
    if proc.returncode != 0:
        log(f"  [ERROR] exit code {proc.returncode}")
    return proc.returncode == 0


def main():
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    now = datetime.now(EASTERN)
    log("=" * 60)
    log("CBB DAILY AUTOMATION")

    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    log(f"Step 1: grading {yesterday}")
    if not run([sys.executable, "results_tracker.py", "--date", yesterday]):
        log("[WARN] grading failed — continuing")

    log("Step 2: generating picks")
    model_ok = run([sys.executable, "cbb_model.py", "--debug"])
    if not model_ok:
        log("[ERROR] model failed — no new picks; grading results are still committed")

    if IN_CI:
        log("Step 3: skipped (GitHub Actions workflow commits)")
        sys.exit(0 if model_ok else 1)

    log("Step 3: commit and push")
    run(["git", "add", "--"] + TRACKED)
    if not subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE_DIR).returncode:
        log("nothing to commit")
        return
    if not run(["git", "commit", "-m", f"auto: {now:%b %d} picks + results"]):
        sys.exit(1)
    if not run(["git", "push"]):
        sys.exit(1)
    log("Done")
    sys.exit(0 if model_ok else 1)


if __name__ == "__main__":
    main()
