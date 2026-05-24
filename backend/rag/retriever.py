from typing import List, Dict, Any, Optional
from collections import defaultdict
import asyncio
import numpy as np
from rank_bm25 import BM25Okapi
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingGenerator
from rag.query_expansion import QueryExpander
from rag.reranker import Reranker
from utils.logger import log

class HybridRetriever:
    """Hybrid retrieval system combining neural (dense vector) and BM25 (lexical) retrieval"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
        query_expander: Optional[QueryExpander] = None,
        reranker: Optional[Reranker] = None
    ):
        """
        Initialize hybrid retriever
        
        Args:
            vector_store: ChromaDB vector store
            embedding_generator: Embedding generator for neural retrieval
            query_expander: Optional query expander (HyDE)
            reranker: Optional cross-encoder reranker
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.query_expander = query_expander
        self.reranker = reranker
        
        # BM25 indices per sector (built on-demand)
        self.bm25_indices = {}
        self.sector_documents = {}
        
        log.info("Initialized HybridRetriever")
    
    async def retrieve(
        self,
        query: str,
        sector: str,
        top_k: int = 5,
        use_hyde: bool = True,
        use_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using hybrid neural (dense vector) + BM25 approach
        
        Args:
            query: Search query
            sector: Sector name ("IT" or "Pharma")
            top_k: Number of results to return
            use_hyde: Whether to use HyDE query expansion
            use_reranking: Whether to use cross-encoder reranking
            
        Returns:
            List of retrieved documents with scores and metadata
        """
        try:
            # Step 1: Query expansion (HyDE)
            search_query = query
            if use_hyde and self.query_expander:
                search_query = await self.query_expander.expand_query(query, sector)
            
            # Step 2 & 3: Parallel retrieval (neural + lexical)
            # Execute both retrievals concurrently for better performance
            neural_results, bm25_results = await asyncio.gather(
                self._neural_retrieve(search_query, sector, top_k * 2),
                self._bm25_retrieve(query, sector, top_k * 2)
            )
            
            # Step 4: Reciprocal Rank Fusion (RRF)
            fused_results = self._reciprocal_rank_fusion(
                neural_results,
                bm25_results,
                top_k * 2
            )
            
            # Step 5: Reranking (optional)
            if use_reranking and self.reranker and fused_results:
                reranked = self.reranker.rerank(
                    query=query,
                    documents=[r["text"] for r in fused_results],
                    top_k=top_k
                )
                
                # Merge reranking scores with fused results
                for i, rerank_item in enumerate(reranked):
                    if i < len(fused_results):
                        fused_results[i]["rerank_score"] = rerank_item["score"]
                        fused_results[i]["final_score"] = (
                            fused_results[i].get("rrf_score", 0) * 0.5 +
                            rerank_item["score"] * 0.5
                        )
                
                # Re-sort by final score
                fused_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
            
            return fused_results[:top_k]
            
        except Exception as e:
            log.error(f"Retrieval failed: {e}")
            return []
    
    async def _neural_retrieve(
        self,
        query: str,
        sector: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve using dense vector embeddings (ChromaDB with sentence-transformers)"""
        try:
            # Query ChromaDB using query text
            # ChromaDB will generate embeddings internally using its default embedding function
            # This works fine for our use case
            results = self.vector_store.query(
                sector=sector,
                query_texts=[query],
                n_results=top_k
            )
            
            # Format results
            retrieved = []
            if results.get("documents") and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                ids = results.get("ids", [[]])[0]
                
                for i in range(len(documents)):
                    doc = documents[i]
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    doc_id = ids[i] if i < len(ids) else f"doc_{i}"
                    
                    # Convert distance to similarity score
                    # ChromaDB uses cosine distance (0-2 range), convert to similarity (0-1)
                    similarity = max(0.0, 1.0 - (distance / 2.0))
                    
                    retrieved.append({
                        "text": doc,
                        "metadata": metadata,
                        "id": doc_id,
                        "neural_score": similarity,
                        "neural_rank": i + 1,
                    })
            
            return retrieved
            
        except Exception as e:
            log.error(f"Neural retrieval failed: {e}")
            return []
    
    async def _bm25_retrieve(
        self,
        query: str,
        sector: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Retrieve using BM25 lexical matching"""
        try:
            # Build BM25 index if not exists
            if sector not in self.bm25_indices:
                await self._build_bm25_index(sector)
            
            if sector not in self.bm25_indices:
                return []
            
            bm25 = self.bm25_indices[sector]
            documents = self.sector_documents[sector]
            
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Get BM25 scores
            scores = bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Format results
            retrieved = []
            for rank, idx in enumerate(top_indices):
                if scores[idx] > 0:  # Only include documents with positive scores
                    retrieved.append({
                        "text": documents[idx]["text"],
                        "metadata": documents[idx]["metadata"],
                        "id": documents[idx].get("id", f"bm25_{idx}"),
                        "bm25_score": float(scores[idx]),
                        "bm25_rank": rank + 1,
                    })
            
            return retrieved
            
        except Exception as e:
            log.error(f"BM25 retrieval failed: {e}")
            return []
    
    async def _build_bm25_index(self, sector: str):
        """Build BM25 index for sector"""
        try:
            # Get all documents from ChromaDB
            # Note: ChromaDB doesn't have a direct "get all" method,
            # so we'll build index when documents are added
            # For now, we'll query with a generic query to get documents
            results = self.vector_store.query(
                sector=sector,
                query_texts=[""],
                n_results=1000  # Get up to 1000 documents
            )
            
            if results.get("documents") and results["documents"][0]:
                documents = []
                for doc, metadata, doc_id in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["ids"][0]
                ):
                    documents.append({
                        "text": doc,
                        "metadata": metadata,
                        "id": doc_id,
                    })
                
                # Tokenize documents
                tokenized_docs = [doc["text"].lower().split() for doc in documents]
                
                # Build BM25 index
                self.bm25_indices[sector] = BM25Okapi(tokenized_docs)
                self.sector_documents[sector] = documents
                
                log.info(f"Built BM25 index for {sector} with {len(documents)} documents")
            
        except Exception as e:
            log.warning(f"Failed to build BM25 index for {sector}: {e}")
    
    def _reciprocal_rank_fusion(
        self,
        neural_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int,
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF)
        
        Args:
            neural_results: Neural (dense vector) retrieval results
            bm25_results: BM25 retrieval results
            top_k: Number of results to return
            k: RRF constant (default: 60)
            
        Returns:
            Fused and sorted results
        """
        # Create document ID to result mapping
        doc_scores = defaultdict(lambda: {"rrf_score": 0.0, "data": None})
        
        # Add neural retrieval scores
        for rank, result in enumerate(neural_results):
            doc_id = result.get("id", f"neural_{rank}")
            rrf_score = 1.0 / (k + rank + 1)
            doc_scores[doc_id]["rrf_score"] += rrf_score
            if doc_scores[doc_id]["data"] is None:
                doc_scores[doc_id]["data"] = result
        
        # Add BM25 scores
        for rank, result in enumerate(bm25_results):
            doc_id = result.get("id", f"bm25_{rank}")
            rrf_score = 1.0 / (k + rank + 1)
            doc_scores[doc_id]["rrf_score"] += rrf_score
            if doc_scores[doc_id]["data"] is None:
                doc_scores[doc_id]["data"] = result
        
        # Sort by RRF score
        fused = []
        for doc_id, score_data in sorted(
            doc_scores.items(),
            key=lambda x: x[1]["rrf_score"],
            reverse=True
        ):
            result = score_data["data"].copy()
            result["rrf_score"] = score_data["rrf_score"]
            fused.append(result)
        
        return fused[:top_k]