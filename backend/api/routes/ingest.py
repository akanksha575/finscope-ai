import os
import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from api.schemas.rag import IngestRequest, IngestResponse
from rag.vector_store import VectorStore
from rag.document_processor import DocumentProcessor
from rag.embeddings import EmbeddingGenerator
from utils.logger import log
from utils.helpers import get_env

router = APIRouter()

# Initialize RAG components (singleton pattern)
_vector_store = None
_document_processor = None
_embedding_generator = None

def get_rag_components():
    """Get or initialize RAG components"""
    global _vector_store, _document_processor, _embedding_generator
    
    if _vector_store is None:
        _vector_store = VectorStore()
    
    if _document_processor is None:
        chunk_size = int(get_env("CHUNK_SIZE", default="500"))
        chunk_overlap = int(get_env("CHUNK_OVERLAP", default="50"))
        _document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    
    return _vector_store, _document_processor, _embedding_generator

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest) -> IngestResponse:
    """
    Ingest document into RAG system
    
    Supports:
    - PDF files via file_path
    - Plain text via text field
    """
    try:
        vector_store, doc_processor, embedding_gen = get_rag_components()
        
        chunks = []
        
        # Process document
        if request.file_path:
            # Process PDF file
            if not os.path.exists(request.file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
            
            log.info(f"Starting PDF processing for: {request.file_path}")
            # Get max pages from env or use default (None = all pages)
            max_pages = int(get_env("PDF_MAX_PAGES", default="0")) or None
            
            # Run PDF processing in executor to avoid blocking
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None,
                doc_processor.process_pdf,
                request.file_path,
                max_pages
            )
            log.info(f"PDF processing completed, extracted {len(chunks)} chunks")
            source_name = request.source_name or Path(request.file_path).stem
            
        elif request.text:
            # Process text
            chunks = doc_processor.process_text(
                request.text,
                source=request.source_name or "text_input"
            )
            source_name = request.source_name or "text_input"
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or text must be provided"
            )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No content extracted from document"
            )
        
        # Generate embeddings and prepare for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            documents.append(chunk["text"])
            
            # Merge chunk metadata with request metadata
            metadata = chunk["metadata"].copy()
            metadata.update(request.metadata)
            metadata["source_name"] = source_name
            metadatas.append(metadata)
        
        # Generate embeddings for custom embedding support
        log.info(f"Adding {len(chunks)} chunks to ChromaDB collection for {request.sector} sector")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            vector_store.add_documents,
            request.sector,
            documents,
            metadatas,
            ids
        )
        
        log.info(f"Successfully ingested {len(chunks)} chunks for {request.sector} sector")
        
        return IngestResponse(
            success=True,
            chunks_ingested=len(chunks),
            sector=request.sector,
            message=f"Successfully ingested {len(chunks)} chunks from {source_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Document ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during ingestion: {str(e)}"
        )

@router.post("/ingest/file")
async def ingest_file_upload(
    file: UploadFile = File(...),
    sector: str = "IT"
):
    """Ingest document from file upload"""
    try:
        if sector not in ["IT", "Pharma"]:
            raise HTTPException(status_code=400, detail="Sector must be IT or Pharma")
        
        log.info(f"Received file upload: {file.filename}, sector: {sector}")
        
        # Save uploaded file temporarily
        upload_dir = Path("./data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        
        log.info(f"Saving uploaded file to: {file_path}")
        # Read file content asynchronously
        content = await file.read()
        file_size = len(content)
        log.info(f"File size: {file_size} bytes")
        
        # Write file in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_bytes(content)
        )
        
        log.info(f"File saved, starting ingestion process")
        
        # Process using ingest endpoint logic
        request = IngestRequest(
            sector=sector,
            file_path=str(file_path),
            source_name=file.filename
        )
        
        return await ingest_document(request)
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"File upload ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/ingest/pretrain")
async def pretrain_documents(force: bool = False):
    """
    Pre-train documents from data/raw_reports/ directory
    
    This endpoint automatically ingests all PDFs from:
    - data/raw_reports/it/ → IT sector collection
    - data/raw_reports/pharma/ → Pharma sector collection
    
    Args:
        force: If True, re-ingest even if already ingested
    
    Returns:
        Summary of pre-training results
    """
    try:
        # Import pretrainer (using relative path from backend)
        import sys
        from pathlib import Path
        
        scripts_path = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        from pretrain_documents import DocumentPretrainer
        
        log.info("Starting document pre-training via API...")
        
        pretrainer = DocumentPretrainer()
        results = await pretrainer.ingest_all(force=force)
        
        # Get final stats
        stats = pretrainer.get_collection_stats()
        
        return {
            "success": True,
            "message": "Pre-training completed",
            "summary": {
                "total_files": results["total_files"],
                "successful": results["successful"],
                "failed": results["failed"],
                "skipped": results["skipped"],
                "total_chunks": results["total_chunks"]
            },
            "results": {
                "IT": results["IT"],
                "Pharma": results["Pharma"]
            },
            "collection_stats": stats
        }
        
    except Exception as e:
        log.error(f"Pre-training failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Pre-training failed: {str(e)}"
        )

@router.get("/ingest/stats")
async def get_ingestion_stats():
    """
    Get statistics about ingested documents in ChromaDB collections
    
    Returns:
        Statistics for each sector collection
    """
    try:
        vector_store, _, _ = get_rag_components()
        
        stats = {}
        for sector in ["IT", "Pharma"]:
            try:
                info = vector_store.get_collection_info(sector)
                stats[sector] = info
            except Exception as e:
                log.error(f"Error getting stats for {sector}: {e}")
                stats[sector] = {"error": str(e)}
        
        return {
            "success": True,
            "collections": stats
        }
        
    except Exception as e:
        log.error(f"Error getting ingestion stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )