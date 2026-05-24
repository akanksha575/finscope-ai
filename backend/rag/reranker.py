from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import CrossEncoder
from utils.logger import log
from utils.helpers import get_env

class Reranker:
    """Cross-encoder reranker for search results"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize reranker
        
        Args:
            model_name: Name of cross-encoder model
        """
        self.model_name = model_name or get_env(
            "RERANKER_MODEL",
            default="cross-encoder/ms-marco-MiniLM-L-12-v2"
        )
        
        log.info(f"Loading reranker model: {self.model_name}")
        try:
            self.model = CrossEncoder(self.model_name, max_length=512)
            log.info("Reranker model loaded successfully")
        except Exception as e:
            log.error(f"Failed to load reranker model: {e}")
            # Fallback to no reranking
            self.model = None
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents by relevance to query
        
        Args:
            query: Search query
            documents: List of document texts
            top_k: Number of top results to return
            
        Returns:
            List of reranked documents with scores
        """
        if not documents:
            return []
        
        if self.model is None:
            # No reranking available, return original order
            return [
                {"text": doc, "score": 0.5, "rank": i}
                for i, doc in enumerate(documents)
            ]
        
        try:
            # Create query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Get relevance scores
            scores = self.model.predict(pairs)
            
            # Sort by score (descending)
            scored_docs = [
                {"text": doc, "score": float(score), "rank": i}
                for i, (doc, score) in enumerate(
                    sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
                )
            ]
            
            return scored_docs[:top_k]
            
        except Exception as e:
            log.error(f"Reranking failed: {e}")
            # Return original order
            return [
                {"text": doc, "score": 0.5, "rank": i}
                for i, doc in enumerate(documents)
            ]