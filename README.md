# RAG Rerank PoC

A simple, two-stage Retrieval-Augmented Generation (RAG) system that uses:

- Retrieval: text-embedding-3-large via OpenAI
- Rerank: Local cross-encoder model (with GPT-4o-mini fallback)
- Answer: GPT-4o for generating the final response

Built with FastAPI, integrating OpenAI embeddings and Pinecone for vector storage.

Ideas from https://www.pinecone.io/learn/series/rag/rerankers/#Power-of-Rerankers

## Features

- Document ingestion with automatic text chunking
- Semantic search using OpenAI embeddings
- Cross-encoder based reranking of search results with LLM fallback
- Answer generation from relevant documents

## Diagram overview

```
 ┌───────────────┐   ingest     ┌──────────────┐
 │  Markdown /   │─────────────►│ Chunker +    │
 │  Text Files   │              │ Embeddings   │
 └───────────────┘              └─────┬────────┘
                                      │ upsert
                                ┌─────▼───────┐
                                │ Pinecone DB │
                                └─────▲───────┘
                                      │ ANN search (top-K)
USER QUERY ─────embed────────────────►│
                                      ▼
                               Candidates (K)
                                      │ rerank
                           ┌──────────▼─────────┐
                           │ Cross-encoder /    │
                           │ LLM judge scores   │
                           └──────────▲─────────┘
                                      │ top-N
                                      ▼
                               High-grade context
                                      │
                               ┌──────▼───────┐
                               │ GPT-4o (LLM) │
                               └──────▲───────┘
                                      │ answer + citations
                                   Final Answer
```

<img width="900" alt="Screenshot 2025-05-18 at 4 29 33 PM" src="https://github.com/user-attachments/assets/432b244d-ab8a-42c7-95f9-e1c53909d12d" />
<img width="900" alt="Screenshot 2025-05-18 at 4 27 41 PM" src="https://github.com/user-attachments/assets/c390fdc6-8b3e-43b3-8935-2f9bff8f0de8" />


## Quick Setup with uv & mise

### Prerequisites

1. Install uv:
   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Install mise:
   ```bash
   # On macOS/Linux
   curl https://mise.run | sh

   # On Windows
   # Download from https://github.com/jdx/mise/releases
   ```

### Automated Setup

The easiest way to get started is using our setup script:

```bash
# Linux/macOS
chmod +x setup.sh
./setup.sh
source .venv/bin/activate

# Windows
.\setup.ps1
.venv\Scripts\activate
```

After running the setup script and activating the environment, you can start the application with:

```bash
mise run dev-all
```

### Manual Setup

1. Clone the repository

2. Create and activate a virtual environment:
   ```bash
   # Create venv
   uv venv

   # Activate it
   source .venv/bin/activate  # On Unix/macOS
   # OR
   .venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   # Install main dependencies
   uv sync

   # Install development dependencies
   uv sync --group dev
   ```

4. Copy `env.example` to `.env` and fill in the required values
5. Run the application: `uvicorn app.main:app --reload`

## Development

### Managing Dependencies

All dependencies are managed through `pyproject.toml`:

```bash
# Add a new runtime dependency
uv add fastapi

# Add a development dependency
uv add --group dev pytest

# Update dependencies
uv sync        # runtime only
uv sync --group dev  # include dev dependencies

# Lock dependencies
uv lock
```

### Project Structure

```
app/
├── api/            # API routes and controllers
├── core/           # Core configuration, logging, exceptions
├── models/         # Data models/schemas
├── services/       # Business logic services
└── main.py         # Application entrypoint
```

### Development Tools

The project uses mise for task automation. Common development tasks can be run through mise:

```bash
# Backend tasks
mise run start      # Start the backend server
mise run dev        # Run the backend development server
mise run test       # Run tests with verbose output
mise run lint       # Run linting checks
mise run format     # Format code and fix auto-fixable issues
mise run check      # Run type checking with explicit bases

# Frontend tasks
mise run frontend-install  # Install frontend dependencies
mise run frontend-dev     # Start the frontend development server
mise run frontend-build   # Build the frontend for production
mise run frontend-preview # Preview the production build

# Composite tasks
mise run install-all     # Install all dependencies (backend + frontend)
mise run dev-all        # Start both backend and frontend development servers
```

### Environment Variables

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=1024
RERANK_MODEL=gpt-4o-mini
ANSWER_MODEL=gpt-4o

# Cross-Encoder Configuration
USE_CROSS_ENCODER=true
CROSS_ENCODER_MODEL=BAAI/bge-reranker-large
DEVICE=cpu
RERANK_BATCH=16
CE_MAX_PAIRS=100V
CE_SCORE_SHIFT=5.0
CE_SCORE_SCALE=1.0
CE_NEUTRAL_THRESHOLD=5.0
LLM_FALLBACK_THRESHOLD=5.0

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index

# Retrieval Configuration
DEFAULT_RETRIEVAL_TOP_K=25
DEFAULT_RERANK_TOP_N=5
CHUNK_SIZE=512
```

## API Endpoints

### POST /ingest

Ingest a document into the knowledge base.

```json
{
  "content": "Document text content",
  "filename": "document.txt",
  "metadata": {
    "source": "user_upload",
    "author": "John Doe"
  }
}
```

### POST /ask

Query the knowledge base and get an answer.

```json
{
  "query": "What is RAG?",
  "top_k": 25,
  "top_n": 5
}
```

### GET /health

Health check endpoint.

## Production Deployment

For production deployment, consider:

1. Using Gunicorn with Uvicorn workers
2. Setting up proper monitoring and observability
3. Implementing rate limiting and authentication
4. Using a proper cache for frequently accessed data

