import openai
from typing import List, Dict, Any
import pinecone
import os
from app.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS
)

# Initialize OpenAI - no proxy settings
openai.api_key = OPENAI_API_KEY

# Initialize Pinecone with the new API - no proxy settings
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
# Connect to the index directly
index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding(text: str) -> List[float]:
    """Get embedding for a single text."""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        # dimensions parameter removed as it's not supported in OpenAI API v1.3.0
        # The dimension is determined by the model automatically
    )
    embedding = response.data[0].embedding

    # Resize embedding if needed to match Pinecone's dimension
    if len(embedding) != EMBEDDING_DIMENSIONS:
        print(f"Warning: Model returned {len(embedding)}-d embedding, but Pinecone expects {EMBEDDING_DIMENSIONS}-d.")
        if len(embedding) > EMBEDDING_DIMENSIONS:
            # Truncate the embedding to the first EMBEDDING_DIMENSIONS dimensions
            embedding = embedding[:EMBEDDING_DIMENSIONS]
            print(f"Embedding truncated to {EMBEDDING_DIMENSIONS} dimensions.")
        else:
            # This shouldn't happen with OpenAI models, but just in case
            print("Error: Embedding dimension is smaller than expected. Cannot proceed.")
            raise ValueError(f"Embedding size ({len(embedding)}) is smaller than Pinecone dimension ({EMBEDDING_DIMENSIONS})")

    return embedding

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for multiple texts."""
    response = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        # dimensions parameter removed as it's not supported in OpenAI API v1.3.0
        # The dimension is determined by the model automatically
    )
    embeddings = [item.embedding for item in response.data]

    # Resize embeddings if needed to match Pinecone's dimension
    if embeddings and len(embeddings[0]) != EMBEDDING_DIMENSIONS:
        print(f"Warning: Model returned {len(embeddings[0])}-d embeddings, but Pinecone expects {EMBEDDING_DIMENSIONS}-d.")
        if len(embeddings[0]) > EMBEDDING_DIMENSIONS:
            # Truncate the embeddings to the first EMBEDDING_DIMENSIONS dimensions
            embeddings = [emb[:EMBEDDING_DIMENSIONS] for emb in embeddings]
            print(f"Embeddings truncated to {EMBEDDING_DIMENSIONS} dimensions.")
        else:
            # This shouldn't happen with OpenAI models, but just in case
            print("Error: Embedding dimension is smaller than expected. Cannot proceed.")
            raise ValueError(f"Embedding size ({len(embeddings[0])}) is smaller than Pinecone dimension ({EMBEDDING_DIMENSIONS})")

    return embeddings

def upsert_embeddings(chunk_ids: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
    """Upsert embeddings to Pinecone."""
    vectors = [
        (chunk_id, embedding, meta)
        for chunk_id, embedding, meta in zip(chunk_ids, embeddings, metadata)
    ]

    # Batch upsert to Pinecone
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)

    return len(vectors)

def query_embeddings(query_embedding: List[float], top_k: int = 25):
    """Query embeddings from Pinecone."""
    # Ensure query embedding matches Pinecone's dimension
    if len(query_embedding) != EMBEDDING_DIMENSIONS:
        print(f"Warning: Query embedding dimension ({len(query_embedding)}) doesn't match Pinecone's dimension ({EMBEDDING_DIMENSIONS}).")
        if len(query_embedding) > EMBEDDING_DIMENSIONS:
            query_embedding = query_embedding[:EMBEDDING_DIMENSIONS]
            print(f"Query embedding truncated to {EMBEDDING_DIMENSIONS} dimensions.")
        else:
            raise ValueError(f"Query embedding size ({len(query_embedding)}) is smaller than Pinecone dimension ({EMBEDDING_DIMENSIONS})")

    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results.matches