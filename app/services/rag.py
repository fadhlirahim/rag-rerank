from typing import Any
import numpy as np

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


def apply_mmr(query_embedding: list[float], candidates: list[dict[str, Any]],
              lambda_param: float = settings.MMR_LAMBDA, top_k: int = None) -> list[dict[str, Any]]:
    """
    Apply Maximal Marginal Relevance to diversify results while maintaining relevance.

    Args:
        query_embedding: The query embedding vector
        candidates: List of candidate documents with their embeddings
        lambda_param: Balance between relevance and diversity (0-1)
        top_k: Number of results to return

    Returns:
        List of selected candidates ordered by MMR score
    """
    if not candidates:
        return []

    if top_k is None:
        top_k = len(candidates)

    if len(candidates) <= top_k:
        return candidates

    # Extract embeddings from metadata if available, otherwise use the vectors from Pinecone
    embeddings = []
    for c in candidates:
        if "embedding" in c:
            embeddings.append(np.array(c["embedding"]))
        elif "vector" in c:
            embeddings.append(np.array(c["vector"]))
        elif "metadata" in c and "embedding" in c["metadata"]:
            embeddings.append(np.array(c["metadata"]["embedding"]))
        else:
            # If no embedding is available, we'll need to reconstruct it
            logger.warning(f"No embedding found for candidate {c['id']}, MMR may be less effective")
            # Use a placeholder - in a real system you might want to fetch these
            embeddings.append(np.zeros(len(query_embedding)))

    embeddings = np.array(embeddings)
    query_embedding = np.array(query_embedding)

    # Normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    embeddings = embeddings / norms

    query_norm = np.linalg.norm(query_embedding)
    if query_norm > 0:
        query_embedding = query_embedding / query_norm

    # Calculate similarities to query
    sim_to_query = np.dot(embeddings, query_embedding)

    # Initialize
    selected_indices = []
    remaining_indices = list(range(len(candidates)))

    # Select first document with highest similarity to query
    best_idx = np.argmax(sim_to_query)
    selected_indices.append(best_idx)
    remaining_indices.remove(best_idx)

    # Select the rest using MMR
    for _ in range(min(top_k - 1, len(candidates) - 1)):
        if not remaining_indices:
            break

        # Similarity to query for remaining documents (relevance component)
        query_sim = np.array([sim_to_query[i] for i in remaining_indices])

        # Calculate max similarity to selected documents (diversity component)
        max_sim_to_selected = np.zeros(len(remaining_indices))

        for i, idx in enumerate(remaining_indices):
            selected_embeddings = embeddings[selected_indices]
            curr_embedding = embeddings[idx].reshape(1, -1)

            # Calculate similarity to all selected documents
            sims = np.dot(curr_embedding, selected_embeddings.T).flatten()

            # Get max similarity
            if len(sims) > 0:
                max_sim_to_selected[i] = np.max(sims)

        # Calculate MMR score: relevance - diversity penalty
        mmr_scores = lambda_param * query_sim - (1 - lambda_param) * max_sim_to_selected

        # Get best scoring document
        mmr_idx = np.argmax(mmr_scores)
        next_best_idx = remaining_indices[mmr_idx]

        # Add to selected
        selected_indices.append(next_best_idx)
        remaining_indices.remove(next_best_idx)

    # Return documents in order of MMR selection
    return [candidates[i] for i in selected_indices]


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
                "vector": match.values if hasattr(match, 'values') else None
            }
            for match in matches
        ]
        logger.debug(f"Retrieved {len(candidates)} candidates for reranking")

        # Check if we should skip MMR for fiction content
        is_fiction = any(
            c.get("metadata", {}).get("is_fiction", False) or
            c.get("metadata", {}).get("genre") == "fiction" or
            c.get("metadata", {}).get("category") == "fiction"
            for c in candidates[:3]  # Check first few to save time
        )

        # Check if query contains narrative elements that would benefit from contiguous passages
        narrative_query = any(term in query.lower() for term in [
            "witness", "wedding", "church", "sequence", "events", "story", "what happened", "how did", "what led to"
        ])

        # Completely skip MMR for fiction with narrative queries or use high lambda to prioritize relevance
        if is_fiction:
            if narrative_query:
                logger.info("Detected fiction content with narrative query, skipping MMR to preserve narrative continuity")
                mmr_candidates = candidates
            else:
                # Use higher lambda for fiction (prioritize relevance over diversity)
                fiction_lambda = settings.FICTION_MMR_LAMBDA  # Use the configured value
                logger.info(f"Using higher MMR lambda for fiction: {fiction_lambda}")
                mmr_candidates = apply_mmr(query_embedding, candidates, lambda_param=fiction_lambda, top_k=min(top_k, len(candidates)))
        else:
            # Apply normal MMR for non-fiction
            logger.debug("Applying MMR to diversify results")
            mmr_candidates = apply_mmr(query_embedding, candidates, top_k=min(top_k, len(candidates)))
            logger.debug(f"Selected {len(mmr_candidates)} diverse candidates with MMR")

        # For fiction narrative queries, we might want to increase top_n
        if is_fiction and narrative_query and top_n < 15:
            original_top_n = top_n
            top_n = 15  # Use more context for narrative queries
            logger.info(f"Increased top_n from {original_top_n} to {top_n} for fiction narrative query")

        # Rerank candidates
        logger.debug(f"Reranking candidates with top_n={top_n}, USE_CROSS_ENCODER={settings.USE_CROSS_ENCODER}")
        reranked = rerank(query, mmr_candidates, top_n)

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
