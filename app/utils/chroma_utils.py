import logging
import chromadb
from pathlib import Path

logger = logging.getLogger(__name__)


def load_chroma_collections(chroma_path: Path):
    try:
        client = chromadb.PersistentClient(path=str(chroma_path))
        return (
            client.get_collection("upsc_syllabus"),
            client.get_collection("upsc_pyq")
        )
    except Exception as e:
        logger.error(f"ChromaDB load failed: {e}")
        return None, None
