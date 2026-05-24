import os
os.environ.setdefault("CHROMA_OTEL_GRANULARITY", "none")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from typing import List, Dict, Any, Optional
from utils.logger import log
from utils.helpers import get_env

# Lazy import chromadb to avoid import errors at module load time
_chromadb = None
_Settings = None

def _get_chromadb():
    """Lazy import chromadb with telemetry disabled"""
    global _chromadb, _Settings
    
    if _chromadb is None:
        try:
            import chromadb
            from chromadb.config import Settings
            _chromadb = chromadb
            _Settings = Settings
        except ImportError as e:
            error_msg = str(e)
            if "_create_exp_backoff_generator" in error_msg or "opentelemetry" in error_msg.lower():
                raise ImportError(
                    "ChromaDB import failed due to OpenTelemetry compatibility issue.\n"
                    "Please run:\n"
                    "pip install --upgrade opentelemetry-api>=1.20.0 opentelemetry-sdk>=1.20.0 "
                    "opentelemetry-exporter-otlp-proto-grpc>=1.20.0 opentelemetry-exporter-otlp-proto-common>=1.20.0"
                ) from e
            raise
    
    return _chromadb, _Settings


class VectorStore:
    """ChromaDB vector store with sector-specific collections"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB vector store
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory or get_env(
            "CHROMA_PERSIST_DIRECTORY",
            default="./data/chromadb"
        )
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Lazy import chromadb
        chromadb, Settings = _get_chromadb()
        
        # Initialize ChromaDB client with telemetry disabled
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Sector-specific collections
        self.collections = {
            "IT": self._get_or_create_collection("it_sector_docs"),
            "Pharma": self._get_or_create_collection("pharma_sector_docs"),
        }
        
        log.info(f"Initialized VectorStore with {len(self.collections)} collections")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"description": f"Documents for {name} sector"}
            )
    
    def add_documents(
        self,
        sector: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to sector-specific collection
        
        Args:
            sector: Sector name ("IT" or "Pharma")
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of document IDs
            embeddings: Optional custom embeddings (if None, ChromaDB generates them)
        """
        if sector not in self.collections:
            raise ValueError(f"Unknown sector: {sector}")
        
        collection = self.collections[sector]
        
        # Ensure all lists have same length
        if not (len(documents) == len(metadatas) == len(ids)):
            raise ValueError("documents, metadatas, and ids must have same length")
        
        if embeddings and len(embeddings) != len(documents):
            raise ValueError("embeddings must have same length as documents")
        
        try:
            if embeddings:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            log.info(f"Added {len(documents)} documents to {sector} collection")
        except Exception as e:
            log.error(f"Error adding documents: {e}")
            raise
    
    def query(
        self,
        sector: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query documents from sector-specific collection
        
        Args:
            sector: Sector name ("IT" or "Pharma")
            query_texts: List of query texts
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dictionary with documents, metadatas, distances, ids
        """
        if sector not in self.collections:
            raise ValueError(f"Unknown sector: {sector}")
        
        collection = self.collections[sector]
        
        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            log.error(f"Error querying collection: {e}")
            raise
    
    def get_collection_info(self, sector: str) -> Dict[str, Any]:
        """Get information about a collection"""
        if sector not in self.collections:
            raise ValueError(f"Unknown sector: {sector}")
        
        collection = self.collections[sector]
        count = collection.count()
        
        return {
            "sector": sector,
            "collection_name": collection.name,
            "document_count": count,
        }
    
    def delete_documents(self, sector: str, ids: List[str]):
        """Delete documents by IDs"""
        if sector not in self.collections:
            raise ValueError(f"Unknown sector: {sector}")
        
        collection = self.collections[sector]
        collection.delete(ids=ids)
        log.info(f"Deleted {len(ids)} documents from {sector} collection")