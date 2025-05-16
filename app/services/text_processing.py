from typing import Any

from app.core import DocumentIngestionError, get_logger, settings
from app.models.domain import TextChunk

# Setup logger
logger = get_logger(__name__)


def split_text(text: str, metadata: dict[str, Any] = None) -> list[TextChunk]:
    """Split a document into chunks of text."""
    try:
        # Simple text splitting by character count
        chunks = []
        for i in range(0, len(text), settings.CHUNK_SIZE):
            chunk_text = text[i : i + settings.CHUNK_SIZE]
            chunk_metadata = {
                **(metadata or {}),
                "start_char": i,
                "end_char": min(i + settings.CHUNK_SIZE, len(text)),
            }
            chunks.append(TextChunk(text=chunk_text, metadata=chunk_metadata))

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Failed to split text: {str(e)}")
        raise DocumentIngestionError(f"Failed to split text: {str(e)}")


def load_document(
    content: str, filename: str, metadata: dict[str, Any] = None
) -> list[TextChunk]:
    """Load a document and split it into chunks."""
    try:
        logger.info(f"Loading document: {filename}")
        doc_metadata = {
            "filename": filename,
            "source": "user_upload",
            **(metadata or {}),
        }
        chunks = split_text(content, doc_metadata)
        logger.info(f"Loaded document into {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Failed to load document: {str(e)}")
        raise DocumentIngestionError(f"Failed to load document: {str(e)}")
