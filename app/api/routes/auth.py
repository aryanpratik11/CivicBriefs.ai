from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import json
import os
from app.services.mailer import send_email

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/test")
def test_auth():
    return {"message": "Auth route working ✅"}


SUBSCRIBERS_FILE = "data/subscribers.json"
os.makedirs("data", exist_ok=True)


class SubscriptionRequest(BaseModel):
    name: str
    email: EmailStr


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_user(request: SubscriptionRequest):
    """
    Subscribe a user to daily UPSC news capsules.
    Saves their email (and name) to a local file for now.
    """
    # Load existing subscribers (if any)
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
            subscribers = json.load(f)
    else:
        subscribers = []

    # Prevent duplicate subscriptions
    if any(sub["email"] == request.email for sub in subscribers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already subscribed."
        )

    # Add new subscriber
    new_subscriber = {
        "name": request.name,
        "email": request.email
    }
    subscribers.append(new_subscriber)

    # Save back to file
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(subscribers, f, indent=2, ensure_ascii=False)

    send_email(
        recipient=request.email,
        subject="Welcome to CivicBriefs.AI 🎉",
        body=f"<h3>Hi {request.name},</h3><p>Thanks for subscribing to our UPSC Daily Capsule!</p>"
    )

    return {
        "status": "success",
        "message": f"🎉 {request.name}, you’ve been subscribed to CivicBriefs.AI daily capsule!",
    }