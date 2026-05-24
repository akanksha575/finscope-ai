from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ResearchAnalysisRequest(BaseModel):
    """Request schema for deep research analysis"""
    query: str = Field(..., min_length=3, max_length=1000, description="Research query")
    sector: Literal["IT", "Pharma", "Unknown"] = Field(..., description="Sector")
    use_rag: bool = Field(True, description="Use RAG document retrieval")
    use_web_search: bool = Field(True, description="Use web search for additional context")
    max_web_results: int = Field(5, ge=1, le=10, description="Maximum web search results")
    rag_top_k: int = Field(10, ge=1, le=20, description="Number of RAG documents to retrieve")

class ResearchSource(BaseModel):
    """Source of information used in research"""
    type: Literal["document", "web", "financial_data"] = Field(..., description="Source type")
    content: str = Field(..., description="Source content")
    url: Optional[str] = Field(None, description="URL if web source")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

class ResearchAnalysisResponse(BaseModel):
    """Response schema for deep research analysis"""
    query: str = Field(..., description="Original query")
    sector: str = Field(..., description="Sector")
    analysis: str = Field(..., description="Comprehensive research analysis")
    executive_summary: str = Field(..., description="Executive summary of findings")
    key_findings: List[str] = Field(..., description="Key findings list")
    sources: List[ResearchSource] = Field(..., description="Sources used in analysis")
    total_sources: int = Field(..., description="Total number of sources")