from typing import List, Dict, Any
import uuid
from app.config import CHUNK_SIZE

class TextChunk:
    def __init__(self, text: str, metadata: Dict[str, Any] = None, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.text = text
        self.metadata = metadata or {}

def split_text(text: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
    """Split a document into chunks of text."""
    # Simple text splitting by character count
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE):
        chunk_text = text[i:i + CHUNK_SIZE]
        chunk_metadata = {
            **(metadata or {}),
            "start_char": i,
            "end_char": min(i + CHUNK_SIZE, len(text)),
        }
        chunks.append(TextChunk(text=chunk_text, metadata=chunk_metadata))
    return chunks

def load_document(content: str, filename: str, metadata: Dict[str, Any] = None) -> List[TextChunk]:
    """Load a document and split it into chunks."""
    doc_metadata = {
        "filename": filename,
        "source": "user_upload",
        **(metadata or {})
    }
    return split_text(content, doc_metadata)