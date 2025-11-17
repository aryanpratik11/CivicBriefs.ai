#!/usr/bin/env python3
"""
generate_news_capsule_pdf.py

Full pipeline:
- Fetch news using your existing news_collection.collect_news_embeddings
- Group chunks into articles, compute article embeddings
- Classify into UPSC categories (embedding-similarity)
- Query ChromaDB for top PYQ & Syllabus snippets
- Summarize article + attach notes using local Llama (via HTTP endpoint)
- Generate Markdown report and convert it to a PDF named:
    news_capsule_<YYYY-MM-DD>.pdf
"""

import os
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import nltk

# Ensure sentence tokenizer available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)
from nltk.tokenize import sent_tokenize

# embeddings & DB
from sentence_transformers import SentenceTransformer
import chromadb

# HTTP client for local Llama server
import requests

# import your news collector
from app.agents.news_collection import collect_news_embeddings
from app.services.news_store import news_store

# reportlab for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY

import re

# -----------------------
# Config
# -----------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("news_capsule")

CHROMA_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "chroma_store"))
SENTENCE_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-mpnet-base-v2")

# local Llama server endpoint (OpenAI-compatible)
LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:8000/v1/chat/completions")

TOP_K_CHROMA = int(os.getenv("TOP_K_CHROMA", 3))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 512))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))

# categories / order
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

# PDF output filename uses current date
TODAY = datetime.utcnow().date().isoformat()
PDF_FILENAME = f"news_capsule_{TODAY}.pdf"
MD_FILENAME = "news_capsules.md"
JSON_FILENAME = "news_capsules.json"

# LLM prompt template
PROMPT_TEMPLATE = """
You are an instruct LLM tuned to produce concise, exam-focused news capsules for UPSC aspirants.

Article Title: {title}
Source: {source}
URL: {url}
Date: {date}

Article (excerpt):
\"\"\"
{article_text}
\"\"\"

Attached PYQ snippets (most semantically relevant):
{pyq_snippets}

Attached Syllabus snippets:
{syllabus_snippets}

Task:
1) Provide a short summary (3-5 sentences) of the article focused on facts and implications for UPSC preparation.
2) For each attached PYQ snippet and Syllabus snippet, add one short note (1-2 lines) explaining why it is relevant to this article and how a student might use it (e.g. revision, practice question, topic mapping).
3) Keep the style crisp and exam-oriented. No speculative claims. If information is unclear, say "source unclear" briefly.

Output format (MARKDOWN):
---
### {title} — Summary
{summary_text}

**Relevant PYQ**  
- Q1: (title / snippet / source) — note

**Relevant Syllabus**  
- S1: (syllabus snippet / topic / note)

--- 

Keep it short and factual.
"""

