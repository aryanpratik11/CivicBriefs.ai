"""app/agents/planner_agent.py

PlannerAgent helps with UPSC preparation by:
- Creating objective tests with balanced section coverage (15 Qs each).
- Evaluating submissions against MongoDB question bank answers.
- Persisting test performance for the user and comparing with prior attempts.
- Producing detailed feedback and a structured study schedule.

When `OPENAI_API_KEY` is provided the agent will attempt to enrich the
study-plan via the OpenAI Chat Completions API; otherwise it falls back to the
deterministic planner so that behaviour stays predictable offline.
"""

import json
import os
import random
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError


THRESHOLDS = [
    (0, 40, "Critical Weak"),
    (40, 60, "Weak"),
    (60, 75, "Average"),
    (75, 90, "Strong"),
    (90, 100, "Excellent"),
]


DEFAULT_BOOKLIST = {
    "Polity": ["Indian Polity — M. Laxmikanth", "NCERT Polity (Class 11-12)"],
    "Economy": ["Indian Economy — Ramesh Singh", "NCERT Economics"],
    "History": ["Spectrum Modern India", "NCERT History"],
    "Geography": ["Oxford School Atlas", "NCERT Geography"],
    "Environment": ["Shankar IAS Environment", "NCERT Biology (relevant)"],
    "Science & Tech": ["NCERT Science", "Current Affairs summaries"],
    "Current Affairs": ["PIB releases", "Rajya Sabha TV Debates"],
}


SECTION_CONFIG: Dict[str, Dict[str, Any]] = {
    "polity": {"label": "Polity", "aliases": ["Polity", "polity"]},
    "economy": {"label": "Economy", "aliases": ["Economy", "economy", "Economic"]},
    "history": {"label": "History", "aliases": ["History", "history"]},
    "geography": {"label": "Geography", "aliases": ["Geography", "geography"]},
    "environment": {"label": "Environment", "aliases": ["Environment", "environment", "Ecology"]},
    "scienceTech": {"label": "Science & Tech", "aliases": ["ScienceTech", "scienceTech", "Science", "Technology"]},
    "currentAffairs": {"label": "Current Affairs", "aliases": ["CurrentAffairs", "Current Affairs", "currentAffairs"]},
}

SECTION_ORDER = list(SECTION_CONFIG.keys())


def classify_score(score: float) -> str:
    for lo, hi, label in THRESHOLDS:
        if lo <= score <= hi:
            return label
    return "Unknown"


