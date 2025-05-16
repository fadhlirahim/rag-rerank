from fastapi import APIRouter, HTTPException

from app.models import DocumentRequest, IngestResponse, QueryRequest, QueryResponse
from app.services.rag import ingest_document, query_knowledge

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: DocumentRequest):
    """Ingest a document into the knowledge base."""
    try:
        chunks_count = await ingest_document(
            content=request.content,
            filename=request.filename,
            metadata=request.metadata,
        )
        return {"chunks_ingested": chunks_count, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    """Query the knowledge base and get an answer."""
    try:
        result = await query_knowledge(
            query=request.query, top_k=request.top_k, top_n=request.top_n
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
