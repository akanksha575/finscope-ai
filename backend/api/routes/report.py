import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi import Query as FastAPIQuery  # Avoid conflict with Django Query model
from asgiref.sync import sync_to_async
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
if not settings.configured:
    django.setup()

from core.models import Query, Report
from api.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportExportRequest,
    ReportExportResponse
)
from reports.exporter import ReportExporter
from utils.logger import log

router = APIRouter(tags=["reports"])

@router.get("/{query_id}", response_model=ReportResponse)
async def get_report(query_id: str):
    """
    Get a research report by query ID
    """
    try:
        query_obj = await sync_to_async(Query.objects.get)(id=query_id)
        report_obj = await sync_to_async(getattr)(query_obj, "report", None)
        
        if not report_obj:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found for query ID: {query_id}"
            )
        
        metadata = report_obj.metadata or {}
        citations = report_obj.citations or []
        all_citations = metadata.get("all_citations", citations)  # All citations for Sources panel
        
        # Phase 8: Include citations with URLs and financial calculations
        report_dict = {
            "title": report_obj.title,
            "executive_summary": report_obj.executive_summary or "",
            "analysis": report_obj.content,
            "key_findings": metadata.get("key_findings", []),
            "recommendations": metadata.get("recommendations", []),
            "financial_highlights": metadata.get("financial_highlights", []),
            "citations": citations,  # Phase 8: Filtered citations with URLs (for report)
            "all_citations": all_citations,  # All citations for Sources panel
            "financial_calculations": metadata.get("financial_calculations", []),  # Phase 8: Financial calculations
            "financial_data": metadata.get("financial_data", {}),  # Financial data for graph generation
            "images_and_graphs": metadata.get("images_and_graphs", [])  # Images and graphs
        }
        
        return ReportResponse(
            query_id=str(query_obj.id),
            query=query_obj.query_text,
            sector=query_obj.sector,
            status=query_obj.status,
            report=report_dict,
            metadata={
                "duration_seconds": report_obj.duration_seconds or 0,
                "total_steps": report_obj.total_steps,
                "sources_used": [c.get("type", "unknown") if isinstance(c, dict) else str(c) for c in citations] if citations else [],
                "plan_type": metadata.get("plan_type"),
                "sections": metadata.get("sections", {})  # Phase 8: Section validation
            },
            created_at=report_obj.created_at,
            updated_at=query_obj.updated_at
        )
        
    except HTTPException:
        # Re-raise HTTPException (like 404) without wrapping
        raise
    except Query.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail=f"Query not found: {query_id}"
        )
    except Exception as e:
        log.error(f"Error retrieving report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving report: {str(e)}"
        )

