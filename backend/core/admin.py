from django.contrib import admin
from .models import Query, ResearchStep, Report

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "query_text",
        "sector",
        "status",
        "plan_type",
        "created_at",
        "updated_at",
    ]
    list_filter = ["sector", "status", "plan_type", "created_at"]
    search_fields = ["query_text", "sector"]
    readonly_fields = ["id", "created_at", "updated_at", "completed_at"]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Query Information", {
            "fields": ("id", "query_text", "sector", "confidence")
        }),
        ("Status", {
            "fields": ("status", "plan_type")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "completed_at")
        }),
    )

@admin.register(ResearchStep)
class ResearchStepAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "query",
        "step_number",
        "action",
        "source",
        "status",
        "started_at",
        "completed_at",
    ]
    list_filter = ["source", "status", "started_at"]
    search_fields = ["action", "query_text", "finding"]
    readonly_fields = ["id", "started_at", "completed_at", "duration_seconds"]
    raw_id_fields = ["query"]
    
    fieldsets = (
        ("Step Information", {
            "fields": ("id", "query", "step_number", "action", "source")
        }),
        ("Query & Finding", {
            "fields": ("query_text", "finding")
        }),
        ("Status & Timing", {
            "fields": ("status", "started_at", "completed_at", "duration_seconds")
        }),
        ("Raw Data", {
            "fields": ("raw_data",),
            "classes": ("collapse",)
        }),
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "query",
        "title",
        "total_steps",
        "duration_seconds",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["title", "executive_summary", "content"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["query"]
    
    fieldsets = (
        ("Report Information", {
            "fields": ("id", "query", "title", "executive_summary")
        }),
        ("Content", {
            "fields": ("content",)
        }),
        ("Metadata", {
            "fields": ("total_steps", "duration_seconds", "citations", "metadata")
        }),
        ("Timestamps", {
            "fields": ("created_at",)
        }),
    )