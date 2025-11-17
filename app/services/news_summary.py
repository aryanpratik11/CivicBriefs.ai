from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.services.mongo import get_collection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArticleSummary:
    title: str
    source: str
    url: str | None
    category: str
    chunk_count: int
    summary_points: List[str]
    pyq_points: List[str]
    syllabus_points: List[str]
    snapshot_date: date


class NewsSummaryService:
    """Loads generated news capsules and exposes simplified summaries."""

    WINDOW_DAYS: Dict[str, int] = {
        "daily": 1,
        "weekly": 7,
        "monthly": 30,
    }

    def __init__(
        self,
        base_file: Path | str | None = None,
        archive_dir: Path | str = "data/news_capsules",
        max_articles_per_section: int = 3,
        collection_name: str = "news",
    ) -> None:
        self.base_file = Path(base_file or "news_capsules.json")
        self.archive_dir = Path(archive_dir)
        self.max_articles_per_section = max(1, max_articles_per_section)
        self.collection: Collection | None = None
        try:
            self.collection = get_collection(collection_name)
        except PyMongoError as exc:
            logger.warning("news_summary: Mongo unavailable; database summaries disabled: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_summary(self, window: str) -> Dict[str, object]:
        normalized_window, selected = self._prepare_window(window)

        articles: List[ArticleSummary] = []
        for snap in selected:
            articles.extend(snap["articles"])

        if not articles:
            raise FileNotFoundError("Snapshots were empty; run the news pipeline first.")

        sections = self._build_sections(articles)
        totals = self._build_totals(articles)
        start_date = min(snap["date"] for snap in selected)
        end_date = max(snap["date"] for snap in selected)

        return {
            "range": normalized_window,
            "generated_at": datetime.utcnow().isoformat(timespec="seconds"),
            "window": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "snapshots": len(selected),
            },
            "totals": totals,
            "sections": sections,
        }

    def get_capsules(self, window: str) -> Dict[str, object]:
        normalized_window, selected = self._prepare_window(window)

        start_date = min(snap["date"] for snap in selected)
        end_date = max(snap["date"] for snap in selected)
        ordered = sorted(selected, key=lambda snap: snap["date"], reverse=True)

        capsules: List[Dict[str, object]] = []
        for snap in ordered:
            articles = snap["articles"]
            if not articles:
                continue
            sections = self._build_sections(articles, limit_per_section=0)
            totals = self._build_totals(articles)
            capsules.append(
                {
                    "date": snap["date"].isoformat(),
                    "weekday": snap["date"].strftime("%A"),
                    "totals": totals,
                    "sections": sections,
                }
            )

        if not capsules:
            raise FileNotFoundError("Snapshots were empty; run the news pipeline first.")

        return {
            "range": normalized_window,
            "generated_at": datetime.utcnow().isoformat(timespec="seconds"),
            "window": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "snapshots": len(selected),
            },
            "capsules": capsules,
        }

    # ------------------------------------------------------------------
    # Snapshot helpers
    # ------------------------------------------------------------------
    def _load_snapshots(self, window: str | None = None) -> List[Dict[str, object]]:
        if self.collection is not None:
            return self._load_snapshots_from_db(window=window)

        # File-based ingestion disabled now that we rely on MongoDB.
        # snapshots: List[Dict[str, object]] = []
        # if self.base_file.exists():
        #     snapshots.append(self._build_snapshot(self.base_file))
        # if self.archive_dir.exists():
        #     for path in sorted(self.archive_dir.glob("*.json")):
        #         snapshots.append(self._build_snapshot(path))
        # snapshots.sort(key=lambda item: item["date"])
        raise FileNotFoundError("MongoDB collection unavailable and local files are disabled.")

    def _load_snapshots_from_db(self, *, window: str | None = None) -> List[Dict[str, object]]:
        if self.collection is None:
            return []

        try:
            query: Dict[str, object]
            if window:
                query = {"type": window}
            else:
                query = {"type": {"$in": list(self.WINDOW_DAYS.keys())}}

            cursor = (
                self.collection.find(
                    query,
                    projection={"date": 1, "type": 1, "news_capsule": 1},
                )
                .sort("date", 1)
            )
        except PyMongoError as exc:
            logger.error("news_summary: failed to fetch snapshots from Mongo: %s", exc)
            raise FileNotFoundError("Unable to load news capsules from database.") from exc

        snapshots: List[Dict[str, object]] = []
        for document in cursor:
            snapshot = self._build_snapshot_from_document(document)
            if snapshot["articles"]:
                snapshots.append(snapshot)

        return snapshots

    def _build_snapshot_from_document(self, document: Dict[str, object]) -> Dict[str, object]:
        snapshot_date = self._coerce_snapshot_date(document.get("date"))
        payload = self._extract_structure(document)
        articles = self._normalize_articles(payload, snapshot_date)
        identifier = document.get("_id")
        return {
            "path": f"mongo:{identifier}",
            "date": snapshot_date,
            "articles": articles,
        }

    def _extract_structure(self, document: Dict[str, object]) -> Dict[str, object]:
        capsule = document.get("news_capsule") if isinstance(document, dict) else None
        if isinstance(capsule, dict):
            structure = capsule.get("structure")
            if isinstance(structure, dict):
                return structure
        return {}

    def _coerce_snapshot_date(self, raw: object) -> date:
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, date):
            return raw
        if isinstance(raw, str):
            try:
                return date.fromisoformat(raw[:10])
            except ValueError:
                logger.debug("news_summary: invalid date string '%s', using utcnow", raw)
        return datetime.utcnow().date()

    def _build_snapshot(self, path: Path) -> Dict[str, object]:
        payload = self._read_json(path)
        snapshot_date = self._infer_snapshot_date(path)
        articles = self._normalize_articles(payload, snapshot_date)
        return {"path": str(path), "date": snapshot_date, "articles": articles}

    def _read_json(self, path: Path) -> Dict[str, object]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _infer_snapshot_date(self, path: Path) -> date:
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", path.stem)
        if match:
            try:
                return date.fromisoformat(match.group(1))
            except ValueError:
                pass
        return datetime.utcfromtimestamp(path.stat().st_mtime).date()

    def _normalize_articles(self, payload: Dict[str, object], snapshot_date: date) -> List[ArticleSummary]:
        articles: List[ArticleSummary] = []
        if not isinstance(payload, dict):
            return articles

        for category, maybe_items in payload.items():
            if not isinstance(maybe_items, list):
                continue
            for item in maybe_items:
                if not isinstance(item, dict):
                    continue
                summary_blocks = self._parse_summary_markdown(item.get("summary", ""))
                articles.append(
                    ArticleSummary(
                        title=item.get("title") or "Untitled",
                        source=item.get("source") or "",
                        url=item.get("url"),
                        category=str(category),
                        chunk_count=int(item.get("chunk_count", 0)),
                        summary_points=summary_blocks["summary"],
                        pyq_points=summary_blocks["pyq"],
                        syllabus_points=summary_blocks["syllabus"],
                        snapshot_date=snapshot_date,
                    )
                )
        return articles

    # ------------------------------------------------------------------
    # Aggregations
    # ------------------------------------------------------------------
    def _select_snapshots(
        self,
        snapshots: Sequence[Dict[str, object]],
        window: str,
    ) -> List[Dict[str, object]]:
        days = self.WINDOW_DAYS[window]
        cutoff = datetime.utcnow().date() - timedelta(days=days - 1)
        selected = [snap for snap in snapshots if snap["date"] >= cutoff]
        return selected

    def _build_sections(
        self,
        articles: Iterable[ArticleSummary],
        *,
        limit_per_section: int | None = None,
    ) -> List[Dict[str, object]]:
        grouped: defaultdict[str, List[ArticleSummary]] = defaultdict(list)
        for article in articles:
            grouped[article.category].append(article)

        sections: List[Dict[str, object]] = []
        limit = self.max_articles_per_section if limit_per_section is None else int(limit_per_section)
        for category, items in grouped.items():
            sorted_items = sorted(
                items,
                key=lambda art: (art.snapshot_date, art.chunk_count, art.title.lower()),
                reverse=True,
            )
            if limit <= 0:
                serialized_items = sorted_items
            else:
                serialized_items = sorted_items[:limit]
            serialized = [self._serialize_article(art) for art in serialized_items]
            sections.append(
                {
                    "label": category,
                    "total_articles": len(items),
                    "articles": serialized,
                }
            )

        sections.sort(key=lambda section: section["total_articles"], reverse=True)
        return sections

    def _build_totals(self, articles: Iterable[ArticleSummary]) -> Dict[str, object]:
        articles_list = list(articles)
        source_counter = Counter(art.source or "Unknown" for art in articles_list)
        category_counter = Counter(art.category for art in articles_list)
        top_sources = [
            {"source": name, "count": count}
            for name, count in source_counter.most_common(5)
        ]
        coverage = [
            {"category": name, "count": count}
            for name, count in category_counter.most_common()
        ]

        return {
            "articles": len(articles_list),
            "categories": len(category_counter),
            "top_sources": top_sources,
            "coverage": coverage,
        }

    def _serialize_article(self, article: ArticleSummary) -> Dict[str, object]:
        return {
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "category": article.category,
            "summary_points": article.summary_points,
            "pyq_points": article.pyq_points,
            "syllabus_points": article.syllabus_points,
            "chunk_count": article.chunk_count,
            "snapshot_date": article.snapshot_date.isoformat(),
        }

    # ------------------------------------------------------------------
    # Markdown parsing
    # ------------------------------------------------------------------
    def _parse_summary_markdown(self, markdown: str) -> Dict[str, List[str]]:
        sections = {"summary": [], "pyq": [], "syllabus": []}
        current: str | None = None
        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            lowered = line.lower()
            if lowered.startswith("**summary"):
                current = "summary"
                continue
            if lowered.startswith("**relevant pyq"):
                current = "pyq"
                continue
            if lowered.startswith("**relevant syllabus"):
                current = "syllabus"
                continue
            if line.startswith("###"):
                continue

            if line.startswith("-") or line.startswith("*"):
                value = line[1:].strip()
                if current:
                    sections[current].append(value or "None")
                continue

            if current == "summary":
                sections[current].append(line)

        for key in sections:
            if not sections[key]:
                sections[key] = ["None"]
        return sections

    def _prepare_window(self, window: str) -> tuple[str, List[Dict[str, object]]]:
        normalized = window.lower()
        if normalized not in self.WINDOW_DAYS:
            raise ValueError(f"Unsupported window '{window}'.")

        snapshots = self._load_snapshots(window=normalized)
        if not snapshots:
            raise FileNotFoundError("No news capsule snapshots available.")

        selected = self._select_snapshots(snapshots, normalized)
        if not selected:
            selected = [snapshots[-1]]

        return normalized, selected


news_summary_service = NewsSummaryService()
