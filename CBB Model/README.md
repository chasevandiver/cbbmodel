# Courtside Edge

College basketball prediction dashboard powered by the CBB Model v2.2.

## Project Structure

```
courtside-edge/
├── public/
│   └── picks/
│       └── latest.json        ← model output (update this daily)
├── src/
│   ├── App.jsx                ← React dashboard (courtside_edge.jsx)
│   └── main.jsx               ← entry point
├── cbb_model.py               ← prediction model
├── index.html
├── package.json
└── vite.config.js
```

## First-Time Setup

```bash
npm install
npm run dev        # local dev at http://localhost:5173
npm run build      # production build → dist/
```

### Deploy to Vercel
```bash
npx vercel         # follow prompts, framework = Vite
```

After the first deploy, Vercel auto-deploys every time you push to main.

## Daily Workflow

Each morning, run the model and push the output:

```bash
# 1. Run the model (from this directory)
python3 cbb_model.py

# 2. Copy output to public folder
cp picks/latest.json public/picks/latest.json

# 3. Commit and push — Vercel auto-deploys in ~20 seconds
git add public/picks/latest.json
git commit -m "picks $(date +%Y%m%d)"
git push
```

Or run it all in one line:
```bash
python3 cbb_model.py && cp picks/latest.json public/picks/latest.json && git add public/picks/latest.json && git commit -m "picks $(date +%Y%m%d)" && git push
```

## Environment Variables

Set these in your shell or Vercel project settings:

| Variable | Description |
|---|---|
| `ODDS_API_KEY` | The Odds API key (rotate the one in source!) |

Add to Vercel: **Project Settings → Environment Variables**

## Model Commands

```bash
python3 cbb_model.py                          # today's picks → JSON
python3 cbb_model.py --output console         # readable console output
python3 cbb_model.py --output console --debug # show team matching
python3 cbb_model.py --date 2026-02-25        # specific date
```

## How the Dashboard Works

- `src/App.jsx` fetches `/picks/latest.json` on load
- Falls back to built-in `SAMPLE_DATA` if the file is missing or empty
- No backend required — it's a fully static site
