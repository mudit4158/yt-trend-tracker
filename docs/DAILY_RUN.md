# Daily run — procedure for Claude

This is the exact procedure the scheduled "Roz Trend Desk" task follows every morning.
It is written for a fresh session that has no memory of how this was set up. Follow it step by step.

- **Dashboard:** https://claude.ai/artifact/4p6KRtvJrjLDfYiKPvbDPv (database collections below)
- **Repo:** github.com/mudit4158/yt-trend-tracker (collector runs at 04:37 IST via GitHub Actions and commits `data/<date>/`)
- **Rules for content decisions:** `docs/playbook.md` (read it every run; it is the source of truth)
- **Language:** everything written for Mudit (dashboard summary, topics, evidence, notes, notification) is in **English**. Video copy inside cards (titles, hooks, outlines, descriptions, tags) is **mostly English with natural Hinglish** — English sentences with the everyday Hindi words people actually use ("SIP kya hai? 5 mistakes to avoid"). DEV titles may add the Devanagari name ("Hanuman Chalisa | हनुमान चालीसा") per the playbook.
- **Budget:** zero. Use only the repo data + your own WebSearch/WebFetch. Never sign up for or call paid services.

## 0. Setup (2 min)
1. `date` in IST → `DATE=YYYY-MM-DD` (Asia/Kolkata).
2. Get the repo: `git clone https://github.com/mudit4158/yt-trend-tracker.git` (if it fails, call the `add_repo` tool with owner `mudit4158`, repo `yt-trend-tracker`, access `push`, then run the clone command it returns).
3. Check `data/$DATE/brief_input.json` exists. If not, the collector is late: `git pull` every 5 minutes for up to 40 minutes. Still missing → continue with the latest earlier date, and say so in the run summary ("Today's data did not arrive; used yesterday's").
4. Read `docs/playbook.md` fully.

## 1. Ledger (no repeats)
1. Export all ideas: ArtifactData `list`, collection `ideas`, `out_dir` = `data/$DATE/in/ideas`, `query.limit` 1000 (follow `next_cursor` if present).
   The tool result lists each document with its `version`. Save them as `data/$DATE/in/versions.json` = `{"<idea id>": <version>, ...}` (needed to mark old ideas Expired).
2. `python3 analyzer/dbsync.py ledger data/$DATE/in/ideas $DATE` → read `data/$DATE/out/ledger.json`.
   - Never suggest a topic cluster listed in `blocked` (unless a *different angle* is allowed and clearly different, or a news topic has a material new development — then label it "Follow-up").
   - Read `learning.rejected` reasons and avoid repeating the same mistake.

## 2. Read the day
Read `data/$DATE/brief_input.json`. It contains: calendar (upcoming events + stage), tracker_top40, per-channel outliers / fast_new / from_top_charts, rising_keywords (autocomplete; `new_suggestions` = new since yesterday), google_trends, x_trends, headlines (by group), reddit, kworb_top20, patterns, failed_sources.
If a source you need failed (see `failed_sources`), fill the gap with WebSearch — especially:
- global tech (USA + China) top stories of the last 24h, filtered by the "India angle" rule;
- India finance rule changes (RBI/SEBI/Income Tax/NPCI) of the last 48h;
- for any calendar event in the BRIEF stage (≤14 days) that has no cards yet: confirm the date on Drik Panchang (or another authoritative panchang) before writing cards.

## 3. Topics
Group the signals into topic clusters per channel (DEV, KID, TFN). Score each 0–100 by the playbook weights (Section 6). Write `data/$DATE/out/topics.json`:
```json
{"date":"YYYY-MM-DD","DEV":[{"name":"Navratri Day-1 Shailputri aarti","score":88,"evidence":"autocomplete naya + 3 outliers 6–11x + event T-15"}],"KID":[...],"TFN":[...],"notes":"one line on anything unusual"}
```
6–10 topics per channel, strongest first. `evidence` is one short line with numbers.

## 4. Idea cards
3–5 cards per channel (more only in festival weeks). Pick from the top topics after the cooldown filter and the hard filters (verification, copyright). Calendar events in the BRIEF stage must get cards before evergreen ideas; an event ≤10 days away with no open card is URGENT — say so in `why_now`.
Every factual claim (finance rules, dates, prices, tech launches) must be checked with WebSearch/WebFetch against an official or reputable source and linked in `sources`. If you cannot verify → `verification: "Needs check"`. False/propaganda/divisive → do not write the card at all (log it in topics notes as avoided).

