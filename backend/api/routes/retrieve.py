from fastapi import APIRouter, HTTPException
from api.schemas.rag import RetrieveRequest, RetrieveResponse, RetrievedDocument
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingGenerator
from rag.query_expansion import QueryExpander
from rag.reranker import Reranker
from rag.retriever import HybridRetriever
from utils.logger import log

router = APIRouter()

# Initialize RAG components (singleton)
_retriever = None

def get_retriever():
    """Get or initialize hybrid retriever"""
    global _retriever
    
    if _retriever is None:
        vector_store = VectorStore()
        embedding_gen = EmbeddingGenerator()
        query_expander = QueryExpander()
        reranker = Reranker()
        
        _retriever = HybridRetriever(
            vector_store=vector_store,
            embedding_generator=embedding_gen,
            query_expander=query_expander,
            reranker=reranker
        )
    
    return _retriever

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(request: RetrieveRequest) -> RetrieveResponse:
    """
    Retrieve documents using hybrid RAG system
    
    Uses ColBERT + BM25 fusion with optional HyDE expansion and reranking
    """
    try:
        retriever = get_retriever()
        
        log.info(f"Retrieving documents for query: {request.query[:80]}...")
        
        # Retrieve documents
        results = await retriever.retrieve(
            query=request.query,
            sector=request.sector,
            top_k=request.top_k,
            use_hyde=request.use_hyde,
            use_reranking=request.use_reranking
        )
        
        # Format response
        documents = []
        for result in results:
            documents.append(RetrievedDocument(
                text=result.get("text", ""),
                metadata=result.get("metadata", {}),
                score=result.get("final_score") or result.get("rrf_score", 0.0),
                source=result.get("metadata", {}).get("source", "unknown")
            ))
        
        return RetrieveResponse(
            query=request.query,
            sector=request.sector,
            documents=documents,
            total_results=len(documents)
        )
        
    except Exception as e:
        log.error(f"Retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during retrieval: {str(e)}"
        )