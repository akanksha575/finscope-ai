from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    """Request schema for deep research"""
    query: str = Field(..., min_length=3, max_length=1000, description="Research query")
    sector: Literal["IT", "Pharma", "Unknown"] = Field(..., description="Sector")
    selected_questions: List[str] = Field(default_factory=list, description="Selected clarification questions from the plan")
    use_rag: bool = Field(False, description="Use RAG if documents are attached (optional)")

class ResearchResponse(BaseModel):
    """Response schema for completed research"""
    query_id: str
    query: str
    sector: str
    plan_type: str
    status: str
    report: dict = Field(..., description="Generated research report")
    total_steps: int
    duration_seconds: float
    sources_used: List[str] = Field(default_factory=list)