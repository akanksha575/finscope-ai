from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

PlanTypeLiteral = Literal["deep"]  # Only deep plans are generated
SectorLiteral = Literal["IT", "Pharma", "Unknown"]

class Plan(BaseModel):
    """Deep research plan with clarification questions."""

    type: PlanTypeLiteral = Field(..., description="Plan depth type (always 'deep')")
    steps: int = Field(..., ge=1, le=25, description="Planned number of research steps")
    questions: List[str] = Field(
        ..., description="Clarification questions to refine research scope before starting"
    )
    estimated_time: str = Field(
        ..., description="Human-readable estimate, e.g. '5 minutes'"
    )
    description: Optional[str] = Field(
        None, description="Short description of when to use this plan"
    )

class PlanRequest(BaseModel):
    """Request schema for research planning."""

    query: str = Field(
        ..., min_length=3, max_length=1000, description="User research query"
    )
    sector: SectorLiteral = Field(
        "Unknown",
        description="Sector classification from query router (IT / Pharma / Unknown)",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return " ".join(v.split())

class PlanResponse(BaseModel):
    """Response schema containing deep research plan."""

    query: str = Field(..., description="Sanitized user query")
    sector: SectorLiteral = Field(
        ..., description="Sector used for planning (IT / Pharma / Unknown)"
    )
    plan: Plan = Field(
        ..., description="Deep research plan with clarification questions"
    )

__all__ = ["Plan", "PlanRequest", "PlanResponse", "PlanTypeLiteral", "SectorLiteral"]