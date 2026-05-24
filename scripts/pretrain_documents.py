import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from rag.vector_store import VectorStore
from rag.document_processor import DocumentProcessor
from utils.logger import log
from utils.helpers import get_env

class DocumentPretrainer:
    """Automatically ingest pre-loaded documents into ChromaDB"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        chunk_size = int(get_env("CHUNK_SIZE", default="500"))
        chunk_overlap = int(get_env("CHUNK_OVERLAP", default="50"))
        self.doc_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Path to raw reports
        project_root = Path(__file__).parent.parent
        self.raw_reports_path = project_root / "data" / "raw_reports"
        
        log.info("Initialized DocumentPretrainer")
    
    def get_documents_to_ingest(self) -> Dict[str, List[Path]]:
        """
        Scan raw_reports directory for PDFs to ingest
        
        Returns:
            Dictionary mapping sector to list of PDF paths
        """
        documents = {"IT": [], "Pharma": []}
        
        if not self.raw_reports_path.exists():
            log.warning(f"Raw reports directory not found: {self.raw_reports_path}")
            return documents
        
        # Scan IT sector
        it_path = self.raw_reports_path / "it"
        if it_path.exists():
            for pdf_file in it_path.glob("*.pdf"):
                documents["IT"].append(pdf_file)
                log.info(f"Found IT document: {pdf_file.name}")
        
        # Scan Pharma sector
        pharma_path = self.raw_reports_path / "pharma"
        if pharma_path.exists():
            for pdf_file in pharma_path.glob("*.pdf"):
                documents["Pharma"].append(pdf_file)
                log.info(f"Found Pharma document: {pdf_file.name}")
        
        return documents
    
    def check_document_ingested(self, sector: str, file_name: str) -> bool:
        """
        Check if a document is already ingested by querying metadata
        
        Args:
            sector: Sector name
            file_name: Name of the PDF file
            
        Returns:
            True if document is already ingested
        """
        try:
            collection = self.vector_store.collections[sector]
            
            # Query for documents with this file_name in metadata
            results = collection.get(
                where={"file_name": {"$eq": file_name}}
            )
            
            return len(results.get("ids", [])) > 0
            
        except Exception as e:
            log.warning(f"Error checking if document {file_name} is ingested: {e}")
            # If check fails, assume not ingested to allow ingestion attempt
            return False
    
    async def ingest_document(self, file_path: Path, sector: str, force: bool = False) -> Dict[str, Any]:
        """
        Ingest a single document
        
        Args:
            file_path: Path to PDF file
            sector: Sector name ("IT" or "Pharma")
            force: If True, re-ingest even if already ingested
            
        Returns:
            Dictionary with ingestion results
        """
        file_name = file_path.stem
        
        # Check if already ingested
        if not force and self.check_document_ingested(sector, file_name):
            log.info(f"Document {file_name} already ingested, skipping (use --force to re-ingest)")
            return {
                "file": file_name,
                "status": "skipped",
                "reason": "already_ingested",
                "chunks": 0
            }
        
        try:
            log.info(f"Processing {file_name} for {sector} sector...")
            
            # Process PDF
            max_pages = int(get_env("PDF_MAX_PAGES", default="0")) or None
            chunks = await asyncio.get_event_loop().run_in_executor(
                None,
                self.doc_processor.process_pdf,
                str(file_path),
                max_pages
            )
            
            if not chunks:
                log.warning(f"No chunks extracted from {file_name}")
                return {
                    "file": file_name,
                    "status": "failed",
                    "reason": "no_chunks",
                    "chunks": 0
                }
            
            # Prepare documents for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            import uuid
            for chunk in chunks:
                chunk_id = f"{sector}_{file_name}_{uuid.uuid4()}"
                ids.append(chunk_id)
                documents.append(chunk["text"])
                
                # Enhanced metadata
                metadata = chunk["metadata"].copy()
                metadata.update({
                    "sector": sector,
                    "file_name": file_name,
                    "file_path": str(file_path),
                    "ingestion_type": "pretrained"
                })
                metadatas.append(metadata)
            
            # Add to ChromaDB
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.vector_store.add_documents,
                sector,
                documents,
                metadatas,
                ids
            )
            
            log.info(f"✓ Successfully ingested {file_name}: {len(chunks)} chunks")
            
            return {
                "file": file_name,
                "status": "success",
                "chunks": len(chunks),
                "sector": sector
            }
            
        except Exception as e:
            log.error(f"Error ingesting {file_name}: {e}")
            import traceback
            log.error(traceback.format_exc())
            return {
                "file": file_name,
                "status": "failed",
                "reason": str(e),
                "chunks": 0
            }
    
    async def ingest_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Ingest all documents from raw_reports directory
        
        Args:
            force: If True, re-ingest even if already ingested
            
        Returns:
            Dictionary with ingestion summary
        """
        documents = self.get_documents_to_ingest()
        
        results = {
            "IT": [],
            "Pharma": [],
            "total_files": 0,
            "total_chunks": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # Ingest IT documents
        log.info(f"Processing {len(documents['IT'])} IT sector documents...")
        for pdf_path in documents["IT"]:
            result = await self.ingest_document(pdf_path, "IT", force=force)
            results["IT"].append(result)
            results["total_files"] += 1
            
            if result["status"] == "success":
                results["successful"] += 1
                results["total_chunks"] += result["chunks"]
            elif result["status"] == "failed":
                results["failed"] += 1
            elif result["status"] == "skipped":
                results["skipped"] += 1
        
        # Ingest Pharma documents
        log.info(f"Processing {len(documents['Pharma'])} Pharma sector documents...")
        for pdf_path in documents["Pharma"]:
            result = await self.ingest_document(pdf_path, "Pharma", force=force)
            results["Pharma"].append(result)
            results["total_files"] += 1
            
            if result["status"] == "success":
                results["successful"] += 1
                results["total_chunks"] += result["chunks"]
            elif result["status"] == "failed":
                results["failed"] += 1
            elif result["status"] == "skipped":
                results["skipped"] += 1
        
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested documents"""
        stats = {}
        
        for sector in ["IT", "Pharma"]:
            try:
                info = self.vector_store.get_collection_info(sector)
                stats[sector] = info
            except Exception as e:
                log.error(f"Error getting stats for {sector}: {e}")
                stats[sector] = {"error": str(e)}
        
        return stats


async def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pre-train documents for RAG system")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest documents even if already ingested"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics only"
    )
    
    args = parser.parse_args()
    
    pretrainer = DocumentPretrainer()
    
    if args.stats:
        # Show statistics only
        stats = pretrainer.get_collection_stats()
        print("\n=== ChromaDB Collection Statistics ===")
        for sector, info in stats.items():
            if "error" not in info:
                print(f"\n{sector} Sector:")
                print(f"  Collection: {info['collection_name']}")
                print(f"  Documents: {info['document_count']}")
            else:
                print(f"\n{sector} Sector: Error - {info['error']}")
        return
    
    # Ingest documents
    print("🚀 Starting document pre-training...")
    print(f"📁 Scanning: {pretrainer.raw_reports_path}")
    
    results = await pretrainer.ingest_all(force=args.force)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Pre-training Summary")
    print("="*60)
    print(f"Total files processed: {results['total_files']}")
    print(f"✓ Successful: {results['successful']}")
    print(f"✗ Failed: {results['failed']}")
    print(f"⊘ Skipped: {results['skipped']}")
    print(f"Total chunks ingested: {results['total_chunks']}")
    
    print("\n📋 Detailed Results:")
    for sector in ["IT", "Pharma"]:
        print(f"\n{sector} Sector:")
        for result in results[sector]:
            status_icon = "✓" if result["status"] == "success" else "✗" if result["status"] == "failed" else "⊘"
            print(f"  {status_icon} {result['file']}: {result.get('chunks', 0)} chunks")
            if result["status"] == "failed":
                print(f"     Error: {result.get('reason', 'Unknown')}")
    
    # Show final stats
    print("\n" + "="*60)
    print("📈 Final Collection Statistics")
    print("="*60)
    stats = pretrainer.get_collection_stats()
    for sector, info in stats.items():
        if "error" not in info:
            print(f"{sector}: {info['document_count']} documents")
    
    print("\n✅ Pre-training complete!")


if __name__ == "__main__":
    asyncio.run(main())