# app/agents/news_agent.py

import os
import json
import logging
from datetime import datetime
from app.agents.news_collection import collect_news_embeddings


# Setup logger
logger = logging.getLogger(__name__)

class NewsAgent:
    """
    Agent responsible for collecting UPSC-relevant news,
    embedding it, and saving the processed results.
    """

    def __init__(self, query: str, fetch_limit: int = 20, from_api: bool = True, extra_urls=None):
        self.query = query
        self.fetch_limit = fetch_limit
        self.from_api = from_api
        self.extra_urls = extra_urls or []
        self.output_dir = "data"
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        print("\n" + "=" * 70)
        print("NEWS AGENT — FETCHING & EMBEDDING")
        print("=" * 70 + "\n")

        logger.info("Starting news collection...")
        
        try:
            # Step 1 — collect data
            embeddings = collect_news_embeddings(
                from_api=self.from_api,
                query=self.query,
                fetch_limit=self.fetch_limit,
                extra_urls=self.extra_urls
            )

            if not embeddings:
                print("⚠ No embeddings found.")
                logger.warning("No embeddings returned.")
                return
            
            logger.info(f"Collected {len(embeddings)} text chunks.")

            # Step 2 — compute statistics
            sources = {}
            for item in embeddings:
                src = item["metadata"].get("source", "unknown")
                sources[src] = sources.get(src, 0) + 1

            # Step 3 — Save summary
            summary = {
                "generated_at": datetime.now().isoformat(),
                "query": self.query,
                "total_chunks": len(embeddings),
                "sources": sources
            }
            summary_path = os.path.join(self.output_dir, "embeddings_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            # Step 4 — Save full data
            full_path = os.path.join(self.output_dir, "embeddings_full.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(embeddings, f, indent=2, ensure_ascii=False)

            print(f"✓ Saved {summary_path}")
            print(f"✓ Saved {full_path}")
            print(f"\nTotal Chunks: {len(embeddings)}")
            print(f"Sources: {sources}")

            logger.info("NewsAgent completed successfully.")

        except Exception as e:
            logger.exception("Error running NewsAgent: %s", e)
            print(f"❌ Error: {e}")
