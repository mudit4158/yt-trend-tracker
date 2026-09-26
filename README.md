# yt-trend-tracker

Daily YouTube India trend research for three channels (Devotional, Kids, Tech + Finance).

- `collector/collect.py` — runs on GitHub Actions at 04:37 IST, pulls free sources, writes `data/<date>/`
- `analyzer/analyze.py` — metrics, Top 500, outliers, patterns, calendar stages, dashboard documents
- `analyzer/dbsync.py` — idea ledger (cooldowns) + dashboard write plan for the daily Claude run
- `docs/playbook.md` — the rules (v0.2); `docs/DAILY_RUN.md` — what the 05:52 IST Claude run does
- `config/` — sources, keywords, calendar, watchlist

Secret needed: `YOUTUBE_API_KEY` (Settings → Secrets and variables → Actions).
Manual run: Actions → daily-collect → Run workflow (tick "rediscover" to rebuild the watchlist).
