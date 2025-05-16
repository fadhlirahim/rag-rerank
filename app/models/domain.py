import uuid
from typing import Any


class TextChunk:
    """Represents a chunk of text with metadata."""

    def __init__(self, text: str, metadata: dict[str, Any] = None, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.text = text
        self.metadata = metadata or {}
