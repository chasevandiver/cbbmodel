#!/usr/bin/env python3
"""
CBB Daily Automation Script
============================
Runs automatically via cron. Each morning:
  1. Grades yesterday's picks against ESPN final scores
  2. Generates today's picks
  3. Copies latest.json to public/
  4. Commits and pushes to GitHub (triggers Vercel deploy)

Cron setup (run `crontab -e` and add):
  0 9 * * * /usr/bin/python3 /Users/chasevandiver/Desktop/Personal/CBBBettingModel/automate.py >> /Users/chasevandiver/Desktop/Personal/CBBBettingModel/logs/auto.log 2>&1

This runs at 9:00 AM daily. Adjust time as needed (all games finish by ~2 AM CT).
"""

import subprocess
import sys
import os
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run(cmd, cwd=BASE_DIR):
    log(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            log(f"  {line}")
    if result.stderr.strip():
        for line in result.stderr.strip().splitlines():
            log(f"  [stderr] {line}")
    if result.returncode != 0:
        log(f"  [ERROR] exit code {result.returncode}")
        return False
    return True

# ── Step 1: Grade yesterday's games ──────────────────────────────────────────
log("=" * 60)
log("CBB DAILY AUTOMATION")
log("=" * 60)

yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
log(f"Step 1: Grading picks for {yesterday}...")
ok = run([sys.executable, "results_tracker.py", "--date", yesterday])
if not ok:
    log("[WARN] Results grading had errors — continuing anyway")

# ── Step 2: Generate today's picks ───────────────────────────────────────────
log("Step 2: Generating today's picks...")
ok = run([sys.executable, "cbb_model.py", "--debug"])
if not ok:
    log("[ERROR] Model failed — aborting git push")
    sys.exit(1)

# ── Step 3: Stage and commit ──────────────────────────────────────────────────
today = datetime.now().strftime("%b %d")
log("Step 3: Committing to git...")

run(["git", "add",
     "public/latest.json",
     "public/results/results.json",
     "picks/"])

# Check if there's anything to commit
status = subprocess.run(["git", "status", "--porcelain"], cwd=BASE_DIR, capture_output=True, text=True)
if not status.stdout.strip():
    log("Nothing new to commit — already up to date")
else:
    run(["git", "commit", "-m", f"auto: {today} picks + grade {yesterday}"])
    ok = run(["git", "push"])
    if not ok:
        log("[WARN] Push failed — trying force push")
        run(["git", "push", "--force"])

log("Done! Site will update in ~30 seconds via Vercel.")
log("=" * 60)
