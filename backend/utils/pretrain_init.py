import os
import asyncio
from pathlib import Path
from utils.logger import log
from utils.helpers import get_env

async def check_and_pretrain_documents(auto_ingest: bool = False):
    """
    Check if pre-trained documents need to be ingested
    
    Args:
        auto_ingest: If True, automatically ingest documents on startup
    """
    try:
        # Check if auto-ingest is enabled
        auto_ingest_enabled = get_env("AUTO_PRETRAIN_DOCUMENTS", default="false").lower() == "true"
        
        if not auto_ingest and not auto_ingest_enabled:
            log.info("Auto pre-training disabled. Use /api/ingest/pretrain endpoint to ingest documents.")
            return
        
        log.info("Checking for pre-trained documents...")
        
        # Import pretrainer
        import sys
        scripts_path = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_path))
        
        from pretrain_documents import DocumentPretrainer
        
        pretrainer = DocumentPretrainer()
        
        # Get documents to ingest
        documents = pretrainer.get_documents_to_ingest()
        total_docs = len(documents["IT"]) + len(documents["Pharma"])
        
        if total_docs == 0:
            log.info("No documents found in data/raw_reports/ directory")
            return
        
        log.info(f"Found {total_docs} documents to potentially ingest")
        
        # Check collection stats
        stats = pretrainer.get_collection_stats()
        it_count = stats.get("IT", {}).get("document_count", 0)
        pharma_count = stats.get("Pharma", {}).get("document_count", 0)
        
        # Check which sectors need ingestion
        it_needs_ingestion = len(documents["IT"]) > 0 and it_count == 0
        pharma_needs_ingestion = len(documents["Pharma"]) > 0 and pharma_count == 0
        
        if it_needs_ingestion or pharma_needs_ingestion:
            log.info(f"Starting auto-ingestion for sectors needing documents...")
            log.info(f"IT: {len(documents['IT'])} documents found, {it_count} already ingested - {'Will ingest' if it_needs_ingestion else 'Skipping'}")
            log.info(f"Pharma: {len(documents['Pharma'])} documents found, {pharma_count} already ingested - {'Will ingest' if pharma_needs_ingestion else 'Skipping'}")
            
            # Ingest all documents (the pretrainer will skip already-ingested ones)
            results = await pretrainer.ingest_all(force=False)
            log.info(f"Auto-ingestion complete: {results['successful']} successful, {results['failed']} failed, {results['skipped']} skipped")
        else:
            if it_count > 0 or pharma_count > 0:
                log.info(f"ChromaDB already has documents (IT: {it_count}, Pharma: {pharma_count}). All sectors have documents.")
            else:
                log.info("No documents found in data/raw_reports/ directories.")
            log.info("Use /api/ingest/pretrain?force=true to re-ingest if needed.")
    
    except Exception as e:
        log.error(f"Error during pre-training check: {e}")
        import traceback
        log.error(traceback.format_exc())
        # Don't fail startup if pre-training fails
        log.warning("Continuing startup despite pre-training check failure")


def init_pretrain_on_startup():
    """
    Initialize pre-training check on startup (non-blocking)
    This should be called from api/main.py on startup
    """
    # Run in background task
    asyncio.create_task(check_and_pretrain_documents(auto_ingest=False))