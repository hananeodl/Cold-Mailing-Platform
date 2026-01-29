from lead_store import _load_all, _save_all, now
import hashlib
from lead_store import now


def lead_id_from_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def get_lead(url: str):
    lead_id = lead_id_from_url(url)
    for lead in _load_all():
        if lead["id"] == lead_id:
            return lead
    return None


def create_or_get_lead(url: str, platform: str):
    leads = _load_all()
    lead = get_lead(url)

    if lead:
        return lead

    lead = {
        "id": lead_id_from_url(url),
        "platform": platform,
        "url": url,
        "status": "NEW",
        "last_message_at": None,
        "reply_at": None,
        "follow_up_count": 0
    }

    leads.append(lead)
    _save_all(leads)
    return lead


def update_lead(url: str, **updates):
    leads = _load_all()
    for lead in leads:
        if lead["id"] == lead_id_from_url(url):
            lead.update(updates)
            _save_all(leads)
            return lead
    return None

def mark_message_sent(url: str):
    return update_lead(
        url,
        status="SENT",
        last_message_at=now()
    )


def can_send_message(url: str) -> bool:
    lead = get_lead(url)
    if not lead:
        return True

    return lead["status"] in {"NEW", "FAILED"}



def mark_followup_sent(url: str, follow_up_count: int):
    update_lead(
        url,
        status="FOLLOWED_UP",
        last_message_at=now(),
        follow_up_count=follow_up_count + 1
    )
