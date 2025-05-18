from typing import Any

from app.core import DocumentIngestionError, get_logger, settings
from app.models.domain import TextChunk

# Setup logger
logger = get_logger(__name__)


def split_text(text: str, metadata: dict[str, Any] = None) -> list[TextChunk]:
    """Split a document into chunks of text with overlap."""
    try:
        words = text.split()
        chunk_size = settings.CHUNK_SIZE  # Now represents word count, not char count
        overlap = int(chunk_size * 0.4)  # 40% overlap

        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            if i + chunk_size > len(words):
                chunk_words = words[i:]
            else:
                chunk_words = words[i:i + chunk_size]

            chunk_text = " ".join(chunk_words)

            # Calculate approximate character positions for reference
            start_char = sum(len(word) + 1 for word in words[:i]) if i > 0 else 0
            end_char = start_char + len(chunk_text)

            chunk_metadata = {
                **(metadata or {}),
                "start_char": start_char,
                "end_char": end_char,
                "start_word": i,
                "end_word": i + len(chunk_words),
            }

            chunks.append(TextChunk(text=chunk_text, metadata=chunk_metadata))

        logger.debug(f"Split text into {len(chunks)} overlapping chunks")
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
        logger.info(f"Loaded document into {len(chunks)} chunks with overlap")
        return chunks
    except Exception as e:
        logger.error(f"Failed to load document: {str(e)}")
        raise DocumentIngestionError(f"Failed to load document: {str(e)}")
