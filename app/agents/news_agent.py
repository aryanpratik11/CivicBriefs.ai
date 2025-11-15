# app/agents/news_agent.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import json
import logging
from pathlib import Path

from app.agents.news.news_collection import collect_news_embeddings
from app.agents.news.generate_news_capsule import generate_news_capsule
from app.utils.pdf_utils import build_pdf_from_markdown
from app.services.news_mailer import send_news_capsule_email

from datetime import datetime, date
today = date.today().isoformat()

# Setup logger
logger = logging.getLogger(__name__)


class NewsAgent:
    """
    Agent responsible for collecting UPSC-relevant news,
    embedding it, generating markdown & PDF capsules,
    and emailing them to subscribers.
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
        print("NEWS AGENT — FULL PIPELINE START")
        print("=" * 70 + "\n")

        logger.info("Starting news collection...")

        try:
            # --------------------------------------------------
            # STEP 1: Collect News + Generate Embeddings
            # --------------------------------------------------
            embeddings = collect_news_embeddings(
                from_api=self.from_api,
                query=self.query,
                fetch_limit=self.fetch_limit,
                extra_urls=self.extra_urls
            )

            if not embeddings:
                print("⚠ No embeddings found.")
                logger.warning("No embeddings returned.")
                return {"status": "failed", "reason": "no_embeddings"}

            logger.info(f"Collected {len(embeddings)} text chunks.")
            print(f"✓ Collected {len(embeddings)} chunks.\n")

            # --------------------------------------------------
            # STEP 2: Compute Statistics
            # --------------------------------------------------
            sources = {}
            for item in embeddings:
                src = item["metadata"].get("source", "unknown")
                sources[src] = sources.get(src, 0) + 1

            # --------------------------------------------------
            # STEP 3: Save Summary JSON
            # --------------------------------------------------
            summary = {
                "generated_at": datetime.now().isoformat(),
                "query": self.query,
                "total_chunks": len(embeddings),
                "sources": sources
            }

            summary_path = os.path.join(self.output_dir, "embeddings_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            print(f"✓ Saved summary → {summary_path}")

            # --------------------------------------------------
            # STEP 4: Save Full Embeddings JSON
            # --------------------------------------------------
            full_path = os.path.join(self.output_dir, "embeddings_full.json")
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(embeddings, f, indent=2, ensure_ascii=False)

            print(f"✓ Saved full embeddings → {full_path}\n")

            # --------------------------------------------------
            # STEP 5: Generate Markdown Capsule
            # --------------------------------------------------
            print("📝 Generating Markdown News Capsule...")
            md_path = generate_news_capsule(embeddings)
            print(f"✓ Markdown capsule created → {md_path}\n")

            # --------------------------------------------------
            # STEP 6: Convert Markdown to PDF
            # --------------------------------------------------
            print("📄 Converting MD → PDF...")
            capsule_dir = Path("data/capsules")
            capsule_dir.mkdir(parents=True, exist_ok=True)
            output_pdf = capsule_dir / f"news_capsule_{today}.pdf"
            pdf_path = build_pdf_from_markdown(md_path, str(output_pdf))
            print(f"✓ PDF created → {pdf_path}\n")

            # --------------------------------------------------
            # STEP 7: Email to Subscribers
            # --------------------------------------------------
            print("📨 Sending news capsule to subscribers...")

            send_news_capsule_email(pdf_path)
            print("✓ Emails sent successfully!\n")

            print("=" * 70)
            print("NEWS AGENT — PIPELINE COMPLETED")
            print("=" * 70)

            logger.info("NewsAgent completed successfully.")

            return {
                "status": "success",
                "summary": summary_path,
                "embeddings": full_path,
                "markdown": md_path,
                "pdf": pdf_path
            }

        except Exception as e:
            logger.exception("Error running NewsAgent: %s", e)
            print(f"❌ Error: {e}")

            return {"status": "failed", "error": str(e)}
        
if __name__ == "__main__":
        # Simple test run
        agent = NewsAgent(
            query="UPSC OR civil services OR current affairs",
            fetch_limit=5,
            from_api=True,
            extra_urls=[]
        )
        
        result = agent.run()
        print("\nFinal Result:", result)
