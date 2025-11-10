# app/agents/news_collection.py
import os
import logging
import uuid
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# embeddings
from sentence_transformers import SentenceTransformer

# text
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize

load_dotenv()

logger = logging.getLogger("news_collection")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)

# Config (env)
NEWS_API_KEYS = [os.getenv("NEWS_API_KEY1"), os.getenv("NEWS_API_KEY2")]
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-mpnet-base-v2")
MAX_CHARS_PER_CHUNK = int(os.getenv("MAX_CHARS_PER_CHUNK", 1500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# -----------------------
# Helper: choose API key
# -----------------------
def _choose_key() -> Optional[str]:
    for k in NEWS_API_KEYS:
        if k and k.strip():
            return k.strip()
    return None

# -----------------------
# News API fetcher
# (assumes newsapi.org like endpoint)
# -----------------------
class NewsFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _choose_key()
        self.base = "https://newsapi.org/v2/everything"
        if not self.api_key:
            logger.warning("No News API key found in .env (NEWS_API_KEY1/2). API fetch will be skipped.")
        else:
            logger.info("News API key loaded successfully")

    def fetch_today(self, q: str = "UPSC OR civil services OR current affairs", language: str = "en", page_size: int = 30) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.error("Cannot fetch: No API key available")
            return []
        
        # Use yesterday to today to get more results
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        params = {
            "q": q,
            "from": yesterday.isoformat(),
            "to": today.isoformat(),
            "sortBy": "publishedAt",
            "language": language,
            "pageSize": page_size,
            "apiKey": self.api_key,
        }
        
        logger.info(f"Fetching news with query: '{q}' from {yesterday} to {today}")
        
        try:
            r = requests.get(self.base, params=params, headers={"Accept": "application/json"}, timeout=15)
            
            # Log response status
            logger.info(f"News API response status: {r.status_code}")
            
            r.raise_for_status()
            data = r.json()
            
            # Log API response details
            status = data.get("status")
            total_results = data.get("totalResults", 0)
            articles = data.get("articles", [])
            
            logger.info(f"API Status: {status}, Total Results: {total_results}, Articles returned: {len(articles)}")
            
            if status != "ok":
                logger.error(f"API returned non-ok status: {data}")
                return []
            
            if total_results == 0:
                logger.warning(f"No articles found for query: '{q}'. Try a simpler query or different date range.")
            
            return articles
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return []
        except Exception as e:
            logger.exception("News API fetch error: %s", e)
            return []

# -----------------------
# Scraping utilities
# -----------------------
def fetch_page(url: str, timeout: int = 15) -> Optional[str]:
    try:
        logger.debug(f"Fetching page: {url}")
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        logger.debug(f"Successfully fetched {url} ({len(r.text)} bytes)")
        return r.text
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.debug(f"fetch_page failed for {url}: {e}")
        return None

def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Try multiple strategies to find article content
    text = ""
    
    # Strategy 1: Look for <article> tag
    article = soup.find("article")
    if article:
        ps = article.find_all("p")
        if ps and len(ps) >= 2:
            text = "\n\n".join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 50)
            if text:
                logger.debug("Extracted text using <article> tag")
                return text

    # Strategy 2: Try common content selectors
    selectors = [
        "div.article-content", "div.article-body", "div.story-body",
        "div.article", "div#content", "div.storyContent", 
        "div.tracking-content", "div.entry-content", "div.post-content",
        "div.td-post-content", "div.content-body", "main article"
    ]
    
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            ps = node.find_all("p")
            if ps and len(ps) >= 2:
                text = "\n\n".join(p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 50)
                if text:
                    logger.debug(f"Extracted text using selector: {sel}")
                    return text

    # Strategy 3: Find all paragraphs and filter by length
    body = soup.body
    if body:
        ps = body.find_all("p")
        # Filter paragraphs that are likely content (not navigation, etc.)
        content_ps = [p.get_text(strip=True) for p in ps if len(p.get_text(strip=True)) > 50]
        if len(content_ps) >= 2:
            text = "\n\n".join(content_ps)
            logger.debug(f"Extracted text using filtered paragraphs ({len(content_ps)} paragraphs)")
            return text

    logger.warning("Could not extract meaningful article text")
    return ""

def scrape_article(url: str) -> str:
    logger.info(f"Scraping article: {url}")
    html = fetch_page(url)
    if not html:
        logger.warning(f"No HTML returned for {url}")
        return ""
    
    text = extract_article_text(html).strip()
    
    if text:
        logger.info(f"Successfully scraped {len(text)} characters from {url}")
    else:
        logger.warning(f"No text extracted from {url}")
    
    return text

# -----------------------
# Cleaning + chunking
# -----------------------
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text_by_sentences(text: str, max_chars: int = MAX_CHARS_PER_CHUNK, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    
    # Minimum text length to chunk
    if len(text) < 100:
        logger.debug(f"Text too short to chunk ({len(text)} chars)")
        return []
    
    try:
        sents = sent_tokenize(text)
    except Exception as e:
        logger.warning(f"Error tokenizing text: {e}. Using simple splitting.")
        # Fallback to simple sentence splitting
        sents = re.split(r'[.!?]+\s+', text)
    
    chunks: List[str] = []
    cur = ""
    
    for sent in sents:
        if len(cur) + len(sent) + 1 <= max_chars:
            cur = (cur + " " + sent).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = sent
    if cur:
        chunks.append(cur)

    # apply simple overlap (prefix of previous chunk)
    if overlap and overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c)
            else:
                prev = overlapped[-1]
                prefix = prev[max(0, len(prev) - overlap):]
                overlapped.append((prefix + " " + c).strip())
        chunks = overlapped
    
    logger.debug(f"Created {len(chunks)} chunks from {len(text)} chars")
    return chunks

# -----------------------
# Embedder
# -----------------------
class Embedder:
    def __init__(self, model_name: str = SENTENCE_TRANSFORMER_MODEL):
        logger.info("Loading SentenceTransformer model: %s", model_name)
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embs = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [e.tolist() for e in embs]

# -----------------------
# Main function: produce embeddings list
# -----------------------
def collect_news_embeddings(
    from_api: bool = True,
    query: str = "UPSC OR civil services OR current affairs",
    fetch_limit: int = 25,
    extra_urls: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch news (API + optional extra_urls), scrape/clean/chunk, embed.
    Returns a list of dicts:
      { "id": str, "text": str, "metadata": {...}, "embedding": [...] }
    """
    logger.info("=== Starting news collection ===")
    
    fetcher = NewsFetcher()
    embedder = Embedder()
    docs_with_embeddings: List[Dict[str, Any]] = []

    # 1) From API
    articles = []
    if from_api:
        articles = fetcher.fetch_today(q=query, page_size=fetch_limit)
        logger.info(f"Got {len(articles)} articles from News API")

    # process articles from API
    successful_scrapes = 0
    failed_scrapes = 0
    
    for idx, art in enumerate(articles):
        url = art.get("url")
        title = art.get("title", "")
        desc = art.get("description", "")
        src = (art.get("source") or {}).get("name", "newsapi")
        
        if not url:
            logger.debug(f"Article {idx+1} has no URL, skipping")
            continue
        
        logger.info(f"Processing article {idx+1}/{len(articles)}: {title[:60]}...")
        
        # Try to scrape article
        text = scrape_article(url)
        
        # Fallback to description if scraping fails
        if not text or len(text) < 100:
            logger.info(f"Using description as fallback for {url}")
            text = desc or title
        
        text = clean_text(text)
        
        if len(text) < 100:
            logger.warning(f"Text too short after cleaning ({len(text)} chars), skipping")
            failed_scrapes += 1
            continue
        
        chunks = chunk_text_by_sentences(text)
        
        if not chunks:
            logger.warning(f"No chunks created for {url}")
            failed_scrapes += 1
            continue
        
        successful_scrapes += 1
        embs = embedder.embed(chunks)
        
        for i, chunk in enumerate(chunks):
            docs_with_embeddings.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": {"source": src, "url": url, "title": title, "chunk_index": i},
                "embedding": embs[i]
            })

    logger.info(f"API articles: {successful_scrapes} successful, {failed_scrapes} failed")

    # 2) extra manual URLs (if provided)
    if extra_urls:
        logger.info(f"Processing {len(extra_urls)} extra URLs")
        for url in extra_urls:
            text = scrape_article(url)
            text = text or ""
            text = clean_text(text)
            
            if len(text) < 100:
                logger.warning(f"Skipping {url} - insufficient text")
                continue
            
            chunks = chunk_text_by_sentences(text)
            if not chunks:
                continue
            
            embs = embedder.embed(chunks)
            for i, chunk in enumerate(chunks):
                docs_with_embeddings.append({
                    "id": str(uuid.uuid4()),
                    "text": chunk,
                    "metadata": {"source": "manual", "url": url, "title": url.split("/")[-1], "chunk_index": i},
                    "embedding": embs[i]
                })

    logger.info(f"=== Collected {len(docs_with_embeddings)} embedded chunks ===")
    return docs_with_embeddings

# If run directly, quick smoke test
if __name__ == "__main__":
    # Test with a simpler query
    res = collect_news_embeddings(
        from_api=True,
        query="India",  # Simpler query for testing
        fetch_limit=1,
        extra_urls=[]
    )
    print(f"\nGot {len(res)} embeddings")
    for r in res[:2]:
        print(f"\nID: {r['id']}")
        print(f"Title: {r['metadata']['title']}")
        print(f"Source: {r['metadata']['source']}")
        print(f"Text preview: {r['text'][:200]}...")