class PlannerAgent:
    """Composite agent that orchestrates testing and planning for learners."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        mongo_uri: Optional[str] = None,
        mongo_db: Optional[str] = None,
        questions_collection: str = "questions",
        users_collection: str = "users",
    ) -> None:
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = mongo_db or os.getenv("MONGODB_DB", "civicbriefs")

        self._client: MongoClient = MongoClient(uri)
        self._db: Database = self._client[db_name]
        self._questions: Collection = self._db[questions_collection]
        self._users: Collection = self._db[users_collection]

    # ------------------------------------------------------------------
    # Test generation
    # ------------------------------------------------------------------
    def prepare_test(self, questions_per_section: int = 15) -> Dict[str, Any]:
        if questions_per_section <= 0:
            raise ValueError("questions_per_section must be positive")

        test_id = str(uuid.uuid4())
        sections_payload: Dict[str, Dict[str, Any]] = {}
        total_questions = 0

        for section in SECTION_ORDER:
            label = SECTION_CONFIG[section]["label"]
            aliases = SECTION_CONFIG[section]["aliases"]

            available = self._questions.count_documents({"subject": {"$in": aliases}})
            if available < questions_per_section:
                raise ValueError(
                    f"Not enough questions for section '{label}' (required={questions_per_section}, available={available})"
                )

            pipeline = [
                {"$match": {"subject": {"$in": aliases}}},
                {"$sample": {"size": questions_per_section}},
            ]

            docs = list(self._questions.aggregate(pipeline))
            random.shuffle(docs)

            questions = []
            for doc in docs:
                qid = doc.get("question_id") or str(doc.get("_id"))
                questions.append(
                    {
                        "question_id": qid,
                        "section": section,
                        "section_label": label,
                        "subject": doc.get("subject"),
                        "topic": doc.get("topic"),
                        "difficulty": doc.get("difficulty"),
                        "question": doc.get("question"),
                        "options": doc.get("options", {}),
                    }
                )

            sections_payload[section] = {
                "label": label,
                "questions": questions,
            }
            total_questions += len(questions)

        return {
            "test_id": test_id,
            "questions_per_section": questions_per_section,
            "total_questions": total_questions,
            "sections": sections_payload,
        }

    # ------------------------------------------------------------------
    # Submission evaluation
    # ------------------------------------------------------------------
    def evaluate_test(self, user_id: Optional[str], answers: Dict[str, str]) -> Dict[str, Any]:
        if not answers:
            raise ValueError("answers payload cannot be empty")

        question_ids = list(answers.keys())
        id_filters = []

        question_id_keys = [qid for qid in question_ids if not ObjectId.is_valid(qid)]
        object_id_keys = [ObjectId(qid) for qid in question_ids if ObjectId.is_valid(qid)]

        if question_id_keys:
            id_filters.append({"question_id": {"$in": question_id_keys}})
        if object_id_keys:
            id_filters.append({"_id": {"$in": object_id_keys}})

        if not id_filters:
            raise ValueError("No valid question identifiers supplied")

        query = id_filters[0] if len(id_filters) == 1 else {"$or": id_filters}

        cursor = self._questions.find(
            query,
            {
                "question_id": 1,
                "question": 1,
                "options": 1,
                "correct_answer": 1,
                "subject": 1,
                "topic": 1,
                "difficulty": 1,
            },
        )

        question_map: Dict[str, Dict[str, Any]] = {}
        for doc in cursor:
            stored_qid = doc.get("question_id")
            if stored_qid:
                question_map[stored_qid] = doc
            fallback_qid = str(doc.get("_id")) if doc.get("_id") else None
            if fallback_qid:
                question_map[fallback_qid] = doc

        missing_ids = [qid for qid in question_ids if qid not in question_map]
        if missing_ids:
            raise ValueError(f"Unknown question_ids supplied: {missing_ids[:5]}")

        section_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "correct": 0, "review": []}
        )

        total_correct = 0
        total_questions = 0

        for qid, response in answers.items():
            doc = question_map[qid]
            section = self._normalize_section(doc.get("subject"))
            label = SECTION_CONFIG[section]["label"]
            correct_option = str(doc.get("correct_answer")).strip().upper()
            chosen = str(response).strip().upper()

            is_correct = chosen == correct_option

            section_stats[section]["total"] += 1
            total_questions += 1

            if is_correct:
                section_stats[section]["correct"] += 1
                total_correct += 1
            else:
                section_stats[section]["review"].append(
                    {
                        "question_id": qid,
                        "section": section,
                        "section_label": label,
                        "question": doc.get("question"),
                        "topic": doc.get("topic"),
                        "difficulty": doc.get("difficulty"),
                        "selected_answer": chosen,
                        "correct_answer": correct_option,
                    }
                )

        section_report: Dict[str, Dict[str, Any]] = {}
        percentage_scores: Dict[str, float] = {}

        for section in SECTION_ORDER:
            stats = section_stats.get(section, {"total": 0, "correct": 0, "review": []})
            total = stats["total"]
            correct = stats["correct"]
            accuracy = round((correct / total) * 100, 2) if total else 0.0
            percentage_scores[SECTION_CONFIG[section]["label"]] = accuracy
            section_report[section] = {
                "label": SECTION_CONFIG[section]["label"],
                "total": total,
                "correct": correct,
                "accuracy": accuracy,
                "incorrect_questions": stats["review"],
            }

        overall_accuracy = round((total_correct / total_questions) * 100, 2) if total_questions else 0.0

        user_doc, persisted = self._persist_score(user_id, percentage_scores)
        history = self._load_history(user_doc)
        feedback = self._build_feedback(history, percentage_scores)
        study_plan = self.generate(percentage_scores, user_id=user_id)

        return {
            "user": self._public_user_payload(user_doc, fallback_id=user_id),
            "test_summary": {
                "total_questions": total_questions,
                "total_correct": total_correct,
                "overall_accuracy": overall_accuracy,
            },
            "section_report": section_report,
            "feedback": feedback,
            "study_plan": study_plan,
            "history": history,
            "persistence": persisted,
        }

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _normalize_section(self, subject: Optional[str]) -> str:
        subject = (subject or "").strip()
        for key, meta in SECTION_CONFIG.items():
            if subject in meta["aliases"]:
                return key
        # fallback to polity when unknown to avoid KeyErrors, but keep trace
        return "polity"

    def _public_user_payload(self, user: Optional[Dict[str, Any]], fallback_id: Optional[str]) -> Dict[str, Any]:
        if not user:
            return {"id": fallback_id}
        return {
            "id": str(user.get("_id")),
            "name": user.get("name"),
            "email": user.get("email"),
            "phoneNumber": user.get("phoneNumber"),
        }

    def _persist_score(self, user_id: Optional[str], scores: Dict[str, float]) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        if not user_id:
            return None, {"saved": False, "message": "user_id not supplied — result not persisted"}

        user_doc = self._find_user(user_id)
        if not user_doc:
            return None, {"saved": False, "message": f"user '{user_id}' not found in database"}

        sections_payload: Dict[str, float] = {}
        for key in SECTION_ORDER:
            label = SECTION_CONFIG[key]["label"]
            value = round(float(scores.get(label, 0.0)), 2)
            sections_payload[key] = value

        entry = {
            "date": datetime.utcnow(),
            "sections": sections_payload,
        }

        try:
            self._users.update_one({"_id": user_doc["_id"]}, {"$push": {"testScores": entry}})
            refreshed = self._users.find_one({"_id": user_doc["_id"]})
            return refreshed, {"saved": True, "message": "Result stored successfully"}
        except PyMongoError as exc:
            return user_doc, {"saved": False, "message": f"Failed to persist result: {exc}"}

    def _find_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        identifier = identifier.strip()
        if ObjectId.is_valid(identifier):
            user = self._users.find_one({"_id": ObjectId(identifier)})
            if user:
                return user
        if "@" in identifier:
            user = self._users.find_one({"email": identifier.lower()})
            if user:
                return user
        # fallback on phone number match
        return self._users.find_one({"phoneNumber": identifier})

    def _load_history(self, user_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not user_doc:
            return {"available": False, "entries": []}

        entries = user_doc.get("testScores", []) or []
        entries.sort(key=lambda item: item.get("date", datetime.min))

        history_payload = []
        for item in entries[-5:]:
            dt = item.get("date")
            iso = dt.isoformat() if isinstance(dt, datetime) else dt
            history_payload.append({"date": iso, "sections": item.get("sections", {})})

        return {"available": bool(history_payload), "entries": history_payload}

    def _build_feedback(self, history: Dict[str, Any], current_scores: Dict[str, float]) -> Dict[str, Any]:
        entries = history.get("entries", [])
        if len(entries) < 2:
            message = "No prior attempts available. Focus on weaker sections highlighted in the report and retake after a week."
            return {
                "summary": message,
                "improved_sections": [],
                "regressed_sections": [],
                "stable_sections": [],
            }

        previous = entries[-2]["sections"]
        improved: List[Dict[str, Any]] = []
        regressed: List[Dict[str, Any]] = []
        stable: List[Dict[str, Any]] = []

        for section in SECTION_ORDER:
            label = SECTION_CONFIG[section]["label"]
            prev_score = float(previous.get(section, 0.0))
            curr_score = float(current_scores.get(label, 0.0))
            delta = round(curr_score - prev_score, 2)

            record = {"section": label, "previous": prev_score, "current": curr_score, "delta": delta}

            if delta > 2:
                improved.append(record)
            elif delta < -2:
                regressed.append(record)
            else:
                stable.append(record)

        parts = []
        if improved:
            parts.append("Improved: " + ", ".join(f"{item['section']} (+{item['delta']}%)" for item in improved))
        if regressed:
            parts.append("Needs attention: " + ", ".join(f"{item['section']} ({item['delta']}%)" for item in regressed))
        if stable:
            parts.append("Stable: " + ", ".join(f"{item['section']}" for item in stable))

        summary = "; ".join(parts) if parts else "Performance comparable to previous attempt."

        return {
            "summary": summary,
            "improved_sections": improved,
            "regressed_sections": regressed,
            "stable_sections": stable,
        }

    # ------------------------------------------------------------------
    # Planner generation (LLM + deterministic fallback)
    # ------------------------------------------------------------------
    def generate(self, performance: Dict[str, float], user_id: Optional[str] = None) -> Dict[str, Any]:
        display_perf = {self._to_display_key(k): v for k, v in performance.items()}
        prompt = self._build_prompt(display_perf)

        if self.api_key:
            try:
                resp = self._call_llm(prompt)
                if resp:
                    return resp
            except Exception:
                pass

        return self._deterministic_generate(display_perf)

    def _to_display_key(self, key: str) -> str:
        key = key.strip()
        # Already a display label
        for meta in SECTION_CONFIG.values():
            if key == meta["label"]:
                return key
        normalized = self._normalize_section(key)
        return SECTION_CONFIG[normalized]["label"]

    def _build_prompt(self, performance: Dict[str, float]) -> str:
        lines = ["You are a UPSC mentor. Generate a planner based on the performance:"]
        for subj, score in performance.items():
            lines.append(f"{subj}: {score}")
        lines.append("Identify weak vs strong sections, give reasons, 7-day micro plan, 30-day roadmap, resources, daily cadence, and PYQ approach.")
        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a UPSC mentor."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 900,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
        data = response.json()
        raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            return json.loads(raw)
        except Exception:
            return {"text": raw}

    def _deterministic_generate(self, perf: Dict[str, float]) -> Dict[str, Any]:
        subjects = list(perf.keys())
        if not subjects:
            return {"message": "No performance data provided."}

        classification = {s: classify_score(perf[s]) for s in subjects}

        weak = [s for s in subjects if classification[s] in ("Critical Weak", "Weak")]
        strong = [s for s in subjects if classification[s] in ("Strong", "Excellent")]

        reasons = {
            s: ("Conceptual gaps and low PYQ coverage." if perf[s] < 60 else "Needs more timed practice to boost accuracy.")
            for s in subjects
        }

        focus = weak[:2] if weak else subjects[:2]
        seven_day = [
            {"day": "Day 1", "plan": f"Brush up NCERT notes for {focus[0]} and jot key mind-maps."},
            {"day": "Day 2", "plan": f"Topic drills + PYQs for {focus[0]}."},
            {"day": "Day 3", "plan": f"Concept revisions for {focus[1] if len(focus) > 1 else subjects[0]} plus 30 MCQs."},
            {"day": "Day 4", "plan": "Current Affairs consolidation — monthly magazine + daily quiz."},
            {"day": "Day 5", "plan": "Geography atlas work + map-based MCQs."},
            {"day": "Day 6", "plan": "Full-length mixed mock (100 Qs) under exam conditions."},
            {"day": "Day 7", "plan": "Error log review + revision flashcards."},
        ]

        sorted_by_need = sorted(subjects, key=lambda s: perf[s])
        week_plans = {
            "Week 1": f"{sorted_by_need[0]} deep dive; integrate PYQs",  # weakest
            "Week 2": f"{sorted_by_need[1] if len(sorted_by_need) > 1 else sorted_by_need[0]} + Current Affairs consolidation",
            "Week 3": "Economy & Environment alternating days + answer writing",
            "Week 4": "Comprehensive revision + mixed mocks (2) + error log fixes",
        }

        topic_resources = {
            s: [
                f"NCERT summary for {s}",
                DEFAULT_BOOKLIST.get(s, ["Standard reference book"])[0],
                "Vision/PT365 notes for rapid revision",
            ]
            for s in subjects
        }

        daily_plan = {
            "mcq_per_day": 60,
            "revision_minutes": 90,
            "structure": "Morning: new concepts | Afternoon: MCQs | Evening: revision + PYQ notes",
        }

        pyq_strategy = "Target the last 7 years topic-wise; maintain an error log and reattempt incorrect PYQs fortnightly."

        return {
            "classification": classification,
            "weak_subjects": weak,
            "strong_subjects": strong,
            "reasons": reasons,
            "7_day_plan": seven_day,
            "30_day_plan": week_plans,
            "topic_resources": topic_resources,
            "booklist": {s: DEFAULT_BOOKLIST.get(s, []) for s in subjects},
            "daily_plan": daily_plan,
            "pyq_strategy": pyq_strategy,
        }


if __name__ == "__main__":
    agent = PlannerAgent()
    test = agent.prepare_test(questions_per_section=1)
    print(json.dumps(test, indent=2))

    demo_answers = {}
    for section in test["sections"].values():
        for q in section["questions"]:
            demo_answers[q["question_id"]] = "A"

    try:
        result = agent.evaluate_test(user_id=None, answers=demo_answers)
        print(json.dumps(result, indent=2, default=str))
    except ValueError as exc:
        print(f"Evaluation error: {exc}")