# -----------------------
# Utilities
# -----------------------
def l2_normalize(a: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(a, axis=-1, keepdims=True)
    norm[norm == 0] = 1e-8
    return a / norm

# -----------------------
# New: call local Llama HTTP server (OpenAI-compatible chat completions)
# -----------------------
def local_llama_call(prompt: str, max_tokens: int = 512, temperature: float = 0.1, endpoint: str = LOCAL_LLM_ENDPOINT, timeout: int = 30) -> str:
    """
    Call local Llama server at endpoint (OpenAI-compatible /v1/chat/completions).
    Returns the text content (string) or empty string on failure.
    """
    payload = {
        "model": "local-llama",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # Parse several possible response shapes:
        # 1) OpenAI-style: data["choices"][0]["message"]["content"]
        # 2) Some local servers: data["choices"][0]["text"]
        # 3) A single top-level text field
        if not isinstance(data, dict):
            return str(data)

        choices = data.get("choices") or []
        if choices:
            first = choices[0]
            # case: first has "message": {"content": "..."}
            if isinstance(first, dict):
                msg = first.get("message")
                if isinstance(msg, dict) and "content" in msg:
                    return msg["content"].strip()
                # fallback: "text" field (older style)
                if "text" in first and isinstance(first["text"], str):
                    return first["text"].strip()
                # some servers return "message" as string
                if isinstance(first.get("text"), dict):
                    # improbable, but handle gracefully
                    return json.dumps(first.get("text"))
            # else fallback to string
            return str(first)
        # fallback: top-level 'text' or 'content'
        if "text" in data and isinstance(data["text"], str):
            return data["text"].strip()
        if "content" in data and isinstance(data["content"], str):
            return data["content"].strip()
        # nothing useful
        logger.warning("local_llama_call: unexpected response shape: %s", list(data.keys()))
        return ""
    except requests.exceptions.RequestException as e:
        logger.warning("local_llama_call: request failed: %s", e)
        return ""
    except Exception as ex:
        logger.exception("local_llama_call: unexpected error: %s", ex)
        return ""

# safe wrapper (keeps same name as original helper)
def call_llm_and_get_text(llm_unused, prompt: str, max_tokens: int, temperature: float) -> str:
    # llm_unused parameter left for compatibility with previous calls
    return local_llama_call(prompt=prompt, max_tokens=max_tokens, temperature=temperature)

def format_snippets_for_prompt(hits: List[Dict[str, Any]], max_chars_each: int = 700) -> str:
    if not hits:
        return "None"
    parts = []
    for i, h in enumerate(hits, 1):
        doc = h.get("document", "")
        meta = h.get("metadata", {})
        preview = re.sub(r"\s+", " ", doc)[:max_chars_each]
        mstr = ", ".join([f"{k}:{v}" for k, v in meta.items() if k in ("pdf_name","pdf_stem","chunk_index","title","url","source")])
        parts.append(f"{i}) {preview}\n-- meta: {mstr}")
    return "\n\n".join(parts)

# -----------------------
# PDF generation helpers (unchanged)
# -----------------------
def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CapsuleTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#1a1a1a',
        spaceAfter=12,
        spaceBefore=8,
        leading=20,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='Summary',
        parent=styles['BodyText'],
        fontSize=11,
        textColor='#2c2c2c',
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        leading=16
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#333333',
        spaceAfter=6,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#404040',
        leftIndent=20,
        spaceAfter=6,
        leading=14
    ))
    return styles

def build_pdf_from_markdown(input_md: str, output_pdf: str):
    # parse simplified markdown that our pipeline creates
    with open(input_md, "r", encoding="utf-8") as f:
        content = f.read()

    # We'll split capsules by the '---' separator used in prompt output
    capsules = [c.strip() for c in content.split('---') if c.strip()]

    # Convert each capsule to structured pieces via simple parsing similar to user's function
    parsed = []
    for cap in capsules:
        lines = cap.splitlines()
        data = {"title": "", "summary": "", "pyq": [], "syllabus": []}
        cur = None
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith('###'):
                t = ln.lstrip('#').strip()
                data['title'] = t
                cur = 'summary'
            elif ln.lower().startswith('**relevant pyq**'):
                cur = 'pyq'
            elif ln.lower().startswith('**relevant syllabus**'):
                cur = 'syllabus'
            elif ln.startswith('-') and cur in ('pyq','syllabus'):
                item = ln.lstrip('-').strip()
                data[cur].append(item)
            else:
                if cur == 'summary':
                    if data['summary']:
                        data['summary'] += ' ' + ln
                    else:
                        data['summary'] = ln
        if data['title']:
            parsed.append(data)

    # Build the PDF document with ReportLab
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    styles = create_styles()
    story = []

    # Header
    story.append(Paragraph("<b>UPSC News Capsules</b>", styles['Title']))
    story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%d %B %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.25*inch))

    for idx, cap in enumerate(parsed):
        story.append(Paragraph(f"<b>{cap['title']}</b>", styles['CapsuleTitle']))
        if cap['summary']:
            story.append(Paragraph(cap['summary'], styles['Summary']))
            story.append(Spacer(1, 0.12*inch))
        if cap['pyq']:
            story.append(Paragraph("<b>Relevant PYQ</b>", styles['SectionHeader']))
            for it in cap['pyq']:
                story.append(Paragraph(f"• {it}", styles['ListItem']))
            story.append(Spacer(1, 0.08*inch))
        if cap['syllabus']:
            story.append(Paragraph("<b>Relevant Syllabus</b>", styles['SectionHeader']))
            for it in cap['syllabus']:
                story.append(Paragraph(f"• {it}", styles['ListItem']))
        if idx < len(parsed) - 1:
            story.append(Spacer(1, 0.2*inch))

    doc.build(story)
    logger.info("PDF created: %s (capsules: %d)", output_pdf, len(parsed))
    print(f"✅ PDF created successfully: {output_pdf}")

