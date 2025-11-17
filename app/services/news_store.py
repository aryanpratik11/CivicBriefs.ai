from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import Any

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.services.mongo import get_collection

logger = logging.getLogger(__name__)

_ALLOWED_TYPES = {"daily", "weekly", "monthly"}


def _coerce_date(value: date | datetime | str | None) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            logger.warning("news_store: invalid date string '%s', using today", value)
    return datetime.utcnow().date().isoformat()


def _sanitize(payload: Any) -> Any:
    try:
        return json.loads(json.dumps(payload, default=str))
    except (TypeError, ValueError):
        return payload


class NewsStore:
    """Persist generated capsules to MongoDB."""

    def __init__(self) -> None:
        self.collection: Collection | None = None
        try:
            collection = get_collection("news")
            collection.create_index([("date", 1), ("type", 1)], unique=True)
            self.collection = collection
        except PyMongoError as exc:
            logger.warning("news_store: Mongo unavailable, skipping persistence: %s", exc)

    def save_capsule(
        self,
        *,
        capsule_payload: Any,
        capsule_date: date | datetime | str | None = None,
        capsule_type: str = "daily",
    ) -> bool:
        if capsule_payload is None:
            raise ValueError("capsule_payload cannot be None")

        if self.collection is None:
            return False

        normalized_type = (capsule_type or "daily").strip().lower()
        if normalized_type not in _ALLOWED_TYPES:
            logger.debug("news_store: unsupported type '%s', defaulting to daily", normalized_type)
            normalized_type = "daily"

        date_str = _coerce_date(capsule_date)
        now = datetime.now(timezone.utc)
        prepared_payload = _sanitize(capsule_payload)

        try:
            self.collection.update_one(
                {"date": date_str, "type": normalized_type},
                {
                    "$set": {
                        "news_capsule": prepared_payload,
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
            return True
        except PyMongoError as exc:
            logger.error("news_store: failed to persist capsule: %s", exc)
            return False


news_store = NewsStore()
