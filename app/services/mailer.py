# app/services/mailer.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load .env credentials
load_dotenv()

EMAIL_USER = os.getenv("SMTP_USERNAME")
EMAIL_PASS = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends an email using Gmail SMTP.
    Returns True if sent successfully, False otherwise.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = recipient
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print(f"✅ Email sent to {recipient}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email to {recipient}: {e}")
        return False