@router.get("", response_model=ReportListResponse)
async def list_reports(
    sector: Optional[str] = FastAPIQuery(None, description="Filter by sector"),
    limit: int = FastAPIQuery(20, ge=1, le=100, description="Number of reports to return"),
    offset: int = FastAPIQuery(0, ge=0, description="Offset for pagination"),
    include_in_progress: bool = FastAPIQuery(True, description="Include in-progress queries")
):
    """
    List all research reports with optional filtering
    """
    try:
        # Build query - include both completed and in-progress queries
        if include_in_progress:
            query = Query.objects.filter(status__in=["completed", "researching", "pending"])
        else:
            query = Query.objects.filter(status="completed")
        
        if sector:
            query = query.filter(sector=sector)
        
        # Get total count
        total = await sync_to_async(query.count)()
        
        # Get reports with pagination
        query = query.order_by("-created_at")[offset:offset + limit]
        queries = await sync_to_async(list)(query.select_related("report"))
        
        reports = []
        for query_obj in queries:
            report_obj = await sync_to_async(getattr)(query_obj, "report", None)
            
            # For in-progress queries without a report yet, create a placeholder response
            if not report_obj and query_obj.status in ["researching", "pending"]:
                reports.append(ReportResponse(
                    query_id=str(query_obj.id),
                    query=query_obj.query_text,
                    sector=query_obj.sector,
                    status=query_obj.status,
                    report={
                        "title": f"Research in progress: {query_obj.query_text[:50]}...",
                        "executive_summary": "Research is currently in progress...",
                        "analysis": "",
                        "key_findings": [],
                        "recommendations": [],
                        "citations": [],
                        "all_citations": [],
                        "financial_highlights": [],
                        "financial_calculations": [],
                        "financial_data": {},
                        "images_and_graphs": []
                    },
                    metadata={
                        "duration_seconds": 0,
                        "total_steps": 0,
                        "sources_used": [],
                        "plan_type": query_obj.plan_type or "deep",
                        "sections": {}
                    },
                    created_at=query_obj.created_at,
                    updated_at=query_obj.updated_at
                ))
                continue
            
            if report_obj:
                metadata = report_obj.metadata or {}
                raw_citations = report_obj.citations or []
                
                # Ensure citations are dictionaries, not strings
                citations = []
                for c in raw_citations:
                    if isinstance(c, dict):
                        citations.append(c)
                    elif isinstance(c, str):
                        # Convert string to citation dict
                        citations.append({
                            "type": c,
                            "url": "",
                            "title": c,
                            "domain": "",
                            "published_date": None
                        })
                    else:
                        # Skip invalid entries
                        continue
                
                # Convert citations to sources_used strings
                # If sources_used is in metadata, use it; otherwise extract from citations
                sources_used = metadata.get("sources_used", [])
                if not sources_used and citations:
                    # Extract source types from citations
                    sources_used = [
                        c.get("type", "unknown") if isinstance(c, dict) else str(c)
                        for c in citations
                    ]
                
                # Get all_citations from metadata
                all_citations = metadata.get("all_citations", citations)
                
                reports.append(ReportResponse(
                    query_id=str(query_obj.id),
                    query=query_obj.query_text,
                    sector=query_obj.sector,
                    status=query_obj.status,
                    report={
                        "title": report_obj.title,
                        "executive_summary": report_obj.executive_summary or "",
                        "analysis": report_obj.content,
                        "key_findings": metadata.get("key_findings", []),
                        "recommendations": metadata.get("recommendations", []),
                        "citations": citations,  # Filtered citations for report
                        "all_citations": all_citations,  # All citations for Sources panel
                        "financial_highlights": metadata.get("financial_highlights", []),
                        "financial_calculations": metadata.get("financial_calculations", []),
                        "financial_data": metadata.get("financial_data", {}),  # Financial data for graph generation
                        "images_and_graphs": metadata.get("images_and_graphs", [])  # Images and graphs
                    },
                    metadata={
                        "duration_seconds": report_obj.duration_seconds or 0,
                        "total_steps": report_obj.total_steps,
                        "sources_used": sources_used,  # List of strings
                        "plan_type": metadata.get("plan_type"),
                        "sections": metadata.get("sections", {})
                    },
                    created_at=report_obj.created_at,
                    updated_at=query_obj.updated_at
                ))
        
        return ReportListResponse(reports=reports, total=total)
        
    except Exception as e:
        log.error(f"Error listing reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing reports: {str(e)}"
        )

@router.post("/export", response_model=ReportExportResponse)
async def export_report(request: ReportExportRequest):
    """
    Export a report in the specified format (PDF, HTML, or Markdown)
    """
    try:
        # Get query and report
        query_obj = await sync_to_async(Query.objects.get)(id=request.query_id)
        report_obj = await sync_to_async(getattr)(query_obj, "report", None)
        
        if not report_obj:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found for query ID: {request.query_id}"
            )
        
        # Prepare report data
        metadata = report_obj.metadata or {}
        financial_data = metadata.get("financial_data", {})
        financial_calculations = metadata.get("financial_calculations", [])
        images_and_graphs = metadata.get("images_and_graphs", [])
        
        log.info(f"Exporting report {request.query_id}: financial_data keys={list(financial_data.keys()) if financial_data else 'none'}, calculations={len(financial_calculations)}")
        
        report_data = {
            "report": {
                "title": report_obj.title,
                "executive_summary": report_obj.executive_summary or "",
                "analysis": report_obj.content,
                "key_findings": metadata.get("key_findings", []),
                "recommendations": metadata.get("recommendations", []),
                "financial_calculations": financial_calculations,
                "financial_data": financial_data,  # Include for graph generation
                "images_and_graphs": images_and_graphs
            },
            "metadata": {
                "financial_data": financial_data  # Also in metadata for exporter
            }
        }
        
        export_metadata = {
            "duration_seconds": report_obj.duration_seconds or 0,
            "total_steps": report_obj.total_steps,
            "sources_used": report_obj.citations or [],
            "plan_type": metadata.get("plan_type"),
            "financial_data": financial_data
        }
        
        # Export using ReportExporter
        exporter = ReportExporter()
        
        if request.format == "pdf":
            file_path = exporter.export_pdf(
                report_data,
                request.query_id,
                query_obj.query_text,
                query_obj.sector,
                export_metadata
            )
        elif request.format == "html":
            file_path = exporter.export_html(
                report_data,
                request.query_id,
                query_obj.query_text,
                query_obj.sector,
                export_metadata
            )
        elif request.format == "markdown":
            file_path = exporter.export_markdown(
                report_data,
                request.query_id,
                query_obj.query_text,
                query_obj.sector,
                export_metadata
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.format}"
            )
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Generate file URL (relative path)
        file_url = f"/api/report/download/{Path(file_path).name}"
        
        return ReportExportResponse(
            query_id=request.query_id,
            format=request.format,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size
        )
        
    except Query.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail=f"Query not found: {request.query_id}"
        )
    except Exception as e:
        log.error(f"Error exporting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting report: {str(e)}"
        )