Write each card to `data/$DATE/out/ideas/<ID>.json` with ID = `<CH>-<DATE>-<NN>` (NN = 01, 02…; must not clash with `existing_ids` in the ledger):
```json
{
  "date": "YYYY-MM-DD", "channel": "TFN", "status": "Suggested", "priority": 82,
  "verification": "Verified | Needs check",
  "kind": "evergreen | festival | news | kid_concept",
  "topic": "short topic name", "topic_cluster": "kebab-case-stable-cluster-id",
  "publish_by": "YYYY-MM-DD", "upload_slot": "Tue 7:00 PM IST",
  "why_now": ["Google Trends 'upi new rule' 50K+ searches", "3 outliers 8–15x in 24h", "NPCI circular 22 Sep"],
  "format": {"type": "Long-form | Short | Compilation", "length": "9–11 min",
             "hook": "exact first line (mostly English, natural Hinglish)", "outline": ["...", "..."],
             "shorts": ["Short 1 idea cut from the video", "..."]},
  "titles": ["≤60 chars, keyword first, mostly English", "...", "..."],
  "thumbnail": "one paragraph brief: main image, ≤4 words text, colours",
  "keywords": {"primary": ["..."], "secondary": ["..."]},
  "description": "full draft: 2-line hook with keyword, chapters, sources, disclaimer (TFN), 3 hashtags",
  "tags": ["5–10 tags incl. spelling variants"],
  "sources": [{"title": "NPCI circular", "url": "https://..."}],
  "risk_flags": "none | text",
  "history": [{"status": "Suggested", "at": "ISO time"}]
}
```
Stable `topic_cluster` ids matter: reuse the same id for the same subject across days (check `ledger.json` and yesterday's `topics`), otherwise the cooldown cannot work.

Titles, thumbnails, descriptions, tags, length, upload slot: follow playbook Section 10, adjusted by today's `patterns` (e.g. if 8–15 min clearly beats other lengths in that channel's area, say so in the card).

## 5. Run summary
Write `data/$DATE/out/run.json`:
```json
{"summary": "3–4 sentences in English: what is trending today, what is most urgent, which 2 ideas to make first", "ideas": 12, "urgent": ["Gandhi Jayanti (KID) 6 din"], "gaps": "sources that failed and how you covered them"}
```

## 6. Write to the dashboard
1. `python3 analyzer/dbsync.py plan $DATE data/$DATE/in/versions.json`
2. For each `data/$DATE/out/batches/batch_N.json`: call ArtifactData `batch` with `url` = dashboard URL and `writes` = the file's array (entries already carry `file_path`, and `if_version` where needed).
   All day documents (`tracker/`, `areas/`, `pulse/`, `patterns/`, `calendar/`, `topics/`, `runs/` keyed by date, and new `ideas/`) are new each day, so they need no version. If the batch fails with `version_mismatch` (e.g. a re-run on the same day), `get` the named document, add its `version` as `if_version` to that entry, and resend.
3. Spot-check: ArtifactData `get` runs/$DATE and one new idea.
4. **Monthly (on the 1st):** keep the database small (limit 5,000 documents). `list` each of `tracker`, `areas`, `pulse`, `patterns`, `calendar`, `topics`, `runs`; delete documents whose date is more than 30 days old with a `batch` of `delete` entries, each pinned with the `if_version` shown in the listing. Never delete `ideas`.

## 7. Save to repo
`git add data/$DATE/out && git commit -m "brief: $DATE" && git push` (skip silently if push is not permitted).

## 8. Notify
Final message (this is what Mudit gets as the notification), in English, short:
- line 1: the run summary's first sentence
- the top 1 idea per channel (ID + first title + publish-by)
- urgent calendar items
- "Dashboard: Roz Trend Desk" (no raw data dumps)

## Sundays — weekly review (extra)
After step 8, compare the last 7 days: which topic clusters kept rising, which idea statuses changed, which Published videos exist (from ledger `learning.published`). Write `data/$DATE/out/weekly.md` with proposed playbook changes (weights, upload times, title patterns) — **do not edit the playbook yourself**; list proposals in the notification so Mudit can approve them.
