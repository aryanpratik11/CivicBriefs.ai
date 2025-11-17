# CivicBriefs.ai

Smart daily news capsules, weekly quizzes, and personalized study schedules for UPSC and civil services preparation — powered by semantic search, embeddings, and LLM orchestration.

CivicBriefs.ai collects and semantically indexes current-affairs content (news, editorials, government releases), links items to previous years' questions (PYQs) and syllabus topics, generates a daily summarized capsule for subscribers, runs weekly quizzes to determine knowledge gaps, creates a personalized weekly study plan, and can push schedule items into Google Calendar.

An AI-powered news collection and embedding system designed to gather, process, and embed news articles related to Indian civil services, UPSC exams, and current affairs.

## Overview

CivicBriefs.ai is a Python-based application that:
- Fetches news articles from the News API based on custom queries
- Extracts and chunks article content intelligently
- Generates vector embeddings using sentence transformers
- Stores and organizes data in multiple formats for easy consumption
- Turns news into actionable study material for civil-services aspirants through an end-to-end pipeline.

The system combines:
- News collection (NewsAPI + custom scrapers),
- Intelligent chunking and embedding (SentenceTransformers + ChromaDB),
- Semantic linking to PYQs and syllabus topics,
- LLM-driven summarization and quiz-generation,
- A planner that converts quiz results into a weekly study schedule,
- Optional integration with Google Calendar for reminders and time-blocks.

**Main agents:**
- **News Agent** — automatic, daily summarized news capsule with semantic search over PYQs and syllabus links.
- **Planner Agent** — generates a personalized weekly study plan by evaluating a learner’s quiz results.
- **Orchestrator** — coordinates fetching, summarization, quiz orchestration, personalization, notifications, and calendar integration.

✨ **Key Capabilities:**
- **Multi-source News Collection** - Fetches articles from NewsAPI.org and custom URLs
- **Intelligent Text Chunking** - Splits articles into semantic chunks with configurable overlap
- **Vector Embeddings** - Generates embeddings using Sentence Transformers (all-mpnet-base-v2)
- **Multiple Output Formats** - Saves data as JSON summaries, full embeddings, text content, and human-readable reports
- **Web Scraping** - Extracts text from HTML content using BeautifulSoup
- **Configurable Parameters** - Easy to adjust chunk size, overlap, fetch limits, and queries
- **Daily summarized news capsule delivered to subscribers** (email / webhook / file).
- **Semantic linking of news to syllabus topics and PYQs** (helps prioritize what to study).
- **Weekly adaptive quiz** to find gaps and focus areas.
- **Planner agent** that builds a personalized weekly study schedule from quiz outcomes.
- **Google Calendar integration** to add study blocks automatically.
- **Pluggable LLM backend**: supports local llama-cpp HTTP server (GGUF) or OpenAI-compatible endpoints.
- **Vector search** over news + PYQs for context-aware summarization.

