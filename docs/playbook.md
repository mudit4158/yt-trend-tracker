# YouTube Research & Content Playbook

**Version:** v0.5 · **Created:** 26 Sep 2026 · **Updated:** 27 Sep 2026 · **Owner:** Mudit
**Purpose:** Single reference for the daily research job and for content decisions across three YouTube channels. Every daily run reads this file first. Changes go in the Changelog at the bottom; bump the version on every change.
**Live copy used by the daily job:** `docs/playbook.md` in the GitHub repo `mudit4158/yt-trend-tracker` (kept in sync with the Project doc).

---

## 0. Goals and principles

- **Goal:** maximise views and build a loyal subscriber base with regular, current, meaningful content.
- **Principle:** never publish false or unverified information, never spread propaganda, never use misleading titles or thumbnails, however well they might perform.
- **OPEN POINT — Ideology & ethics framework:** to be formalised later. Until then the Verification Gate (Section 7) applies to every idea.
- **Model philosophy:** everything in this file is a starting hypothesis. Weekly reviews compare it with our own channel analytics and update it (Section 10).

## 1. Channels

| ID | Channel | Language (default) | Core audience |
|---|---|---|---|
| DEV | Devotional songs | Songs in Hindi (bhajans/aartis); titles & descriptions mostly English + Hinglish | Adults 25+, families, early-morning and festival listeners |
| KID | Children educational + entertainment | Mostly English with simple Hinglish | Parents of 2–8 year olds; the kids themselves |
| TFN | Tech + financial awareness & education | Mostly English with natural Hinglish | 18–40, first-time investors, smartphone users |

**Language rule (all channels):** video copy is *mostly English with natural Hinglish* — English sentences with the everyday Hindi words people actually use. Everything written for Mudit (dashboard, summaries, notes) is in English.

## 2. Daily research scope

Every day the job answers:
1. **What is India watching?** Overall tracker of the top 500+ Indian videos, ranked by views gained in the last 24 hours (not lifetime views).
2. **What is rising in each channel's area?** Topics, formats and outlier videos.
3. **What should we make next?** 3–5 ranked idea cards per channel (format in Section 8), each passed through the Verification Gate.
4. **What is coming up?** Festivals and events on the calendar, with the lead times in Section 4.

Mudit's own ideas and refinements are researched on demand the same way — see Section 15 and `docs/ADHOC_IDEA.md`.

## 3. Sources

**Budget rule (until the 2-week review on 10 Oct 2026): zero.** Only free sources: the YouTube Data API free quota, public RSS/HTML pages fetched by the GitHub Actions collector, and Claude's own web search / browser. Paid scrapers (Apify, X API) are listed as improvements, not used.

### A. YouTube (core)
- Official "most popular in India" lists, pulled per category (Music, Education, Entertainment, Science & Tech, People & Blogs, Howto & Style, News, Comedy, Film & Animation).
- **Channel watchlist:** 150–300 channels, 50–100 per channel area. Daily snapshot of every upload's views, used for view growth and outlier scores. This is the main source for kids' content and Shorts, which rarely show up in the popular lists.
- **Keyword list per channel:** a small, rotating set of searches (they are expensive on the daily API limit).
- **Music charts:** Kworb India weekly chart and YouTube Music Charts India (for DEV).

### B. What people are searching for
- Google Trends India: YouTube-search view, daily trending searches, and rising related queries for our keywords.

### C. Calendar feed (high priority)
- Hindu festival and vrat calendar from Panchang dates (Drik Panchang or equivalent).
- Weekly deity days: Mon (Shiva), Tue (Hanuman), Thu (Vishnu/Sai/Guru), Sat (Shani/Hanuman).
- Monthly observances: Ekadashi, Purnima, Amavasya, Pradosh, Sankashti.
- School year: CBSE and major state board exam windows, school holidays, results.
- Finance: Union Budget, RBI policy dates, tax deadlines (ITR, advance tax), GST changes, new SEBI/RBI rules taking effect, IPO calendar.
- Tech: major launch events (Apple, Samsung, Google, OnePlus/Xiaomi India launches), big sales (Flipkart/Amazon festive sales).

