from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.services.mongo import get_collection

logger = logging.getLogger(__name__)


class ReportStore:
    """Read-only accessor for persisted planner reports."""

    def __init__(self, collection_name: str = "reports") -> None:
        self.collection: Optional[Collection] = None
        try:
            collection = get_collection(collection_name)
            collection.create_index([("user_id", 1), ("date", -1)])
            collection.create_index([("user_email", 1), ("date", -1)])
            self.collection = collection
        except PyMongoError as exc:
            logger.warning("report_store: Mongo unavailable; report lookups disabled: %s", exc)

    def latest_for_user(
        self,
        *,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if self.collection is None:
            return None
        queries: List[Dict[str, Any]] = []
        if user_id:
            queries.append({"user_id": user_id})
        if user_email:
            queries.append({"user_email": user_email.strip().lower()})
        if not queries:
            return None

        for query in queries:
            try:
                doc = self.collection.find_one(query, sort=[("date", -1)])
            except PyMongoError as exc:
                logger.error("report_store: failed to fetch latest report: %s", exc)
                return None
            if doc:
                return self._serialize(doc)
        return None

    def _serialize(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        payload = doc.get("report") or {}
        summary = payload.get("test_summary") or {}
        section_report = payload.get("section_report") or {}
        feedback = payload.get("feedback") or {}

        sections: List[Dict[str, Any]] = []
        if isinstance(section_report, dict):
            for slug, meta in section_report.items():
                if not isinstance(meta, dict):
                    continue
                sections.append(
                    {
                        "slug": slug,
                        "label": meta.get("label") or self._fallback_label(slug),
                        "accuracy": self._to_float(meta.get("accuracy")),
                        "correct": self._to_int(meta.get("correct")),
                        "total": self._to_int(meta.get("total")),
                    }
                )
        sections.sort(key=lambda item: item["label"])

        return {
            "id": self._stringify(doc.get("_id")),
            "user_id": doc.get("user_id"),
            "user_email": doc.get("user_email"),
            "date": self._serialize_date(doc.get("date")),
            "overall_accuracy": self._to_float(summary.get("overall_accuracy")),
            "total_questions": self._to_int(summary.get("total_questions")),
            "total_correct": self._to_int(summary.get("total_correct")),
            "sections": sections,
            "feedback_summary": feedback.get("summary"),
        }

    @staticmethod
    def _serialize_date(value: Any) -> Optional[str]:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time()).isoformat()
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _fallback_label(slug: str) -> str:
        cleaned = (slug or "").replace("_", " ").strip()
        return cleaned.title() or "Section"

    @staticmethod
    def _stringify(value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number != number:  # NaN check
            return None
        return round(number, 2)

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


def _build_report_store() -> ReportStore:
    return ReportStore()


report_store = _build_report_store()
