from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ReportMetadata(BaseModel):
    """Report metadata (Phase 8 enhanced)"""
    duration_seconds: float
    total_steps: int
    sources_used: List[str]
    plan_type: Optional[str] = None
    sections: Optional[Dict[str, bool]] = Field(default={}, description="Required sections validation")

class ReportContent(BaseModel):
    """Report content structure (Phase 8 enhanced)"""
    title: str
    executive_summary: str
    analysis: str
    key_findings: List[str]
    recommendations: List[str]
    financial_highlights: Optional[List[str]] = Field(default=[], description="Financial highlights from calculations")
    citations: Optional[List[Dict[str, Any]]] = Field(default=[], description="Citations with URLs")
    financial_calculations: Optional[List[Dict[str, Any]]] = Field(default=[], description="Programmatic financial calculations")

class ReportResponse(BaseModel):
    """Report response schema"""
    query_id: str
    query: str
    sector: str
    status: str
    report: ReportContent
    metadata: ReportMetadata
    created_at: datetime
    updated_at: datetime

class ReportListResponse(BaseModel):
    """List of reports response"""
    reports: List[ReportResponse]
    total: int

class ReportExportRequest(BaseModel):
    """Request for report export"""
    format: Literal["pdf", "html", "markdown"] = Field(..., description="Export format")
    query_id: str = Field(..., description="Query ID of the report to export")

class ReportExportResponse(BaseModel):
    """Response for report export"""
    query_id: str
    format: str
    file_path: str
    file_url: str
    file_size: int