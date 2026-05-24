"""
WebSocket consumers for real-time research updates
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from utils.logger import log
from guardrails.safety_checker import safety_checker
from utils.helpers import validate_query, sanitize_query
from core.models import Query, ResearchStep
from research.orchestrator import ResearchOrchestrator
from research.state import ResearchState
from reports.synthesizer import ReportSynthesizer
from utils.cache import get_cache_manager, generate_cache_key, CACHE_TTL


class ResearchStreamConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time research progress streaming"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orchestrator = None  # Store orchestrator instance
    
    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        log.info("WebSocket research connection accepted")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        log.info(f"WebSocket research disconnected: {close_code}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            query = data.get("query")
            sector = data.get("sector", "Unknown")
            selected_questions = data.get("selected_questions", [])
            
            if not query:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "error": "Query is required"
                }))
                await self.close()
                return
            
            # Safety checks
            class MockRequest:
                def __init__(self, client_host):
                    self.client = type('obj', (object,), {'host': client_host})()
                    self.headers = {}
            
            client_ip = self.scope.get("client", [None, None])[0] or "websocket"
            mock_request = MockRequest(client_ip)
            
            safety_result = await safety_checker.validate_request(
                query=query,
                request=mock_request
            )
            
            if not safety_result["allowed"]:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "error": safety_result["reason"],
                    "category": safety_result.get("category", "validation_error")
                }))
                await self.close()
                return
            
            sanitized_query = safety_result["sanitized_query"]
            
            # Validate query
            is_valid, error_msg = validate_query(sanitized_query)
            if not is_valid:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "error": error_msg
                }))
                await self.close()
                return
            
            log.info(f"WebSocket research started: {sanitized_query[:80]}...")
            
            # Send initial status
            await self.send(text_data=json.dumps({
                "type": "status",
                "status": "planning",
                "message": "Starting research workflow...",
                "progress": 0.0,
                "timestamp": timezone.now().isoformat()
            }))
            
            # Start research workflow
            await self._run_research_workflow(sanitized_query, sector, selected_questions)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            log.error(f"WebSocket research error: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": str(e)
            }))
            await self.close()
    
    async def _run_research_workflow(
        self,
        query: str,
        sector: str,
        selected_questions: list
    ):
        """Run the research workflow and stream updates"""
        try:
            # Create query record
            query_obj = await sync_to_async(Query.objects.create)(
                query_text=query,
                sector=sector,
                status="researching",
                plan_type="deep"
            )
            
            start_time = timezone.now()
            
            # Initialize orchestrator
            orchestrator = ResearchOrchestrator()
            self._orchestrator = orchestrator  # Store for later use
            workflow = orchestrator.build_workflow()
            
            # Initialize state
            initial_state: ResearchState = {
                "query": query,
                "sector": sector,
                "selected_questions": selected_questions,
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
                "pdf_file_path": None,
                "use_pdf_only": False,
                "started_at": start_time,
                "completed_at": None,
                "error": None
            }
            
            # Execute workflow with streaming (with increased recursion limit)
            try:
                # Try with config first (for newer LangGraph versions)
                config = {"recursion_limit": 50}
                workflow_stream = workflow.astream(initial_state, config=config)
            except (KeyError, TypeError, ValueError) as e:
                # LangGraph might not support config or uses different format
                if "configurable" in str(e) or "config" in str(e).lower():
                    log.warning(f"Config not supported in this LangGraph version, using defaults: {e}")
                    workflow_stream = workflow.astream(initial_state)
                else:
                    raise
            except (ImportError, AttributeError) as e:
                if "CheckpointAt" in str(e) or "checkpoint" in str(e).lower():
                    # Fallback: try without config (uses default recursion limit)
                    log.warning(f"Checkpoint error detected, using default config: {e}")
                    workflow_stream = workflow.astream(initial_state)
                else:
                    raise
            
            final_state = initial_state
            recursion_error_occurred = False
            sent_progress_updates = 0  # Track how many updates we've sent
            last_progress = 0.0
            last_status = "planning"
            
            def calculate_overall_progress(status: str, current_step: int, total_steps: int, findings_count: int) -> float:
                """Calculate overall progress (0-1) based on workflow stage"""
                nonlocal last_progress, last_status
                
                if status == "planning":
                    progress = 0.05
                elif status == "researching":
                    max_expected_steps = max(1, total_steps or 25)
                    research_progress = min(findings_count / max_expected_steps, 1.0)
                    progress = 0.1 + (research_progress * 0.8)
                elif status == "synthesizing":
                    progress = 0.95
                elif status == "completed":
                    progress = 1.0
                else:
                    progress = last_progress
                
                if status == last_status or status == "researching":
                    progress = max(progress, last_progress)
                
                last_progress = progress
                last_status = status
                return progress
            
            try:
                async for state_update in workflow_stream:
                    # Update final state
                    for node_name, node_state in state_update.items():
                        filtered_state = {k: v for k, v in node_state.items() 
                                         if k in ResearchState.__annotations__}
                        final_state.update(filtered_state)
                    
                    # Handle different node types and send appropriate updates
                    for node_name, node_state in state_update.items():
                        if node_name == "plan_queries":
                            # Planning phase
                            research_queries = node_state.get("research_queries", [])
                            overall_progress = calculate_overall_progress("planning", 0, 0, 0)
                            await self.send(text_data=json.dumps({
                                "type": "progress",
                                "status": "planning",
                                "message": f"Generated {len(research_queries)} research queries",
                                "queries": research_queries,
                                "progress": float(overall_progress),
                                "timestamp": timezone.now().isoformat()
                            }))
                        
                        elif node_name == "execute_research":
                            # Research phase - send detailed progress updates
                            progress_updates = node_state.get("progress_updates", [])
                            findings = node_state.get("findings", [])
                            current_step = node_state.get("current_step", 0)
                            total_steps = node_state.get("total_steps", 25)
                            
                            # Calculate overall progress
                            overall_progress = calculate_overall_progress("researching", current_step, total_steps, len(findings))
                            
                            # Send only NEW progress updates to avoid duplicates
                            new_updates = progress_updates[sent_progress_updates:]
                            sent_progress_updates = len(progress_updates)
                            
                            for update in new_updates:
                                # Ensure update is a dict
                                if isinstance(update, dict):
                                    # Send individual tool updates
                                    update_type = update.get("type", "progress")
                                    tool = update.get("tool", "")
                                    url = update.get("url", "")
                                    query_text = update.get("query", "")
                                    message = update.get("message", update.get("text", ""))
                                    
                                    # Create message if not present
                                    if not message:
                                        if tool and query_text:
                                            message = f"{tool}: {query_text[:50]}..."
                                        elif tool:
                                            message = f"Using {tool}..."
                                        else:
                                            message = "Processing..."
                                    
                                    # Determine the update type for frontend
                                    frontend_type = "progress"
                                    if update_type in ["tool_start", "tool_complete", "url_accessed", "data_received", "tool_error"]:
                                        frontend_type = update_type
                                    elif tool:
                                        # If we have a tool, use tool_complete
                                        frontend_type = "tool_complete"
                                    
                                    await self.send(text_data=json.dumps({
                                        "type": frontend_type,
                                        "tool": tool,
                                        "url": url if url else None,
                                        "query": query_text if query_text else None,
                                        "message": message,
                                        "progress": float(overall_progress),
                                        "status": "researching",
                                        "timestamp": timezone.now().isoformat()
                                    }))
                            
                            # Send summary update periodically (even if no new updates)
                            if len(findings) > 0 and len(findings) % 3 == 0:  # Every 3 findings
                                await self.send(text_data=json.dumps({
                                    "type": "progress",
                                    "status": "researching",
                                    "message": f"Completed {len(findings)} research steps",
                                    "progress": float(overall_progress),
                                    "findings_count": len(findings),
                                    "timestamp": timezone.now().isoformat()
                                }))
                        
                        elif node_name == "synthesize_findings":
                            # Synthesis phase
                            overall_progress = calculate_overall_progress("synthesizing", 0, 0, 0)
                            await self.send(text_data=json.dumps({
                                "type": "status",
                                "status": "synthesizing",
                                "message": "Synthesizing final report with financial calculations and citations...",
                                "progress": float(overall_progress),
                                "timestamp": timezone.now().isoformat()
                            }))
            except RuntimeError as e:
                if "recursion limit" in str(e).lower():
                    recursion_error_occurred = True
                    log.warning(f"Recursion limit reached, but continuing with current findings: {e}")
                    # Continue with the findings we have so far
                else:
                    raise
            
            # Synthesize report (even if recursion limit was hit, use findings we have)
            findings = final_state.get("findings", [])
            if findings or recursion_error_occurred:
                await self.send(text_data=json.dumps({
                    "type": "status",
                    "status": "synthesizing",
                    "message": "Synthesizing final report..."
                }))
                
                synthesizer = ReportSynthesizer()
                
                # Extract citations from results (not just from final_state)
                # This ensures we get all citations from web_search_results and financial_data_results
                # Use the orchestrator instance that was already created
                citations = []
                if hasattr(self, '_orchestrator') and self._orchestrator:
                    citations = self._orchestrator._extract_citations_from_results(
                        web_results=final_state.get("web_search_results", []),
                        financial_results=final_state.get("financial_data_results", [])
                    )
                else:
                    # Create orchestrator if not available
                    orchestrator = ResearchOrchestrator()
                    citations = orchestrator._extract_citations_from_results(
                        web_results=final_state.get("web_search_results", []),
                        financial_results=final_state.get("financial_data_results", [])
                    )
                
                # Also check if citations are already in final_state (from synthesize_findings node)
                if not citations:
                    citations = final_state.get("citations", [])
                
                log.info(f"Extracted {len(citations)} citations for report")
                
                # Use findings if available, otherwise create a minimal report
                if findings:
                    report = await synthesizer.synthesize_report(
                        original_query=query,
                        sector=sector,
                        findings=findings,
                        accumulated_knowledge=final_state.get("accumulated_knowledge", ""),
                        citations=citations
                    )
                    # The synthesizer already includes financial_data, but ensure it's there
                    if "financial_data" not in report:
                        financial_data = synthesizer._extract_financial_data(findings)
                        report["financial_data"] = financial_data
                    
                    # Ensure citations are in the report
                    if not report.get("citations"):
                        report["citations"] = citations
                    if not report.get("all_citations"):
                        report["all_citations"] = citations
                else:
                    # Create a minimal report if no findings
                    financial_data = synthesizer._extract_financial_data(findings) if findings else {}
                    report = {
                        "title": f"Research Report: {query[:50]}...",
                        "executive_summary": "Research completed but limited findings were available.",
                        "analysis": f"Research query: {query}\n\nLimited findings were gathered during research.",
                        "key_findings": ["Research completed with available information"],
                        "recommendations": ["Consider refining the query for more specific results"],
                        "citations": citations,
                        "all_citations": citations,
                        "financial_calculations": [],
                        "financial_data": financial_data,
                        "images_and_graphs": []
                    }
                
                final_state["report"] = report
                final_state["citations"] = citations  # Store in final_state for later use
            
            # Update query status
            completed_time = timezone.now()
            query_obj.status = "completed"
            query_obj.completed_at = completed_time
            await sync_to_async(query_obj.save)()
            
            duration = (completed_time - start_time).total_seconds()
            
            # Save report to database (always try to save, even if minimal)
            from core.models import Report
            report_data = final_state.get("report", {})
            
            if not report_data:
                # Create minimal report if none exists
                report_data = {
                    "title": f"Research Report: {query[:50]}...",
                    "executive_summary": "Research completed.",
                    "analysis": f"Research query: {query}",
                    "key_findings": [],
                    "recommendations": [],
                    "citations": [],
                    "all_citations": [],
                    "financial_calculations": [],
                    "financial_data": {},
                    "images_and_graphs": []
                }
            
            citations = report_data.get("citations", [])
            all_citations = report_data.get("all_citations", citations)
            financial_calculations = report_data.get("financial_calculations", [])
            financial_data = report_data.get("financial_data", {})
            images_and_graphs = report_data.get("images_and_graphs", [])
            
            sources_used = []
            if final_state.get("web_search_results"):
                sources_used.append("web_search")
            if final_state.get("financial_data_results"):
                sources_used.append("financial_data")
            
            try:
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
                            "financial_data": financial_data,
                            "images_and_graphs": images_and_graphs,
                            "sources_used": sources_used,
                            "plan_type": "deep",
                            "sections": report_data.get("sections", {}),
                            "all_citations": all_citations
                        }
                    }
                )
                log.info(f"Report {'created' if created else 'updated'} in database: {report_obj.id} with {len(citations)} citations, {len(all_citations)} all_citations, financial_data keys: {list(financial_data.keys()) if financial_data else 'none'}")
            except Exception as save_error:
                log.error(f"Error saving report to database: {save_error}", exc_info=True)
                # Don't fail the whole workflow if saving fails
            
            # Ensure report is saved before sending completion
            # Force database commit by accessing the saved object
            try:
                # Refresh from DB to ensure it's committed
                await sync_to_async(query_obj.refresh_from_db)()
                if hasattr(query_obj, 'report'):
                    await sync_to_async(query_obj.report.refresh_from_db)()
            except Exception as refresh_error:
                log.warning(f"Could not refresh from DB: {refresh_error}")
                # Small delay as fallback
                await asyncio.sleep(0.05)
            
            # Send completion (ensure all values are JSON-serializable)
            report_data = final_state.get("report", {})
            # Ensure report data is JSON-serializable
            if report_data:
                # Convert any non-serializable values
                serializable_report = {}
                for key, value in report_data.items():
                    try:
                        json.dumps(value)  # Test if serializable
                        serializable_report[key] = value
                    except (TypeError, ValueError):
                        # Convert to string if not serializable
                        serializable_report[key] = str(value) if value is not None else None
                report_data = serializable_report
            
            # Extract citations for sources panel - ensure they're in the report structure
            citations = report_data.get("citations", []) if report_data else []
            all_citations = report_data.get("all_citations", citations) if report_data else []
            
            # If citations are empty, try to extract from final_state
            if not all_citations:
                all_citations = final_state.get("citations", [])
                if not citations:
                    citations = all_citations
            
            # If still empty, try to extract from results directly
            if not all_citations:
                # Use the orchestrator instance that was already created
                if hasattr(self, '_orchestrator') and self._orchestrator:
                    all_citations = self._orchestrator._extract_citations_from_results(
                        web_results=final_state.get("web_search_results", []),
                        financial_results=final_state.get("financial_data_results", [])
                    )
                else:
                    # Create orchestrator if not available
                    orchestrator = ResearchOrchestrator()
                    all_citations = orchestrator._extract_citations_from_results(
                        web_results=final_state.get("web_search_results", []),
                        financial_results=final_state.get("financial_data_results", [])
                    )
                if not citations:
                    citations = all_citations
            
            log.info(f"Final citations count: {len(citations)} citations, {len(all_citations)} all_citations")
            
            # Get sources_used from final_state or construct from available data
            sources_used = []
            if final_state.get("web_search_results"):
                sources_used.append("web_search")
            if final_state.get("financial_data_results"):
                sources_used.append("financial_data")
            if not sources_used and all_citations:
                # Extract source types from citations
                sources_used = [
                    c.get("type", "unknown") if isinstance(c, dict) else str(c)
                    for c in all_citations
                ]
            
            # Ensure all_citations is in the report structure for frontend
            if report_data:
                if not report_data.get("all_citations"):
                    report_data["all_citations"] = all_citations
                if not report_data.get("citations"):
                    report_data["citations"] = citations
            
            # Ensure citations are properly formatted (list of dicts with required fields)
            formatted_citations = []
            formatted_all_citations = []
            
            for cit in citations:
                if isinstance(cit, dict) and cit.get("url"):
                    formatted_citations.append({
                        "title": cit.get("title", "Source"),
                        "url": cit.get("url", ""),
                        "type": cit.get("type", "web"),
                        "domain": cit.get("domain", ""),
                        "published_date": cit.get("published_date"),
                        "symbol": cit.get("symbol")
                    })
            
            for cit in all_citations:
                if isinstance(cit, dict) and cit.get("url"):
                    formatted_all_citations.append({
                        "title": cit.get("title", "Source"),
                        "url": cit.get("url", ""),
                        "type": cit.get("type", "web"),
                        "domain": cit.get("domain", ""),
                        "published_date": cit.get("published_date"),
                        "symbol": cit.get("symbol")
                    })
            
            log.info(f"Formatted citations: {len(formatted_citations)} citations, {len(formatted_all_citations)} all_citations")
            
            # Ensure images_and_graphs are included
            images_and_graphs = report_data.get("images_and_graphs", [])
            log.info(f"Frontend report: images_and_graphs count: {len(images_and_graphs)}")
            if images_and_graphs:
                log.info(f"Sample image URL: {images_and_graphs[0].get('url', 'N/A')[:100] if images_and_graphs else 'N/A'}")
            
            # Format report for frontend (matching ReportResponse structure)
            frontend_report = {
                "query_id": str(query_obj.id),
                "query": query,
                "sector": sector,
                "status": "completed",
                "report": {
                    "title": report_data.get("title", "Research Report"),
                    "executive_summary": report_data.get("executive_summary", ""),
                    "analysis": report_data.get("analysis", ""),
                    "key_findings": report_data.get("key_findings", []),
                    "recommendations": report_data.get("recommendations", []),
                    "citations": formatted_citations,  # Use formatted citations
                    "all_citations": formatted_all_citations,  # All citations for Sources panel
                    "financial_highlights": report_data.get("financial_highlights", []),
                    "financial_calculations": report_data.get("financial_calculations", []),
                    "financial_data": report_data.get("financial_data", {}),
                    "images_and_graphs": images_and_graphs  # Ensure this is included
                },
                "metadata": {
                    "duration_seconds": duration,
                    "total_steps": final_state.get("total_steps", 0),
                    "sources_used": sources_used,
                    "plan_type": "deep",
                    "sections": report_data.get("sections", {})
                },
                "created_at": completed_time.isoformat(),
                "updated_at": completed_time.isoformat()
            }
            
            log.info(f"Sending completion message with {len(formatted_all_citations)} citations to frontend")
            
            await self.send(text_data=json.dumps({
                "type": "complete",  # Frontend expects "complete" not "completed"
                "query_id": str(query_obj.id),
                "status": "completed",
                "duration_seconds": float(duration),
                "report": frontend_report,  # Send properly structured report
                "progress": 1.0,
                "message": "Research completed successfully",
                "timestamp": timezone.now().isoformat()
            }))
            
        except Exception as e:
            log.error(f"Research workflow error: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "type": "error",
                "error": str(e)
            }))
        finally:
            await self.close()
