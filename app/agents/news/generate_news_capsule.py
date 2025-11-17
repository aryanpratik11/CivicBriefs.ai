#!/usr/bin/env python3
"""
app/agents/news/generate_news_capsule.py
"""

import os
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import numpy as np

from sentence_transformers import SentenceTransformer
import chromadb

# local helpers
from app.utils.llm_utils import local_llama_call
from app.utils.markdown_utils import format_snippets_for_prompt

logger = logging.getLogger("generate_news_capsule")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")

CHROMA_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "app/agents/chroma_store"))
SENTENCE_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-mpnet-base-v2")
LOCAL_LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "256"))
LOCAL_LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
TOP_K_CHROMA = int(os.getenv("TOP_K_CHROMA", "3"))
TODAY = datetime.utcnow().date().isoformat()

CATEGORIES = [
    "Polity & Governance",
    "Economy",
    "International Relations",
    "Environment & Ecology",
    "Science & Technology",
    "Social Issues",
    "Security",
    "History & Culture",
    "Geography",
    "Ethics & Society"
]

# ---------------------------------------------------------------------
# FIXED TEMPLATE — Removed unused {summary_text} placeholder
# ---------------------------------------------------------------------
PROMPT_TEMPLATE = """
You are an instruct LLM tuned to produce concise, exam-focused news capsules for UPSC.

Article Title: {title}
Source: {source}
URL: {url}
Date: {date}

Article (excerpt):
\"\"\"
{article_text}
\"\"\"

Attached PYQ snippets:
{pyq_snippets}

Attached Syllabus snippets:
{syllabus_snippets}

Task:
1. Give a crisp UPSC-focused summary (3–5 sentences).
2. For each PYQ + Syllabus snippet, add a 1–2 line note explaining relevance.
3. Output clean MARKDOWN using the following structure:

---
### {title} — Summary

**Summary**
- ...

**Relevant PYQ**
- ...

**Relevant Syllabus**
- ...

---
"""


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def l2_normalize(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32)
    norm = np.linalg.norm(a, axis=-1, keepdims=True)
    norm[norm == 0] = 1e-8
    return a / norm


def _compute_category_embeddings(model_name: str = SENTENCE_MODEL) -> np.ndarray:
    logger.info("Loading SentenceTransformer: %s", model_name)
    model = SentenceTransformer(model_name)

    prompts = [f"{c} news relevant to UPSC civil services" for c in CATEGORIES]
    embs = model.encode(prompts, convert_to_numpy=True, show_progress_bar=False)
    return l2_normalize(np.array(embs, dtype=np.float32))

def enforce_markdown_structure(raw: str, title: str):
    """
    Normalize and sanitize the LLM output into the strict capsule format.
    Ensures:
    - Clean markdown
    - Exactly 3 bullets max for PYQ & Syllabus
    - Correct headers
    - Removal of garbage lines
    - Guaranteed structure
    """

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    summary, pyq, syl = [], [], []
    section = None

    for ln in lines:

        # Section detection
        if ln.lower().startswith("**relevant pyq"):
            section = "pyq"; 
            continue
        if ln.lower().startswith("**relevant syllabus"):
            section = "syl"; 
            continue
        if ln.startswith("###"):
            section = "summary"
            continue

        # Bucket content
        if section == "summary":
            summary.append(ln)
        elif section == "pyq" and ln.startswith("-"):
            pyq.append(ln.lstrip("- ").strip())
        elif section == "syl" and ln.startswith("-"):
            syl.append(ln.lstrip("- ").strip())

    # Enforce limits
    if not summary:
        summary = ["Summary not available."]
    pyq = pyq[:3] if pyq else ["None found"]
    syl = syl[:3] if syl else ["None found"]

    # Construct markdown
    final = [
        "---",
        f"### {title} — Summary",
        "",
        "**Summary**",
    ] + [f"- {s}" for s in summary] + [
        "",
        "**Relevant PYQ**",
    ] + [f"- {p}" for p in pyq] + [
        "",
        "**Relevant Syllabus**",
    ] + [f"- {s}" for s in syl] + [
        "---"
    ]

    return "\n".join(final)

