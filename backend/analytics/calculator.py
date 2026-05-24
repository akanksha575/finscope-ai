from typing import Dict, Any, List
from datetime import timedelta
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Count, Avg, Q
from core.models import Query, Report, ResearchStep
from utils.logger import log

class MetricsCalculator:
    """Calculates various analytics metrics"""
    
    def __init__(self):
        log.info("Initialized MetricsCalculator")
    
    async def get_overview_stats(self) -> Dict[str, Any]:
        """Get overview statistics"""
        # Total queries
        total_queries = await sync_to_async(Query.objects.count)()
        
        # Completed queries
        completed_queries = await sync_to_async(
            Query.objects.filter(status="completed").count
        )()
        
        # Failed queries
        failed_queries = await sync_to_async(
            Query.objects.filter(status="failed").count
        )()
        
        # Success rate
        success_rate = (completed_queries / total_queries * 100) if total_queries > 0 else 0
        
        # Total reports
        total_reports = await sync_to_async(Report.objects.count)()
        
        # Average response time
        avg_response_time = await sync_to_async(
            lambda: Report.objects.aggregate(
                avg_time=Avg("duration_seconds")
            )["avg_time"] or 0
        )()
        
        return {
            "total_queries": total_queries,
            "completed_queries": completed_queries,
            "failed_queries": failed_queries,
            "success_rate": round(success_rate, 2),
            "total_reports": total_reports,
            "average_response_time": round(avg_response_time, 2)
        }
    
    async def get_sector_distribution(self) -> Dict[str, int]:
        """Get query distribution by sector"""
        distribution = await sync_to_async(
            lambda: dict(
                Query.objects.values("sector")
                .annotate(count=Count("id"))
                .values_list("sector", "count")
            )
        )()
        
        return {
            "IT": distribution.get("IT", 0),
            "Pharma": distribution.get("Pharma", 0),
            "Unknown": distribution.get("Unknown", 0)
        }
    
    async def get_plan_type_distribution(self) -> Dict[str, int]:
        """Get query distribution by plan type"""
        distribution = await sync_to_async(
            lambda: dict(
                Query.objects.exclude(plan_type__isnull=True)
                .values("plan_type")
                .annotate(count=Count("id"))
                .values_list("plan_type", "count")
            )
        )()
        
        return {
            "deep": distribution.get("deep", 0)
        }
    
    async def get_tool_usage_stats(self) -> Dict[str, int]:
        """Get tool usage statistics"""
        tool_stats = await sync_to_async(
            lambda: dict(
                ResearchStep.objects.values("source")
                .annotate(count=Count("id"))
                .values_list("source", "count")
            )
        )()
        
        return {
            "web_search": tool_stats.get("Tavily", 0),
            "financial_data": tool_stats.get("yfinance", 0),
            "web_scraper": tool_stats.get("Web", 0),
            "rag": tool_stats.get("RAG", 0),
            "api": tool_stats.get("API", 0)
        }
    
    async def get_response_time_trend(
        self, 
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get response time trend over time"""
        start_date = timezone.now() - timedelta(days=days)
        
        reports = await sync_to_async(list)(
            Report.objects.filter(created_at__gte=start_date)
            .order_by("created_at")
            .values("created_at", "duration_seconds")
        )
        
        return [
            {
                "date": report["created_at"].isoformat(),
                "duration_seconds": report["duration_seconds"] or 0
            }
            for report in reports
        ]
    
    async def get_daily_stats(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get daily statistics"""
        from django.db.models.functions import TruncDate
        
        start_date = timezone.now() - timedelta(days=days)
        
        daily_stats = await sync_to_async(list)(
            Query.objects.filter(created_at__gte=start_date)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status="completed")),
                failed=Count("id", filter=Q(status="failed"))
            )
            .order_by("date")
        )
        
        return [
            {
                "date": stat["date"].isoformat() if stat["date"] else None,
                "total_queries": stat["total"],
                "completed_queries": stat["completed"],
                "failed_queries": stat["failed"]
            }
            for stat in daily_stats
        ]
    
    async def get_sector_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics by sector"""
        # Query 1: Get query counts grouped by sector (total and completed in one query)
        query_stats = await sync_to_async(list)(
            Query.objects.values("sector")
            .annotate(
                total_queries=Count("id"),
                completed_queries=Count("id", filter=Q(status="completed"))
            )
        )
        
        # Query 2: Get average response times grouped by sector
        response_times = await sync_to_async(list)(
            Report.objects.values("query__sector")
            .annotate(avg_response_time=Avg("duration_seconds"))
        )
        
        # Build response time lookup
        response_time_map = {
            item["query__sector"]: item["avg_response_time"] or 0
            for item in response_times
        }
        
        # Build performance dictionary
        performance = {}
        for stat in query_stats:
            sector = stat["sector"]
            total = stat["total_queries"]
            completed = stat["completed_queries"]
            
            performance[sector] = {
                "total_queries": total,
                "completed_queries": completed,
                "success_rate": round((completed / total * 100) if total > 0 else 0, 2),
                "avg_response_time": round(response_time_map.get(sector, 0), 2)
            }
        
        # Ensure all sectors are present (even if no data)
        for sector in ["IT", "Pharma", "Unknown"]:
            if sector not in performance:
                performance[sector] = {
                    "total_queries": 0,
                    "completed_queries": 0,
                    "success_rate": 0.0,
                    "avg_response_time": 0.0
                }
        
        return performance
    
    async def get_top_queries(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent completed queries ordered by creation date (most recent first)"""
        # Get queries with their report durations
        queries = await sync_to_async(list)(
            Query.objects.filter(status="completed")
            .select_related("report")
            .order_by("-created_at")[:limit]
            .values(
                "id",
                "query_text",
                "sector",
                "plan_type",
                "created_at",
                "report__duration_seconds"
            )
        )
        
        return [
            {
                "query_id": str(q["id"]),
                "query": q["query_text"][:100] + "..." if len(q["query_text"]) > 100 else q["query_text"],
                "sector": q["sector"],
                "plan_type": q["plan_type"],
                "created_at": q["created_at"].isoformat() if q["created_at"] else None,
                "duration_seconds": q["report__duration_seconds"] or 0
            }
            for q in queries
        ]