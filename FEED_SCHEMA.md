# Shared pick feed (schema 1.0)

A sport-agnostic JSON feed so one slate/tracking app can load picks from
several models (CBB today; CFB and NBA repos publish the same shape). Each
model repo exports its own feed into `public/feed/<sport>/`, which the
dashboard host serves as static files:

```
/feed/cbb/index.json          manifest: current season, file list, season + all-time summary
/feed/cbb/slate.json          the most recently published slate (today's picks)
/feed/cbb/season-2027.json    every pick published for a season, graded where a final exists
```

`export_feed.py` writes these from `picks/*.json` and
`public/results/results.json`; it never changes either source. The schema is
`feed_schema.json` (JSON Schema 2020-12); `python3 export_feed.py --validate`
checks every file it writes.

## Conventions

- **Sport codes**: `cbb`, `cfb`, `nba`, `nfl`. `league` is the display league
  (`NCAAM`, `NCAAF`, `NBA`, `NFL`).
- **Season**: an integer plus a label. Each sport keeps its own calendar rule
  (CBB and NBA are labeled by the year they end, `2027` = "2026-27"; CFB is
  labeled by the year it starts, `2026` = "2026"). Consumers group and filter on
  `season`, never on dates.
- **Spreads are always home-relative**: `spread_home` is the home team's
  number, negative when the home team is favored. The model's projection uses
  the same convention, so `edge.spread = market.spread_home - model.spread_home`
  and a positive edge means the model likes the home side against the line.
- **Totals**: `edge.total = model.total - market.total`; positive means the
  model leans over.
- **Times**: `start_time` is UTC ISO-8601. `slate_date` is the local
  (US/Eastern) date the pick was published for and is the key a slate app
  should group on.
- **Grades**: `W`, `L`, `P` (push) or `null` when nothing was bet.
- **Status**: `pending` (not yet graded, tipped within the last day or in the
  future), `final` (graded), `no_result` (never graded: cancelled, postponed,
  or no final score found).
- Unknown values are `null`, never omitted and never `0`.
- **Freshness**: `slate.json` is rewritten by the morning picks run and again
  after every closing-line snapshot (`.github/workflows/lines.yml`), so
  `closing` on a pending record is at most one snapshot interval old. A
  consumer that wants the current line reads `closing` when present and
  `market` otherwise; `market` never changes once a pick is published.

## Envelope (slate and season files)

| field | type | notes |
|---|---|---|
| `schema_version` | string | `"1.0"` |
| `kind` | `slate` \| `season` | |
| `sport`, `league`, `sport_name` | string | |
| `model` | `{name, version}` | version of the model that produced the newest record |
| `generated_at` | ISO-8601 | when the feed was written |
| `season`, `season_label` | int, string | |
| `slate_date` | date | slate files only |
| `records` | Record[] | one per game pick |

## Record

| field | type | notes |
|---|---|---|
| `id` | string | `"<sport>:<game_id>"`, unique across sports |
| `sport`, `league`, `season`, `season_label` | | repeated per record so rows can be merged across files |
| `slate_date` | date | Eastern date the pick was published for |
| `game_id`, `game_id_source` | string | ESPN event id for CBB |
| `start_time` | ISO-8601 UTC | |
| `status` | `pending` \| `final` \| `no_result` | |
| `home`, `away` | Team | `{name, abbr, logo, record, rank}`; `rank` null when unranked |
| `venue`, `neutral_site`, `conference_game`, `broadcast` | | |
| `model` | Model | `spread_home`, `total`, `home_score`, `away_score`, `home_win_prob` (0-100), `confidence` (0-100), `tempo` (projected possessions per team; optional, null when the model has no pace), `confidence_tier` (`high` ≥70, `medium` 40-70, `low` <40), `pick` `{team, abbr, side}` |
| `market` | Market \| null | line at pick time: `spread_home`, `total`, `favorite`, `bookmaker`, `captured_at` |
| `closing` | Market \| null | last line captured before tip, same shape |
| `edge` | Edge | `spread`, `total` (signed, see conventions), `value_rating` (abs spread edge), `is_best_bet` |
| `bet` | Bet | `side` (`home` \| `away` \| `none`), `cover_line` (what home must win by, null if no line) |
| `result` | Result \| null | `home_score`, `away_score`, `margin_home`, `total`, `winner`, `su_correct`, `ats`, `ou_call`, `ou_result`, `ou_correct`, `clv` (pts of line movement in the bet's favor, null without a closing line) |
| `tags` | string[] | any of `best_bet`, `value`, `high_confidence`, `tournament`, `conference` |

## Index

| field | notes |
|---|---|
| `schema_version`, `sport`, `league`, `sport_name`, `model`, `generated_at` | as above |
| `season`, `season_label` | the current season |
| `files` | `{slate: "slate.json", season: "season-2027.json"}` relative to the index |
| `seasons` | `[{season, label, file, records, final, pending, no_result}]`, newest first |
| `slate` | `{date, total_games, pending}` |
| `summary` | current-season record blocks: `ats`, `su`, `ou`, `by_confidence`, `value_plays`, `best_bets`, `clv`, `calibration`, `total_graded`, `ats_graded` |
| `all_time` | same blocks over every graded game in the repo |

Record blocks are `{w, l, p, pct}`; `su` is `{correct, total, pct}`; `ou` is
`{over, under, push, model_correct, model_gradeable, model_pct}`.

## Adding a sport

Copy `export_feed.py`, change the `SPORT` constant and `season_for`, and map
your pick/result fields in `to_record`. Keep every key, use `null` for what
your model does not produce, and run `--validate` before publishing.
