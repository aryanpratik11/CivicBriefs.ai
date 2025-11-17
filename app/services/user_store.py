from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Protocol
from uuid import uuid4

import bcrypt
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.services.mongo import get_collection


class UserStoreProtocol(Protocol):
    def create_user(self, *, name: str, email: str, password: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        ...

    def verify_credentials(self, email: str, password: str) -> Dict[str, Any]:
        ...

    def create_session(self, user_id: str) -> str:
        ...

    def drop_session(self, token: str) -> None:
        ...

    def resolve_token(self, token: str) -> Optional[Dict[str, Any]]:
        ...

    def public_view(self, user: Dict[str, Any]) -> Dict[str, Any]:
        ...


class MongoUserStore:
    """Mongo-backed user/session store."""

    def __init__(self, session_ttl_hours: int = 24) -> None:
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.users: Collection = get_collection("users")
        self.sessions: Collection = get_collection("sessions")
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.users.create_index("email", unique=True)
        ttl_seconds = int(self.session_ttl.total_seconds())
        self.sessions.create_index("created_at", expireAfterSeconds=ttl_seconds)

    @staticmethod
    def _normalize_user(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        return doc

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email = email.lower().strip()
        doc = self.users.find_one({"email": email})
        return self._normalize_user(doc)

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.users.find_one({"id": user_id})
        return self._normalize_user(doc)

    def create_user(
        self,
        *,
        name: str,
        email: str,
        password: str,
        phone_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        email = email.lower().strip()
        if self.get_user_by_email(email):
            raise ValueError("An account with this email already exists.")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        now = datetime.now(timezone.utc).isoformat()
        user_doc: Dict[str, Any] = {
            "id": f"user_{uuid4().hex}",
            "name": name.strip(),
            "email": email,
            "phone_number": phone_number.strip() if phone_number else None,
            "password_hash": password_hash,
            "created_at": now,
        }

        self.users.insert_one(user_doc)
        return user_doc

    def verify_credentials(self, email: str, password: str) -> Dict[str, Any]:
        user = self.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password.")

        stored_hash = user.get("password_hash")
        if not stored_hash:
            raise ValueError("Password not set for this account.")

        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            raise ValueError("Invalid email or password.")
        return user

    def create_session(self, user_id: str) -> str:
        for _ in range(3):
            token = secrets.token_urlsafe(32)
            try:
                self.sessions.insert_one({
                    "_id": token,
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc),
                })
                return token
            except DuplicateKeyError:
                continue
        raise RuntimeError("Failed to create session token")

    def drop_session(self, token: str) -> None:
        self.sessions.delete_one({"_id": token})

    def resolve_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        session = self.sessions.find_one({"_id": token})
        if not session:
            return None

        user = self.get_user_by_id(session.get("user_id"))
        if not user:
            self.sessions.delete_one({"_id": token})
            return None
        return user

    def public_view(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "phone_number": user.get("phone_number"),
            "created_at": user.get("created_at"),
        }


def _build_user_store() -> UserStoreProtocol:
    try:
        return MongoUserStore()
    except PyMongoError as exc:
        raise RuntimeError("Unable to initialize Mongo-backed user store. Verify MongoDB Atlas connectivity.") from exc


user_store: UserStoreProtocol = _build_user_store()


def sanitize_user(user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    return user_store.public_view(user)
