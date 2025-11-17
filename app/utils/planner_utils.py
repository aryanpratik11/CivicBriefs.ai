# app/utils/planner_utils.py
from typing import Dict, Any
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MEMORY_PATH = os.environ.get("PLANNER_MEMORY_PATH", "planner_memory.json")


def normalize_percentages(section_percentages: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize input percentages (0..100 or 0..1) and drop keys like 'Total'.
    Returns mapping subject -> pct (0..1)
    """
    cleaned = {}
    for k, v in section_percentages.items():
        if not isinstance(k, str):
            continue
        key_lower = k.strip().lower()
        if key_lower in ("total", "overall", "grand total"):
            continue
        try:
            pct = float(v)
        except Exception:
            continue
        pct = max(0.0, min(100.0, pct))
        cleaned[k.strip()] = pct / 100.0
    return cleaned


def compute_subject_weights_from_percentages(section_percentages: Dict[str, float], amplify_exponent: float = 1.6) -> Dict[str, float]:
    """
    Compute normalized weights (sum to 1). Lower percentage => higher weakness => larger weight.
    """
    normalized = normalize_percentages(section_percentages)
    raw = {}
    for subj, pct in normalized.items():
        weakness = 1.0 - pct
        raw[subj] = weakness ** amplify_exponent
    total = sum(raw.values())
    if total <= 0 or not raw:
        n = max(1, len(normalized))
        return {k: 1.0 / n for k in normalized.keys()}
    weights = {k: v / total for k, v in raw.items()}
    logger.debug("Computed subject weights: %s", weights)
    return weights


def allocate_weekly_hours(weights: Dict[str, float], base_hours: Dict[str, float], extra_hours: float = 6.0) -> Dict[str, float]:
    """
    Allocate weekly hours: base + proportional extra hours.
    """
    allocations = {}
    for subj, base in base_hours.items():
        w = weights.get(subj, 0.0)
        allocations[subj] = round(float(base) + extra_hours * w, 2)

    # adjust scaling so totals equal base_sum + extra_hours (fix rounding)
    desired_total = sum(base_hours.values()) + extra_hours
    current_total = sum(allocations.values()) if allocations else 0.0
    if current_total > 0:
        scale = desired_total / current_total
        for k in allocations:
            allocations[k] = round(allocations[k] * scale, 2)
    logger.debug("Allocated weekly hours: %s", allocations)
    return allocations


# Minimal deterministic fallback: simple 3-slot per day skeleton (used only if LLM fails)
FALLBACK_DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FALLBACK_TEMPLATE = {
    "Monday": ["Polity: chapter + notes", "Polity: PYQs/MCQs", "Current Affairs: editorials/PIB"],
    "Tuesday": ["History: chapter", "History: revision/map", "Current Affairs: notes"],
    "Wednesday": ["Geography: chapter", "Environment: topic", "Map/diagrams revision"],
    "Thursday": ["Economy: concept reading", "Economy: MCQs", "Current Affairs: economy notes"],
    "Friday": ["Optional: core topic", "Optional: notes", "Optional: PYQ practice"],
    "Saturday": ["CSAT: quant practice", "CSAT: comprehension", "Weekly revision"],
    "Sunday": ["Full Prelims practice (morning)", "Mains answer writing (afternoon)", "Deep revision (evening)"],
}


def fallback_schedule_text() -> str:
    """
    Return a compact 3-slot-per-day fallback schedule (used only when LLM fails).
    """
    lines = []
    for day in FALLBACK_DAY_ORDER:
        lines.append(f"📅 {day}")
        slots = [("Morning 09:00 - 12:00", FALLBACK_TEMPLATE[day][0]),
                 ("Afternoon 14:00 - 17:00", FALLBACK_TEMPLATE[day][1]),
                 ("Evening 18:30 - 21:30", FALLBACK_TEMPLATE[day][2])]
        for header, act in slots:
            lines.append(header)
            lines.append(f"- {act}")
        lines.append("")  # blank line
    return "\n".join(lines)


# --- memory helpers --- #
def load_memory(path: str = MEMORY_PATH) -> dict:
    if not os.path.exists(path):
        return {"exchanges": [], "summaries": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load memory; returning fresh structure.")
        return {"exchanges": [], "summaries": []}


def save_memory(mem: dict, path: str = MEMORY_PATH) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
        logger.debug("Memory saved to %s", path)
    except Exception:
        logger.exception("Failed to save memory to %s", path)


def make_summary_text(allocations: Dict[str, float], top_n: int = 3) -> str:
    ranked = sorted(allocations.items(), key=lambda kv: -kv[1])[:top_n]
    parts = [f"{k}:{v:.1f}h" for k, v in ranked]
    ts = datetime.utcnow().isoformat() + "Z"
    return f"{ts} Focus top: {', '.join(parts)}."