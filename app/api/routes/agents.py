# app/api/routes/agents.py
from fastapi import APIRouter
from app.agents.news_agent import NewsAgent


router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/news")
def run_news_agent():
    """
    Trigger the NewsAgent to fetch and embed UPSC-relevant news.
    """
    agent = NewsAgent(
        query="UPSC OR civil services OR current affairs OR Indian polity",
        fetch_limit=10
    )
    agent.run()
    return {"status": "success", "message": "NewsAgent executed successfully ✅"}
