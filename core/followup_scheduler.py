from datetime import datetime
from core.lead_store import _load_all

FOLLOW_UP_DELAY_DAYS = 3
MAX_FOLLOW_UPS = 1   # start with ONE follow-up only


def _days_since(iso_ts: str) -> int:
    dt = datetime.fromisoformat(iso_ts)
    return (datetime.utcnow() - dt).days


def get_followup_candidates():
    """
    Returns leads eligible for follow-up
    """
    candidates = []

    for lead in _load_all():

        if lead["status"] != "SENT":
            continue

        if lead["reply_at"] is not None:
            continue

        if lead["follow_up_count"] >= MAX_FOLLOW_UPS:
            continue

        if not lead["last_message_at"]:
            continue

        if _days_since(lead["last_message_at"]) >= FOLLOW_UP_DELAY_DAYS:
            candidates.append(lead)

    return candidates
