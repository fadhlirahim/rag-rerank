# RAG Embeddings Concept

A simple, two-stage Retrieval-Augmented Generation (RAG) system that uses:
- Retrieval: text-embedding-3-large via OpenAI
- Rerank: GPT-4o-mini for scoring relevance
- Answer: GPT-4o for generating the final response

## Architecture

This implementation follows a simple but effective RAG pattern:
1. Documents are chunked and embedded, then stored in Pinecone
2. On query, the system:
   - Retrieves top-k semantic matches via embeddings
   - Reranks results using GPT-4o-mini
   - Generates an answer with GPT-4o using only the top results

## Setup

### Prerequisites
- Python 3.11+
- OpenAI API key
- Pinecone account and API key

### Installation

1. Clone the repository:
```
git clone https://github.com/fadhlirahim/rag-embeddings-concept.git
cd rag-embeddings-concept
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up environment variables by creating a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index_name
```

### Pinecone Setup
1. Create a Pinecone account if you don't have one already
2. Create a new index with:
   - Dimensions: 1024
   - Metric: cosine
   - Name: (use the same name you set in PINECONE_INDEX_NAME)

## Usage

### Running the Server

Start the FastAPI server:
```
python run.py
```

Start the frontend:
```
cd frontend
npm install
npm run dev
```

### API Endpoints

#### Ingest a Document
```
POST /ingest
```
Request body:
```json
{
  "content": "Your document content here",
  "filename": "document.txt",
  "metadata": {
    "source": "user_upload",
    "category": "documentation"
  }
}
```

#### Ask a Question
```
POST /ask
```
Request body:
```json
{
  "query": "Your question here",
  "top_k": 25,
  "top_n": 5
}
```

## Performance Considerations

As noted in the design document:
- Embedding is the slow part (~0.3s per 1K tokens). Parallel batching is recommended for production.
- GPT reranking dominates latency (300-400ms for 25 documents).
- At scale, consider fine-tuning a smaller reranker model.

## Security Notes

This prototype sends raw document content to third-party LLM services. In a production environment, consider:
- Scrubbing relevant before sending to external services
- Implementing a local model for sensitive information
- Adding authentication and rate limiting to the API
