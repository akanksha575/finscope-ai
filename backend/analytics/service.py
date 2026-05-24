from typing import Dict, Any, List, Optional, TypedDict, Awaitable
import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from analytics.calculator import MetricsCalculator
from utils.logger import log

class DashboardData(TypedDict, total=False):
    """Type definition for dashboard data structure"""
    overview: Dict[str, Any]
    sector_distribution: Dict[str, int]
    plan_type_distribution: Dict[str, int]
    tool_usage: Dict[str, int]
    response_time_trend: List[Dict[str, Any]]
    daily_stats: List[Dict[str, Any]]
    sector_performance: Dict[str, Dict[str, Any]]
    top_queries: List[Dict[str, Any]]
    generated_at: str
    errors: Dict[str, str]  # Optional: tracks which metrics failed


class AnalyticsService:
    """Service for analytics operations"""
    
    def __init__(self):
        self.calculator = MetricsCalculator()
        log.info("Initialized AnalyticsService")
    
    async def _safe_get_metric(
        self, 
        metric_name: str, 
        metric_func: Awaitable[Any], 
        default_value: Any = None,
        errors: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Safely execute a metric calculation with error handling and optional timeout
        
        Args:
            metric_name: Name of the metric for logging
            metric_func: Async coroutine to execute
            default_value: Default value to return on error
            errors: Optional dictionary to track errors (mutated in place)
            timeout: Optional timeout in seconds (raises asyncio.TimeoutError if exceeded)
            
        Returns:
            Metric result or default value on error/timeout
        """
        try:
            if timeout is not None:
                return await asyncio.wait_for(metric_func, timeout=timeout)
            else:
                return await metric_func
        except asyncio.TimeoutError:
            error_msg = f"TimeoutError: Timeout after {timeout}s"
            log.error(f"Timeout calculating {metric_name}: {error_msg}")
            if errors is not None:
                errors[metric_name] = error_msg
            return default_value
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            log.error(f"Error calculating {metric_name}: {e}", exc_info=True)
            if errors is not None:
                errors[metric_name] = error_msg
            return default_value
    
    async def get_dashboard_data(
        self,
        days: int = 7,
        top_queries_limit: int = 10,
        metric_timeout: Optional[float] = None
    ) -> DashboardData:
        """
        Get comprehensive dashboard data
        
        Metrics are fetched in parallel for better performance.
        Individual metric failures are handled gracefully.
        
        Args:
            days: Number of days for trend/statistics calculations
            top_queries_limit: Number of top queries to return
            metric_timeout: Optional timeout in seconds per metric (default: no timeout)
            
        Returns:
            Complete dashboard data dictionary with optional errors field
        """
        # Track errors for visibility
        errors: Dict[str, str] = {}
        
        # Fetch all metrics in parallel for better performance
        overview, sector_dist, plan_dist, tool_usage, response_trend, daily_stats, sector_perf, top_queries = await asyncio.gather(
            self._safe_get_metric("overview_stats", self.calculator.get_overview_stats(), {}, errors, metric_timeout),
            self._safe_get_metric("sector_distribution", self.calculator.get_sector_distribution(), {}, errors, metric_timeout),
            self._safe_get_metric("plan_type_distribution", self.calculator.get_plan_type_distribution(), {}, errors, metric_timeout),
            self._safe_get_metric("tool_usage", self.calculator.get_tool_usage_stats(), {}, errors, metric_timeout),
            self._safe_get_metric("response_time_trend", self.calculator.get_response_time_trend(days), [], errors, metric_timeout),
            self._safe_get_metric("daily_stats", self.calculator.get_daily_stats(days), [], errors, metric_timeout),
            self._safe_get_metric("sector_performance", self.calculator.get_sector_performance(), {}, errors, metric_timeout),
            self._safe_get_metric("top_queries", self.calculator.get_top_queries(top_queries_limit), [], errors, metric_timeout)
        )
        
        result: DashboardData = {
            "overview": overview,
            "sector_distribution": sector_dist,
            "plan_type_distribution": plan_dist,
            "tool_usage": tool_usage,
            "response_time_trend": response_trend,
            "daily_stats": daily_stats,
            "sector_performance": sector_perf,
            "top_queries": top_queries,
            "generated_at": timezone.now().isoformat()
        }
        
        # Include errors if any occurred
        if errors:
            result["errors"] = errors
        
        return result
    
    async def get_metrics_summary(
        self,
        metric_timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get lightweight metrics summary (high-level stats only)
        
        Metrics are fetched in parallel for better performance.
        Individual metric failures are handled gracefully.
        
        Args:
            metric_timeout: Optional timeout in seconds per metric (default: no timeout)
        
        Returns:
            Summary metrics dictionary
        """
        # Track errors for visibility
        errors: Dict[str, str] = {}
        
        # Fetch summary metrics in parallel
        overview, sector_dist, plan_dist, tool_usage = await asyncio.gather(
            self._safe_get_metric("overview_stats", self.calculator.get_overview_stats(), {}, errors, metric_timeout),
            self._safe_get_metric("sector_distribution", self.calculator.get_sector_distribution(), {}, errors, metric_timeout),
            self._safe_get_metric("plan_type_distribution", self.calculator.get_plan_type_distribution(), {}, errors, metric_timeout),
            self._safe_get_metric("tool_usage", self.calculator.get_tool_usage_stats(), {}, errors, metric_timeout)
        )
        
        result = {
            "overview": overview,
            "sector_distribution": sector_dist,
            "plan_type_distribution": plan_dist,
            "tool_usage": tool_usage
        }
        
        # Include errors if any occurred
        if errors:
            result["errors"] = errors
        
        return result