### D. News
- **India:** Google News feeds by topic (business, tech, religion/culture, education).
- **Official primary sources:** RBI, SEBI, PIB, Income Tax Department, NPCI, CBSE press releases and circulars.
- **Global tech (not just India):**
  - **USA:** TechCrunch, The Verge, Ars Technica, Wired, Bloomberg Tech, Hacker News front page.
  - **China:** South China Morning Post (Tech), TechNode, Pandaily, Caixin Global, KrASIA.
  - **Global:** Reuters Technology, Rest of World (emerging markets angle).
- **"India angle" filter:** a global tech story qualifies for TFN only if it affects Indian users in some way — launch in India, price, jobs, apps Indians use, policy, or a clear "this is coming to you" story.

### E. Social media
- **X (Twitter):**
  - India trending topics — free, from trends24.in (hourly snapshots of the last 24h).
  - *Improvement (paid, after review):* curated X lists of Indian tech/finance voices, US + China tech journalists and founders, official accounts via Apify or the X API.
- **Instagram:** *Improvement (paid, after review):* Reels by hashtag and tracked accounts via Apify. Until then, Instagram signals come only from what the daily run finds with web search.
- **Reddit:** r/IndiaInvestments, r/personalfinanceindia, r/india, r/developersIndia, r/IndianGaming, r/technology, r/indianparents.
- **Streaming charts:** JioSaavn and Spotify India devotional/kids charts (for DEV and KID).
- **Not tracked for now:** TikTok (banned in India), ShareChat/Moj/Josh (hard to scrape; revisit in phase 3).

### F. Verification sources (for the gate)
- PIB Fact Check, BOOM, Alt News, Vishvas News, Factly.
- RBI/SEBI/Income Tax/NPCI originals.
- For devotional texts: authoritative published sources (Gita Press editions etc.) for lyrics, stories and dates.

## 4. Calendar lead times

Every festival or event gets a countdown. T = event date.

| Stage | When | What happens |
|---|---|---|
| Watch | T-30 to T-15 | Appears on the dashboard calendar; search trend starts being tracked |
| Brief | **T-14** | Full idea cards issued for all relevant channels |
| Production deadline | **T-5 (hard minimum, per Mudit)** | Content must be ready. If an event is first spotted inside T-10, it is flagged URGENT |
| Publish window | T-7 to T-1 (festival search usually peaks in the last few days) | Shorts can go out closer to the day; long-form earlier so it is indexed |
| Day-of | T | Short / community post; reuse of existing content |

Multi-day festivals (Navratri, Diwali week) get a content series planned at the Brief stage.

## 5. Pipeline (daily job)

**Architecture & timing (IST):**
- **01:43 — Collector**, backup 03:43 (GitHub Actions, repo `mudit4158/yt-trend-tracker`): fetches all sources, computes metrics, commits `data/<date>/`. Runs on GitHub because Claude's workspace cannot reach YouTube/Google directly. The API key is a GitHub secret. Why so early: GitHub starts scheduled jobs late when busy (on 27 Sep the 04:37 job started ~06:49 and the brief had to use the previous day's data), so the collector now runs ~4 hours before the brief, with a backup run that skips itself if data already exists.
- **05:52 — Daily Claude run** (scheduled task): reads the data + this playbook, applies the ledger, writes topics and idea cards, researches any queued requests from Mudit, updates the dashboard, sends the notification. If today's data is still missing after 40 minutes it uses the previous day's data plus web research and flags the brief as stale. Procedure: `docs/DAILY_RUN.md` in the repo.
- **~06:15 — Brief ready.** Why this time: the brief is waiting when the day starts; data covers the full previous day; there are ~10 hours before the Kids (4–7 PM) and Tech+Finance (7–9 PM) upload slots; Devotional content for early-morning slots is planned days ahead via the calendar.

Steps:

1. **Read this playbook** and the ideas ledger.
2. **Collect.** Pull each source (Section 3); store raw snapshots with timestamps.
3. **Standardise.** Convert every item to one record:
   source, id, title, channel/account, publish time, views, likes, comments, length, Short or long, language, category, tags.
