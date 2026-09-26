"""Delete bulky raw snapshots older than N days; keep analysis, brief_input, db docs and status."""
import datetime as dt, sys
from pathlib import Path
keep_days = int(sys.argv[1]) if len(sys.argv) > 1 else 21
root = Path(__file__).resolve().parents[1] / "data"
cut = dt.date.today() - dt.timedelta(days=keep_days)
for d in root.iterdir() if root.exists() else []:
    try:
        day = dt.date.fromisoformat(d.name)
    except ValueError:
        continue
    if day < cut:
        for f in d.glob("*.json"):
            if f.name.startswith(("youtube_", "news", "reddit", "autocomplete")):
                f.unlink()