## Table of Contents
- [About](#about)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quickstart (Install & Run)](#quickstart-install--run)
- [Configuration / Environment Variables](#configuration--environment-variables)
- [Agents & Workflows](#agents--workflows)
- [Local LLM — WSL notes](#local-llm-optional----wsl-notes)
- [Google Calendar integration](#google-calendar-integration)
- [Data storage & vector DB](#data-storage--vector-db)
- [APIs & Scripts](#apis--scripts)
- [Usage](#usage)
- [Output Files](#output-files)
- [Dependencies](#dependencies)
- [Testing & debugging](#testing--debugging)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Security & Privacy](#security--privacy)
- [Deployment & Scheduling](#deployment--scheduling)
- [Roadmap & Improvements](#roadmap--improvements)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)
- [Contact & Support](#contact--support)

## About
CivicBriefs.ai is an end-to-end pipeline that turns news into actionable study material for civil-services aspirants.

## Key Features
See the ✨ **Key Capabilities** section in [Overview](#overview) for a full list.

## Architecture
High-level flow:
```
Input: News API / custom URLs / govt press releases / RSS / PYQ corpus
    ↓
Fetcher & Scraper (articles → clean text)
    ↓
Chunker (semantic chunking with overlap)
    ↓
Embedding generator (sentence-transformers → vectors)
    ↓
Vector DB (ChromaDB) + semantic search (match news → PYQs/syllabus)
    ↓
News Agent (LLM summarization + syllabus linking)
    ↓
Deliver daily capsules to subscribers
    ↓
Weekly: Planner Agent generates quiz → quizzes analyzed → schedule produced
    ↓
Orchestrator schedules tasks, triggers notifications, and writes to Google Calendar
```

ASCII diagram:
```
┌────────────┐ ┌─────────────┐ ┌────────────┐ ┌────────────┐
│ News / PYQ │ → │ Fetch & │ → │ Chunking & │ → │ Embeddings │
│ sources │ │ Scrape │ │ Cleanup │ │ (Chroma) │
└────────────┘ └─────────────┘ └────────────┘ └────────────┘
                                                     ↓
                                              ┌─────────────┐
                                              │ News Agent │
                                              │ Planner │
                                              │ Orchestrator│
                                              └─────────────┘
                                                     ↓
                                        Subscribers / Google Calendar / Reports
```

Detailed architecture:
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

## Project Structure
```
CivicBriefs.ai/
├── app/
│ ├── main.py # Entry point for the application
│ ├── requirements.txt # Python dependencies
│ ├── agents/
│ │ └── news_collection.py # Core news fetching and embedding logic
│ │ └── generate_news_capsule.py # Generate a single capsule (used by cron / scheduler)
│ │ └── planner_agent.py # quiz generation and schedule creation
│ ├── api/
│ │ └── routes/ # API endpoints (expandable)
│ ├── orchestrator.py # scheduler and workflow coordinator
│ └── services/ # Service layer (expandable)
├── scripts/
│ └── dev_server.py # runs the FastAPI dev server
├── data/
│ └── chroma/ # ChromaDB storage
└── README.md # This file
```

## Quickstart (Install & Run)
### Prerequisites
- Python 3.8+ (3.10 recommended)
- pip
- MongoDB 4.4+ (local or Atlas) — used for users/subscribers/sessions
- ChromaDB or compatible vector store
- News API key (newsapi.org or custom feeds)
- Google Cloud project + OAuth2 credentials for Calendar integration (optional)
- Optional: Local LLM (llama-cpp + GGUF model) — WSL recommended on Windows (instructions below)

1. **Clone the repo**
   ```bash
   git clone https://github.com/aryanpratik11/CivicBriefs.ai.git
   cd CivicBriefs.ai
   ```

2. **Create & activate virtualenv**
   Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   Linux / macOS:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r app/requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the repo root (example below).

5. **Run the pipeline (example)**
   - Run a one-off news capsule generator:
     ```bash
     # From repository root
     python -m app.agents.generate_news_capsule
     ```
   - Run the API (dev server):
     ```bash
     # Development server (defaults to port 8005)
     python scripts/dev_server.py
     # or
     python -m app
     ```

### Setup for Legacy News Collection
1. **Clone the repository:**
   ```bash
   git clone https://github.com/aryanpratik11/CivicBriefs.ai.git
   cd CivicBriefs.ai
   ```
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r app/requirements.txt
   ```
4. **Configure environment variables:**
   See [Configuration / Environment Variables](#configuration--environment-variables).

### MongoDB Atlas configuration
- Create a free or paid cluster in [MongoDB Atlas](https://www.mongodb.com/atlas) and add your current IP to the network allow list.
- Create a database user with `readWrite` access to the `civicbriefs` database (or your preferred name) and plug the credentials into the `MONGODB_URI` string above.
- Optional variables:
  - `MONGODB_SELECTION_TIMEOUT_MS` (default `5000`) controls how long the driver waits for a healthy node.
  - `MONGODB_TLS_ALLOW_INVALID_CERTS` can be set to `1` when using self-signed certificates during development.
  - `MONGODB_DB` selects the logical database; set it if you don't want to use the default `civicbriefs`.
> JSON fallbacks have been removed—if MongoDB is unreachable, the API will now fail fast so you can fix the Atlas configuration rather than silently writing to local files.

## Configuration / Environment Variables
Create a `.env` file with the following common variables (example):
```env
# News
NEWS_API_KEY1=your_news_api_key_here
NEWS_API_KEY2=backup_key_if_any
# Embedding model
SENTENCE_TRANSFORMER_MODEL=all-mpnet-base-v2
# Chunking
MAX_CHARS_PER_CHUNK=1500
CHUNK_OVERLAP=200
# MongoDB
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster-host>/?retryWrites=true&w=majority
MONGODB_DB=civicbriefs
# Chroma
CHROMA_DIR=./data/chroma
# LLM endpoint (OpenAI style)
LLM_API_URL=http://localhost:8000/v1/chat/completions
LLM_API_KEY=
# Google Calendar (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth2callback
GOOGLE_TOKEN_FILE=./.google_token.json
# App
APP_HOST=127.0.0.1
APP_PORT=8005
```

### Configuration Options
| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `NEWS_API_KEY1` | None | Primary News API key |
| `NEWS_API_KEY2` | None | Backup News API key |
| `HUGGINGFACE_TOKEN1` | None | HUGGINGFACE ACCESS TOKEN |
| `HUGGINGFACE_TOKEN2` | None | HUGGINGFACE ACCESS TOKEN |
| `SENTENCE_TRANSFORMER_MODEL` | all-mpnet-base-v2 | Embedding model name |
| `MAX_CHARS_PER_CHUNK` | 1500 | Maximum characters per text chunk |
| `CHUNK_OVERLAP` | 200 | Characters to overlap between chunks |
| `MONGODB_URI` | mongodb://localhost:27017 | Connection string for the primary MongoDB deployment |
| `MONGODB_DB` | civicbriefs | Database where `users`, `sessions`, and `subscribers` collections live |
| `APP_HOST` | 127.0.0.1 | Host interface for the FastAPI dev server |
| `APP_PORT` | 8005 | Port for the FastAPI dev server |
| `APP_RELOAD` | true | Toggle hot-reload when using the bundled launchers |

huggingface-cli login and enter the HUGGINGFACE_TOKEN ID

### Legacy Configuration
Edit the `CONFIG` dictionary in `app/main.py`:
```python
CONFIG = {
    "from_api": True, # Fetch from News API
    "query": "india OR UPSC OR civil services OR current affairs", # Search query
    "fetch_limit": 20, # Number of articles to fetch
    "extra_urls": [] # Additional URLs to scrape
}
```

## Agents & Workflows
- **News Agent**
  - Fetches news (NewsAPI or configured feeds).
  - Cleans HTML, chunks content, generates embeddings.
  - Performs semantic search over PYQ & syllabus embeddings to find relevant links.
  - Generates a human-friendly capsule summary via LLM with evidence links.
  - Stores capsule and optionally emails or posts it to subscriber endpoints.
- **Planner Agent**
  - Generates weekly quizzes (LLM-generated or templated).
  - Scores quiz responses, determines strength/weakness areas.
  - Builds a weekly study plan (time allocation, topic sequence).
  - Can produce a PDF/HTML plan and push events to Google Calendar.
- **Orchestrator**
  - Runs scheduled jobs (daily capsule generation, weekly quiz generation).
  - Coordinates downstream tasks: delivery, analytics, calendar writes.
  - Handles retries, logging, and failure notifications.

## Local LLM (optional) — WSL notes
CivicBriefs.ai supports using a local LLM exposed through a llama-cpp server (GGUF) to avoid remote API costs and latency. The old instructions used a WSL + Windows split (recommended for Windows users). Key points:
- Run llama-cpp.server inside WSL where GGUF models are stored.
- The pipeline (running in Windows venv) uses HTTP requests to the local server:
  - POST to /v1/chat/completions with model and messages (OpenAI-compatible format).
- Do NOT install llama-cpp-python in the Windows venv if you are using the HTTP server.
If you plan to use a hosted LLM (OpenAI / Azure), set LLM_API_URL and credentials instead.

This project uses:
- WSL (Ubuntu) for running a fast local Llama 3.2–1B GGUF model
- Windows venv for running the Python pipeline (news → chroma → LLM → PDF)
- llama-cpp server for exposing GGUF as an OpenAI-compatible HTTP API
This README ensures you never confuse WSL environment with Windows venv.

📌 **Overview of the Architecture**
```
┌──────────────────────┐
│ Windows Environment │
│ venv/ │
│ - runs pipeline │
│ - uses requests → │──────────────┐
└──────────────────────┘ │
                                      │ HTTP (OpenAI compatible)
                                      ▼
                            ┌──────────────────────┐
                            │ WSL Ubuntu │
                            │ venv: wsl-llama │
                            │ llama_cpp.server │
                            │ loads GGUF model │
                            └──────────────────────┘
```

⚙️ **1. Install WSL and Ubuntu**  
If not installed:  
`wsl --install`  
Then open Ubuntu from Start Menu.

🧱 **2. Create WSL venv (used ONLY for running llama-cpp local server)**  
Inside Ubuntu:  
`cd /mnt/c/Users/Admin/Documents/Codes/AI/CivicBriefs.ai`  
`python3 -m venv wsl-llama`  
`source wsl-llama/bin/activate`  
You should now see:  
`(wsl-llama) user@LAPTOP:/mnt/c/...`

📦 **3. Install server dependencies in WSL**  
These are ONLY installed inside WSL:  
`python -m pip install --upgrade pip setuptools wheel`  
`python -m pip install llama-cpp-python fastapi uvicorn starlette sse-starlette starlette-context pydantic pydantic_settings`

🧰 **4. Download the Quantized LLM in Windows**  
Use your existing script:  
`C:\...CivicBriefs.ai\app\agents\get_model.py`  
This downloads:  
`app/agents/models/llama-3.2-1b-instruct-q4_k_m.gguf`

🚀 **5. Run the Llama Local Server in WSL**  
Back in Ubuntu:  
`source wsl-llama/bin/activate`  
`python -m llama_cpp.server \  
  --model "/mnt/c/Users/Admin/Documents/Codes/AI/CivicBriefs.ai/app/agents/models/llama-3.2-1b-instruct-q4_k_m.gguf" \  
  --n_ctx 4096 \  
  --host 0.0.0.0 \  
  --port 8000`  
Expected output:  
`INFO: Uvicorn running on http://0.0.0.0:8000`  
`INFO: Application startup complete.`

🧪 **6. Test the Local LLM Endpoint**  
From WSL or Windows PowerShell:  
`curl http://localhost:8000/v1/models`  
You should get:  
`{"data":[{"id":"local-llama","object":"model"}]}`

🧪 **7. Test text generation**  
`curl -X POST http://localhost:8000/v1/chat/completions \  
  -H "Content-Type: application/json" \  
  -d '{  
    "model": "local-llama",  
    "messages": [{"role": "user", "content": "Say hello"}]  
  }'`

🧩 **8. Your Windows venv (Pipeline Environment)**  
⚠️ Do NOT install llama-cpp-python in Windows.  
Your Windows venv is only for:  
- embeddings (SentenceTransformer)  
- ChromaDB  
- requests  
- PDF generation  
- your news pipeline scripts  
Activate it in Windows PowerShell only:  
`cd "C:\Users\Admin\Documents\Codes\AI\CivicBriefs.ai"`  
`.\venv\Scripts\Activate.ps1`  
Verify:  
`python -m pip --version`

🔁 **9. How Pipeline Communicates with WSL LLM**  
Your updated pipeline uses:  
```python
import requests
def llama_local(prompt):
    res = requests.post(
        "http://localhost:8000/v1/chat/completions",
        json={
            "model": "local-llama",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 512
        }
    )
    return res.json()["choices"][0]["message"]["content"]
```
No llama_cpp import is needed inside Windows.

🏃 **10. Run Full Pipeline (Windows venv)**  
In PowerShell:  
`cd "C:\Users\Admin\Documents\Codes\AI\CivicBriefs.ai"`  
`.\venv\Scripts\Activate.ps1`  
`python -m app.agents.generate_news_capsule` run from the main directory

### TO run the generate_news_capsule.py follow these
See steps above for full WSL + Windows setup.

## Google Calendar Integration
The planner can create time-blocked events in a Google Calendar for a subscriber. Setup:
1. Create a Google Cloud project and enable Calendar API.
2. Create OAuth 2.0 credentials (Web application or Desktop).
3. Provide `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` and run the OAuth flow.
4. The pipeline stores an access/refresh token at `GOOGLE_TOKEN_FILE`. The orchestrator uses refresh tokens to create calendar events.

## Data storage & vector DB
- **MongoDB** holds user accounts, subscribers, sessions, scheduling metadata.
  - Collections: `users` for account profiles and hashed credentials.
  - `sessions` for short-lived auth tokens (TTL-based cleanup).
  - `subscribers` for daily capsule recipients.
- **ChromaDB** (or configured vector store) holds embeddings for news, PYQs, syllabus topics, and produced chunk metadata inside `./data/chroma` or `app/agents/chroma_store/`.
- Output files (reports, PDF capsules) are produced to a configured `data/` directory.

## APIs & Scripts
- `app/agents/generate_news_capsule.py` — Generate a single capsule (used by cron / scheduler).
- `app/agents/news_collection.py` — core scraping and embedding logic.
- `app/agents/planner_agent.py` — quiz generation and schedule creation.
- `app/orchestrator.py` — scheduler and workflow coordinator.
- `scripts/dev_server.py` — runs the FastAPI dev server.

The project includes placeholders for:
- **API Routes** - `/api/routes/` for REST endpoints
- **Services** - `/app/services/` for business logic
These are ready to be expanded for API functionality.

## Usage
### Running the API (development)
The FastAPI server now defaults to port **8005**. Pick either of these commands:
```bash
# Recommended: keeps reload watchers scoped to app/, web/, and data/
python scripts/dev_server.py
# Shortcut: same settings, handy for ad-hoc runs
python -m app
```
Both launchers call `uvicorn app.main:app` with `--reload` and honor the
`APP_HOST`, `APP_PORT`, and `APP_RELOAD` environment variables if you need to
override the defaults.

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

### Usage examples
Generate and preview a daily capsule:
```bash
python -m app.agents.generate_news_capsule --limit 20 --dry-run
```
Run orchestrator in test mode:
```bash
python -m app.orchestrator --test
```
Create and run the weekly planner (simulate):
```bash
python -m app.agents.planner_agent --simulate --user test@example.com
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
- **fastapi** - Web framework for API
- **uvicorn** - ASGI server
- **pymongo** - MongoDB driver
- **google-api-python-client** - For Calendar integration
- **reportlab** - For PDF generation (added for enhanced reporting)

See `app/requirements.txt` for the complete list.

## Testing & Debugging
- Logs: application uses structured logging — check console logs or configured log files.
- If embeddings fail, verify `SENTENCE_TRANSFORMER_MODEL` and that torch is installed with compatible CUDA/CPU.
- If Chromadb errors occur, check `CHROMA_DIR` permissions.
- For Google Calendar failures, re-run the OAuth flow and inspect saved token file.

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

## Security & Privacy
- Do not commit `.env` or credential/token files.
- Treat subscriber data sensitively — store minimal PII needed and provide opt-out.
- Revoke Google tokens for deactivated subscribers.

## Deployment & Scheduling
- The orchestrator is designed to run on a scheduler (cron, systemd timer, or a managed job).
- For production, containerize services and use managed MongoDB (Atlas) and persistent storage for Chroma.
- Consider a job queue (Redis + RQ/Celery) for heavy tasks (embedding generation, PDF creation).

## Roadmap & Improvements
- Web UI / dashboard to manage subscribers, preview daily capsules, view analytics.
- Multi-language support for regional news.
- Better personalization with longer learner history and spaced-repetition.
- CI/CD, tests, and production-ready deployment manifests.
- Email delivery pipeline with templating and unsubscribe management.
- REST API endpoints for dynamic queries
- Vector database integration (ChromaDB)
- Caching for repeated queries
- Support for multiple languages
- Real-time news streaming
- Advanced filtering and categorization
- Dashboard for visualizations

## Contributing
Contributions are welcome. Helpful tasks:
- Improve QA & tests for agents
- Add API endpoints for subscription management
- Enhance the planner algorithm (time-budgeting heuristics)
- Add more data sources and robust scrapers

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

Please open issues and PRs on GitHub. If you plan a large change, open an issue first with your design.

## License
This repository does not include a license file by default. Add a LICENSE (e.g., MIT) if you want permissive reuse.

## Authors
- **Aryan Pratik**     — original project author
- **Pavan Kumar**      - Contributor
- **Aditya Gupta**     - Contributor
- **Deepak Sharma**    - Contributor
- **Aman Chaurasia**   - Contributor
- Contributors — see GitHub repo for full list

GitHub: [@aryanpratik11](https://github.com/aryanpratik11)

## Contact & Support
Open an issue on the repository for bugs, feature requests, or questions.

For issues, questions, or suggestions, please open an issue on the GitHub repository.

---
**Last Updated:** November 18, 2025
