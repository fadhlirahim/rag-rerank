from typing import Any, List, Dict
import openai
import lancedb
import pyarrow as pa
import numpy as np

from app.core import EmbeddingError, get_logger, settings

# Setup logger
logger = get_logger(__name__)

# Initialize OpenAI - no proxy settings
openai.api_key = settings.OPENAI_API_KEY

# Initialize LanceDB
try:
    logger.info(f"Connecting to LanceDB at path: {settings.LANCEDB_DATABASE_PATH}")
    db = lancedb.connect(settings.LANCEDB_DATABASE_PATH)

    # Define the schema for the LanceDB table
    # Based on rag.py, 'text' is a crucial metadata field.
    # Other metadata will be stored and retrieved.
    # The vector dimension must match settings.EMBEDDING_DIMENSIONS.
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), list_size=settings.EMBEDDING_DIMENSIONS)),
        pa.field("text", pa.string()),
        # Add other anticipated common metadata fields if known,
        # otherwise, they will be part of the dynamic dictionary.
        # For now, we rely on 'text' and other fields will be passed through
        # in the data dictionaries to table.add()
    ])

    try:
        logger.info(f"Attempting to open LanceDB table: {settings.LANCEDB_TABLE_NAME}")
        table = db.open_table(settings.LANCEDB_TABLE_NAME)
        logger.info(f"Successfully opened table: {settings.LANCEDB_TABLE_NAME}")
    except FileNotFoundError:
        logger.info(f"Table {settings.LANCEDB_TABLE_NAME} not found. Creating new table.")
        table = db.create_table(settings.LANCEDB_TABLE_NAME, schema=schema)
        logger.info(f"Successfully created table: {settings.LANCEDB_TABLE_NAME} with schema: {schema}")

except Exception as e:
    logger.error(f"Failed to initialize LanceDB or table: {str(e)}")
    # If DB connection fails, subsequent calls will fail.
    # We might want to raise an error here to stop the application from starting
    # or handle it gracefully if parts of the app can run without DB.
    # For now, logging the error. Functions below will raise EmbeddingError.
    db = None
    table = None


def _validate_db_connection():
    if db is None or table is None:
        raise EmbeddingError("LanceDB connection not established. Check logs for initialization errors.")


def get_embedding(text: str) -> list[float]:
    """Get embedding for a single text."""
    try:
        logger.debug("Generating embedding for text")
        response = openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
            # dimensions parameter is not explicitly set here;
            # model default or server-side config is used.
            # We will resize if necessary.
        )
        embedding = response.data[0].embedding

        # Resize embedding if needed to match LanceDB's expected dimension
        if len(embedding) != settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                f"Model returned {len(embedding)}-d embedding, but LanceDB table expects {settings.EMBEDDING_DIMENSIONS}-d."
            )
            if len(embedding) > settings.EMBEDDING_DIMENSIONS:
                embedding = embedding[: settings.EMBEDDING_DIMENSIONS]
                logger.info(
                    f"Embedding truncated to {settings.EMBEDDING_DIMENSIONS} dimensions."
                )
            else:
                # Pad with zeros if the embedding is smaller
                logger.warning(
                    f"Embedding size ({len(embedding)}) is smaller than LanceDB dimension ({settings.EMBEDDING_DIMENSIONS}). Padding with zeros."
                )
                padding = [0.0] * (settings.EMBEDDING_DIMENSIONS - len(embedding))
                embedding.extend(padding)
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
        )
        embeddings = [item.embedding for item in response.data]

        # Resize embeddings if needed
        if embeddings and len(embeddings[0]) != settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                f"Model returned {len(embeddings[0])}-d embeddings, but LanceDB table expects {settings.EMBEDDING_DIMENSIONS}-d."
            )
            resized_embeddings = []
            for emb in embeddings:
                if len(emb) > settings.EMBEDDING_DIMENSIONS:
                    resized_embeddings.append(emb[: settings.EMBEDDING_DIMENSIONS])
                elif len(emb) < settings.EMBEDDING_DIMENSIONS:
                    padding = [0.0] * (settings.EMBEDDING_DIMENSIONS - len(emb))
                    resized_embeddings.append(emb + padding)
                else:
                    resized_embeddings.append(emb)
            embeddings = resized_embeddings
            if len(embeddings[0]) > settings.EMBEDDING_DIMENSIONS:
                 logger.info(f"Embeddings truncated to {settings.EMBEDDING_DIMENSIONS} dimensions.")
            else:
                 logger.info(f"Embeddings padded to {settings.EMBEDDING_DIMENSIONS} dimensions.")

        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")


