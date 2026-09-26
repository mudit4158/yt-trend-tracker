"""Helpers for the daily Claude run: cooldown ledger + dashboard write plan.

  python analyzer/dbsync.py ledger <ideas_dir> <date>
      Reads the ideas exported from the dashboard (ArtifactData list with out_dir),
      writes data/<date>/out/ledger.json with:
        blocked   topic clusters that must NOT be suggested today (with reason + until)
        open      ideas still Suggested/Accepted/In production
        expire    Suggested ideas older than 7 days -> to be marked Expired
        learning  recent Rejected reasons and Published ideas (feedback for the model)

  python analyzer/dbsync.py plan <date> [versions_json]
      Builds data/<date>/out/batches/batch_N.json (<=50 writes each) that set:
        analyzer docs (tracker/areas/pulse/patterns/calendar), topics/<date>,
        ideas/<id> (new cards), ideas/<id> Expired updates, meta/latest,
        runs/<date>. Every document is new each day, so no version pins are needed
        (except Expired updates, which take versions from the ideas listing).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COOLDOWN = {  # days after the idea was Published
    "evergreen": 60,
    "news": 14,
    "kid_concept": 30,
    "festival": 300,  # until the festival comes round again (calendar re-triggers it)
}


def _d(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except ValueError:
        return None


def ledger(ideas_dir: str, date: str) -> None:
    today = dt.date.fromisoformat(date)
    ideas = []
    for p in Path(ideas_dir).rglob("*.json"):
        try:
            doc = json.loads(p.read_text())
        except Exception:
            continue
        doc = doc.get("data", doc) if isinstance(doc, dict) else doc
        doc.setdefault("id", p.stem)
        ideas.append(doc)
    blocked, open_, expire, learning = [], [], [], {"rejected": [], "published": [], "refinements": []}
    for i in ideas:
        for r in i.get("refinements") or []:
            if isinstance(r, dict) and (_d(r.get("at")) or today) >= today - dt.timedelta(days=30):
                learning["refinements"].append({"id": i["id"], "channel": i.get("channel"), "asked": r.get("instructions"), "on": str(r.get("at", ""))[:10]})
        st = i.get("status", "Suggested")
        cl = i.get("topic_cluster")
        when = _d(i.get("published_at") or i.get("updated_at") or i.get("date"))
        if st in ("Accepted", "In production"):
            blocked.append({"cluster": cl, "reason": st, "until": "open"})
            open_.append({"id": i["id"], "status": st, "title": (i.get("titles") or [""])[0]})
        elif st == "Suggested":
            age = (today - (_d(i.get("date")) or today)).days
            if age > 7:
                expire.append(i["id"])
            else:
                blocked.append({"cluster": cl, "reason": f"already suggested {i.get('date')} (still open)", "until": "open"})
                open_.append({"id": i["id"], "status": st, "title": (i.get("titles") or [""])[0]})
        elif st == "Published" and when:
            until = when + dt.timedelta(days=COOLDOWN.get(i.get("kind", "evergreen"), 60))
            if until >= today:
                blocked.append({"cluster": cl, "reason": f"published {when}", "until": until.isoformat(),
                                "different_angle_after": (when + dt.timedelta(days=30)).isoformat() if i.get("kind") == "evergreen" else None})
            learning["published"].append({"id": i["id"], "cluster": cl, "url": i.get("published_url"), "on": when.isoformat()})
        elif st == "Rejected" and when:
            until = when + dt.timedelta(days=14)
            if until >= today:
                blocked.append({"cluster": cl, "reason": f"rejected {when}: {i.get('reject_reason', '')}", "until": until.isoformat()})
            learning["rejected"].append({"cluster": cl, "reason": i.get("reject_reason"), "on": when.isoformat()})
    out = ROOT / "data" / date / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ledger.json").write_text(json.dumps({"blocked": blocked, "open": open_, "expire": expire,
                                                 "learning": learning, "total_ideas": len(ideas),
                                                 "existing_ids": sorted(i["id"] for i in ideas)}, ensure_ascii=False, indent=1))
    print(f"ideas={len(ideas)} blocked={len(blocked)} expire={len(expire)} -> {out/'ledger.json'}")


def plan(date: str, versions_path: str | None) -> None:
    """versions_path: optional JSON {"<idea id>": version} copied from the ideas listing (needed only to expire ideas)."""
    versions = json.loads(Path(versions_path).read_text()) if versions_path and Path(versions_path).exists() else {}
    day = ROOT / "data" / date
    out = day / "out"
    writes = []
    for f in sorted((day / "db").glob("*.json")):
        coll, doc_id = f.stem.split("__", 1)
        writes.append({"op": "set", "collection": coll, "doc_id": doc_id, "file_path": str(f)})
    if (out / "topics.json").exists():
        writes.append({"op": "set", "collection": "topics", "doc_id": date, "file_path": str(out / "topics.json")})
    for f in sorted((out / "ideas").glob("*.json")) if (out / "ideas").exists() else []:
        writes.append({"op": "set", "collection": "ideas", "doc_id": f.stem, "file_path": str(f)})
    ledger_p = out / "ledger.json"
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).isoformat(timespec="minutes")
    if ledger_p.exists():
        for iid in json.loads(ledger_p.read_text()).get("expire", []):
            p = out / "expire" / f"{iid}.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"status": "Expired", "updated_at": now}))
            w = {"op": "update", "collection": "ideas", "doc_id": iid, "file_path": str(p)}
            if versions.get(iid):
                w["if_version"] = versions[iid]
            writes.append(w)
    # one run document per day (new documents need no version pin)
    run = json.loads((out / "run.json").read_text()) if (out / "run.json").exists() else {}
    status = json.loads((day / "status.json").read_text()) if (day / "status.json").exists() else {}
    failed = sorted(k for k, v in status.items() if isinstance(v, dict) and v.get("ok") is False)
    run_doc = {"date": date, "finished_ist": now[11:16] + " IST", "failed_sources": failed, **run}
    (out / "run_doc.json").write_text(json.dumps(run_doc, ensure_ascii=False, indent=1))
    writes.append({"op": "set", "collection": "runs", "doc_id": date, "file_path": str(out / "run_doc.json")})
    bdir = out / "batches"
    bdir.mkdir(parents=True, exist_ok=True)
    for f in bdir.glob("*.json"):
        f.unlink()
    for n in range(0, len(writes), 50):
        (bdir / f"batch_{n // 50 + 1}.json").write_text(json.dumps(writes[n:n + 50], indent=1))
    print(f"{len(writes)} writes in {len(list(bdir.glob('*.json')))} batch file(s) -> {bdir}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "ledger":
        ledger(sys.argv[2], sys.argv[3])
    elif cmd == "plan":
        plan(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        sys.exit(__doc__)
