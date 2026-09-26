# Ad-hoc idea research — procedure for Claude

Used when Mudit submits his own idea, either from the dashboard's **Add my idea** form (which starts the
"Roz Trend Desk — research my idea" task with the request id) or directly in chat.
Goal: research it the same way as daily suggestions and add a complete idea card to the ledger.

- **Dashboard:** https://claude.ai/artifact/4p6KRtvJrjLDfYiKPvbDPv
- **Rules:** `docs/playbook.md` (read it first). Language, verification gate, card format and cooldowns all apply.
- **Budget:** zero — repo data + your own WebSearch/WebFetch only.

## 1. Get the request
- From the dashboard: the message contains `REQ-...` ids. For each: ArtifactData `get` collection `requests`, doc = that id. Fields: `idea` (text), `channel` (DEV/KID/TFN/ANY), `angle`, `links`, `target_date`, `status`, and the doc `version`.
  Also process any other request still in status `Queued` (ArtifactData `query` on `requests` where status == Queued).
- From chat: take the idea text, channel and any notes from Mudit's message; there is no request doc (create one with status `Researching` so it shows on the dashboard).
- Set the request to `status: "Researching"` (ArtifactData `update`, `if_version` = its version).

## 2. Research
1. Clone the repo and read `docs/playbook.md`. Read the latest `data/<date>/brief_input.json` (newest date folder) and search it for the idea's keywords: outliers, fast_new, rising_keywords, tracker, headlines, x_trends, google_trends. Note every match with numbers.
2. WebSearch / WebFetch:
   - **Demand:** how much this topic is being watched/searched now (recent YouTube videos on it with views, news, Google Trends mentions, festival/event dates).
   - **Competition:** the top 5 existing YouTube videos on the topic (title, channel, views, age, length) and what is missing in them — that gap is our angle.
   - **Facts:** verify every factual claim against an official or reputable source (RBI/SEBI/NPCI/PIB/Income Tax, company announcements, authoritative panchang or texts). Record links.
   - **Timing:** any date that makes it urgent (rule effective date, festival, launch, exam).
3. Ledger check: ArtifactData `list` ideas (out_dir) and run `python3 analyzer/dbsync.py ledger <dir> <today>`. If the topic is blocked by a cooldown, still write the card but add the reason in `risk_flags` ("Overlaps <ID>, published <date>") — Mudit's own ideas are never silently dropped.
4. If the idea fails the verification gate (false, unverifiable, propaganda, divisive, harmful, copyright problem), still write the card with `verification: "Avoid"`, explain why in `risk_flags`, and suggest a safe alternative angle in `why_now`.
5. If the channel is `ANY`, pick the best-fitting channel and say why in `why_now`.

## 3. Write the card
Same JSON as the daily cards (see `docs/DAILY_RUN.md` step 4), plus:
- `"origin": "Mudit"`, `"request_id": "REQ-..."`, `"idea_original": "<Mudit's words>"`
- ID = `<CH>-<today>-U<NN>` (U = user idea; NN not clashing with existing ids)
- `priority` scored with playbook Section 6 like any other idea; `status: "Suggested"`
- A `competition` field shaped exactly `{"videos": [{"title","channel","views","age","url"}], "gap": "one line"}` (top 5 videos).
- Keep every list field a JSON array of strings (`why_now`, `titles`, `tags`, `format.outline`, `format.shorts`) and `sources` an array of `{"title","url"}` — the dashboard expects these shapes.

Write it with ArtifactData `set` (collection `ideas`, new id — no version needed).
Then update the request: `status: "Ready"`, `idea_id`, `summary` (2 lines: verdict + best angle), `researched_at` (if_version = latest).
If research fails midway, set `status: "Failed"` with a one-line `error`.

## 4. Save and notify
Commit the card JSON to `data/<today>/out/ideas/` in the repo and push (skip if not permitted).
Final message (English, short): idea → verdict (priority, verification), best angle, publish-by date, and "Card added to Ideas Ledger on Roz Trend Desk".

## Refinements (type "refine") — Mudit asks to research an existing card again
A request with `type: "refine"` carries `idea_id` (any card — daily suggestion or Mudit's own) and `instructions` (what was off and what he wants instead).
1. Set the request to `Researching`. `get` the card `ideas/<idea_id>` and note its `version`.
2. Read the whole card plus all earlier `refinements` on it. **Mudit's newest instructions override the original brief and any earlier choice** — audience, angle, length, channel, facts to focus on or drop.
3. Research again with those instructions (same steps as section 2 above: demand, competition, facts, timing, guardrails). Re-score priority honestly — it can go down.
4. Update **the same card** with ArtifactData `update` (`if_version` = the version from step 1; on mismatch re-read and retry once):
   - every field you changed (titles, format, hook, outline, keywords, description, tags, thumbnail, publish_by, priority, verification, sources, competition, risk_flags…)
   - `revision`: previous revision + 1 (start at 2)
   - `refinements`: the existing array plus `{"at": now ISO, "instructions": "<Mudit's words>", "changes": "one line: what changed and why", "request_id": "REQ-..."}`
   - `previous`: a snapshot of the old `{titles, priority, verification, format, publish_by}` (keep only the most recent snapshot)
   - Do **not** change `status`, `history`, `date`, `origin` or `topic_cluster` (unless Mudit asked to change the topic itself — then say so in `changes`).
5. Mark the request `Ready` with `summary` (what changed, new priority) and `researched_at`.
6. Notification: "Refined <ID>: <what changed>".
