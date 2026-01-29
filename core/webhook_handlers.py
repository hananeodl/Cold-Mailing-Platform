from core.notifications import send_email


def notify_reply(data):
    subject = "📩 New Reply Received"
    body = f"""
Platform: {data.get('platform')}
From: {data.get('sender_name')}

Message:
{data.get('message')}

URL:
{data.get('listing_url')}
"""
    send_email(subject, body)
