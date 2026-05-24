from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    """Request schema for document ingestion"""
    sector: Literal["IT", "Pharma"] = Field(..., description="Sector for document")
    file_path: Optional[str] = Field(None, description="Path to document file (PDF)")
    text: Optional[str] = Field(None, description="Text content to ingest")
    source_name: Optional[str] = Field(None, description="Source document name")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

class IngestResponse(BaseModel):
    """Response schema for document ingestion"""
    success: bool = Field(..., description="Whether ingestion succeeded")
    chunks_ingested: int = Field(..., description="Number of chunks ingested")
    sector: str = Field(..., description="Sector")
    message: Optional[str] = Field(None, description="Status message")

class RetrieveRequest(BaseModel):
    """Request schema for RAG retrieval"""
    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    sector: Literal["IT", "Pharma"] = Field(..., description="Sector to search")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    use_hyde: bool = Field(True, description="Use HyDE query expansion")
    use_reranking: bool = Field(True, description="Use cross-encoder reranking")

class RetrievedDocument(BaseModel):
    """Retrieved document with metadata"""
    text: str = Field(..., description="Document text")
    metadata: dict = Field(default_factory=dict, description="Document metadata")
    score: float = Field(..., description="Relevance score")
    source: Optional[str] = Field(None, description="Source document")

class RetrieveResponse(BaseModel):
    """Response schema for RAG retrieval"""
    query: str = Field(..., description="Original query")
    sector: str = Field(..., description="Sector searched")
    documents: List[RetrievedDocument] = Field(..., description="Retrieved documents")
    total_results: int = Field(..., description="Total number of results")