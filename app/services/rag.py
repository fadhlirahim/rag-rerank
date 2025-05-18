from typing import Any

from app.core import DocumentIngestionError, QueryError, get_logger, settings
from app.services.embedding import (
    get_embedding,
    get_embeddings,
    query_embeddings,
    upsert_embeddings,
)
from app.services.llm import generate_answer
from app.services.rerankers import rerank
from app.services.text_processing import load_document

# Setup logger
logger = get_logger(__name__)


async def ingest_document(
    content: str, filename: str, metadata: dict[str, Any] = None
) -> int:
    """Ingest a document into the RAG system."""
    try:
        logger.info(f"Ingesting document: {filename}")

        # Split document into chunks
        chunks = load_document(content, filename, metadata)
        logger.debug(f"Document split into {len(chunks)} chunks")

        # Get embeddings for chunks
        texts = [chunk.text for chunk in chunks]
        logger.debug(f"Getting embeddings for {len(texts)} chunks")
        embeddings = get_embeddings(texts)

        # Prepare metadata for Pinecone
        chunk_ids = [chunk.id for chunk in chunks]
        chunk_metadata = [{"text": chunk.text, **chunk.metadata} for chunk in chunks]

        # Upsert to vector database
        count = upsert_embeddings(chunk_ids, embeddings, chunk_metadata)
        logger.info(f"Successfully ingested {count} chunks")
        return count
    except Exception as e:
        logger.error(f"Document ingestion failed: {str(e)}")
        raise DocumentIngestionError(f"Document ingestion failed: {str(e)}")


async def query_knowledge(
    query: str, top_k: int = None, top_n: int = None
) -> dict[str, Any]:
    """Query the RAG system."""
    try:
        # Use defaults if not provided
        top_k = top_k or settings.DEFAULT_RETRIEVAL_TOP_K
        top_n = top_n or settings.DEFAULT_RERANK_TOP_N

        logger.info(f"Processing query with top_k={top_k}, top_n={top_n}")
        logger.debug(f"Query: {query}")

        # Get query embedding
        logger.debug("Getting query embedding")
        query_embedding = get_embedding(query)

        # Retrieve similar documents
        logger.debug(f"Retrieving similar documents with top_k={top_k}")
        matches = query_embeddings(query_embedding, top_k)

        # Convert matches to candidate format for reranking
        candidates = [
            {
                "id": match.id,
                "text": match.metadata["text"],
                "score": match.score,
                "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
            }
            for match in matches
        ]
        logger.debug(f"Retrieved {len(candidates)} candidates for reranking")

        # Rerank candidates
        logger.debug(f"Reranking candidates with top_n={top_n}, USE_CROSS_ENCODER={settings.USE_CROSS_ENCODER}")
        reranked = rerank(query, candidates, top_n)

        # Log reranking results
        mean_score = sum(doc["score"] for doc in reranked) / len(reranked) if reranked else 0
        logger.debug(f"Reranking complete, mean relevance score: {mean_score:.2f}")

        # Generate answer
        logger.debug("Generating answer")
        answer = generate_answer(query, reranked)
        logger.info("Query processing completed successfully")

        return {"query": query, "answer": answer, "sources": reranked}
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise QueryError(f"Query processing failed: {str(e)}")
