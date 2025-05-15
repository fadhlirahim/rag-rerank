from typing import List, Dict, Any
from app.services.embedding import get_embedding, get_embeddings, upsert_embeddings, query_embeddings
from app.services.text_processing import TextChunk, load_document
from app.services.llm import rerank, generate_answer
from app.config import DEFAULT_RETRIEVAL_TOP_K, DEFAULT_RERANK_TOP_N

async def ingest_document(content: str, filename: str, metadata: Dict[str, Any] = None) -> int:
    """Ingest a document into the RAG system."""
    # Split document into chunks
    chunks = load_document(content, filename, metadata)

    # Get embeddings for chunks
    texts = [chunk.text for chunk in chunks]
    embeddings = get_embeddings(texts)

    # Prepare metadata for Pinecone
    chunk_ids = [chunk.id for chunk in chunks]
    chunk_metadata = [
        {
            "text": chunk.text,
            **chunk.metadata
        } for chunk in chunks
    ]

    # Upsert to vector database
    count = upsert_embeddings(chunk_ids, embeddings, chunk_metadata)
    return count

async def query_knowledge(query: str, top_k: int = DEFAULT_RETRIEVAL_TOP_K, top_n: int = DEFAULT_RERANK_TOP_N) -> Dict[str, Any]:
    """Query the RAG system."""
    # Get query embedding
    query_embedding = get_embedding(query)

    # Retrieve similar documents
    matches = query_embeddings(query_embedding, top_k)

    # Convert matches to candidate format for reranking
    candidates = [
        {
            "id": match.id,
            "text": match.metadata["text"],
            "score": match.score,
            "metadata": {k: v for k, v in match.metadata.items() if k != "text"}
        }
        for match in matches
    ]

    # Rerank candidates
    reranked = rerank(query, candidates, top_n)

    # Generate answer
    answer = generate_answer(query, reranked)

    return {
        "query": query,
        "answer": answer,
        "sources": reranked
    }