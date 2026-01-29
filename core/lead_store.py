import json
from pathlib import Path
from datetime import datetime

LEADS_FILE = Path("data/leads.json")
LEADS_FILE.parent.mkdir(exist_ok=True)


def _load_all():
    if not LEADS_FILE.exists():
        return []
    return json.loads(LEADS_FILE.read_text(encoding="utf-8"))


def _save_all(leads):
    LEADS_FILE.write_text(
        json.dumps(leads, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def now():
    return datetime.utcnow().isoformat()
