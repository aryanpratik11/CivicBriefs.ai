"""
Build embeddings for UPSC Syllabus,PYQ Stores them separately in ChromaDB for semantic search

SUMMARY
-------
NORMAL MODE:
    python embed_upsc.py
    → Builds embeddings from PDFs

QUERY MODE:
    python embed_upsc.py --query "..." 
    → Searches your embeddings database

"""


import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from tqdm import tqdm
import fitz  # PyMuPDF
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# NLTK for sentence tokenization
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download("punkt", quiet=True)

from nltk.tokenize import sent_tokenize

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# -------------------- Configuration --------------------
class Config:
    PDF_DIR = Path("upsc_pyq_syllabus")
    PERSIST_DIR = Path("chroma_store")
    CHUNK_SIZE = 500  # approximate tokens (using 4 chars per token)
    CHUNK_OVERLAP = 100
    EMBEDDING_MODEL = "all-mpnet-base-v2"  # Better quality than MiniLM
    BATCH_SIZE = 32


# -------------------- PDF Processing --------------------
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF using PyMuPDF"""
    texts = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text and text.strip():
                texts.append(text)
        doc.close()
        logger.info(f"Extracted text from {pdf_path.name} ({len(texts)} pages)")
    except Exception as e:
        logger.error(f"Failed to read {pdf_path}: {e}")
        return ""
    
    return "\n".join(texts).strip()


def chunk_text_by_sentences(
    text: str,
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 100,
    chars_per_token: int = 4
) -> List[str]:
    """
    Chunk text by sentences with approximate token-based sizing
    """
    if not text or len(text) < 50:
        return []
    
    target_chars = chunk_size_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token
    
    try:
        sentences = sent_tokenize(text)
    except Exception as e:
        logger.warning(f"Tokenization failed, using regex: {e}")
        import re
        sentences = re.split(r'[.!?]+\s+', text)
    
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence) + 1  # +1 for space
        
        if current_length + sentence_length <= target_chars:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk).strip())
            
            # Handle overlap
            if overlap_chars > 0:
                overlap_sentences = []
                overlap_length = 0
                for sent in reversed(current_chunk):
                    overlap_sentences.insert(0, sent)
                    overlap_length += len(sent) + 1
                    if overlap_length >= overlap_chars:
                        break
                current_chunk = overlap_sentences
                current_length = sum(len(s) + 1 for s in current_chunk)
            else:
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())
    
    return chunks


# -------------------- Embedder --------------------
class PDFEmbedder:
    def __init__(self, model_name: str = Config.EMBEDDING_MODEL):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Model loaded successfully")
    
    def embed_texts(self, texts: List[str], batch_size: int = Config.BATCH_SIZE) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()


# -------------------- Main Processing --------------------
def build_embeddings(
    pdf_dir: Path = Config.PDF_DIR,
    persist_dir: Path = Config.PERSIST_DIR,
    chunk_size: int = Config.CHUNK_SIZE,
    chunk_overlap: int = Config.CHUNK_OVERLAP
):
    """
    Main function to process PDFs and create embeddings
    """
    print("\n" + "=" * 70)
    print("UPSC PDF EMBEDDING BUILDER")
    print("=" * 70 + "\n")
    
    # Validate paths
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")
    
    persist_dir = Path(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    
    # Find PDFs
    all_pdfs = sorted(list(pdf_dir.glob("*.pdf")))
    if not all_pdfs:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")
    
    # Categorize PDFs (case-insensitive prefix check on the stem)
    syllabus_pdfs = [p for p in all_pdfs if p.stem.strip().upper().startswith("UPSC_CSE")]
    pyq_pdfs = [p for p in all_pdfs if p not in syllabus_pdfs]
    
    print(f"Found {len(all_pdfs)} PDFs:")
    print(f"  - Syllabus: {len(syllabus_pdfs)} files")
    print(f"  - PYQ: {len(pyq_pdfs)} files")
    print()
    
    # Initialize embedder
    embedder = PDFEmbedder()
    
    # Initialize ChromaDB
    logger.info(f"Initializing ChromaDB at {persist_dir}")
    client = chromadb.PersistentClient(path=str(persist_dir))
    
    # Get or create collections
    try:
        syllabus_collection = client.get_or_create_collection(
            name="upsc_syllabus",
            metadata={"description": "UPSC Civil Services Exam Syllabus"}
        )
        pyq_collection = client.get_or_create_collection(
            name="upsc_pyq",
            metadata={"description": "UPSC Previous Year Questions"}
        )
    except Exception as e:
        logger.error(f"Failed to create collections: {e}")
        raise
    
    # Process each category
    def process_pdf_category(
        pdf_list: List[Path],
        collection,
        category_name: str
    ) -> Dict:
        """Process a list of PDFs and add to collection"""
        if not pdf_list:
            logger.warning(f"No PDFs found for {category_name}")
            return {"total_chunks": 0, "total_pdfs": 0}
        
        print(f"\n{'=' * 70}")
        print(f"Processing {category_name.upper()}")
        print("=" * 70)
        
        all_ids = []
        all_documents = []
        all_metadatas = []
        all_embeddings = []
        
        stats = {
            "total_pdfs": len(pdf_list),
            "total_chunks": 0,
            "pdf_details": []
        }
        
        for pdf_path in tqdm(pdf_list, desc=f"Processing {category_name}"):
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                logger.warning(f"No text extracted from {pdf_path.name}")
                continue
            
            # Chunk text
            chunks = chunk_text_by_sentences(
                text,
                chunk_size_tokens=chunk_size,
                overlap_tokens=chunk_overlap
            )
            
            if not chunks:
                logger.warning(f"No chunks created from {pdf_path.name}")
                continue
            
            logger.info(f"Created {len(chunks)} chunks from {pdf_path.name}")
            
            # Create metadata and IDs
            for i, chunk in enumerate(chunks):
                chunk_id = f"{pdf_path.stem}__chunk_{i}"
                all_ids.append(chunk_id)
                all_documents.append(chunk)
                
                metadata = {
                    "pdf_name": pdf_path.name,
                    "pdf_stem": pdf_path.stem,
                    "category": category_name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_length": len(chunk),
                    "created_at": datetime.now().isoformat()
                }
                all_metadatas.append(metadata)
            
            stats["pdf_details"].append({
                "name": pdf_path.name,
                "chunks": len(chunks),
                "text_length": len(text)
            })
            stats["total_chunks"] += len(chunks)
        
        if not all_documents:
            logger.warning(f"No documents to embed for {category_name}")
            return stats
        
        # Generate embeddings in batches
        print(f"\nGenerating embeddings for {len(all_documents)} chunks...")
        all_embeddings = embedder.embed_texts(all_documents)
        
        # Add to ChromaDB
        print(f"Adding {len(all_documents)} chunks to ChromaDB...")
        try:
            collection.add(
                ids=all_ids,
                documents=all_documents,
                metadatas=all_metadatas,
                embeddings=all_embeddings
            )
            logger.info(f"Successfully added {len(all_documents)} chunks to {category_name}")
        except Exception as e:
            logger.error(f"Failed to add to ChromaDB: {e}")
            raise
        
        # Save metadata summary
        metadata_file = persist_dir / f"{category_name}_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved metadata to {metadata_file}")
        
        return stats
    
    # Process both categories
    syllabus_stats = process_pdf_category(syllabus_pdfs, syllabus_collection, "syllabus")
    pyq_stats = process_pdf_category(pyq_pdfs, pyq_collection, "pyq")
    
    # Final summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"\nSyllabus:")
    print(f"  PDFs processed: {syllabus_stats['total_pdfs']}")
    print(f"  Total chunks: {syllabus_stats['total_chunks']}")
    print(f"\nPYQ:")
    print(f"  PDFs processed: {pyq_stats['total_pdfs']}")
    print(f"  Total chunks: {pyq_stats['total_chunks']}")
    print(f"\nChromaDB path: {persist_dir}")
    print(f"Collections: upsc_syllabus, upsc_pyq")
    print("=" * 70 + "\n")
    
    # Save overall summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "pdf_directory": str(pdf_dir),
        "persist_directory": str(persist_dir),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": Config.EMBEDDING_MODEL,
        "syllabus": syllabus_stats,
        "pyq": pyq_stats
    }
    
    summary_file = persist_dir / "embedding_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved summary to {summary_file}")


# -------------------- Query Helper --------------------
def query_embeddings(
    query: str,
    collection_name: str = "upsc_pyq",
    top_k: int = 5,
    persist_dir: Path = Config.PERSIST_DIR
):
    """
    Query the embeddings database
    
    Args:
        query: Search query string
        collection_name: Either "upsc_syllabus" or "upsc_pyq"
        top_k: Number of results to return
        persist_dir: Path to ChromaDB storage
    """
    persist_dir = Path(persist_dir)
    
    if not persist_dir.exists():
        raise FileNotFoundError(f"ChromaDB directory not found: {persist_dir}")
    
    # Load client and collection
    client = chromadb.PersistentClient(path=str(persist_dir))
    
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        raise ValueError(f"Collection '{collection_name}' not found: {e}")
    
    # Generate query embedding
    embedder = PDFEmbedder()
    query_embedding = embedder.embed_texts([query])[0]
    
    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results
    formatted_results = []
    for i in range(len(results["ids"][0])):
        formatted_results.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
            "similarity_score": 1 - results["distances"][0][i]  # Convert distance to similarity
        })
    
    return formatted_results


# -------------------- CLI --------------------
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build embeddings for UPSC Syllabus and PYQ PDFs"
    )
    parser.add_argument(
        "--pdf_dir",
        type=str,
        default="upsc_pyq_syllabus",
        help="Directory containing PDFs"
    )
    parser.add_argument(
        "--persist_dir",
        type=str,
        default="chroma_store",
        help="Directory for ChromaDB storage"
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=500,
        help="Approximate chunk size in tokens"
    )
    parser.add_argument(
        "--chunk_overlap",
        type=int,
        default=100,
        help="Approximate chunk overlap in tokens"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query the database instead of building (for testing)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="upsc_pyq",
        choices=["upsc_syllabus", "upsc_pyq"],
        help="Collection to query"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Number of results to return for query"
    )
    
    args = parser.parse_args()
    
    if args.query:
        # Query mode
        print(f"\nQuerying collection '{args.collection}' for: {args.query}")
        results = query_embeddings(
            query=args.query,
            collection_name=args.collection,
            top_k=args.top_k,
            persist_dir=Path(args.persist_dir)
        )
        
        print(f"\nTop {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{'=' * 70}")
            print(f"Result  {i} (Similarity: {result['similarity_score']:.4f})")
            print(f"{'=' * 70}")
            print(f"PDF: {result['metadata']['pdf_name']}")
            print(f"Chunk: {result['metadata']['chunk_index'] + 1}/{result['metadata']['total_chunks']}")
            print(f"\nContent:\n{result['document'][:500]}...")
            print()
    else:
        # Build mode
        build_embeddings(
            pdf_dir=Path(args.pdf_dir),
            persist_dir=Path(args.persist_dir),
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )


if __name__ == "__main__":
    main()
