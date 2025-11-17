"""Utility helpers for persisting study schedules as .ics calendar events."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from ics import Calendar, Event

CALENDAR_PATH = os.getenv("CALENDAR_FILE", "study_plan.ics")


class CalendarTool:
    """Simple calendar utility for writing study sessions into an .ics file."""

    def __init__(self, calendar_path: Optional[str] = None) -> None:
        self.calendar_path = calendar_path or CALENDAR_PATH

    def _ensure_parent_dir(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.calendar_path))
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load_calendar(self) -> Calendar:
        if os.path.exists(self.calendar_path):
            with open(self.calendar_path, "r", encoding="utf-8") as handle:
                return Calendar(handle.read())
        return Calendar()

    def _save_calendar(self, calendar: Calendar) -> None:
        self._ensure_parent_dir()
        with open(self.calendar_path, "w", encoding="utf-8") as handle:
            handle.write(str(calendar))

    def add_event(self, title: str, start_time: str, end_time: str) -> str:
        """Persist a study session to the local .ics calendar file."""
        try:
            calendar = self._load_calendar()
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")

            event = Event()
            event.name = title
            event.begin = start_dt
            event.end = end_dt

            calendar.events.add(event)
            self._save_calendar(calendar)
            return f"[Calendar] Added: {title} ({start_dt} -> {end_dt})"
        except Exception as exc:  # pragma: no cover - defensive guard around optional feature
            return f"[Calendar Error] {exc}"
