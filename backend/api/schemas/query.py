from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class QueryRequest(BaseModel):
    """Request schema for query classification"""
    query: str = Field(..., min_length=3, max_length=1000, description="User research query")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitize query"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return " ".join(v.split())  # Normalize whitespace

class ClassificationResponse(BaseModel):
    """Response schema for query classification"""
    sector: Literal["IT", "Pharma", "Unknown"] = Field(..., description="Assigned sector")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: str = Field(..., description="Explanation of classification")
    decline_message: Optional[str] = Field(None, description="Message if query is out of scope")
    error: Optional[str] = Field(None, description="Error message if classification failed")