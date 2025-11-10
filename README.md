# CivicBriefs.ai

An AI-powered news collection and embedding system designed to gather, process, and embed news articles related to Indian civil services, UPSC exams, and current affairs.

## Overview

CivicBriefs.ai is a Python-based application that:
- Fetches news articles from the News API based on custom queries
- Extracts and chunks article content intelligently
- Generates vector embeddings using sentence transformers
- Stores and organizes data in multiple formats for easy consumption

## Features

✨ **Key Capabilities:**
- **Multi-source News Collection** - Fetches articles from NewsAPI.org and custom URLs
- **Intelligent Text Chunking** - Splits articles into semantic chunks with configurable overlap
- **Vector Embeddings** - Generates embeddings using Sentence Transformers (all-mpnet-base-v2)
- **Multiple Output Formats** - Saves data as JSON summaries, full embeddings, text content, and human-readable reports
- **Web Scraping** - Extracts text from HTML content using BeautifulSoup
- **Configurable Parameters** - Easy to adjust chunk size, overlap, fetch limits, and queries

## Project Structure

```
CivicBriefs.ai/
├── app/
│   ├── main.py                 # Entry point for the application
│   ├── requirements.txt         # Python dependencies
│   ├── agents/
│   │   └── news_collection.py  # Core news fetching and embedding logic
│   ├── api/
│   │   └── routes/             # API endpoints (expandable)
│   └── services/               # Service layer (expandable)
└── README.md                    # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- News API key (from [newsapi.org](https://newsapi.org))

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aryanpratik11/CivicBriefs.ai.git
   cd CivicBriefs.ai
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r app/requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```
   NEWS_API_KEY1=your_news_api_key_here
   NEWS_API_KEY2=your_backup_news_api_key_here
   SENTENCE_TRANSFORMER_MODEL=all-mpnet-base-v2
   MAX_CHARS_PER_CHUNK=1500
   CHUNK_OVERLAP=200
   ```

## Usage

### Running the News Collection

```bash
cd app
python main.py
```

This will:
1. Fetch news articles based on the configured query
2. Process and generate embeddings for each chunk
3. Save results in multiple formats
4. Display a summary report

### Configuration

Edit the `CONFIG` dictionary in `app/main.py`:

```python
CONFIG = {
    "from_api": True,           # Fetch from News API
    "query": "india OR UPSC OR civil services OR current affairs",  # Search query
    "fetch_limit": 20,          # Number of articles to fetch
    "extra_urls": []            # Additional URLs to scrape
}
```

## Output Files

The application generates the following output files:

| File | Description |
|------|-------------|
| `embeddings_summary.json` | Metadata for all chunks (lightweight) |
| `embeddings_full.json` | Complete data with vector embeddings |
| `articles_text.json` | Raw text content organized by article |
| `collection_report.txt` | Human-readable summary report |

## Dependencies

Key libraries used:

- **requests** - HTTP client for API calls
- **beautifulsoup4** - HTML parsing and web scraping
- **sentence-transformers** - Semantic text embedding
- **nltk** - Natural language processing
- **chromadb** - Vector database
- **scikit-learn** - Machine learning utilities
- **torch** - Deep learning framework
- **transformers** - Pre-trained transformer models
- **dotenv** - Environment variable management

See `app/requirements.txt` for the complete list.

## Architecture

```
Input (News API / Custom URLs)
    ↓
News Fetcher (fetch articles)
    ↓
HTML Parser (extract text with BeautifulSoup)
    ↓
Text Chunker (intelligent segmentation)
    ↓
Embedding Generator (Sentence Transformers)
    ↓
Output Formatter (JSON/TXT)
    ↓
Output Files (Summary, Full, Text, Report)
```

## Configuration Options

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NEWS_API_KEY1` | None | Primary News API key |
| `NEWS_API_KEY2` | None | Backup News API key |
| `SENTENCE_TRANSFORMER_MODEL` | all-mpnet-base-v2 | Embedding model name |
| `MAX_CHARS_PER_CHUNK` | 1500 | Maximum characters per text chunk |
| `CHUNK_OVERLAP` | 200 | Characters to overlap between chunks |

## API & Services

The project includes placeholders for:
- **API Routes** - `/api/routes/` for REST endpoints
- **Services** - `/app/services/` for business logic

These are ready to be expanded for API functionality.

## Logging

The application provides detailed logging output to track:
- News API fetch operations
- Text processing and chunking
- Embedding generation
- File save operations
- Error conditions

## Error Handling

The application includes comprehensive error handling for:
- Missing API keys
- Network failures
- Invalid HTML content
- File write errors
- Embedding generation failures

## Future Enhancements

Potential improvements:
- REST API endpoints for dynamic queries
- Vector database integration (ChromaDB)
- Caching for repeated queries
- Support for multiple languages
- Real-time news streaming
- Advanced filtering and categorization
- Dashboard for visualizations

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Author

**Aryan Pratik**
- GitHub: [@aryanpratik11](https://github.com/aryanpratik11)

## Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.

---

**Last Updated:** November 11 2025
