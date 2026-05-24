"""
Helper function for PDF-based research

This is separated to avoid circular imports
"""

from api.schemas.research_engine import ResearchRequest
from fastapi import Request, HTTPException
from utils.logger import log


async def start_research_with_pdf_flag(
    request: ResearchRequest,
    http_request: Request,
    pdf_file_path: str
):
    """
    Start research with PDF file path flag
    
    This is called after PDF ingestion to proceed with research
    """
    from asgiref.sync import sync_to_async
    from core.models import Query as QueryModel, ResearchStep as ResearchStepModel
    from research.orchestrator import ResearchOrchestrator
    from research.state import ResearchState
    from guardrails.safety_checker import safety_checker
    from utils.helpers import validate_query
    from django.utils import timezone
    import json
    
    # Safety checks
    safety_result = await safety_checker.validate_request(
        query=request.query,
        request=http_request
    )
    
    if not safety_result["allowed"]:
        status_code = 400 if safety_result.get("category") != "rate_limit" else 429
        raise HTTPException(
            status_code=status_code,
            detail=safety_result["reason"]
        )
    
    sanitized_query = safety_result["sanitized_query"]
    
    # Validation
    is_valid, error_msg = validate_query(sanitized_query)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    log.info(f"Starting PDF-based research: {sanitized_query[:80]}...")
    
    # Create query record
    query_obj = await sync_to_async(QueryModel.objects.create)(
        query_text=sanitized_query,
        sector=request.sector,
        status="researching",
        plan_type="deep"
    )
    
    start_time = timezone.now()
    
    # Initialize orchestrator
    orchestrator = ResearchOrchestrator()
    workflow = orchestrator.build_workflow()
    
    # Initialize state with PDF flag
    initial_state: ResearchState = {
        "query": sanitized_query,
        "sector": request.sector,
        "selected_questions": request.selected_questions,
        "query_id": str(query_obj.id),
        "current_step": 0,
        "total_steps": 0,
        "status": "planning",
        "research_queries": [],
        "web_search_results": [],
        "financial_data_results": [],
        "web_scraper_results": [],
        "calculator_results": [],
        "findings": [],
        "accumulated_knowledge": "",
        "intelligence_markers": {},
        "progress_updates": [],
        "report": None,
        "pdf_file_path": pdf_file_path,
        "use_pdf_only": True,  # Force PDF-only mode
        "started_at": start_time,
        "completed_at": None,
        "error": None
    }
    
    # Execute workflow
    final_state = await workflow.ainvoke(initial_state)
    
    # Save research steps
    for i, finding in enumerate(final_state.get("findings", []), 1):
        await sync_to_async(ResearchStepModel.objects.create)(
            query=query_obj,
            step_number=i,
            action=finding.get("query", "Research step"),
            source="PDF_RAG",
            query_text=finding.get("query", ""),
            finding=json.dumps(finding.get("key_insights", [])),
            raw_data=finding,
            status="completed",
            started_at=start_time,
            completed_at=timezone.now()
        )
    
    # Update query status
    completed_time = timezone.now()
    query_obj.status = "completed"
    query_obj.completed_at = completed_time
    await sync_to_async(query_obj.save)()
    
    duration = (completed_time - start_time).total_seconds()
    
    # Extract sources used
    sources_used = ["pdf_rag"]
    if final_state.get("financial_data_results"):
        sources_used.append("financial_data")
    
    log.info(f"PDF-based research completed in {duration:.2f} seconds")
    
    # Save report
    report_data = final_state.get("report", {})
    if report_data:
        from core.models import Report
        
        citations = report_data.get("citations", [])
        all_citations = report_data.get("all_citations", citations)
        if not citations:
            citations = [{"type": "pdf", "url": "", "title": "Uploaded PDF"}]
            all_citations = citations
        
        financial_calculations = report_data.get("financial_calculations", [])
        
        report_obj, created = await sync_to_async(Report.objects.update_or_create)(
            query=query_obj,
            defaults={
                "title": report_data.get("title", "Research Report"),
                "content": report_data.get("analysis", ""),
                "executive_summary": report_data.get("executive_summary", ""),
                "total_steps": final_state.get("total_steps", 0),
                "duration_seconds": duration,
                "citations": citations,
                "metadata": {
                    "key_findings": report_data.get("key_findings", []),
                    "recommendations": report_data.get("recommendations", []),
                    "financial_highlights": report_data.get("financial_highlights", []),
                    "financial_calculations": financial_calculations,
                    "sources_used": sources_used,
                    "plan_type": "deep",
                    "sections": report_data.get("sections", {}),
                    "all_citations": all_citations,
                    "pdf_file": pdf_file_path
                }
            }
        )
        log.info(f"Report saved: {report_obj.id}")
    
    from api.schemas.research_engine import ResearchResponse
    return ResearchResponse(
        query_id=str(query_obj.id),
        query=sanitized_query,
        sector=request.sector,
        plan_type="deep",
        status="completed",
        report=report_data,
        total_steps=final_state.get("total_steps", 0),
        duration_seconds=duration,
        sources_used=sources_used
    )