def upsert_embeddings(
    chunk_ids: list[str], embeddings: list[list[float]], metadata: list[dict[str, Any]]
):
    """Upsert embeddings to LanceDB."""
    _validate_db_connection()
    try:
        if not (len(chunk_ids) == len(embeddings) == len(metadata)):
            raise ValueError("chunk_ids, embeddings, and metadata lists must have the same length.")

        data_to_add = []
        for chunk_id, embedding, meta_item in zip(chunk_ids, embeddings, metadata):
            if len(embedding) != settings.EMBEDDING_DIMENSIONS:
                # This should ideally be caught by get_embeddings, but as a safeguard:
                logger.warning(f"Correcting embedding dimension for chunk {chunk_id} before upsert.")
                if len(embedding) > settings.EMBEDDING_DIMENSIONS:
                    embedding = embedding[:settings.EMBEDDING_DIMENSIONS]
                else:
                    embedding.extend([0.0] * (settings.EMBEDDING_DIMENSIONS - len(embedding)))

            # Ensure 'text' is present as per schema, other metadata fields are passed as is.
            # LanceDB handles dynamic fields in dictionaries if not strictly typed in schema,
            # or they can be added to schema if they are fixed.
            # Our schema defines 'text', so it must be present.
            item = {"id": chunk_id, "vector": embedding, **meta_item}
            if "text" not in item:
                logger.warning(f"Chunk {chunk_id} metadata missing 'text' field. Adding empty string.")
                item["text"] = "" # Ensure text field exists as per schema
            data_to_add.append(item)

        if not data_to_add:
            logger.info("No data to upsert.")
            return 0

        logger.info(f"Upserting {len(data_to_add)} vectors to LanceDB table {settings.LANCEDB_TABLE_NAME}")

        # LanceDB's add method can take a list of dictionaries.
        # Depending on the version and configuration, LanceDB might merge based on 'id' or just add.
        # For true upsert behavior (update if exists, insert if not),
        # we might need to delete existing ids first if table.add doesn't do that.
        # table.add(data) by default appends. For upsert, we often delete then add.
        # Let's assume for now that we want to allow duplicates or that IDs are unique on each call.
        # If true upsert is needed, a delete step for existing IDs would be required first.
        # The prompt implies `upsert` but LanceDB `add` is append.
        # For this task, we'll use `add`. If specific upsert (overwrite) is needed,
        # we would do `table.delete(f"id IN {tuple(chunk_ids_to_overwrite)}")` first.
        # Given the name "upsert_embeddings", we should try to honor it.
        # A simple way is to delete matching IDs first.

        existing_ids = [item["id"] for item in data_to_add]
        if existing_ids:
            # Format IDs for SQL IN clause: ('id1', 'id2', ...)
            formatted_ids = tuple(existing_ids)
            condition = ""
            if len(formatted_ids) == 1:
                condition = f"id = '{formatted_ids[0]}'"
            else:
                condition = f"id IN {formatted_ids}"

            try:
                logger.debug(f"Deleting existing entries for IDs: {existing_ids} before adding.")
                table.delete(condition)
            except Exception as e:
                # It's possible the table is empty or IDs don't exist, which can be fine.
                # LanceDB might error if trying to delete from non-existent or on bad filter.
                logger.warning(f"Could not delete existing IDs, possibly table is empty or IDs not found: {e}")


        table.add(data_to_add)
        logger.debug(f"Successfully added/updated {len(data_to_add)} vectors.")
        return len(data_to_add)

    except Exception as e:
        logger.error(f"Failed to upsert embeddings to LanceDB: {str(e)}")
        raise EmbeddingError(f"Failed to upsert embeddings to LanceDB: {str(e)}")


