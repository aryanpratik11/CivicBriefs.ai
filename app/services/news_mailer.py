from pathlib import Path

from app.services.mailer import send_mail_with_attachment
from app.services.subscriber_store import subscriber_store


def load_subscribers():
    return subscriber_store.list_emails()


def send_news_capsule_email(pdf_path: str):
    """
    Sends the generated PDF news capsule to all subscribers.
    """
    try:
        pdf = Path(pdf_path)

        if not pdf.exists():
            print(f"❌ PDF not found: {pdf_path}")
            return False

        subscribers = load_subscribers()
        if not subscribers:
            print("⚠️ No subscribers to send email.")
            return False

        print("📨 Sending News Capsule PDF to subscribers...")

        for email in subscribers:
            send_mail_with_attachment(
                to_email=email,
                subject="Your Daily Financial News Capsule",
                body="Please find attached your news capsule for today.",
                attachment_path=str(pdf)
            )

        print("✅ News capsule PDF emailed to all subscribers.")
        return True

    except Exception as e:
        print(f"❌ Error sending news capsule PDF: {e}")
        return False
