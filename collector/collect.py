"""Daily collector. Runs on GitHub Actions (which has open internet access).

Writes everything for one IST date into data/<YYYY-MM-DD>/:
  youtube_popular.json   most-popular chart per category (India)
  youtube_watchlist.json recent uploads of watchlist channels
  youtube_search.json    keyword searches (rotating subset)
  autocomplete.json      YouTube search suggestions per keyword (free)
  trends.json            Google Trends daily trending searches (India)
  news.json              Google News + tech/official/fact-check RSS items
  reddit.json            top posts of the day per subreddit
  x_trends.json          X (Twitter) India trending topics (trends24)
  kworb.json             YouTube India weekly music chart
  status.json            per-source ok/error log

A failing source never stops the run. No paid services are used.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path

import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config" / "sources.json").read_text())
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
NOW = dt.datetime.now(IST)
TODAY = os.environ.get("RUN_DATE") or NOW.strftime("%Y-%m-%d")
OUT = ROOT / "data" / TODAY
OUT.mkdir(parents=True, exist_ok=True)
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
YT = "https://www.googleapis.com/youtube/v3"
UA = {"User-Agent": "Mozilla/5.0 (yt-trend-tracker; personal research; contact via GitHub)"}

status: dict[str, dict] = {}
quota_used = 0


def save(name: str, obj) -> None:
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1))


def log(source: str, ok: bool, detail: str = "", count: int | None = None) -> None:
    status[source] = {"ok": ok, "detail": detail[:300], "count": count}
    print(("OK   " if ok else "FAIL ") + source, count if count is not None else "", detail[:120], flush=True)


def allowed(url: str) -> bool:
    """Respect robots.txt for HTML pages we scrape."""
    p = urllib.parse.urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    try:
        r = requests.get(f"{p.scheme}://{p.netloc}/robots.txt", headers=UA, timeout=15)
        if r.status_code >= 400:
            return True
        rp.parse(r.text.splitlines())
        return rp.can_fetch(UA["User-Agent"], url)
    except Exception:
        return True


# ---------------------------------------------------------------- YouTube API
def yt(endpoint: str, cost: int = 1, **params) -> dict:
    global quota_used
    params["key"] = API_KEY
    r = requests.get(f"{YT}/{endpoint}", params=params, timeout=30)
    quota_used += cost
    if r.status_code != 200:
        raise RuntimeError(f"{endpoint} {r.status_code}: {r.text[:200]}")
    return r.json()


def iso_duration_seconds(d: str) -> int:
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m:
        return 0
    days, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return days * 86400 + h * 3600 + mi * 60 + s


def slim_video(v: dict, extra: dict | None = None) -> dict:
    sn, st, cd = v.get("snippet", {}), v.get("statistics", {}), v.get("contentDetails", {})
    rec = {
        "id": v["id"],
        "title": sn.get("title"),
        "channel_id": sn.get("channelId"),
        "channel": sn.get("channelTitle"),
        "published": sn.get("publishedAt"),
        "category_id": sn.get("categoryId"),
        "lang": sn.get("defaultAudioLanguage") or sn.get("defaultLanguage"),
        "tags": (sn.get("tags") or [])[:15],
        "desc": (sn.get("description") or "")[:300],
        "thumb": (sn.get("thumbnails", {}).get("medium") or {}).get("url"),
        "live": sn.get("liveBroadcastContent"),
        "duration_s": iso_duration_seconds(cd.get("duration", "")),
        "views": int(st.get("viewCount", 0) or 0),
        "likes": int(st.get("likeCount", 0) or 0),
        "comments": int(st.get("commentCount", 0) or 0),
        "made_for_kids": (v.get("status") or {}).get("madeForKids"),
    }
    if extra:
        rec.update(extra)
    return rec


def video_details(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        try:
            res = yt("videos", part="snippet,statistics,contentDetails,status", id=",".join(chunk), maxResults=50)
            for v in res.get("items", []):
                out[v["id"]] = v
        except Exception as e:  # keep going
            print("videos.list failed", e)
    return out


def collect_popular() -> None:
    cfg = CONFIG["youtube"]
    rows: dict[str, dict] = {}
    for cat in cfg["popular_category_ids"]:
        token, rank = None, 0
        for _ in range(cfg["popular_pages_per_category"]):
            params = dict(part="snippet,statistics,contentDetails,status", chart="mostPopular",
                          regionCode=cfg["region"], maxResults=50)
            if cat != "0":
                params["videoCategoryId"] = cat
            if token:
                params["pageToken"] = token
            try:
                res = yt("videos", **params)
            except Exception as e:
                status.setdefault("youtube_popular_errors", {"ok": True, "detail": "", "count": 0})
                status["youtube_popular_errors"]["detail"] += f"cat {cat}: {str(e)[:60]}; "
                break
            for v in res.get("items", []):
                rank += 1
                rec = rows.get(v["id"])
                if rec is None:
                    rows[v["id"]] = slim_video(v, {"charts": {cat: rank}})
                else:
                    rec["charts"][cat] = rank
            token = res.get("nextPageToken")
            if not token:
                break
    save("youtube_popular.json", list(rows.values()))
    log("youtube_popular", bool(rows), f"{len(rows)} unique videos", len(rows))


def load_watchlist() -> dict:
    p = ROOT / "config" / "watchlist_resolved.json"
    return json.loads(p.read_text()) if p.exists() else {"updated": None, "channels": {}}


def discover_watchlist(force: bool = False) -> dict:
    """Weekly refresh of the watchlist: manual handles + channels behind top search results."""
    wl = load_watchlist()
    last = wl.get("updated")
    if not force and last and (NOW.date() - dt.date.fromisoformat(last)).days < 7:
        return wl
    disc = CONFIG["watchlist_discovery"]
    channels: dict[str, dict] = {}
    # manual handles
    for area, handles in disc["manual_handles"].items():
        for h in handles:
            try:
                res = yt("channels", part="id", forHandle=h)
                for it in res.get("items", []):
                    channels[it["id"]] = {"area": area, "source": "manual", "handle": h}
            except Exception as e:
                print("handle failed", h, e)
    # discovery via search
    for area, queries in disc["queries"].items():
        for q in queries:
            try:
                res = yt("search", cost=100, part="snippet", q=q, type="video", regionCode="IN",
                         relevanceLanguage="hi", order="viewCount", maxResults=50,
                         publishedAfter=(NOW - dt.timedelta(days=90)).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
                for it in res.get("items", []):
                    cid = it["snippet"]["channelId"]
                    channels.setdefault(cid, {"area": area, "source": f"search:{q}"})
            except Exception as e:
                print("discovery search failed", q, e)
    # channel stats + uploads playlist
    ids = list(channels)
    for i in range(0, len(ids), 50):
        try:
            res = yt("channels", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]), maxResults=50)
            for c in res.get("items", []):
                channels[c["id"]].update({
                    "title": c["snippet"]["title"],
                    "subs": int(c["statistics"].get("subscriberCount", 0) or 0),
                    "videos": int(c["statistics"].get("videoCount", 0) or 0),
                    "uploads": c["contentDetails"]["relatedPlaylists"]["uploads"],
                })
        except Exception as e:
            print("channels.list failed", e)
    # keep manual + top by subs and a slice of small channels (outliers live there)
    keep: dict[str, dict] = {}
    cap = disc["max_channels_per_area"]
    for area in disc["queries"]:
        pool = [(cid, c) for cid, c in channels.items() if c.get("area") == area and c.get("uploads")]
        manual = [(cid, c) for cid, c in pool if c["source"] == "manual"]
        rest = sorted([p for p in pool if p[1]["source"] != "manual"], key=lambda x: -x[1].get("subs", 0))
        big = rest[: int(cap * 0.6)]
        small = [p for p in rest[int(cap * 0.6):] if 10_000 <= p[1].get("subs", 0) <= 2_000_000][: cap - len(big)]
        for cid, c in manual + big + small:
            keep[cid] = c
    wl = {"updated": NOW.date().isoformat(), "channels": keep}
    (ROOT / "config" / "watchlist_resolved.json").write_text(json.dumps(wl, ensure_ascii=False, indent=1))
    log("watchlist_discovery", bool(keep), f"{len(keep)} channels kept", len(keep))
    return wl


def collect_watchlist(wl: dict) -> None:
    n = CONFIG["youtube"]["watchlist_recent_uploads"]
    vid_area: dict[str, str] = {}
    for cid, c in wl.get("channels", {}).items():
        try:
            res = yt("playlistItems", part="contentDetails", playlistId=c["uploads"], maxResults=n)
            for it in res.get("items", []):
                vid_area[it["contentDetails"]["videoId"]] = c["area"]
        except Exception as e:
            print("playlistItems failed", c.get("title"), str(e)[:80])
    det = video_details(list(vid_area))
    rows = [slim_video(v, {"area": vid_area[vid], "channel_subs": wl["channels"].get(v["snippet"]["channelId"], {}).get("subs")})
            for vid, v in det.items()]
    save("youtube_watchlist.json", rows)
    log("youtube_watchlist", bool(rows), f"{len(rows)} videos from {len(wl.get('channels', {}))} channels", len(rows))


def todays_keywords(area: str, k: int) -> list[str]:
    kws = CONFIG["keywords"][area]
    start = (NOW.toordinal() * k) % len(kws)
    return [kws[(start + i) % len(kws)] for i in range(k)]


def collect_search() -> None:
    cfg = CONFIG["youtube"]
    after = (NOW - dt.timedelta(hours=cfg["search_window_hours"])).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    hits: dict[str, dict] = {}
    for area in CONFIG["keywords"]:
        for q in todays_keywords(area, cfg["searches_per_channel_per_day"]):
            try:
                res = yt("search", cost=100, part="snippet", q=q, type="video", regionCode="IN",
                         relevanceLanguage="hi", order="viewCount", publishedAfter=after, maxResults=25)
                for it in res.get("items", []):
                    hits.setdefault(it["id"]["videoId"], {"area": area, "query": q})
            except Exception as e:
                print("search failed", q, str(e)[:80])
    det = video_details(list(hits))
    rows = [slim_video(v, hits[vid]) for vid, v in det.items()]
    save("youtube_search.json", rows)
    log("youtube_search", bool(rows), f"{len(rows)} videos", len(rows))


# ---------------------------------------------------------------- free web sources
def collect_autocomplete() -> None:
    out = {}
    for area, kws in CONFIG["keywords"].items():
        for q in kws:
            try:
                r = requests.get(CONFIG["youtube_autocomplete"].format(q=urllib.parse.quote(q)), headers=UA, timeout=15)
                out[q] = {"area": area, "suggestions": r.json()[1][:10]}
            except Exception as e:
                out[q] = {"area": area, "error": str(e)[:80]}
            time.sleep(0.3)
    save("autocomplete.json", out)
    ok = sum(1 for v in out.values() if "suggestions" in v)
    log("youtube_autocomplete", ok > 0, f"{ok}/{len(out)} keywords", ok)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(url: str, limit: int = 40) -> list[dict]:
    """Minimal RSS/Atom parser (stdlib only). Keeps Google Trends' ht:* fields."""
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:  # malformed feed: lenient fallback
        soup = BeautifulSoup(r.content, "html.parser")
        return [{"title": (it.find("title").get_text(strip=True) if it.find("title") else None),
                 "link": (it.find("link").get("href") or it.find("link").get_text(strip=True)) if it.find("link") else None,
                 "published": (it.find("pubdate") or it.find("published") or it.find("updated")).get_text(strip=True)
                 if (it.find("pubdate") or it.find("published") or it.find("updated")) else None,
                 "summary": ""} for it in soup.find_all(["item", "entry"])[:limit]]
    entries = [e for e in root.iter() if _local(e.tag) in ("item", "entry")]
    items = []
    for e in entries[:limit]:
        f: dict[str, str] = {}
        for c in e:
            name = _local(c.tag)
            if name == "link" and c.get("href"):
                f.setdefault("link", c.get("href"))
            elif name == "news_item":
                t = next((x.text for x in c if _local(x.tag) == "news_item_title"), None)
                if t:
                    f.setdefault("news", t)
            elif c.text and name not in f:
                f[name] = c.text.strip()
        items.append({
            "title": f.get("title"),
            "link": f.get("link"),
            "published": f.get("pubDate") or f.get("published") or f.get("updated"),
            "summary": BeautifulSoup(f.get("description") or f.get("summary") or "", "html.parser").get_text(" ")[:300],
            **({"traffic": f["approx_traffic"]} if f.get("approx_traffic") else {}),
            **({"news": f["news"]} if f.get("news") else {}),
        })
    return items


