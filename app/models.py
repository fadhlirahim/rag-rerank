from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DocumentRequest(BaseModel):
    content: str = Field(..., description="The content of the document to ingest")
    filename: str = Field(..., description="The filename of the document")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the document")

class IngestResponse(BaseModel):
    chunks_ingested: int = Field(..., description="Number of chunks ingested")
    status: str = Field(..., description="Status of the ingestion process")

class QueryRequest(BaseModel):
    query: str = Field(..., description="The query to search for")
    top_k: Optional[int] = Field(default=None, description="Number of documents to retrieve in the first stage")
    top_n: Optional[int] = Field(default=None, description="Number of documents to rerank in the second stage")

class SourceDocument(BaseModel):
    id: str = Field(..., description="The document ID")
    text: str = Field(..., description="The text content of the document")
    score: float = Field(..., description="The relevance score")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")

class QueryResponse(BaseModel):
    query: str = Field(..., description="The original query")
    answer: str = Field(..., description="The generated answer")
    sources: List[SourceDocument] = Field(..., description="The source documents used to generate the answer")