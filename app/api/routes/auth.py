from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.services.mailer import send_email
from app.services.subscriber_store import subscriber_store
from app.services.user_store import sanitize_user, user_store

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/test")
def test_auth():
    return {"message": "Auth route working ✅"}



class SubscriptionRequest(BaseModel):
    name: str
    email: EmailStr


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)
    phone_number: str | None = Field(default=None, min_length=8, max_length=16)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)


def _parse_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header.")
    return token


def _current_user(token: str = Depends(_parse_token)):
    user = user_store.resolve_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please log in again.")
    return user, token


@router.post("/signup")
def signup_user(payload: SignupRequest):
    try:
        user = user_store.create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            phone_number=payload.phone_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = user_store.create_session(user_id=user["id"])
    return {"token": token, "user": sanitize_user(user)}


@router.post("/login")
def login_user(payload: LoginRequest):
    try:
        user = user_store.verify_credentials(email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = user_store.create_session(user_id=user["id"])
    return {"token": token, "user": sanitize_user(user)}


@router.get("/session")
def fetch_session(context=Depends(_current_user)):
    user, _ = context
    return {"user": sanitize_user(user)}


@router.post("/logout")
def logout_user(context=Depends(_current_user)):
    _, token = context
    user_store.drop_session(token)
    return {"status": "success"}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_user(request: SubscriptionRequest):
    """
    Subscribe a user to daily UPSC news capsules using the MongoDB store.
    """
    try:
        subscriber_store.add_subscriber(name=request.name, email=request.email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    send_email(
        recipient=request.email,
        subject="Welcome to CivicBriefs.AI 🎉",
        body=f"<h3>Hi {request.name},</h3><p>Thanks for subscribing to our UPSC Daily Capsule!</p>"
    )

    return {
        "status": "success",
        "message": f"🎉 {request.name}, you’ve been subscribed to CivicBriefs.AI daily capsule!",
    }