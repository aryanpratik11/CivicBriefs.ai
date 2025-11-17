from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.routes.auth import _current_user
from app.services.news_summary import news_summary_service

router = APIRouter(prefix="/news", tags=["news"])

WindowSelector = Literal["daily", "weekly", "monthly"]


@router.get("/summaries")
def fetch_news_summaries(
    window: WindowSelector = Query(
        default="daily",
        description="Time window for summaries",
    ),
    context=Depends(_current_user),
):
    # Ensure session is valid before returning data
    _user, _token = context
    try:
        return news_summary_service.get_summary(window)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/capsules")
def fetch_news_capsules(
    window: WindowSelector = Query(
        default="daily",
        description="Time window for capsules",
    ),
    context=Depends(_current_user),
):
    _user, _token = context
    try:
        return news_summary_service.get_capsules(window)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
