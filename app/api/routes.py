from fastapi import APIRouter, HTTPException

from app.models import (
    DeleteResponse,
    DeleteVectorsRequest,
    DocumentRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from app.services.embedding import delete_all_vectors, delete_vectors
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

@router.post("/reset", response_model=DeleteResponse)
async def reset_index():
    """Reset the vector database by deleting all vectors."""
    try:
        result = delete_all_vectors()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@router.post("/delete", response_model=DeleteResponse)
async def delete_index_vectors(request: DeleteVectorsRequest):
    """Delete specific vectors by their IDs."""
    try:
        if not request.ids:
            # If no IDs provided, delete all
            return await reset_index()

        result = delete_vectors(request.ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