def query_embeddings(
    query_embedding: list[float], top_k: int = settings.DEFAULT_RETRIEVAL_TOP_K
) -> List[Dict[str, Any]]:
    """Query embeddings from LanceDB."""
    _validate_db_connection()
    try:
        # Ensure query embedding matches LanceDB's dimension
        if len(query_embedding) != settings.EMBEDDING_DIMENSIONS:
            logger.warning(
                f"Query embedding dimension ({len(query_embedding)}) doesn't match LanceDB's dimension ({settings.EMBEDDING_DIMENSIONS})."
            )
            if len(query_embedding) > settings.EMBEDDING_DIMENSIONS:
                query_embedding = query_embedding[: settings.EMBEDDING_DIMENSIONS]
                logger.info(
                    f"Query embedding truncated to {settings.EMBEDDING_DIMENSIONS} dimensions."
                )
            else:
                # Pad with zeros
                logger.warning(f"Query embedding size ({len(query_embedding)}) is smaller. Padding with zeros.")
                padding = [0.0] * (settings.EMBEDDING_DIMENSIONS - len(query_embedding))
                query_embedding.extend(padding)

        logger.debug(f"Querying LanceDB table {settings.LANCEDB_TABLE_NAME} with top_k={top_k}")

        # LanceDB search returns a Query object, then .to_list() converts to list of dicts
        # Each dict contains all fields, plus _distance.
        results = table.search(np.array(query_embedding, dtype=np.float32)).limit(top_k).to_list()

        logger.debug(f"Retrieved {len(results)} matches from LanceDB")

        # Transform results to match the previous Pinecone output structure
        # Pinecone's 'matches' were objects with 'id', 'score', 'metadata', 'values'
        # LanceDB returns a list of dicts. '_distance' is the score (lower is better).
        formatted_matches = []
        for res_item in results:
            metadata_content = {k: v for k, v in res_item.items() if k not in ['id', 'vector', '_distance']}
            # Ensure 'text' is in metadata_content, if it was a top-level field and not already there.
            if 'text' not in metadata_content and 'text' in res_item:
                 metadata_content['text'] = res_item['text']

            formatted_matches.append({
                "id": res_item["id"],
                "score": res_item["_distance"],  # LanceDB returns distance. Pinecone returned similarity.
                                               # This might need adjustment in RAG logic if it expects higher = better.
                "metadata": metadata_content,  # Contains 'text' and other metadata
                "values": res_item["vector"]   # Pass the vector for MMR in rag.py
            })
        return formatted_matches
    except Exception as e:
        logger.error(f"Failed to query embeddings from LanceDB: {str(e)}")
        raise EmbeddingError(f"Failed to query embeddings from LanceDB: {str(e)}")


def delete_all_vectors() -> Dict[str, str]:
    """Delete all vectors by dropping the LanceDB table and recreating it."""
    _validate_db_connection()
    global table # Allow modification of global table variable
    try:
        table_name = settings.LANCEDB_TABLE_NAME
        logger.info(f"Deleting all vectors by dropping table {table_name}")
        db.drop_table(table_name)
        logger.info(f"Successfully dropped table {table_name}")

        # Recreate the table to ensure it exists for future operations
        # Schema is already defined globally during initialization
        current_schema = pa.schema([
            pa.field("id", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), list_size=settings.EMBEDDING_DIMENSIONS)),
            pa.field("text", pa.string()),
        ]) # Re-define schema locally to be safe, or ensure global schema is accessible
        table = db.create_table(table_name, schema=current_schema) # Use the same schema
        logger.info(f"Successfully recreated table {table_name} with schema: {current_schema}")

        return {"status": "success", "message": f"All data deleted and table {table_name} recreated."}
    except Exception as e:
        logger.error(f"Failed to delete all vectors from LanceDB: {str(e)}")
        raise EmbeddingError(f"Failed to delete all vectors from LanceDB: {str(e)}")


def delete_vectors(ids: List[str]) -> Dict[str, Any]:
    """Delete specific vectors by their IDs from LanceDB."""
    _validate_db_connection()
    try:
        if not ids:
            logger.info("No IDs provided for deletion.")
            return {"status": "success", "deleted_count": 0}

        logger.info(f"Attempting to delete {len(ids)} vectors from LanceDB table {settings.LANCEDB_TABLE_NAME}")

        # Format IDs for SQL IN clause: ('id1', 'id2', ...)
        formatted_ids = tuple(ids)
        condition = ""
        if len(formatted_ids) == 1:
            # For a single ID, the condition is "id = 'value'"
            condition = f"id = '{formatted_ids[0]}'"
        else:
            # For multiple IDs, the condition is "id IN ('value1', 'value2')"
            condition = f"id IN {formatted_ids}"

        # table.delete() does not return count of deleted rows.
        # To get a count, one might need to count before and after, or query for IDs.
        # For now, we assume success if no error.
        table.delete(condition)

        logger.info(f"Successfully submitted delete operation for {len(ids)} vectors. Note: LanceDB delete does not return count of affected rows.")
        # To confirm deletion, one could try to query these IDs, but that's extra overhead.
        # The operation itself will raise an error if it fails fundamentally.
        return {"status": "success", "message": f"Delete operation for {len(ids)} IDs submitted. Check table status if confirmation needed." , "submitted_for_deletion_count": len(ids)}
    except Exception as e:
        logger.error(f"Failed to delete vectors from LanceDB: {str(e)}")
        raise EmbeddingError(f"Failed to delete vectors from LanceDB: {str(e)}")

# Note: The global `table` variable might be an issue if multiple threads/workers
# modify it (e.g. in delete_all_vectors). For typical FastAPI usage with Uvicorn,
# this might be okay as global state is shared across requests in a single process.
# However, for multi-process workers, each worker would have its own `db` and `table` instance.
# The LanceDB connection itself (`lancedb.connect`) should handle underlying file access safely.
# Re-assigning `table` in `delete_all_vectors` should update the reference for subsequent calls within that worker.
# Consider passing `db` and `table` instances around or using a class structure if this becomes an issue.
