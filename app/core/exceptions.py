class BaseAppException(Exception):
    """Base exception for all application exceptions."""

    status_code = 500


class DocumentIngestionError(BaseAppException):
    """Raised when document ingestion fails."""

    status_code = 422


class EmbeddingError(BaseAppException):
    """Raised when embedding generation fails."""

    status_code = 500


class QueryError(BaseAppException):
    """Raised when querying fails."""

    status_code = 500


class LLMError(BaseAppException):
    """Raised when LLM operations fail."""

    status_code = 500
