from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Protocol

from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.services.mongo import get_collection


class SubscriberStoreProtocol(Protocol):
    def add_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        ...

    def list_emails(self) -> List[str]:
        ...


class MongoSubscriberStore:
    """Mongo-backed subscriber storage."""

    def __init__(self) -> None:
        self.collection: Collection = get_collection("subscribers")
        self.collection.create_index("email", unique=True)

    def add_subscriber(self, *, name: str, email: str) -> Dict[str, str]:
        doc = {
            "name": name.strip(),
            "email": email.lower().strip(),
            "created_at": datetime.now(timezone.utc),
        }
        try:
            self.collection.insert_one(doc)
        except DuplicateKeyError as exc:
            raise ValueError("This email is already subscribed.") from exc
        return {"name": doc["name"], "email": doc["email"]}

    def list_emails(self) -> List[str]:
        cursor = self.collection.find({}, {"email": 1, "_id": 0})
        return [doc["email"] for doc in cursor if doc.get("email")]


def _build_store() -> SubscriberStoreProtocol:
    try:
        return MongoSubscriberStore()
    except PyMongoError as exc:
        raise RuntimeError("Unable to initialize Mongo-backed subscriber store. Verify MongoDB Atlas connectivity.") from exc


subscriber_store: SubscriberStoreProtocol = _build_store()