def collect_trends() -> None:
    try:
        items = parse_feed(CONFIG["google_trends_rss"], 60)
        save("trends.json", items)
        log("google_trends", bool(items), "", len(items))
    except Exception as e:
        log("google_trends", False, str(e))


def collect_news() -> None:
    out: dict[str, dict] = {}
    for area, qs in CONFIG["google_news_queries"].items():
        for q in qs:
            url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:1d")
                   + "&hl=en-IN&gl=IN&ceid=IN:en")
            key = f"gnews:{area}:{q}"
            try:
                out[key] = {"area": area, "group": "google_news", "items": parse_feed(url, 15)}
                log(key, True, "", len(out[key]["items"]))
            except Exception as e:
                log(key, False, str(e))
    for group, feeds in CONFIG["rss_feeds"].items():
        for name, url in feeds.items():
            key = f"rss:{name}"
            try:
                out[key] = {"group": group, "items": parse_feed(url, 25)}
                log(key, bool(out[key]["items"]), "", len(out[key]["items"]))
            except Exception as e:
                log(key, False, str(e))
    save("news.json", out)


def collect_reddit() -> None:
    """One combined request (Reddit rate-limits GitHub's IPs hard); split posts back per subreddit."""
    out: dict[str, list] = {s: [] for s in CONFIG["reddit_subs"]}
    url = "https://www.reddit.com/r/" + "+".join(CONFIG["reddit_subs"]) + "/top/.rss?t=day&limit=100"
    for attempt in range(3):
        try:
            items = parse_feed(url, 100)
            for it in items:
                m = re.search(r"reddit\.com/r/([^/]+)/", it.get("link") or "")
                sub = m.group(1) if m else "other"
                key = next((s for s in out if s.lower() == sub.lower()), sub)
                out.setdefault(key, []).append(it)
            log("reddit", bool(items), "", len(items))
            break
        except Exception as e:
            if attempt == 2:
                log("reddit", False, str(e))
            time.sleep(20)
    save("reddit.json", out)


