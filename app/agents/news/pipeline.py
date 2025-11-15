#!/usr/bin/env python3
"""
generate_news_capsule.py

Main UPSC News Capsule Pipeline:
- Fetch UPSC-relevant articles
- Group chunks into articles
- Classify into UPSC categories
- Retrieve PYQ & Syllabus context from ChromaDB
- Summarize each article using the local Llama server
- Build Markdown + JSON + PDF
"""

import os
import json
import uuid
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

from sentence_transformers import SentenceTransformer
import chromadb

# -----------------------
# Local Imports (Clean)
# -----------------------
from app.agents.news.news_collection import collect_news_embeddings
from app.utils.llm_utils import local_llama_call
from app.utils.markdown_utils import format_snippets_for_prompt
from app.utils.pdf_utils import build_pdf_from_markdown
from app.services.news_mailer import send_news_capsule_email

# -----------------------
# Setup NLTK
# -----------------------
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)

# -----------------------
# Logging
# -----------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("news_capsule")

# -----------------------
# Config
# -----------------------
CHROMA_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "app/agents/chroma_store"))
SENTENCE_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-mpnet-base-v2")

LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT",
                               "http://localhost:8000/v1/chat/completions")

TOP_K_CHROMA = int(os.getenv("TOP_K_CHROMA", 3))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 512))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))

TODAY = datetime.utcnow().date().isoformat()
PDF_FILENAME = f"news_capsule_{TODAY}.pdf"
MD_FILENAME = "news_capsules.md"
JSON_FILENAME = "news_capsules.json"

# -----------------------
# UPSC Categories
# -----------------------
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

# -----------------------
# Prompt Template
# -----------------------
PROMPT_TEMPLATE = """You are creating a concise UPSC exam-focused news summary.

Article: {title}
Source: {source}

Content:
{article_text}

Most relevant PYQ questions found:
{pyq_snippets}

Most relevant Syllabus topics found:
{syllabus_snippets}

IMPORTANT: Output ONLY in this exact format:

---
### {title} — Summary

[3–5 sentence summary — exam-focused]

**Relevant PYQ**
- bullet 1
- bullet 2
- bullet 3

**Relevant Syllabus**
- bullet 1
- bullet 2
- bullet 3
---

RULES:
- Keep summary factual
- Max 3 bullet points each for PYQ/Syllabus
- If none found, write "- None found"
"""

