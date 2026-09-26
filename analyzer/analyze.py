"""Turns one day's raw collection into metrics, patterns and dashboard-ready documents.

Input : data/<date>/*.json (from collector) + previous days for deltas
Output: data/<date>/analysis.json      full metrics
        data/<date>/brief_input.json   compact digest the daily Claude run reads to write idea cards
        data/<date>/db/*.json           one file per dashboard database document
Pure standard library; runs offline.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
DATE = (sys.argv[1] if len(sys.argv) > 1 else None) or os.environ.get("RUN_DATE") or dt.datetime.now(IST).strftime("%Y-%m-%d")
DAY = ROOT / "data" / DATE
DBDIR = DAY / "db"
DBDIR.mkdir(parents=True, exist_ok=True)
RUN_TIME = dt.datetime.fromisoformat(DATE + "T05:00:00+05:30")

CATS = {"1": "Film & Animation", "2": "Autos", "10": "Music", "15": "Pets & Animals", "17": "Sports",
        "19": "Travel", "20": "Gaming", "22": "People & Blogs", "23": "Comedy", "24": "Entertainment",
        "25": "News & Politics", "26": "Howto & Style", "27": "Education", "28": "Science & Tech", "0": "All"}
SCRIPTS = [("hi", "ऀ", "ॿ"), ("bn", "ঀ", "৿"), ("pa", "਀", "੿"),
           ("gu", "઀", "૿"), ("or", "଀", "୿"), ("ta", "஀", "௿"),
           ("te", "ఀ", "౿"), ("kn", "ಀ", "೿"), ("ml", "ഀ", "ൿ"), ("ur", "؀", "ۿ")]
AREA_HINTS = {
    "DEV": r"bhajan|aarti|chalisa|mantra|bhakti|devotional|hanuman|shiv|krishna|shyam|ram |durga|mata|devi|ganesh|sai |puja|katha|navratri|diwali|chhath|mahadev|भजन|आरती|चालीसा|मंत्र|भक्ति",
    "KID": r"kids|nursery|rhyme|bal geet|children|abcd|phonics|cartoon|kahani|poem|for kids|बच्चों|बाल|कविता|कहानी",
    "TFN": r"sip|mutual fund|stock|share market|tax|upi|rbi|sebi|loan|emi|credit|insurance|gold price|iphone|smartphone|launch|ai |chatgpt|gadget|tech|scam|fraud|bank|budget|salary|invest",
}


def load(name: str, day: Path = DAY, default=None):
    p = day / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def language(title: str, lang: str | None) -> str:
    counts = Counter()
    for ch in title or "":
        for code, lo, hi in SCRIPTS:
            if lo <= ch <= hi:
                counts[code] += 1
    if counts:
        return counts.most_common(1)[0][0]
    if lang:
        return lang.split("-")[0]
    return "latin"  # English or Hinglish in Roman script


def parse_time(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        try:
            return parsedate_to_datetime(s)
        except Exception:
            return None


def length_bucket(sec: int, short: bool) -> str:
    if short:
        return "Short (≤3m)"
    for lim, name in ((240, "≤4m"), (480, "4–8m"), (900, "8–15m"), (1800, "15–30m"), (3600, "30–60m")):
        if sec <= lim:
            return name
    return "60m+"


def title_features(t: str) -> dict:
    t = t or ""
    return {
        "has_number": bool(re.search(r"\d", t)),
        "question": "?" in t or bool(re.search(r"\b(kya|kaise|kyun|kab|how|why|what)\b", t, re.I)),
        "devanagari": bool(re.search(r"[ऀ-ॿ]", t)),
        "emoji": bool(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", t)),
        "all_caps_word": bool(re.search(r"\b[A-Z]{4,}\b", t)),
        "pipe_or_dash": "|" in t or " - " in t,
        "len": len(t),
    }


def prior_views(days_back: int = 3) -> dict[str, tuple[int, dt.datetime]]:
    """Views from the most recent earlier snapshot, per video id."""
    seen: dict[str, tuple[int, dt.datetime]] = {}
    d0 = dt.date.fromisoformat(DATE)
    for k in range(days_back, 0, -1):
        d = (d0 - dt.timedelta(days=k)).isoformat()
        day = ROOT / "data" / d
        when = dt.datetime.fromisoformat(d + "T05:00:00+05:30")
        for f in ("youtube_popular.json", "youtube_watchlist.json", "youtube_search.json"):
            for v in load(f, day, []) or []:
                seen[v["id"]] = (v["views"], when)
    return seen


def enrich(v: dict, prev: dict) -> dict:
    pub = parse_time(v.get("published"))
    age_h = max((RUN_TIME - pub).total_seconds() / 3600, 1) if pub else None
    short = (v.get("duration_s") or 0) <= 180 and (v.get("duration_s") or 0) > 0
    gain = None
    if v["id"] in prev:
        pv, pwhen = prev[v["id"]]
        hrs = max((RUN_TIME - pwhen).total_seconds() / 3600, 1)
        gain = int((v["views"] - pv) * 24 / hrs)
    velocity = v["views"] / age_h if age_h else None
    est = gain if gain is not None else (v["views"] if age_h and age_h <= 24 else (int(velocity * 24) if velocity else 0))
    eng = (v.get("likes", 0) + v.get("comments", 0)) / v["views"] if v.get("views") else 0
    pub_ist = pub.astimezone(IST) if pub else None
    return {
        **v,
        "age_h": round(age_h, 1) if age_h else None,
        "short": short,
        "length_bucket": length_bucket(v.get("duration_s") or 0, short),
        "lang_detected": language(v.get("title"), v.get("lang")),
        "views_24h": gain,
        "est_24h": est,
        "velocity_h": round(velocity, 1) if velocity else None,
        "engagement": round(eng, 4),
        "pub_hour_ist": pub_ist.hour if pub_ist else None,
        "pub_weekday_ist": pub_ist.strftime("%a") if pub_ist else None,
        "area_guess": next((a for a, rx in AREA_HINTS.items() if re.search(rx, (v.get("title") or "") + " " + " ".join(v.get("tags") or []), re.I)), None),
    }


def compact(v: dict) -> dict:
    return {k: v.get(k) for k in ("id", "title", "channel", "views", "views_24h", "est_24h", "velocity_h", "age_h",
                                   "duration_s", "short", "length_bucket", "lang_detected", "category", "engagement",
                                   "outlier", "area", "area_guess", "thumb", "pub_hour_ist", "query") if v.get(k) is not None}


def summarize_patterns(rows: list[dict]) -> dict:
    if not rows:
        return {}
    by_len = defaultdict(list)
    for r in rows:
        by_len[r["length_bucket"]].append(r["est_24h"] or 0)
    hours = Counter(r["pub_hour_ist"] for r in rows if r.get("pub_hour_ist") is not None and (r.get("age_h") or 999) <= 24 * 7)
    feats = [title_features(r.get("title")) for r in rows]
    n = len(feats)
    langs = Counter(r["lang_detected"] for r in rows)
    return {
        "n": n,
        "length": {b: {"share": round(len(v) / n, 3), "median_24h": int(statistics.median(v))} for b, v in sorted(by_len.items())},
        "shorts_share": round(sum(r["short"] for r in rows) / n, 3),
        "publish_hour_ist": dict(sorted(hours.items())),
        "language_share": {k: round(c / n, 3) for k, c in langs.most_common()},
        "title": {k: round(sum(f[k] for f in feats) / n, 3) for k in ("has_number", "question", "devanagari", "emoji", "all_caps_word", "pipe_or_dash")},
        "title_len_median": int(statistics.median(f["len"] for f in feats)),
        "median_engagement": round(statistics.median(r["engagement"] for r in rows), 4),
    }


def calendar_view() -> dict:
    cal = json.loads((ROOT / "config" / "calendar.json").read_text())
    today = dt.date.fromisoformat(DATE)
    upcoming = []
    for e in cal["events"]:
        d = dt.date.fromisoformat(e["date"])
        left = (d - today).days
        if 0 <= left <= 45:
            stage = ("today" if left == 0 else "publish window" if left < 5 else "production deadline today" if left == 5 else
                     "BRIEF + production" if left <= 14 else "watch" if left <= 30 else "upcoming")
            upcoming.append({**e, "days_left": left, "stage": stage,
                             "production_deadline": (d - dt.timedelta(days=5)).isoformat(),
                             "urgent": left <= 10})
    week = []
    for k in range(1, 8):
        d = today + dt.timedelta(days=k)
        w = cal["weekly"][d.strftime("%A")]
        week.append({"date": d.isoformat(), "weekday": d.strftime("%A"), **w})
    return {"upcoming": upcoming, "next_7_days_deity": week}


def main() -> None:
    prev = prior_views()
    popular = [enrich(v, prev) for v in load("youtube_popular.json", default=[]) or []]
    for v in popular:
        v["category"] = CATS.get(v.get("category_id"), v.get("category_id"))
    watch = [enrich(v, prev) for v in load("youtube_watchlist.json", default=[]) or []]
    search = [enrich(v, prev) for v in load("youtube_search.json", default=[]) or []]

    # ---- overall tracker (top 500 by 24h gain / estimate)
    tracker = sorted(popular, key=lambda r: -(r["est_24h"] or 0))[:500]
    for i, r in enumerate(tracker, 1):
        r["rank"] = i

    # ---- outliers inside each channel's own recent uploads
    by_ch = defaultdict(list)
    for v in watch:
        by_ch[v["channel_id"]].append(v)
    for vids in by_ch.values():
        med = statistics.median([x["views"] for x in vids]) or 1
        for x in vids:
            x["outlier"] = round(x["views"] / med, 2)
    areas = {}
    for area in ("DEV", "KID", "TFN"):
        w = [v for v in watch if v.get("area") == area and (v.get("age_h") or 1e9) <= 24 * 14]
        s = [v for v in search if v.get("area") == area]
        areas[area] = {
            "outliers": [compact(v) for v in sorted(w, key=lambda r: -(r.get("outlier") or 0))[:25]],
            "fast_new": [compact(v) for v in sorted(s, key=lambda r: -(r.get("velocity_h") or 0))[:25]],
            "from_top_charts": [compact(v) for v in tracker if v.get("area_guess") == area][:20],
            "patterns": summarize_patterns(w + s),
        }

    # ---- keyword signals: autocomplete suggestions that are new vs yesterday
    ac = load("autocomplete.json", default={}) or {}
    yday = (dt.date.fromisoformat(DATE) - dt.timedelta(days=1)).isoformat()
    ac_prev = load("autocomplete.json", ROOT / "data" / yday, {}) or {}
    rising = defaultdict(list)
    for q, v in ac.items():
        new = [s for s in v.get("suggestions", []) if s not in (ac_prev.get(q, {}).get("suggestions") or [])]
        if new and ac_prev:
            rising[v["area"]].append({"keyword": q, "new_suggestions": new[:6]})
        elif v.get("suggestions"):
            rising[v["area"]].append({"keyword": q, "suggestions": v["suggestions"][:6]})

    # ---- web pulse
    trends = load("trends.json", default=[]) or []
    x_tr = load("x_trends.json", default=[]) or []
    x_prev = {t["topic"] for t in (load("x_trends.json", ROOT / "data" / yday, []) or [])}
    for t in x_tr:
        t["new_today"] = t["topic"] not in x_prev if x_prev else None
    news = load("news.json", default={}) or {}
    cutoff = RUN_TIME - dt.timedelta(hours=36)
    headlines = defaultdict(list)
    seen_titles = set()
    for key, block in news.items():
        grp = block.get("area") or block.get("group")
        for it in block.get("items", []):
            t = (it.get("title") or "").strip()
            pt = parse_time(it.get("published"))
            if not t or t.lower() in seen_titles or (pt and pt < cutoff):
                continue
            seen_titles.add(t.lower())
            headlines[grp].append({"title": t, "link": it.get("link"), "source": key.split(":", 1)[-1]})
    reddit = load("reddit.json", default={}) or {}
    kworb = load("kworb.json", default=[]) or []
    status = load("status.json", default={}) or {}
    failed = sorted(k for k, v in status.items() if isinstance(v, dict) and v.get("ok") is False)

    patterns = {"tracker_top500": summarize_patterns(tracker), **{f"area_{a}": areas[a]["patterns"] for a in areas}}
    cal = calendar_view()

    analysis = {"date": DATE, "tracker": tracker, "areas": areas, "rising_keywords": rising, "trends": trends,
                "x_trends": x_tr, "headlines": headlines, "reddit": reddit, "kworb": kworb, "patterns": patterns,
                "calendar": cal, "source_status": status, "failed_sources": failed}
    dump(DAY / "analysis.json", analysis)

    # ---- compact digest for the idea-writing step
    brief = {
        "date": DATE,
        "failed_sources": failed,
        "calendar": cal,
        "tracker_top40": [compact(v) for v in tracker[:40]],
        "areas": {a: {k: v[k] for k in ("outliers", "fast_new", "from_top_charts")} for a, v in areas.items()},
        "rising_keywords": rising,
        "google_trends": [{"q": t["title"], "traffic": t.get("traffic"), "news": t.get("news")} for t in trends[:30]],
        "x_trends": x_tr[:40],
        "headlines": {g: h[:15] for g, h in headlines.items()},
        "reddit": {s: [p["title"] for p in posts[:8]] for s, posts in reddit.items()},
        "kworb_top20": kworb[:20],
        "patterns": patterns,
    }
    dump(DAY / "brief_input.json", brief)

    # ---- dashboard documents (collection, doc_id, data)
    docs = []
    for n in range(0, len(tracker), 100):
        docs.append(("tracker", f"{DATE}_{n // 100 + 1}", {"date": DATE, "part": n // 100 + 1,
                                                           "rows": [compact(v) for v in tracker[n:n + 100]]}))
    docs.append(("areas", DATE, {"date": DATE, **{a: {k: v[k] for k in ("outliers", "fast_new", "from_top_charts")} for a, v in areas.items()},
                                  "rising_keywords": rising}))
    docs.append(("pulse", DATE, {"date": DATE, "google_trends": brief["google_trends"], "x_trends": x_tr[:50],
                                  "headlines": {g: h[:25] for g, h in headlines.items()},
                                  "reddit": brief["reddit"], "kworb_top20": kworb[:20],
                                  "failed_sources": failed,
                                  "source_count": sum(1 for v in status.values() if isinstance(v, dict) and v.get("ok"))}))
    docs.append(("patterns", DATE, {"date": DATE, **patterns}))
    docs.append(("calendar", "upcoming", {"date": DATE, **cal}))
    for coll, doc_id, data in docs:
        dump(DBDIR / f"{coll}__{doc_id}.json", data)
    print(f"analysis done: tracker={len(tracker)} watch={len(watch)} search={len(search)} docs={len(docs)} failed={failed}")


if __name__ == "__main__":
    main()
