import os
from email.message import EmailMessage
import aiosmtplib
from fastapi import BackgroundTasks

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER or "no-reply@example.com")

async def _send_email(to_email: str, subject: str, html_body: str):
    if not SMTP_HOST:
        print("SMTP not configured. Would send invoice to:", to_email)
        print(html_body)
        return

    message = EmailMessage()
    message["From"] = FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("This email contains an HTML invoice.")
    message.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )

def send_invoice_background(background_tasks: BackgroundTasks, to_email: str, subject: str, html_body: str):
    background_tasks.add_task(_send_email, to_email, subject, html_body)