def collect_x_trends() -> None:
    out = []
    for url in CONFIG["x_trends_pages"]:
        if not allowed(url):
            log("x_trends", False, "robots.txt disallows")
            continue
        try:
            r = requests.get(url, headers=UA, timeout=25)
            soup = BeautifulSoup(r.content, "html.parser", from_encoding="utf-8")
            first = soup.select_one("ol.trend-card__list") or soup.find("ol")
            names = [a.get_text(strip=True) for a in (first.select("a") if first else [])]
            # also collect all cards (last ~24h, hourly) to measure persistence
            counts: dict[str, int] = {}
            for ol in soup.select("ol.trend-card__list"):
                for a in ol.select("a"):
                    t = a.get_text(strip=True)
                    counts[t] = counts.get(t, 0) + 1
            out = [{"topic": t, "rank_now": (names.index(t) + 1) if t in names else None, "hours_trending": c}
                   for t, c in sorted(counts.items(), key=lambda x: -x[1])][:80]
        except Exception as e:
            log("x_trends", False, str(e))
    save("x_trends.json", out)
    if out:
        log("x_trends", True, "", len(out))


def collect_kworb() -> None:
    rows = []
    for url in CONFIG["kworb_pages"]:
        if not allowed(url):
            log("kworb", False, "robots.txt disallows")
            continue
        try:
            r = requests.get(url, headers=UA, timeout=25)
            soup = BeautifulSoup(r.text, "html.parser")
            for tr in soup.select("table tr")[1:101]:
                tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(tds) >= 7:
                    rows.append({"pos": tds[0], "track": tds[2], "weeks": tds[3], "peak": tds[4],
                                 "weekly_views": tds[-2], "change": tds[-1]})
        except Exception as e:
            log("kworb", False, str(e))
    save("kworb.json", rows)
    if rows:
        log("kworb", True, "", len(rows))


def main() -> None:
    print("Collecting for", TODAY)
    if API_KEY:
        try:
            wl = discover_watchlist(force=NOW.weekday() == 6 or "--rediscover" in sys.argv)
            collect_popular()
            collect_watchlist(wl)
            collect_search()
        except Exception as e:
            log("youtube_api", False, str(e))
    else:
        log("youtube_api", False, "YOUTUBE_API_KEY secret not set")
    for fn in (collect_autocomplete, collect_trends, collect_news, collect_reddit, collect_x_trends, collect_kworb):
        try:
            fn()
        except Exception as e:
            log(fn.__name__, False, str(e))
    status["_meta"] = {"date": TODAY, "finished_ist": dt.datetime.now(IST).isoformat(timespec="minutes"),
                       "youtube_quota_units": quota_used}
    save("status.json", status)
    print("quota units used:", quota_used)


if __name__ == "__main__":
    main()
