import re
from typing import List, Dict, Any


def format_snippets_for_prompt(
    hits: List[Dict[str, Any]],
    max_chars_each: int = 700
) -> str:
    """
    Format ChromaDB search results into readable blocks for LLM prompting.
    """

    if not hits:
        return "None"

    parts = []
    for i, h in enumerate(hits, 1):
        doc = h.get("document", "")
        meta = h.get("metadata", {})

        preview = re.sub(r"\s+", " ", doc)[:max_chars_each]
        meta_str = ", ".join(
            f"{k}:{v}"
            for k, v in meta.items()
            if k in ("pdf_name", "pdf_stem", "chunk_index", "title", "url", "source")
        )

        parts.append(f"{i}) {preview}\n-- meta: {meta_str}")

    return "\n\n".join(parts)
