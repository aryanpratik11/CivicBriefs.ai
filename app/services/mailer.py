# app/services/mailer.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
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
    Sends a plain HTML email using SMTP.
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


def send_mail_with_attachment(to_email: str, subject: str, body: str, attachment_path: str) -> bool:
    """
    Sends an email with a PDF or any file attached.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        # Email body
        msg.attach(MIMEText(body, "html"))

        # Attach file
        if not os.path.exists(attachment_path):
            print(f"❌ Attachment not found: {attachment_path}")
            return False

        with open(attachment_path, "rb") as f:
            file_part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))

        file_part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(file_part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print(f"📧 Email with attachment sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email with attachment to {to_email}: {e}")
        return False
