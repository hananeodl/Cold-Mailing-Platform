import smtplib
from email.mime.text import MIMEText

SMTP_HOST = "smtp.ionos.de"
SMTP_PORT = 587
SMTP_USER = "interessent@immo-vt.de"
SMTP_PASSWORD = "YOUR_PASSWORD"

TO_EMAIL = "interessent@immo-vt.de"


def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