# -------------------------------------------------------
# Main generator
# -------------------------------------------------------
def generate_news_capsule(
    embedded_chunks: List[Dict[str, Any]],
    md_path: str = "news_capsules.md",
    json_path: str = "news_capsules.json",
    date_str: Optional[str] = None,
    top_k_chroma: int = TOP_K_CHROMA,
    llm_max_tokens: int = LOCAL_LLM_MAX_TOKENS,
    llm_temperature: float = LOCAL_LLM_TEMPERATURE,
) -> str:

    date_str = date_str or TODAY
    logger.info("generate_news_capsule: starting (chunks=%d)", len(embedded_chunks))

    # -----------------------------------------
    # If no chunks → write empty file
    # -----------------------------------------
    if not embedded_chunks:
        logger.warning("No embedded chunks provided.")
        md_text = f"# News Capsule — Date: {date_str}\n\n_No articles collected_\n"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        return {
            "md_path": md_path,
            "json_path": json_path,
            "date": date_str,
            "structure": {},
            "markdown": md_text,
        }

    # -----------------------------------------
    # Group chunks into articles
    # -----------------------------------------
    articles = {}
    for chunk in embedded_chunks:
        meta = chunk.get("metadata", {}) or {}
        url = meta.get("url") or meta.get("source_url") or chunk.get("id") or str(uuid.uuid4())
        title = meta.get("title") or url
        source = meta.get("source") or meta.get("publisher") or "unknown"

        if url not in articles:
            articles[url] = {
                "title": title,
                "source": source,
                "url": url,
                "chunks": [],
                "embs": []
            }

        articles[url]["chunks"].append(chunk.get("text", ""))
        emb = np.array(chunk.get("embedding", []), dtype=np.float32)
        articles[url]["embs"].append(emb)

    # -----------------------------------------
    # Build article-level embeddings
    # -----------------------------------------
    for url, art in list(articles.items()):
        if not art["chunks"]:
            del articles[url]
            continue

        art["text"] = "\n\n".join([c for c in art["chunks"] if c])

        try:
            art_emb = np.vstack(art["embs"])
            art["embedding"] = l2_normalize(np.mean(art_emb, axis=0))
        except Exception:
            emb_len = art["embs"][0].shape[-1] if art["embs"] else 768
            art["embedding"] = l2_normalize(np.zeros((emb_len,), dtype=np.float32))

        art["chunk_count"] = len(art["chunks"])

    logger.info("Grouped into %d articles", len(articles))

    # -----------------------------------------
    # Category embeddings
    # -----------------------------------------
    try:
        cat_embs = _compute_category_embeddings()
    except Exception as e:
        logger.exception("Category embedding failed; using random fallback: %s", e)
        cat_embs = l2_normalize(np.random.randn(len(CATEGORIES), 768).astype(np.float32))

    # -----------------------------------------
    # Connect to Chroma
    # -----------------------------------------
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        pyq_col = client.get_collection(name="upsc_pyq")
        syllabus_col = client.get_collection(name="upsc_syllabus")
        logger.info("Connected to ChromaDB.")
    except Exception as e:
        logger.warning("Chroma unavailable: %s", e)
        pyq_col = syllabus_col = None

    # -----------------------------------------
    # Final output bucket
    # -----------------------------------------
    output_data = {c: [] for c in CATEGORIES}

    # -----------------------------------------
    # Process each article
    # -----------------------------------------
    for url, art in articles.items():
        emb = art["embedding"]

        # classify category
        emb_n = l2_normalize(emb)
        sims = (cat_embs @ emb_n)
        category = CATEGORIES[int(np.argmax(sims))]

        # query chroma
        pyq_hits, syl_hits = [], []

        if pyq_col is not None:
            try:
                res = pyq_col.query(
                    query_embeddings=[emb_n.tolist()],
                    n_results=top_k_chroma,
                    include=["documents", "metadatas", "distances"],
                )
                for i in range(len(res["ids"][0])):
                    pyq_hits.append({
                        "id": res["ids"][0][i],
                        "document": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "distance": res["distances"][0][i]
                    })
            except Exception as e:
                logger.debug("PYQ query failed: %s", e)

        if syllabus_col is not None:
            try:
                res = syllabus_col.query(
                    query_embeddings=[emb_n.tolist()],
                    n_results=top_k_chroma,
                    include=["documents", "metadatas", "distances"],
                )
                for i in range(len(res["ids"][0])):
                    syl_hits.append({
                        "id": res["ids"][0][i],
                        "document": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i],
                        "distance": res["distances"][0][i]
                    })
            except Exception as e:
                logger.debug("Syllabus query failed: %s", e)

        # prepare prompt
        pyq_snips = format_snippets_for_prompt(pyq_hits)
        syl_snips = format_snippets_for_prompt(syl_hits)

        article_excerpt = art["text"][:4000]

        prompt = PROMPT_TEMPLATE.format(
            title=art["title"],
            source=art["source"],
            url=art["url"],
            date=date_str,
            article_text=article_excerpt,
            pyq_snippets=pyq_snips,
            syllabus_snippets=syl_snips,
        )

        # LLM call
        try:
            resp = local_llama_call(prompt, max_tokens=llm_max_tokens, temperature=llm_temperature)
            if resp and len(resp.strip()) > 10:
                summary_md = enforce_markdown_structure(resp, art["title"])
            else:
                summary_md = ""

        except Exception as e:
            logger.warning("LLM failed: %s", e)
            summary_md = ""

        # fallback helpers
        def _format_hits_section(hits):
            """Render up to three hit snippets, falling back to '- None'."""
            if not hits:
                return "- None"

            snippets = []
            for hit in hits[:3]:
                snippet = hit["document"][:150].replace("\n", " ")
                snippets.append(f"- {snippet}")
            return "\n".join(snippets)

        # fallback summary
        # fallback summary
        if not summary_md:
            text = article_excerpt.replace("\n", " ").strip()
            sents = text.split(". ")
            short = ". ".join(sents[:2]).strip()
            if not short.endswith("."):
                short += "."

            pyq_section = _format_hits_section(pyq_hits)
            syl_section = _format_hits_section(syl_hits)

            raw_fallback = (
                f"### {art['title']} — Summary\n"
                f"{short}\n\n"
                "**Relevant PYQ**\n" +
                f"{pyq_section}\n" +
                "\n**Relevant Syllabus**\n" +
                f"{syl_section}\n"
            )

            summary_md = enforce_markdown_structure(raw_fallback, art["title"])

        # append
        output_data[category].append({
            "title": art["title"],
            "url": art["url"],
            "source": art["source"],
            "chunk_count": art["chunk_count"],
            "summary": summary_md,
            "pyq_hits": pyq_hits,
            "syllabus_hits": syl_hits,
        })

    # -----------------------------------------
    # Build Markdown file
    # -----------------------------------------
    md_lines = [f"# News Capsule — Date: {date_str}\n"]

    for cat in CATEGORIES:
        md_lines.append(f"## {cat}\n")
        items = output_data[cat]
        if not items:
            md_lines.append("_No articles in this category_\n")
            continue

        for it in items:
            md_lines.append(it["summary"] + "\n")
            md_lines.append(f"- Source: {it['source']}  \n- URL: {it['url']}  \n- Chunks: {it['chunk_count']}\n")
            md_lines.append("")   # just blank line

    md_text = "\n".join(md_lines)

    # -----------------------------------------
    # Write files
    # -----------------------------------------
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info("Saved Markdown -> %s", md_path)
    logger.info("Saved JSON -> %s", json_path)

    return {
        "md_path": md_path,
        "json_path": json_path,
        "date": date_str,
        "structure": output_data,
        "markdown": md_text,
    }
