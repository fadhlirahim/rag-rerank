from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    DocumentRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse
)
from app.services.rag import ingest_document, query_knowledge

app = FastAPI(
    title="RAG API",
    description="A simple RAG (Retrieval-Augmented Generation) API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: DocumentRequest):
    """Ingest a document into the knowledge base."""
    try:
        chunks_count = await ingest_document(
            content=request.content,
            filename=request.filename,
            metadata=request.metadata
        )
        return {
            "chunks_ingested": chunks_count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    """Query the knowledge base and get an answer."""
    try:
        result = await query_knowledge(
            query=request.query,
            top_k=request.top_k,
            top_n=request.top_n
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)