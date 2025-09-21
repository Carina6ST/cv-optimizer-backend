import os, smtplib, ssl
from email.message import EmailMessage
from typing import Optional

DEV_LOG = os.getenv("EMAIL_DEV_LOG", "false").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@example.com")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_TLS  = os.getenv("SMTP_TLS", "true").lower() == "true"

def send_email(to: str, subject: str, html: str) -> None:
    if DEV_LOG or not SMTP_HOST:
        print(f"[EMAIL DEV LOG] To: {to}\nSubject: {subject}\nHTML:\n{html}\n")
        return
    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("This email contains HTML content.")
    msg.add_alternative(html, subtype="html")

    if SMTP_TLS:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls(context=context)
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            if SMTP_USER and SMTP_PASS:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