4. **Compute.**
   - 24-hour view growth
   - Velocity (views per hour since publishing)
   - Outlier score (video views ÷ that channel's median views over its last 20 uploads)
   - Engagement rate ((likes + comments) ÷ views)
5. **Tag.** Assign each item a topic cluster, channel fit (DEV/KID/TFN/none), format, hook type and title pattern.
6. **Detect trends.** Rank topic clusters by rise speed and cross-platform spread (the same topic rising on 2+ of YouTube, Google Trends, X, news, Instagram).
7. **Generate ideas.** Score ideas with Section 6 and check them against the cooldown rules (Section 9).
8. **Verification Gate** (Section 7).
9. **Write outputs** to the dashboard database: overall tracker, topic trends, idea cards, calendar.

## 6. Idea scoring model (v0.1)

Priority score out of 100:

| Factor | Weight | Meaning |
|---|---|---|
| Trend velocity | 25 | How fast the topic is rising (YouTube + Google Trends) |
| Cross-platform spread | 15 | Number of platforms showing the rise |
| Channel fit | 15 | How squarely it fits the channel's audience |
| Competition gap | 15 | Demand is high but few good videos exist yet (few recent uploads, low-quality top results) |
| Timeliness / lead time | 10 | Calendar events inside the Brief window score high |
| Evergreen value | 10 | Will it keep earning views after the trend fades? |
| Earnings potential | 10 | Higher-paying topics (finance > tech > education > music) |

**Hard filters (fail = idea dropped, whatever the score):**
- Fails the Verification Gate.
- Inside a cooldown period (Section 9).
- Copyright risk (label-owned songs, copyrighted characters).

The weights are reviewed weekly against real results.

## 7. Verification Gate

Each idea gets one of three statuses:
- ✅ **Verified** — core facts confirmed against a primary or official source (linked in the card).
- ⚠️ **Needs check** — plausible but not yet confirmed; cannot move to production until verified.
- ⛔ **Avoid** — false, unverifiable, propaganda, communal/divisive angle, fear-mongering, or harmful.

**Channel-specific rules:**
- **TFN:**
  - Educational content only; no buy/sell calls on specific stocks or securities (SEBI rules restrict unregistered investment advice).
  - Every financial claim cites RBI/SEBI/IT Dept/official source.
  - Standard disclaimer in the description.
- **KID:**
  - Content must be age-appropriate and genuinely educational.
  - No copyrighted characters.
  - Set as "made for kids" on YouTube.
  - No clickbait aimed at children.
- **DEV:**
  - Original compositions or traditional public-domain bhajans/aartis only, no covers of label-owned songs.
  - Lyrics and stories taken from authoritative texts.
  - Respectful treatment; no sectarian or divisive framing.

**Cross-channel guardrails (all ideas, including Mudit's own):**
- **Trending ≠ usable:** ignore coordinated hashtag campaigns and political or sectarian trends, however big (log them in topics notes as avoided).
- **Cross-check news:** check news-based ideas against the original announcement and the fact-checkers (PIB Fact Check, BOOM, Alt News, Vishvas News). Where reliable reports disagree, say so in `risk_flags`.
- **No amplifying fakes:** scam/deepfake explainers never replay the fake at length and blur its links and numbers.
- **No divisive framing:** no communal, caste or sectarian angles.
- **No fear-selling:** no "dosh"/curse scares, miracle remedies, or health or money claims without evidence.
- **Honest packaging:** titles and thumbnails never promise what the video doesn't deliver.
- **No harm stories:** crime, violence and victim stories in the news are not turned into content.
- **Mudit's ideas are never dropped silently:** if one fails, write the card with `verification: "Avoid"`, the reason, and a safer angle.
- **Human in charge:** nothing is published automatically; playbook changes are proposed, never self-applied.

## 8. Idea card format

Every suggestion is delivered in this exact structure:

```
IDEA ID: TFN-2026-10-03-02            Status: Suggested
Channel: TFN        Priority: 82/100   Verification: ✅ Verified
Topic cluster: upi-new-rules-oct-2026
Publish by: 06 Oct 2026 (reason: rule takes effect 08 Oct)

WHY NOW (evidence)
- Google Trends "UPI new rule" +340% in 48h (India)
- 3 outlier videos on the topic: 8–15x channel median in 24h
- NPCI circular dated DD-MM-YYYY (link)

FORMAT
- Long-form, 9–11 min (+ 2 Shorts cut from it)
- Hook (first 5 sec): <exact line>
- Outline: 1) … 2) … 3) …

TITLES (3 options, ≤60 characters, keyword first)
1. …
2. …
3. …

THUMBNAIL BRIEF
- Main image / face expression, max 3–4 words of text, colours, contrast note

KEYWORDS
- Primary: …   Secondary: …   (Hindi + Hinglish + English spellings)

DESCRIPTION (draft)
- First 2 lines: hook + main keyword
- Chapters, sources, disclaimer, 3 hashtags

TAGS: …
UPLOAD SLOT: Tue 7:00 PM IST
VERIFICATION SOURCES: <links>
RISK FLAGS: none / …
```

**Idea statuses:** Suggested → Planned (Accept) → Published (with the video's URL), or Rejected (with a reason). Unused suggestions become Expired after 7 days. Cards for Mudit's ideas also carry origin "Mudit", his original wording, and the top 5 competing videos with the gap they leave.

## 9. No-repeat / cooldown rules

- **Idea ledger.** Every idea is stored in the dashboard database with its topic cluster, status, dates and *kind* (evergreen / festival / news / kid_concept), which sets its cooldown.
- **Duplicate check.** Before suggesting anything, the job compares the idea's topic cluster, and its meaning (not just exact words), with everything in the ledger.

| Situation | Cooldown |
|---|---|
| Published — evergreen topic (a specific bhajan, a concept like "What is SIP") | 60 days for the same angle; a clearly different angle allowed after 30 days |
| Published — festival topic | Until the next occurrence of that festival (the calendar re-triggers it) |
| Published — news/trend topic | 14 days, unless there is a material new development (new circular, new launch); then it's suggested as a clearly labelled follow-up |
| KID concept (e.g. "numbers 1–10 in Hindi") | 30 days; later versions must change the format (song vs story vs game) |
| Rejected | 14 days, then allowed back only if the evidence has changed |
| Suggested but not acted on | Stays open (not repeated) for 7 days, then marked Expired; the cluster may come back only with fresh evidence |
| Planned (Accepted) | Never re-suggested while open |

After each upload, Mudit (or the daily job, if it can see the channel) marks the idea as Published with the video's URL.

## 10. Metadata & publishing playbook (v0.1 — hypotheses to test)

These are starting rules based on general best practice. We replace them with what our own analytics show after 4–6 weeks.

### Titles
- 60 characters max (longer gets cut off on mobile); main keyword in the first 3–4 words.
- Write the way the audience searches:
  - DEV — English/Roman first, Devanagari name added (e.g. "Hanuman Chalisa | हनुमान चालीसा")
  - KID — simple English with familiar Hindi words
  - TFN — mostly English with natural Hinglish ("SIP kya hai? 5 mistakes to avoid")
- Proven patterns: number + benefit ("5 UPI rules…"), question ("Is your SIP safe?"), time-bound ("New rules from 1 Oct"), curiosity with a true payoff.
- Never promise what the video does not deliver.

### Thumbnails
- 1280×720, readable at phone size; 3–4 words of text at most; strong contrast; one focal point.
- **DEV:** clear deity image (original or properly licensed art), warm colours, the festival or day named.
- **KID:** bright primary colours, the character or object, no text or very little.
- **TFN:** a face with expression (if presenter-led) + one bold number or word; consistent brand colour.
- Test 2–3 variants using YouTube's built-in thumbnail test when available.

### Descriptions
- The first 2 lines carry the hook plus the main keyword (they show in search).
- Then add:
  - Chapters (timestamps) for long-form
  - Sources (TFN)
  - Lyrics (DEV, when original or public domain)
  - Links to related videos and playlists
  - Disclaimer (TFN)
- 3 relevant hashtags; the first three appear above the title. Don't use many hashtags; YouTube ignores all of them if there are too many.

### Tags
- Low weight in YouTube's ranking. Use 5–10: the exact main keyword, spelling variants (Hindi/Roman, common misspellings), the channel name.

### Keywords
- Built daily from Google Trends rising queries, YouTube search autocomplete and competitors' outlier titles.
- Stored per channel as three lists: evergreen core, seasonal, trending-now.

### Length & format
- **DEV:** long-form 8–30 min (aarti/chalisa loops and jukeboxes are watched on TV and in the background) + Shorts clips of chorus/darshan.
- **KID:** 3–5 min single songs/lessons + 20–60 min compilations (big for TV viewing) + Shorts.
- **TFN:** 8–15 min explainers (mid-roll ads above 8 min) + 30–60 sec Shorts that point to the full video.

### Upload times (IST) — starting hypotheses
- **DEV:**
  - 5:00–7:00 AM, and around 6:00 PM for evening aarti.
  - Publish before the deity's weekday (e.g. a Hanuman video goes up Monday night or early Tuesday).
- **KID:** 4:00–7:00 PM weekdays; 8:00–11:00 AM weekends.
- **TFN:** 7:00–9:00 PM weekdays; Sunday morning.
- Publish about 1–2 hours before the target viewing time so the video is indexed.

### Frequency (starting target)
- **DEV:** 2 long + 5 Shorts per week (more in festival weeks)
- **KID:** 2 long + 3 Shorts per week
- **TFN:** 2 long + 5 Shorts per week

## 11. Dashboard

Private artifact **Roz Trend Desk** (https://claude.ai/artifact/4p6KRtvJrjLDfYiKPvbDPv) with a built-in database (UI in English). Data collections (day documents older than 30 days are deleted monthly):
- `runs/<date>` — run log and daily summary
- `tracker/<date>_1..5` — Top 500 in 5 parts
- `areas/<date>` — per-channel outliers, fast-rising videos, autocomplete signals
- `pulse/<date>` — Google Trends, X trends, music chart, Reddit, headlines
- `patterns/<date>` — length / upload hour / title / language stats
- `topics/<date>` — trend clusters with scores (written by Claude)
- `ideas/<id>` — the ledger (cards + statuses); never deleted
- `calendar/<date>` — events with T-minus stages (latest is shown)
- `requests/<id>` — Mudit's own ideas submitted for research (see `docs/ADHOC_IDEA.md`)
- Watchlist and keywords live in the repo (`config/`).

**Views:** see Section 15.

## 12. Improvement loop

- **Weekly (Sunday):**
  - Compare our published videos' click-through, retention and views with what the model predicted.
  - Adjust scoring weights, upload times and title patterns (the daily run proposes; Mudit approves).
  - Record the changes in the Changelog.
- **Monthly:**
  - Refresh the watchlist (add rising channels, drop dead ones).
  - Review sources.
  - Review costs.

## 13. Phases

- **Phase 1 (now, free):** YouTube API + autocomplete, Google Trends, news & global tech RSS, official RBI/SEBI/PIB, fact-check feeds, Reddit RSS, X trends (trends24), YouTube India music chart (kworb), calendar, dashboard, idea cards.
- **Review (10 Oct 2026):** after 2 weeks of results, decide budget.
- **Phase 2 (paid, if approved):** X lists (API/Apify), Instagram Reels (Apify), streaming charts, Playboard.
- **Phase 3:** our own channel analytics feeding back into scoring; ShareChat/Moj evaluation.

## 14. Open points
1. Ideology & ethics framework (to formalise).
2. Size of the overall tracker (500 now; revisit at review).
3. Budget for paid data — decided: zero until the 10 Oct 2026 review.
4. Presenter-led (face) or faceless for each channel.


## 15. Interaction model & decisions log

How Mudit works with the system, and the decisions behind it. The daily run and the on-demand research both follow these.

### Dashboard (Roz Trend Desk)
- Private artifact, UI in English, pinned to the Claude sidebar; the Project doc `00-dashboard-roz-trend-desk.md` links to it. (An artifact can't be placed inside a Project, so the doc + pin are the entry points.)
- Tabs: Today's Brief · Top 500 · Channel Pulse · Web Pulse · Calendar · My Ideas · Ideas Ledger · Patterns.
- ☰ menu (top right): Data sources (with live OK/failed status), Metrics & logic, Guardrails & filters, Schedule & process. It is hand-written into the page — update it whenever sources, scoring or guardrails change.
- Ideas Ledger shows every idea as a row; ▸ on the right of a row opens the full card with all details and actions.

### Card actions
- **Actions ▾** holds three buttons side by side: **Accept · Reject · Published**. An input appears only after a click: Reject asks for a short reason, Published asks for the YouTube link.
- **Accept** = "I'll make this" — shown as **Planned**; the idea is reserved and not re-suggested while open. "In production" was removed as a separate step (old data showing it is displayed as Planned).
- **Reject** reasons and **Published** links are the main feedback: they drive cooldowns and teach the model.
- **Refine & research again** sits outside the Actions menu, under each card.

### Mudit's own ideas
- Two entry points: dashboard **+ Add my idea** (idea, channel or "Not sure", optional angle, links, target date) or chat ("Research my idea: …").
- The dashboard starts the on-demand task "Roz Trend Desk — research my idea" instantly through the Claude Code Remote connector; if that can't start, the request stays Queued and the next morning run picks it up.
- Each idea is researched like a daily suggestion — demand, top 5 competing videos and the gap, verified facts, timing, guardrails — and saved as a `U` card (`<CH>-<date>-U<NN>`, origin "Mudit", marked "Your idea").
- Mudit's ideas are never dropped silently: a failing idea is saved as **Avoid** with the reason and a safer angle.

### Refinements
- **Never override Claude's suggestions with Mudit's ideas.** Refining a daily suggestion ALWAYS creates a new card in My Ideas (`derived_from` the suggestion); the suggestion itself is never modified. It shows "Your variants of this suggestion"; the new card shows "Made from …". (Decision 26 Sep 2026, after the Navratri card DEV-2026-09-26-01 was refined in place — it was restored to its original and the refined version became DEV-2026-09-26-U02.)
- Refining Mudit's own card updates that same card (revision number, refinement history with what was asked and what changed, `previous` snapshot, and an `original` snapshot on the first refinement).
- **Alignment check:** a refinement of Mudit's own card must stay on the same subject (angle, audience, depth, length, focus, packaging may change). A different subject fails the refinement with the reason "Not aligned with <card>" and is registered as a new idea automatically — so a card's topic and its metrics can't be quietly rewritten.
- Refinement notes from the last 30 days feed the daily run as standing preferences (e.g. "shorter", "for beginners").
- The weekly review scores the model on each card's original suggestion, never on refined versions or variants.

### Research history & statuses
- Every card shows its **Research history**: each run's input (daily trend data, Mudit's idea text, or his refinement note, plus angle/links) and status — **Queued, Running, Completed, Failed** — with the result or the failure reason.
- My Ideas lists Mudit's submitted ideas and variants of daily suggestions with the same statuses; refinements of his own cards show on the card itself ("Refining…").

### Data & reliability decisions
- Claude's workspace can't reach YouTube/Google directly, so collection runs free on GitHub Actions; the YouTube Data API key lives only as a GitHub secret (never in chat). Only the Data API is used; Analytics/Reporting APIs come later for our own channels.
- GitHub runs scheduled jobs late when it's busy, so the collector runs at 01:43 IST with a 03:43 backup (decision 27 Sep 2026, after the 04:37 run started ~2h15m late and the brief used the previous day's data).
- Cards must keep fixed field shapes (lists as arrays, `sources` as `{title,url}`, `competition` as `{videos, gap}`); the page also tolerates other shapes and a broken card never blanks the page.
- Daily documents are new each day (no overwrites); ideas are never deleted; data older than 30 days is pruned monthly.
- Failing feeds are rerouted through Google News where a site blocks the collector (RBI, BOOM, KrASIA, Moneycontrol PF); Reddit is fetched in one combined request.

## Changelog
- **v0.5 (27 Sep 2026):** collector moved to 01:43 IST with a 03:43 backup after GitHub delayed the 04:37 run by ~2h15m on 27 Sep; late-data briefs are flagged `stale_data`.
- **v0.4 (26 Sep 2026):** Section 15 — interaction model & decisions: dashboard layout and ☰ menu, Accept/Reject/Published actions (Planned status), own-idea research, refinements (never override Claude's suggestions — variants become new cards; own cards refine in place with an alignment check), research history statuses, reliability decisions.
- **v0.3 (26 Sep 2026):** cross-channel guardrails (campaign trends, cross-checking, no amplifying fakes, no fear-selling, no harm stories, Mudit's ideas never dropped); Mudit's own ideas researched on demand (`requests` collection, `docs/ADHOC_IDEA.md`); dashboard menu documents sources, logic and guardrails.
- **v0.2 (26 Sep 2026):** language rule (mostly English + natural Hinglish for videos; English for dashboard), zero-budget free sources with paid items moved to improvements, architecture and run times (collector 04:37, Claude 05:52, brief ~06:15 IST), 7-day expiry for unused suggestions, idea kinds for cooldown, dashboard collections.
- **v0.1 (26 Sep 2026):** initial playbook — sources incl. global US/China tech and X, calendar lead times (T-14 brief, T-5 hard minimum), artifact dashboard, idea card format, cooldown rules, metadata playbook.