@router.get("/download/{filename}")
async def download_report(filename: str):
    """
    Download an exported report file
    """
    try:
        file_path = Path("outputs/reports") / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename}"
            )
        
        # Determine media type
        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith(".html"):
            media_type = "text/html"
        elif filename.endswith(".md"):
            media_type = "text/markdown"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )
        
    except Exception as e:
        log.error(f"Error downloading report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading report: {str(e)}"
        )

@router.get("/{query_id}/html", response_class=HTMLResponse)
async def get_report_html(query_id: str):
    """
    Get report as HTML (rendered)
    """
    try:
        query_obj = await sync_to_async(Query.objects.get)(id=query_id)
        report_obj = await sync_to_async(getattr)(query_obj, "report", None)
        
        if not report_obj:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found for query ID: {query_id}"
            )
        
        # Prepare report data
        metadata = report_obj.metadata or {}
        report_data = {
            "report": {
                "title": report_obj.title,
                "executive_summary": report_obj.executive_summary or "",
                "analysis": report_obj.content,
                "key_findings": metadata.get("key_findings", []),
                "recommendations": metadata.get("recommendations", [])
            }
        }
        
        export_metadata = {
            "duration_seconds": report_obj.duration_seconds or 0,
            "total_steps": report_obj.total_steps,
            "sources_used": report_obj.citations or [],
            "plan_type": metadata.get("plan_type")
        }
        
        # Format as HTML
        from reports.formatter import ReportFormatter
        formatter = ReportFormatter()
        html_content = formatter.format_html(
            report_data,
            query_obj.query_text,
            query_obj.sector,
            export_metadata
        )
        
        return HTMLResponse(content=html_content)
        
    except Query.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail=f"Query not found: {query_id}"
        )
    except Exception as e:
        log.error(f"Error rendering HTML report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error rendering HTML report: {str(e)}"
        )

@router.delete("/all")
async def delete_all_reports():
    """
    Delete all research reports
    Note: This route must come before /{query_id} to avoid route matching conflicts
    """
    try:
        # Get all completed queries
        queries = await sync_to_async(list)(Query.objects.filter(status="completed"))
        count = len(queries)
        
        # Delete all queries (Reports will be deleted automatically due to CASCADE)
        for query_obj in queries:
            await sync_to_async(query_obj.delete)()
        
        log.info(f"Deleted {count} reports")
        
        return {
            "message": f"Deleted {count} report(s) successfully",
            "count": count
        }
        
    except Exception as e:
        log.error(f"Error deleting all reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting all reports: {str(e)}"
        )

@router.delete("/{query_id}")
async def delete_report(query_id: str):
    """
    Delete a research report by query ID
    """
    try:
        query_obj = await sync_to_async(Query.objects.get)(id=query_id)
        
        # Delete the query (Report will be deleted automatically due to CASCADE)
        await sync_to_async(query_obj.delete)()
        
        log.info(f"Deleted report for query ID: {query_id}")
        
        return {
            "message": "Report deleted successfully",
            "query_id": query_id
        }
        
    except Query.DoesNotExist:
        raise HTTPException(
            status_code=404,
            detail=f"Query not found: {query_id}"
        )
    except Exception as e:
        log.error(f"Error deleting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting report: {str(e)}"
        )