from typing import Any

import openai
import pinecone

from app.core import EmbeddingError, get_logger, settings

# Setup logger
logger = get_logger(__name__)

# Initialize OpenAI - no proxy settings
openai.api_key = settings.OPENAI_API_KEY

# Initialize Pinecone with the new API - no proxy settings
pc = pinecone.Pinecone(api_key=settings.PINECONE_API_KEY)
# Connect to the index directly
index = pc.Index(name=settings.PINECONE_INDEX_NAME)


def get_embedding(text: str) -> list[float]:
    """Get embedding for a single text."""
    try:
        logger.debug("Generating embedding for text")
        response = openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
            # dimensions parameter removed as it's not supported in OpenAI API v1.3.0
            # The dimension is determined by the model automatically
        )
        embedding = response.data[0].embedding

        # Resize embedding if needed to match Pinecone's dimension
        if len(embedding) != settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                f"Model returned {len(embedding)}-d embedding, but Pinecone expects {settings.EMBEDDING_DIMENSIONS}-d."
            )
            if len(embedding) > settings.EMBEDDING_DIMENSIONS:
                # Truncate the embedding to the first EMBEDDING_DIMENSIONS dimensions
                embedding = embedding[: settings.EMBEDDING_DIMENSIONS]
                logger.info(
                    f"Embedding truncated to {settings.EMBEDDING_DIMENSIONS} dimensions."
                )
            else:
                # This shouldn't happen with OpenAI models, but just in case
                error_msg = f"Embedding size ({len(embedding)}) is smaller than Pinecone dimension ({settings.EMBEDDING_DIMENSIONS})"
                logger.error(error_msg)
                raise EmbeddingError(error_msg)

        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {str(e)}")
        raise EmbeddingError(f"Failed to generate embedding: {str(e)}")


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts."""
    try:
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        response = openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
            # dimensions parameter removed as it's not supported in OpenAI API v1.3.0
            # The dimension is determined by the model automatically
        )
        embeddings = [item.embedding for item in response.data]

        # Resize embeddings if needed to match Pinecone's dimension
        if embeddings and len(embeddings[0]) != settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                f"Model returned {len(embeddings[0])}-d embeddings, but Pinecone expects {settings.EMBEDDING_DIMENSIONS}-d."
            )
            if len(embeddings[0]) > settings.EMBEDDING_DIMENSIONS:
                # Truncate the embeddings to the first EMBEDDING_DIMENSIONS dimensions
                embeddings = [
                    emb[: settings.EMBEDDING_DIMENSIONS] for emb in embeddings
                ]
                logger.info(
                    f"Embeddings truncated to {settings.EMBEDDING_DIMENSIONS} dimensions."
                )
            else:
                # This shouldn't happen with OpenAI models, but just in case
                error_msg = f"Embedding size ({len(embeddings[0])}) is smaller than Pinecone dimension ({settings.EMBEDDING_DIMENSIONS})"
                logger.error(error_msg)
                raise EmbeddingError(error_msg)

        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")


def upsert_embeddings(
    chunk_ids: list[str], embeddings: list[list[float]], metadata: list[dict[str, Any]]
):
    """Upsert embeddings to Pinecone."""
    try:
        vectors = [
            (chunk_id, embedding, meta)
            for chunk_id, embedding, meta in zip(
                chunk_ids, embeddings, metadata, strict=False
            )
        ]

        logger.info(f"Upserting {len(vectors)} vectors to Pinecone")

        # Batch upsert to Pinecone
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            index.upsert(vectors=batch)
            logger.debug(
                f"Upserted batch {i // batch_size + 1} of {len(vectors) // batch_size + 1}"
            )

        return len(vectors)
    except Exception as e:
        logger.error(f"Failed to upsert embeddings: {str(e)}")
        raise EmbeddingError(f"Failed to upsert embeddings: {str(e)}")


def query_embeddings(
    query_embedding: list[float], top_k: int = settings.DEFAULT_RETRIEVAL_TOP_K
):
    """Query embeddings from Pinecone."""
    try:
        # Ensure query embedding matches Pinecone's dimension
        if len(query_embedding) != settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                f"Query embedding dimension ({len(query_embedding)}) doesn't match Pinecone's dimension ({settings.EMBEDDING_DIMENSIONS})."
            )
            if len(query_embedding) > settings.EMBEDDING_DIMENSIONS:
                query_embedding = query_embedding[: settings.EMBEDDING_DIMENSIONS]
                logger.info(
                    f"Query embedding truncated to {settings.EMBEDDING_DIMENSIONS} dimensions."
                )
            else:
                error_msg = f"Query embedding size ({len(query_embedding)}) is smaller than Pinecone dimension ({settings.EMBEDDING_DIMENSIONS})"
                logger.error(error_msg)
                raise EmbeddingError(error_msg)

        logger.debug(f"Querying Pinecone with top_k={top_k}")
        results = index.query(
            vector=query_embedding, top_k=top_k, include_metadata=True
        )
        logger.debug(f"Retrieved {len(results.matches)} matches from Pinecone")
        return results.matches
    except Exception as e:
        logger.error(f"Failed to query embeddings: {str(e)}")
        raise EmbeddingError(f"Failed to query embeddings: {str(e)}")
