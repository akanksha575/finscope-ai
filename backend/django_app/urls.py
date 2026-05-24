from django.contrib import admin
from django.urls import path, include
from api import views

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Root endpoint
    path("", views.root, name="root"),
    
    # Health check
    path("api/health", views.health_check, name="health"),
    
    # Classification
    path("api/classify", views.ClassifyView.as_view(), name="classify"),
    
    # Planning
    path("api/plan", views.PlanView.as_view(), name="plan"),
    
    # Research
    path("api/research/analyze", views.ResearchAnalyzeView.as_view(), name="research_analyze"),
    path("api/research/start", views.ResearchStartView.as_view(), name="research_start"),
    path("api/research/start/pdf", views.ResearchStartPDFView.as_view(), name="research_start_pdf"),
    
    # Reports
    path("api/report/<str:query_id>", views.ReportDetailView.as_view(), name="report_detail"),  # GET and DELETE
    path("api/report", views.ReportListView.as_view(), name="report_list"),
    path("api/report/<str:query_id>/export", views.ReportExportView.as_view(), name="report_export"),
    
    # RAG - Ingest
    path("api/ingest", views.IngestView.as_view(), name="ingest"),
    path("api/ingest/file", views.IngestFileUploadView.as_view(), name="ingest_file"),
    
    # RAG - Retrieve
    path("api/retrieve", views.RetrieveView.as_view(), name="retrieve"),
    
    # Analytics
    path("api/analytics/dashboard", views.AnalyticsDashboardView.as_view(), name="analytics_dashboard"),
    path("api/analytics/metrics", views.AnalyticsMetricsView.as_view(), name="analytics_metrics"),
    path("api/analytics/overview", views.AnalyticsOverviewView.as_view(), name="analytics_overview"),
    path("api/analytics/sectors", views.AnalyticsSectorsView.as_view(), name="analytics_sectors"),
    path("api/analytics/plan-types", views.AnalyticsPlanTypesView.as_view(), name="analytics_plan_types"),
    path("api/analytics/tool-usage", views.AnalyticsToolUsageView.as_view(), name="analytics_tool_usage"),
    path("api/analytics/response-time-trend", views.AnalyticsResponseTimeTrendView.as_view(), name="analytics_response_time_trend"),
    path("api/analytics/daily-stats", views.AnalyticsDailyStatsView.as_view(), name="analytics_daily_stats"),
    path("api/analytics/sector-performance", views.AnalyticsSectorPerformanceView.as_view(), name="analytics_sector_performance"),
    path("api/analytics/top-queries", views.AnalyticsTopQueriesView.as_view(), name="analytics_top_queries"),
]