# -----------------------
# Main pipeline
# -----------------------
def run(fetch_limit: int = 30):
    logger.info("Loading embedding model: %s", SENTENCE_MODEL)
    embedder = SentenceTransformer(SENTENCE_MODEL)

    # connect to chroma
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        syllabus_col = client.get_collection(name="upsc_syllabus")
        pyq_col = client.get_collection(name="upsc_pyq")
        logger.info("Connected to ChromaDB at %s", CHROMA_DIR)
    except Exception as e:
        logger.exception("ChromaDB connection error: %s", e)
        syllabus_col, pyq_col = None, None

    # Check local Llama server quickly (no exception if offline)
    llm_available = False
    try:
        test = requests.get(LOCAL_LLM_ENDPOINT.replace("/v1/chat/completions", "/v1/models"), timeout=3)
        if test.status_code == 200:
            llm_available = True
            logger.info("Local Llama server reachable at %s", LOCAL_LLM_ENDPOINT)
        else:
            logger.warning("Local Llama server returned status %s (will fallback to extractive summaries)", test.status_code)
    except Exception:
        logger.warning("Local Llama server not reachable at %s (will fallback to extractive summaries)", LOCAL_LLM_ENDPOINT)

    # category embeddings
    logger.info("Computing category embeddings for classification...")
    cat_prompts = [f"{c} news and current affairs relevant to UPSC civil services" for c in CATEGORIES]
    cat_embs = embedder.encode(cat_prompts, convert_to_numpy=True, show_progress_bar=False)
    cat_embs = l2_normalize(np.array(cat_embs))

    # 1) fetch news chunks
    logger.info("Fetching news chunks (limit=%d)...", fetch_limit)
    chunks = collect_news_embeddings(from_api=True, query="UPSC OR civil services OR current affairs", fetch_limit=fetch_limit, extra_urls=[])
    logger.info("Fetched %d chunks", len(chunks))

    # group chunks by URL (form articles)
    articles = {}
    for item in chunks:
        url = item["metadata"].get("url") or item.get("id") or str(uuid.uuid4())
        title = item["metadata"].get("title", "") or url
        source = item["metadata"].get("source", "newsapi")
        text = item["text"]
        emb = np.array(item["embedding"], dtype=np.float32)
        if url not in articles:
            articles[url] = {"title": title, "source": source, "url": url, "chunks": [], "embs": []}
        articles[url]["chunks"].append(text)
        articles[url]["embs"].append(emb)

    # finalize article-level embedding and text
    for url, v in list(articles.items()):
        v["text"] = "\n\n".join(v["chunks"])
        v["embedding"] = l2_normalize(np.mean(np.vstack(v["embs"]), axis=0))
        v["chunk_count"] = len(v["chunks"])

    logger.info("Grouped into %d articles", len(articles))

    # Prepare output structure grouped by category
    output_structure = {cat: [] for cat in CATEGORIES}

    # iterate articles
    for url, art in articles.items():
        emb = art["embedding"]
        # classify by nearest category (dot product since normalized)
        sims = (cat_embs @ emb)
        cat_idx = int(np.argmax(sims))
        category = CATEGORIES[cat_idx]

        # semantic search in chroma
        pyq_hits, syllabus_hits = [], []
        if pyq_col:
            try:
                res_pyq = pyq_col.query(query_embeddings=[emb.tolist()], n_results=TOP_K_CHROMA, include=["documents", "metadatas", "distances"])
                ids = res_pyq["ids"][0]
                docs = res_pyq["documents"][0]
                metas = res_pyq["metadatas"][0]
                dists = res_pyq["distances"][0]
                for i in range(len(ids)):
                    pyq_hits.append({"id": ids[i], "document": docs[i], "metadata": metas[i], "distance": dists[i]})
            except Exception as e:
                logger.warning("Chroma pyq query failed: %s", e)
        if syllabus_col:
            try:
                res_syl = syllabus_col.query(query_embeddings=[emb.tolist()], n_results=TOP_K_CHROMA, include=["documents", "metadatas", "distances"])
                ids = res_syl["ids"][0]
                docs = res_syl["documents"][0]
                metas = res_syl["metadatas"][0]
                dists = res_syl["distances"][0]
                for i in range(len(ids)):
                    syllabus_hits.append({"id": ids[i], "document": docs[i], "metadata": metas[i], "distance": dists[i]})
            except Exception as e:
                logger.warning("Chroma syllabus query failed: %s", e)

        # prepare prompt attachments
        pyq_snips = format_snippets_for_prompt(pyq_hits)
        syl_snips = format_snippets_for_prompt(syllabus_hits)
        article_text = art["text"][:4000]

        prompt = PROMPT_TEMPLATE.format(
            title=art["title"],
            source=art["source"],
            url=art["url"],
            date=TODAY,
            article_text=article_text,
            pyq_snippets=pyq_snips,
            syllabus_snippets=syl_snips,
            summary_text="{summary_text}"  # placeholder
        )

        summary_md = ""
        if llm_available:
            logger.info("Calling LLM server for article: %s", art["title"])
            llm_out = local_llama_call(prompt=prompt, max_tokens=LLM_MAX_TOKENS, temperature=LLM_TEMPERATURE)
            if llm_out and len(llm_out.strip()) > 10:
                summary_md = llm_out
            else:
                logger.warning("LLM server returned empty or short output; falling back to extractive summary")
        else:
            logger.warning("LLM server unavailable; using fallback extractive summary")

        # fallback extractive summary: first 2 sentences
        if not summary_md:
            sents = sent_tokenize(article_text)
            summary_fallback = " ".join(sents[:2]) if sents else article_text[:400]
            summary_md = f"### {art['title']} — Summary\n{summary_fallback}\n\n**Relevant PYQ**\n"
            if pyq_hits:
                for i, h in enumerate(pyq_hits, 1):
                    doc_preview = (h.get("document","")[:200].replace("\n"," "))
                    summary_md += f"- Q{i}: {doc_preview} — source: {h.get('metadata',{}).get('pdf_name','unknown')}\n"
            else:
                summary_md += "- None\n"
            summary_md += "\n**Relevant Syllabus**\n"
            if syllabus_hits:
                for i, h in enumerate(syllabus_hits, 1):
                    doc_preview = (h.get("document","")[:200].replace("\n"," "))
                    summary_md += f"- S{i}: {doc_preview} — source: {h.get('metadata',{}).get('pdf_name','unknown')}\n"
            else:
                summary_md += "- None\n"

        # append result
        output_structure[category].append({
            "title": art["title"],
            "url": art["url"],
            "source": art["source"],
            "chunk_count": art["chunk_count"],
            "summary": summary_md,
            "pyq_hits": pyq_hits,
            "syllabus_hits": syllabus_hits
        })

    # Build Markdown report
    logger.info("Building Markdown report: %s", MD_FILENAME)
    md_lines = []
    md_lines.append(f"# News Capsule    Date : {TODAY}\n")
    for cat in CATEGORIES:
        md_lines.append(f"## {cat}\n")
        items = output_structure.get(cat, [])
        if not items:
            md_lines.append("_No articles in this category_\n")
            continue
        for i, it in enumerate(items, 1):
            sm = it["summary"].strip()
            if not sm.startswith("###"):
                md_lines.append(f"### {i}. {it['title']}\n")
                md_lines.append(sm + "\n")
            else:
                md_lines.append(sm + "\n")
            md_lines.append(f"- Source: {it['source']}  \n- URL: {it['url']}  \n- Chunks: {it['chunk_count']}\n")
            md_lines.append("\n---\n")

    md_text = "\n".join(md_lines)
    with open(MD_FILENAME, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(JSON_FILENAME, "w", encoding="utf-8") as f:
        json.dump(output_structure, f, indent=2, default=str)

    logger.info("Saved Markdown -> %s and JSON -> %s", MD_FILENAME, JSON_FILENAME)

    persisted = news_store.save_capsule(
        capsule_payload={"structure": output_structure, "markdown": md_text},
        capsule_date=TODAY,
        capsule_type="daily",
    )
    if persisted:
        logger.info("News capsule stored in MongoDB collection 'news'.")
    else:
        logger.warning("News capsule could not be stored in MongoDB. Continuing with local artifacts.")

    # Create PDF
    logger.info("Generating PDF -> %s", PDF_FILENAME)
    try:
        build_pdf_from_markdown(MD_FILENAME, PDF_FILENAME)
    except Exception as e:
        logger.exception("PDF generation failed: %s", e)

    logger.info("Pipeline complete. Output PDF: %s", PDF_FILENAME)


if __name__ == "__main__":
    run(fetch_limit=int(os.getenv("FETCH_LIMIT", "5")))