# -----------------------
# Helpers
# -----------------------
def l2_normalize(a: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(a, axis=-1, keepdims=True)
    norm[norm == 0] = 1e-8
    return a / norm


# -----------------------
# Main pipeline
# -----------------------
def run(fetch_limit: int = 30):
    logger.info("Loading embedding model: %s", SENTENCE_MODEL)
    embedder = SentenceTransformer(SENTENCE_MODEL)

    # -----------------------
    # Connect to ChromaDB
    # -----------------------
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        syllabus_col = client.get_collection(name="upsc_syllabus")
        pyq_col = client.get_collection(name="upsc_pyq")
        logger.info("Connected to ChromaDB at %s", CHROMA_DIR)
    except Exception as e:
        logger.exception("Failed to connect to ChromaDB: %s", e)
        syllabus_col, pyq_col = None, None

    # -----------------------
    # Check local LLM availability
    # -----------------------
    llm_available = False
    try:
        resp = requests.get(
            LOCAL_LLM_ENDPOINT.replace("/v1/chat/completions", "/v1/models"),
            timeout=3
        )
        if resp.status_code == 200:
            llm_available = True
            logger.info("Local Llama reachable.")
    except:
        logger.warning("Local Llama server not reachable. Using fallback summarizer.")

    # -----------------------
    # Category embeddings
    # -----------------------
    cat_prompts = [
        f"{c} news relevant to UPSC civil services" for c in CATEGORIES
    ]
    cat_embs = embedder.encode(cat_prompts, convert_to_numpy=True)
    cat_embs = l2_normalize(np.array(cat_embs))

    # -----------------------
    # Step 1 — News Collection
    # -----------------------
    logger.info("Fetching news chunks...")
    chunks = collect_news_embeddings(
        from_api=True,
        query="UPSC OR civil services OR current affairs",
        fetch_limit=fetch_limit
    )
    logger.info("Fetched %d chunks", len(chunks))

    # -----------------------
    # Step 2 — Group chunks into articles
    # -----------------------
    articles = {}
    for item in chunks:
        url = item["metadata"].get("url") or str(uuid.uuid4())
        title = item["metadata"].get("title", url)
        source = item["metadata"].get("source", "newsapi")

        if url not in articles:
            articles[url] = {
                "title": title,
                "source": source,
                "url": url,
                "chunks": [],
                "embs": []
            }

        articles[url]["chunks"].append(item["text"])
        articles[url]["embs"].append(np.array(item["embedding"], dtype=np.float32))

    for url, art in articles.items():
        art["text"] = "\n\n".join(art["chunks"])
        art["embedding"] = l2_normalize(np.mean(np.vstack(art["embs"]), axis=0))
        art["chunk_count"] = len(art["chunks"])

    logger.info("Grouped into %d articles", len(articles))

    # -----------------------
    # Output structure
    # -----------------------
    output = {cat: [] for cat in CATEGORIES}

    # -----------------------
    # Step 3 — Process each article
    # -----------------------
    for url, art in articles.items():
        emb = art["embedding"]

        # Category classification
        sims = (cat_embs @ emb)
        category = CATEGORIES[int(np.argmax(sims))]

        # Chroma searches
        pyq_hits, syl_hits = [], []

        if pyq_col:
            try:
                res = pyq_col.query(
                    query_embeddings=[emb.tolist()],
                    n_results=TOP_K_CHROMA,
                    include=["documents", "metadatas", "distances"]
                )
                ids = res["ids"][0]
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                dists = res["distances"][0]

                for i in range(len(ids)):
                    pyq_hits.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i],
                        "distance": dists[i],
                    })
            except:
                logger.warning("Chroma PYQ query failed.")

        if syllabus_col:
            try:
                res = syllabus_col.query(
                    query_embeddings=[emb.tolist()],
                    n_results=TOP_K_CHROMA,
                    include=["documents", "metadatas", "distances"]
                )
                ids = res["ids"][0]
                docs = res["documents"][0]
                metas = res["metadatas"][0]
                dists = res["distances"][0]

                for i in range(len(ids)):
                    syl_hits.append({
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i],
                        "distance": dists[i],
                    })
            except:
                logger.warning("Chroma syllabus query failed.")

        # Prompt formatting
        pyq_snips = format_snippets_for_prompt(pyq_hits)
        syl_snips = format_snippets_for_prompt(syl_hits)

        prompt = PROMPT_TEMPLATE.format(
            title=art["title"],
            source=art["source"],
            article_text=art["text"][:4000],
            pyq_snippets=pyq_snips,
            syllabus_snippets=syl_snips,
        )

        # -----------------------
        # Step 4 — Summarize (LLM or fallback)
        # -----------------------
        summary_md = ""

        if llm_available:
            llm_out = local_llama_call(
                prompt=prompt,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE
            )
            if llm_out and len(llm_out.strip()) > 10:
                summary_md = llm_out

        # fallback extractive summary
        if not summary_md:
            sents = sent_tokenize(art["text"])
            summary_md = (
                f"### {art['title']} — Summary\n"
                f"{' '.join(sents[:2])}\n\n"
                "**Relevant PYQ**\n" +
                ("\n".join([f"- {h['document'][:200].replace('\n',' ')}"
                            for h in pyq_hits[:3]]) or "- None") +
                "\n\n**Relevant Syllabus**\n" +
                ("\n".join([f"- {h['document'][:200].replace('\n',' ')}"
                            for h in syl_hits[:3]]) or "- None")
            )

        # Store result
        output[category].append({
            "title": art["title"],
            "url": art["url"],
            "source": art["source"],
            "chunk_count": art["chunk_count"],
            "summary": summary_md,
            "pyq_hits": pyq_hits,
            "syllabus_hits": syl_hits
        })

    # -----------------------
    # Step 5 — Build Markdown + JSON
    # -----------------------
    md_lines = [f"# News Capsule — Date: {TODAY}\n"]

    for cat in CATEGORIES:
        md_lines.append(f"## {cat}\n")
        if not output[cat]:
            md_lines.append("_No articles in this category_\n")
            continue
        for it in output[cat]:
            md_lines.append(it["summary"].strip() + "\n")
            md_lines.append(f"- Source: {it['source']}")
            md_lines.append(f"- URL: {it['url']}")
            md_lines.append(f"- Chunks: {it['chunk_count']}\n")
            md_lines.append("---\n")

    md_text = "\n".join(md_lines)
    with open(MD_FILENAME, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    logger.info("Markdown & JSON saved.")

    # -----------------------
    # Step 6 — Build PDF + Email
    # -----------------------
    build_pdf_from_markdown(MD_FILENAME, PDF_FILENAME)
    send_news_capsule_email(PDF_FILENAME)

    logger.info("Pipeline completed. PDF: %s", PDF_FILENAME)


if __name__ == "__main__":
    run(fetch_limit=int(os.getenv("FETCH_LIMIT", "5")))
