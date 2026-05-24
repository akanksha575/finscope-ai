from fastapi import APIRouter, HTTPException, Query as FastAPIQuery
from typing import Optional
from analytics.service import AnalyticsService
from api.schemas.analytics import (
    DashboardResponse,
    MetricsSummaryResponse
)
from utils.logger import log

router = APIRouter(tags=["analytics"])

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    days: int = FastAPIQuery(7, ge=1, le=30, description="Number of days to include")
):
    """
    Get comprehensive analytics dashboard data
    """
    try:
        service = AnalyticsService()
        dashboard_data = await service.get_dashboard_data(days=days)
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        log.error(f"Error generating dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating dashboard: {str(e)}"
        )

@router.get("/metrics", response_model=MetricsSummaryResponse)
async def get_metrics():
    """
    Get metrics summary
    """
    try:
        service = AnalyticsService()
        metrics = await service.get_metrics_summary()
        
        return MetricsSummaryResponse(**metrics)
        
    except Exception as e:
        log.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metrics: {str(e)}"
        )

@router.get("/overview")
async def get_overview():
    """
    Get overview statistics
    """
    try:
        service = AnalyticsService()
        overview = await service.calculator.get_overview_stats()
        
        return overview
        
    except Exception as e:
        log.error(f"Error getting overview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting overview: {str(e)}"
        )

@router.get("/sectors")
async def get_sector_distribution():
    """
    Get query distribution by sector
    """
    try:
        service = AnalyticsService()
        distribution = await service.calculator.get_sector_distribution()
        
        return distribution
        
    except Exception as e:
        log.error(f"Error getting sector distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sector distribution: {str(e)}"
        )

@router.get("/plan-types")
async def get_plan_type_distribution():
    """
    Get query distribution by plan type
    """
    try:
        service = AnalyticsService()
        distribution = await service.calculator.get_plan_type_distribution()
        
        return distribution
        
    except Exception as e:
        log.error(f"Error getting plan type distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting plan type distribution: {str(e)}"
        )

@router.get("/tools")
async def get_tool_usage():
    """
    Get tool usage statistics
    """
    try:
        service = AnalyticsService()
        tool_usage = await service.calculator.get_tool_usage_stats()
        
        return tool_usage
        
    except Exception as e:
        log.error(f"Error getting tool usage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting tool usage: {str(e)}"
        )

@router.get("/response-time")
async def get_response_time_trend(
    days: int = FastAPIQuery(7, ge=1, le=30, description="Number of days")
):
    """
    Get response time trend over time
    """
    try:
        service = AnalyticsService()
        trend = await service.calculator.get_response_time_trend(days=days)
        
        return {"trend": trend, "days": days}
        
    except Exception as e:
        log.error(f"Error getting response time trend: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting response time trend: {str(e)}"
        )

@router.get("/daily")
async def get_daily_stats(
    days: int = FastAPIQuery(7, ge=1, le=30, description="Number of days")
):
    """
    Get daily statistics
    """
    try:
        service = AnalyticsService()
        daily_stats = await service.calculator.get_daily_stats(days=days)
        
        return {"daily_stats": daily_stats, "days": days}
        
    except Exception as e:
        log.error(f"Error getting daily stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting daily stats: {str(e)}"
        )

@router.get("/sector-performance")
async def get_sector_performance():
    """
    Get performance metrics by sector
    """
    try:
        service = AnalyticsService()
        performance = await service.calculator.get_sector_performance()
        
        return performance
        
    except Exception as e:
        log.error(f"Error getting sector performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sector performance: {str(e)}"
        )

@router.get("/top-queries")
async def get_top_queries(
    limit: int = FastAPIQuery(10, ge=1, le=50, description="Number of queries to return")
):
    """
    Get top queries by various metrics
    """
    try:
        service = AnalyticsService()
        top_queries = await service.calculator.get_top_queries(limit=limit)
        
        return {"queries": top_queries, "limit": limit}
        
    except Exception as e:
        log.error(f"Error getting top queries: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting top queries: {str(e)}"
        )