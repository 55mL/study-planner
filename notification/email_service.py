# notification/email_service.py
import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

def send_email(to_email, subject, body_html):
    msg = MIMEText(body_html, "html", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())