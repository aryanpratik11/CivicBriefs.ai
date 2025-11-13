# app/main.py
import json
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.news_collection import collect_news_embeddings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to collect news embeddings and save results
    """
    print("\n" + "=" * 70)
    print("NEWS COLLECTION & EMBEDDING SYSTEM")
    print("=" * 70 + "\n")
    
    logger.info("Starting news collection process...")
    
    # Configuration
    CONFIG = {
        "from_api": True,
        "query": "india OR UPSC OR civil services OR current affairs",
        "fetch_limit": 20,
        "extra_urls": []  # Add full URLs here, not just domains
    }
    
    # Collect embeddings
    try:
        embeddings = collect_news_embeddings(
            from_api=CONFIG["from_api"],
            query=CONFIG["query"],
            fetch_limit=CONFIG["fetch_limit"],
            extra_urls=CONFIG["extra_urls"]
        )
        
        print(f"\n{'=' * 70}")
        print(f"✓ COLLECTION COMPLETE")
        print(f"{'=' * 70}")
        print(f"Total embedded chunks: {len(embeddings)}")
        
        if len(embeddings) == 0:
            logger.warning("No embeddings were created.")
            print("\n⚠ No embeddings created. Check logs for details.")
            return
        
        # Display statistics
        print(f"\n{'=' * 70}")
        print("STATISTICS")
        print("=" * 70)
        
        # Group by source
        sources = {}
        for item in embeddings:
            source = item["metadata"].get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        print("\nChunks by source:")
        for source, count in sources.items():
            print(f"  {source}: {count} chunks")
        
        # Show samples
        print(f"\n{'=' * 70}")
        print("SAMPLE CHUNKS (First 3)")
        print("=" * 70)
        
        for i, item in enumerate(embeddings[:3], 1):
            print(f"\n--- CHUNK {i} ---")
            print(f"ID: {item['id']}")
            print(f"Title: {item['metadata'].get('title', 'N/A')[:80]}")
            print(f"Source: {item['metadata'].get('source', 'N/A')}")
            print(f"Chunk Index: {item['metadata'].get('chunk_index', 0)}")
            print(f"Embedding Dimension: {len(item['embedding'])}")
            print(f"\nText Preview:")
            print(f"  {item['text'][:250]}...")
        
        # Save results
        print(f"\n{'=' * 70}")
        print("SAVING RESULTS")
        print("=" * 70)
        
        # 1. Summary (lightweight)
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_chunks": len(embeddings),
            "query": CONFIG["query"],
            "sources": sources,
            "items": [
                {
                    "id": item["id"],
                    "title": item["metadata"]["title"],
                    "source": item["metadata"]["source"],
                    "url": item["metadata"]["url"],
                    "chunk_index": item["metadata"]["chunk_index"],
                    "text_length": len(item["text"])
                }
                for item in embeddings
            ]
        }
        
        with open("embeddings_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print("✓ Saved embeddings_summary.json")
        
        # 2. Full data with embeddings
        full_data = {
            "generated_at": datetime.now().isoformat(),
            "total_chunks": len(embeddings),
            "query": CONFIG["query"],
            "embeddings": embeddings
        }
        
        with open("embeddings_full.json", "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=2, ensure_ascii=False)
        print("✓ Saved embeddings_full.json")
        
        # 3. Text content only
        articles_dict = {}
        for item in embeddings:
            url = item["metadata"]["url"]
            if url not in articles_dict:
                articles_dict[url] = {
                    "title": item["metadata"]["title"],
                    "source": item["metadata"]["source"],
                    "url": url,
                    "chunks": []
                }
            articles_dict[url]["chunks"].append({
                "chunk_index": item["metadata"]["chunk_index"],
                "text": item["text"]
            })
        
        text_content = {
            "generated_at": datetime.now().isoformat(),
            "total_articles": len(articles_dict),
            "articles": list(articles_dict.values())
        }
        
        with open("articles_text.json", "w", encoding="utf-8") as f:
            json.dump(text_content, f, indent=2, ensure_ascii=False)
        print("✓ Saved articles_text.json")
        
        # 4. Human-readable report
        with open("collection_report.txt", "w", encoding="utf-8") as f:
            f.write("NEWS COLLECTION REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Query: {CONFIG['query']}\n")
            f.write(f"Total Chunks: {len(embeddings)}\n")
            f.write(f"Total Articles: {len(articles_dict)}\n\n")
            
            f.write("SOURCES:\n")
            for source, count in sources.items():
                f.write(f"  - {source}: {count} chunks\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("ARTICLES:\n")
            f.write("=" * 70 + "\n\n")
            
            for idx, (url, article) in enumerate(articles_dict.items(), 1):
                f.write(f"{idx}. {article['title']}\n")
                f.write(f"   Source: {article['source']}\n")
                f.write(f"   URL: {url}\n")
                f.write(f"   Chunks: {len(article['chunks'])}\n\n")
        
        print("✓ Saved collection_report.txt")
        
        print(f"\n{'=' * 70}")
        print("✓ ALL FILES SAVED SUCCESSFULLY")
        print("=" * 70)
        print("\nOutput files:")
        print("  1. embeddings_summary.json  - Metadata only")
        print("  2. embeddings_full.json     - Complete with vectors")
        print("  3. articles_text.json       - Text content")
        print("  4. collection_report.txt    - Summary report")
        print(f"\n{'=' * 70}\n")
        
        logger.info("News collection completed successfully!")
        
    except Exception as e:
        logger.exception("Error during news collection: %s", e)
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()