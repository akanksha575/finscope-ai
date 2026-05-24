from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class OverviewStats(BaseModel):
    """Overview statistics"""
    total_queries: int
    completed_queries: int
    failed_queries: int
    success_rate: float
    total_reports: int
    average_response_time: float

class SectorDistribution(BaseModel):
    """Sector distribution"""
    IT: int
    Pharma: int
    Unknown: int

class PlanTypeDistribution(BaseModel):
    """Plan type distribution"""
    quick: int
    standard: int
    deep: int

class ToolUsage(BaseModel):
    """Tool usage statistics"""
    web_search: int
    financial_data: int
    web_scraper: int
    rag: int
    api: int

class ResponseTimePoint(BaseModel):
    """Response time data point"""
    date: str
    duration_seconds: float

class DailyStats(BaseModel):
    """Daily statistics"""
    date: Optional[str]
    total_queries: int
    completed_queries: int
    failed_queries: int

class SectorPerformance(BaseModel):
    """Sector performance metrics"""
    total_queries: int
    completed_queries: int
    success_rate: float
    avg_response_time: float

class TopQuery(BaseModel):
    """Top query information"""
    query_id: str
    query: str
    sector: str
    plan_type: Optional[str]
    created_at: Optional[str]
    duration_seconds: float

class DashboardResponse(BaseModel):
    """Complete dashboard data"""
    overview: OverviewStats
    sector_distribution: SectorDistribution
    plan_type_distribution: PlanTypeDistribution
    tool_usage: ToolUsage
    response_time_trend: List[ResponseTimePoint]
    daily_stats: List[DailyStats]
    sector_performance: Dict[str, SectorPerformance]
    top_queries: List[TopQuery]
    generated_at: str

class MetricsSummaryResponse(BaseModel):
    """Metrics summary response"""
    overview: OverviewStats
    sector_distribution: SectorDistribution
    plan_type_distribution: PlanTypeDistribution
    tool_usage: ToolUsage