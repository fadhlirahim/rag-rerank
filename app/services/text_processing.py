from typing import Any
import re
from app.core import DocumentIngestionError, get_logger, settings
from app.models.domain import TextChunk

# Setup logger
logger = get_logger(__name__)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving paragraph structure."""
    # Simple sentence splitting - can be enhanced with nltk or spacy if available
    # This pattern matches sentence boundaries while preserving paragraph breaks
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]


def split_text(text: str, metadata: dict[str, Any] = None) -> list[TextChunk]:
    """Split a document into chunks of text with overlap based on sentences."""
    try:
        # Split the text into sentences
        sentences = split_into_sentences(text)

        # Use configured chunk size and overlap
        chunk_size = settings.CHUNK_SIZE  # Now represents approximate token count
        chunk_overlap = settings.CHUNK_OVERLAP

        chunks = []
        current_chunk = []
        current_size = 0
        current_start_char = 0

        for sentence in sentences:
            # Approximate token count as words / 0.75 (avg tokens per word)
            sentence_size = len(sentence.split()) / 0.75

            # If adding this sentence would exceed chunk size and we have content,
            # create a chunk and start a new one with overlap
            if current_size + sentence_size > chunk_size and current_chunk:
                # Join sentences into a single text
                chunk_text = " ".join(current_chunk)
                end_char = current_start_char + len(chunk_text)

                chunk_metadata = {
                    **(metadata or {}),
                    "start_char": current_start_char,
                    "end_char": end_char,
                }

                # Store the chunk
                chunks.append(TextChunk(text=chunk_text, metadata=chunk_metadata))

                # Handle overlap for next chunk - keep sentences that fit within overlap
                overlap_size = 0
                overlap_sentences = []

                # Work backwards through current chunk to find sentences for overlap
                for s in reversed(current_chunk):
                    s_size = len(s.split()) / 0.75
                    if overlap_size + s_size <= chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += s_size
                    else:
                        break

                # Start new chunk with overlap sentences
                current_chunk = overlap_sentences
                current_size = overlap_size
                # Calculate new start position
                current_start_char = end_char - len(" ".join(overlap_sentences))
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_size += sentence_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            end_char = current_start_char + len(chunk_text)

            chunk_metadata = {
                **(metadata or {}),
                "start_char": current_start_char,
                "end_char": end_char,
            }

            chunks.append(TextChunk(text=chunk_text, metadata=chunk_metadata))

        logger.debug(f"Split text into {len(chunks)} overlapping chunks based on sentences")
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

        # Debug metadata for troubleshooting
        if metadata:
            logger.debug(f"Document metadata: {metadata}")
        else:
            logger.debug("No metadata provided for document")

        # Determine document type for custom chunking strategies
        # Check metadata for genre first, then fallback to filename heuristic
        is_fiction = False
        fiction_source = None

        if metadata:
            # Check if genre is explicitly set to 'fiction'
            if metadata.get("genre") == "fiction":
                is_fiction = True
                fiction_source = "genre"
                logger.info(f"Document {filename} identified as fiction from genre metadata")
            # Also check category for backward compatibility
            elif metadata.get("category") == "fiction":
                is_fiction = True
                fiction_source = "category"
                logger.info(f"Document {filename} identified as fiction from category metadata")

        # Fallback to filename extension heuristic if not determined from metadata
        if not is_fiction and filename.endswith((".md", ".txt")):
            # This is just a fallback - metadata should be the primary source
            logger.info(f"Document {filename} has fiction-compatible extension, but not marked as fiction")

        doc_metadata = {
            "filename": filename,
            "source": "user_upload",
            "is_fiction": is_fiction,
            "fiction_source": fiction_source,
            **(metadata or {}),
        }

        chunks = split_text(content, doc_metadata)
        logger.info(f"Loaded document into {len(chunks)} chunks with overlap. Fiction: {is_fiction}")
        return chunks
    except Exception as e:
        logger.error(f"Failed to load document: {str(e)}")
        raise DocumentIngestionError(f"Failed to load document: {str(e)}")
