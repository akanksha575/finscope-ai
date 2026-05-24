import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from django.utils import timezone
from langgraph.graph import StateGraph, END
from research.state import ResearchState
from research.query_generator import QueryGenerator
from research.tool_executor import ToolExecutor
from agents.base_agent import BaseAgent
from reports.synthesizer import ReportSynthesizer
from core.models import Query, ResearchStep
from utils.logger import log
from research.complexity import plan_for_query, QueryType
from research.dimensions import get_dimensions, get_dimension_keywords, update_dimension_coverage
from research.validation import extract_numeric_claims, merge_claim_evidence, unvalidated_claims as get_unvalidated_claims
from research.query_intelligence import (
    CoverageTracker,
    QueryHistory,
    PhaseManager,
    ThreadExtractor
)
from research.query_intent_parser import parse_query_intent
from utils.company_tickers import extract_primary_company_name
from research.query_intelligence import findings_similarity

class ResearchOrchestrator:
    """Orchestrates deep research workflow using LangGraph with ITERATIVE research"""
    
    def __init__(self):
        self.query_generator = QueryGenerator()
        self.tool_executor = ToolExecutor()
        self.synthesizer = ReportSynthesizer()  # Use enhanced Phase 8 synthesizer
        # Import sector agents for iterative intelligence
        from agents.it_sector_agent import ITSectorAgent
        from agents.pharma_sector_agent import PharmaSectorAgent
        self.it_agent = ITSectorAgent()
        self.pharma_agent = PharmaSectorAgent()
        log.info("Initialized ResearchOrchestrator with intelligent deep research system")
    
    def _serialize_coverage_tracker(self, tracker: CoverageTracker) -> Dict:
        """Serialize coverage tracker for state storage"""
        return {
            "sector": tracker.sector,
            "dimensions": {
                name: {
                    "covered": cov.covered,
                    "confidence": cov.confidence,
                    "queries_used": cov.queries_used
                }
                for name, cov in tracker.dimensions.items()
            }
        }
    
    def _deserialize_coverage_tracker(self, data: Dict) -> CoverageTracker:
        """Deserialize coverage tracker from state"""
        tracker = CoverageTracker(sector=data["sector"])
        for name, cov_data in data.get("dimensions", {}).items():
            if name in tracker.dimensions:
                tracker.dimensions[name].covered = cov_data.get("covered", False)
                tracker.dimensions[name].confidence = cov_data.get("confidence", "none")
                tracker.dimensions[name].queries_used = cov_data.get("queries_used", 0)
        return tracker
    
    def build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with iterative research loop"""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        # NOTE: Node names are consumed by the WebSocket streaming endpoint; keep them stable.
        workflow.add_node("plan_queries", self._plan_initial_queries_node)
        workflow.add_node("execute_research", self._execute_iterative_research_node)
        workflow.add_node("synthesize_findings", self._synthesize_findings_node)
        
        # Define edges with conditional logic for iterative research
        workflow.set_entry_point("plan_queries")
        workflow.add_edge("plan_queries", "execute_research")
        workflow.add_conditional_edges(
            "execute_research",
            self._should_continue_research,
            {
                "continue": "execute_research",  # Loop back for more research
                "synthesize": "synthesize_findings"  # Stop and synthesize
            }
        )
        workflow.add_edge("synthesize_findings", END)
        
        # Compile workflow (LangGraph 0.0.20 doesn't require checkpoint)
        # The recursion limit can be set during execution if needed
        return workflow.compile()
    
    async def _plan_initial_queries_node(self, state: ResearchState) -> Dict[str, Any]:
        """Generate initial batch of research queries (first iteration)"""
        log.info(f"Planning initial queries for: {state['query']}")
        
        selected_questions = state.get("selected_questions", [])

        # Parse query intent to extract companies, requirements, constraints
        intent = parse_query_intent(state["query"], state.get("sector"))
        log.info(f"Parsed intent: companies={intent.companies}, requirements={intent.requirements}")
        
        # Use cleaned query (instruction-stripped) for planning
        planning_query = intent.cleaned_query if intent.cleaned_query else state["query"]
        
        # Complexity & dimension planning
        plan = plan_for_query(planning_query)
        dims = get_dimensions(state["sector"], plan.query_type)
        dims_covered = {d: False for d in dims}
        
        # Initialize intelligent tracking objects
        coverage_tracker = CoverageTracker(sector=state["sector"])
        query_history = QueryHistory()
        phase_manager = PhaseManager()
        
        # Generate initial query using query generator (pass cleaned query)
        initial_queries = await self.query_generator.generate_research_queries(
            original_query=planning_query,  # Use cleaned query
            sector=state["sector"],
            selected_questions=selected_questions
        )
        
        # Add to history
        if initial_queries:
            query_history.add_query(initial_queries[0])
        
        return {
            "research_queries": initial_queries,
            "current_step": 0,
            # total_steps is used as an expected step count for UI; use max_steps (up to 25 for deep research)
            "total_steps": min(plan.max_steps, 25),
            "status": "researching",
            "intelligence_markers": {
                "query_type": plan.query_type.value,
                "complexity": plan.complexity.value,
                "min_steps": plan.min_steps,
                "max_steps": min(plan.max_steps, 25),  # Allow up to 25 steps for deep research
                "dimensions": dims,
                "dimensions_covered": dims_covered,
                "consecutive_no_new_info": 0,
                "consecutive_web_failures": 0,
                "sources_required": 8,
                "claim_registry": {},
                "iterations_completed": 0,
                "queries_executed": 0,
                "interesting_threads": [],
                "_should_stop": False,
                # Store serialized tracking objects
                "coverage_tracker_state": self._serialize_coverage_tracker(coverage_tracker),
                "query_history_queries": query_history.queries,
                "phase_manager_state": {
                    "current_phase": phase_manager.current_phase,
                    "steps_in_phase": phase_manager.steps_in_phase,
                    "total_steps": phase_manager.total_steps
                }
            }
        }
    
    async def _execute_iterative_research_node(self, state: ResearchState) -> Dict[str, Any]:
        """
        Execute research queries ITERATIVELY - each step builds on previous findings.
        
        Critical behavior:
        - Execute EXACTLY ONE query per iteration (no shallow parallel batches)
        - Generate the NEXT query based on ALL prior findings + uncovered dimensions + validation needs
        - Stop only after min depth is achieved AND dimensions covered AND 3 consecutive no-new-info steps
        """
        current_queries = state.get("research_queries", [])
        existing_findings = state.get("findings", [])
        accumulated_knowledge = state.get("accumulated_knowledge", "")
        intelligence_markers = state.get("intelligence_markers", {})
        current_step = state.get("current_step", 0)
        
        max_steps = int(intelligence_markers.get("max_steps", 25))
        # Allow up to 25 steps for deep research (was capped at 20)
        max_steps = min(max_steps, 25)
        min_steps = int(intelligence_markers.get("min_steps", 8))
        query_type_val = intelligence_markers.get("query_type", QueryType.COMPANY_DEEP_DIVE.value)
        try:
            query_type = QueryType(query_type_val)
        except Exception:
            query_type = QueryType.COMPANY_DEEP_DIVE

        dims = intelligence_markers.get("dimensions") or []
        dims_covered = intelligence_markers.get("dimensions_covered") or {d: False for d in dims}
        dim_keywords = get_dimension_keywords(state["sector"], query_type)
        claim_registry = intelligence_markers.get("claim_registry") or {}
        prev_claim_count = len(claim_registry)
        consecutive_no_new_info = int(intelligence_markers.get("consecutive_no_new_info", 0))
        consecutive_web_failures = int(intelligence_markers.get("consecutive_web_failures", 0))

        # Execute queries from the batch
        # Process one query at a time to ensure quality, but ensure we have enough queries to reach 18-20
        current_query = current_queries[0] if current_queries else None
        if not current_query:
            intelligence_markers["_should_stop"] = True
            return {
                "status": "synthesizing",
                "research_queries": [],
                "intelligence_markers": intelligence_markers,
            }

        log.info(f"Iterative research step {len(existing_findings) + 1}/{max_steps}: {current_query[:120]}")
        
        # Collect progress updates - create a new list to avoid mutating state directly
        existing_progress_updates = state.get("progress_updates", [])
        new_progress_updates = []
        
        async def progress_callback(update: Dict[str, Any]):
            """Callback to collect progress updates"""
            new_progress_updates.append(update)
            log.info(f"Progress: {update.get('message', '')}")
        
        # Execute tools sequentially for THIS query (web search first; finance optionally)
        use_pdf_only = state.get("use_pdf_only", False)
        results = await self.tool_executor.execute_sequential(
            query=current_query,
            sector=state["sector"],
            tools=["web_search", "financial_data"],
            tool_params={
                "web_search_max_results": 5,
                "web_search_depth": "advanced",
                "web_search_include_answer": True,
                "rag_top_k": 10,
            },
            progress_callback=progress_callback,
            query_idx=len(existing_findings),
            total_queries=max_steps,
            use_pdf_only=use_pdf_only,
        )

        web_results = results.get("web_search", [])
        financial_results = results.get("financial_data", [])

        # Detect web-search failures (tool error or zero results) to avoid hammering the same approach.
        web_data_for_failure = {}
        if web_results and isinstance(web_results, list) and isinstance(web_results[0], dict):
            web_data_for_failure = web_results[0].get("data") or {}
        web_error = web_data_for_failure.get("error") if isinstance(web_data_for_failure, dict) else None
        web_result_count = 0
        if isinstance(web_data_for_failure, dict):
            web_result_count = len(web_data_for_failure.get("results") or [])
        web_failed = bool(web_error) or web_result_count == 0
        if web_failed:
            consecutive_web_failures += 1
        else:
            consecutive_web_failures = 0
        intelligence_markers["consecutive_web_failures"] = consecutive_web_failures
        intelligence_markers["_last_web_error"] = str(web_error)[:200] if web_error else None

        step_number = len(existing_findings) + 1
        finding = {
            "query": current_query,
            "step_number": step_number,
            "web_sources": len(web_results),
            "financial_sources": len(financial_results),
            "key_insights": self._extract_insights(web_results, financial_results),
            "data": {
                "web_search": web_results[0].get("data", {}) if web_results else {},
                "financial_data": financial_results[0].get("data", {}) if financial_results else {},
            },
        }

        # Extract claims + evidence from web results (domain/url)
        web_data = (finding.get("data") or {}).get("web_search") or {}
        # Tavily structure: {results:[{url,title,content,...}], answer:"..."}
        urls = []
        domains = []
        snippets = []
        if isinstance(web_data, dict):
            for r in (web_data.get("results") or [])[:5]:
                if isinstance(r, dict):
                    u = r.get("url") or ""
                    if u:
                        urls.append(u)
                        domains.append(self._extract_domain(u))
                    c = r.get("content") or ""
                    if c:
                        snippets.append(c)
            if web_data.get("answer"):
                snippets.append(str(web_data.get("answer")))

        # Update claim registry for each domain/snippet
        for i, snippet in enumerate(snippets[:6]):
            domain = domains[i] if i < len(domains) else "unknown"
            url = urls[i] if i < len(urls) else None
            claims = extract_numeric_claims(snippet)
            if claims:
                claim_registry = merge_claim_evidence(claim_registry, claims, domain=domain, url=url)
        new_claim_count = len(claim_registry)

        # Update accumulated knowledge after each finding
        accumulated_knowledge = self._update_accumulated_knowledge(accumulated_knowledge, finding)

        all_findings = existing_findings + [finding]
        
        # Update intelligence markers
        intelligence_markers["iterations_completed"] = intelligence_markers.get("iterations_completed", 0) + 1
        intelligence_markers["queries_executed"] = len(all_findings)
        intelligence_markers["interesting_threads"] = self._identify_interesting_threads(all_findings)

        # Dimension coverage update
        coverage_text = " ".join([
            current_query,
            " ".join(str(x) for x in (finding.get("key_insights") or [])),
            " ".join(snippets[:3]),
        ])
        dims_covered = update_dimension_coverage(dims_covered, dim_keywords, coverage_text)
        intelligence_markers["dimensions_covered"] = dims_covered
        intelligence_markers["claim_registry"] = claim_registry
        
        # Novelty detection: new domains OR new validated claims OR newly covered dimensions.
        newly_covered = sum(1 for d in dims if dims_covered.get(d)) - sum(1 for d in dims if (intelligence_markers.get("_prev_dims_covered") or {}).get(d))
        prev_domains = set(intelligence_markers.get("_seen_domains") or [])
        new_domains = set(domains) - prev_domains
        intelligence_markers["_seen_domains"] = list(prev_domains | set(domains))
        intelligence_markers["_prev_dims_covered"] = dict(dims_covered)

        has_new_info = bool(new_domains) or newly_covered > 0 or (new_claim_count > prev_claim_count)
        if has_new_info:
            consecutive_no_new_info = 0
        else:
            consecutive_no_new_info += 1
        intelligence_markers["consecutive_no_new_info"] = consecutive_no_new_info

        # Citations count (unique urls)
        seen_urls = set(intelligence_markers.get("_seen_urls") or [])
        for u in urls:
            if u:
                seen_urls.add(u)
        intelligence_markers["_seen_urls"] = list(seen_urls)
        citations_count = len(seen_urls)

        # Stopping criteria (matches prompt):
        # - meet min steps for complexity
        # - cover all dimensions
        # - 3 consecutive no-new-info steps
        # - have 8+ unique sources (unless max_steps reached)
        steps_completed = len(all_findings)
        all_dims_covered = all(dims_covered.get(d, False) for d in dims) if dims else True
        enough_sources = citations_count >= int(intelligence_markers.get("sources_required", 8))
        # Align with spec: stop if no new significant info in last 2 searches.
        no_more_info = consecutive_no_new_info >= 2

        # For deep research, ensure we do at least min_steps before considering stopping
        # Only apply all stopping criteria if we've done at least min_steps
        should_stop = False
        if steps_completed < min_steps:
            # Before min_steps, don't stop (unless max_steps reached)
            should_stop = False
        elif steps_completed >= min_steps:
            # After min_steps, check all criteria but be lenient for deep research
            # For deep research, we want comprehensive coverage, so only stop if:
            # - All dimensions covered AND
            # - (No new info for 3+ steps OR enough sources) AND
            # - At least min_steps completed
            should_stop = (
                all_dims_covered
                and (no_more_info or enough_sources)
            )
            # But don't stop too early - ensure we've done meaningful research
            # For deep research (18-20 steps), ensure we complete at least 18 steps
            if steps_completed < max(min_steps + 2, 18):
                should_stop = False

        if steps_completed >= max_steps:
            log.warning(f"Force stopping: maximum steps reached ({steps_completed}/{max_steps})")
            should_stop = True
        elif steps_completed < 18 and max_steps >= 18:
            # For deep research, ensure we do at least 18 steps before stopping
            should_stop = False
            log.info(f"Continuing research: {steps_completed} steps completed, target is 18-20 steps (min_steps={min_steps}, max_steps={max_steps})")

        intelligence_markers["_should_stop"] = should_stop

        # Diminishing-returns stop: if last 2 findings are near-identical, stop once minimum depth is reached
        # and dimensions are covered.
        if not should_stop and steps_completed >= min_steps and all_dims_covered and len(all_findings) >= 2:
            sim = findings_similarity(all_findings[-2], all_findings[-1])
            intelligence_markers["_last_findings_similarity"] = sim
            if sim > 0.80:
                log.info(f"Stopping due to diminishing returns: last-2 findings similarity={sim:.2f}")
                should_stop = True
                intelligence_markers["_should_stop"] = True
        
        # Generate next query if not stopping
        next_queries = []
        if not should_stop:
            missing_dims = [d for d in dims if not dims_covered.get(d, False)]
            
            # Reconstruct tracking objects from state
            coverage_tracker_data = intelligence_markers.get("coverage_tracker_state")
            if coverage_tracker_data:
                coverage_tracker = self._deserialize_coverage_tracker(coverage_tracker_data)
            else:
                coverage_tracker = CoverageTracker(sector=state["sector"])
            
            query_history = QueryHistory()
            query_history.queries = intelligence_markers.get("query_history_queries", [])
            
            phase_manager_data = intelligence_markers.get("phase_manager_state", {})
            phase_manager = PhaseManager(
                current_phase=phase_manager_data.get("current_phase", "overview"),
                steps_in_phase=phase_manager_data.get("steps_in_phase", 0),
                total_steps=phase_manager_data.get("total_steps", 0)
            )
            
            # Strategy shift after repeated web failures: use an ultra-simple fallback query.
            if consecutive_web_failures >= 3:
                company = extract_primary_company_name(state["query"]) or " ".join(state["query"].split()[:5])
                aspect = missing_dims[0] if missing_dims else ("pipeline" if state["sector"] == "Pharma" else "financial performance")
                next_query = f"{company} {aspect} 2025"
                # Reset after strategy change to avoid permanent fallback mode.
                intelligence_markers["consecutive_web_failures"] = 0
            else:
                next_query = await self.query_generator.generate_next_query(
                    original_query=state["query"],
                    sector=state["sector"],
                    previous_findings=all_findings,
                    accumulated_knowledge=accumulated_knowledge,
                    selected_questions=state.get("selected_questions", []),
                    query_type=query_type,
                    dimensions_not_covered=missing_dims,
                    unvalidated_claims=get_unvalidated_claims(claim_registry),
                    citations_count=citations_count,
                    query_history=query_history,
                    coverage_tracker=coverage_tracker,
                    phase_manager=phase_manager,
                )
            
            # Update stored tracking objects
            intelligence_markers["coverage_tracker_state"] = self._serialize_coverage_tracker(coverage_tracker)
            intelligence_markers["query_history_queries"] = query_history.queries
            intelligence_markers["phase_manager_state"] = {
                "current_phase": phase_manager.current_phase,
                "steps_in_phase": phase_manager.steps_in_phase,
                "total_steps": phase_manager.total_steps
            }
            
            if next_query:
                next_queries = [next_query]
                log.info(f"Generated next iterative query: {next_query[:80]}...")
            else:
                # If we haven't reached 18 steps yet, generate more queries
                if steps_completed < 18 and max_steps >= 18:
                    log.info(f"Only {steps_completed} steps completed, generating additional queries to reach 18")
                    # Force generate more queries
                    additional_query = await self.query_generator.generate_next_query(
                        original_query=state["query"],
                        sector=state["sector"],
                        previous_findings=all_findings,
                        accumulated_knowledge=accumulated_knowledge,
                        selected_questions=state.get("selected_questions", []),
                        query_type=query_type,
                        dimensions_not_covered=missing_dims,
                        unvalidated_claims=get_unvalidated_claims(claim_registry),
                        citations_count=citations_count,
                        query_history=query_history,
                        coverage_tracker=coverage_tracker,
                        phase_manager=phase_manager,
                    )
                    if additional_query:
                        next_queries = [additional_query]
                        should_stop = False
                        intelligence_markers["_should_stop"] = False
                        log.info(f"Generated additional query to reach 18 steps: {additional_query[:80]}...")
                    else:
                        log.info("No next query generated - research complete")
                        should_stop = True
                        intelligence_markers["_should_stop"] = True
                else:
                    log.info("No next query generated - research complete")
                    should_stop = True
                    intelligence_markers["_should_stop"] = True
        
        # Ensure we retain all previous inputs and outputs by accumulating them
        # Get existing results from state to ensure nothing is lost
        existing_web_results = state.get("web_search_results", [])
        existing_financial_results = state.get("financial_data_results", [])
        
        # Combine all results (previous + new) - ensure no deletion
        final_web_results = existing_web_results + web_results
        final_financial_results = existing_financial_results + financial_results
        # Combine existing progress updates with new ones
        final_progress_updates = existing_progress_updates + new_progress_updates
        
        return {
            "web_search_results": final_web_results,  # Retain all previous + new
            "financial_data_results": final_financial_results,  # Retain all previous + new
            "findings": all_findings,  # Already accumulated above
            "accumulated_knowledge": accumulated_knowledge,
            "research_queries": next_queries,  # Next batch for iteration
            "current_step": len(all_findings),
            "total_steps": max_steps,
            "status": "synthesizing" if should_stop else "researching",
            "intelligence_markers": intelligence_markers,  # Contains _should_stop
            "progress_updates": final_progress_updates  # Retain all previous + new
        }
    
    def _should_continue_research(self, state: ResearchState) -> str:
        """
        Determine if research should continue or synthesize
        
        This is used by LangGraph conditional edges to route the workflow
        """
        # Get should_stop from intelligence_markers instead of direct state key
        intelligence_markers = state.get("intelligence_markers", {})
        should_stop = intelligence_markers.get("_should_stop", False)
        max_steps = int(intelligence_markers.get("max_steps", state.get("total_steps", 25) or 25))
        
        steps_completed = len(state.get("findings", []))
        if steps_completed >= max_steps:
            log.warning(f"Force stopping: Steps exceeded (completed: {steps_completed}, max: {max_steps})")
            return "synthesize"
        
        # Also check status
        if state.get("status") == "synthesizing":
            return "synthesize"
        
        return "synthesize" if should_stop else "continue"
    
    async def _check_stopping_criteria(
        self,
        all_findings: List[Dict[str, Any]],
        sector: str
    ) -> bool:
        """
        Check if research should stop based on stopping criteria
        
        Criteria from documentation:
        - Minimum 5 steps completed
        - All research dimensions covered
        - No new significant information found
        - Maximum 20 steps reached
        """
        # Deprecated in favor of explicit prompt-aligned stopping logic in the execute node.
        # Keep for backward compatibility but avoid early stopping.
        return False
    
    def _has_significant_new_information(
        self,
        recent_findings: List[Dict[str, Any]],
        previous_findings: List[Dict[str, Any]]
    ) -> bool:
        """Check if recent findings contain significant new information"""
        if not recent_findings:
            return False
        
        # Extract insights from recent findings
        recent_insights = []
        for finding in recent_findings:
            recent_insights.extend(finding.get("key_insights", []))
        
        # Extract insights from previous findings
        previous_insights = []
        for finding in previous_findings:
            previous_insights.extend(finding.get("key_insights", []))
        
        # Check if recent insights contain new information
        recent_text = " ".join(str(i).lower() for i in recent_insights)
        previous_text = " ".join(str(i).lower() for i in previous_insights)
        
        # Simple heuristic: if recent insights are significantly different
        if len(recent_insights) == 0:
            return False
        
        # Check for new keywords/concepts
        recent_words = set(recent_text.split())
        previous_words = set(previous_text.split())
        new_words = recent_words - previous_words
        
        # If more than 20% new words, consider it significant
        if len(new_words) > len(recent_words) * 0.2:
            return True
        
        return False
    
    def _identify_interesting_threads(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Identify interesting threads from findings for next queries"""
        threads = []
        
        for finding in findings[-5:]:  # Look at last 5 findings
            insights = finding.get("key_insights", [])
            
            # Extract interesting concepts
            for insight in insights:
                insight_str = str(insight).lower()
                if "growth" in insight_str or "increase" in insight_str:
                    threads.append("growth trends")
                if "ai" in insight_str or "artificial intelligence" in insight_str:
                    threads.append("AI capabilities")
                if "cloud" in insight_str:
                    threads.append("cloud services")
                if "pipeline" in insight_str:
                    threads.append("drug pipeline")
                if "patent" in insight_str:
                    threads.append("patent landscape")
        
        return list(set(threads))  # Remove duplicates
    
    def _update_accumulated_knowledge(
        self,
        current_knowledge: str,
        new_finding: Dict[str, Any]
    ) -> str:
        """Update accumulated knowledge with new finding"""
        insights = new_finding.get("key_insights", [])
        query = new_finding.get("query", "")
        
        if insights:
            new_knowledge = f"\n\n[Step {new_finding.get('step_number', 0)}] Query: {query}\n"
            new_knowledge += "\n".join(f"- {insight[:200]}" for insight in insights[:3])
            
            # Limit accumulated knowledge to avoid token limits
            combined = current_knowledge + new_knowledge
            if len(combined) > 5000:
                # Keep most recent knowledge
                lines = combined.split("\n")
                combined = "\n".join(lines[-50:])  # Keep last 50 lines
            
            return combined
        
        return current_knowledge
    
    async def _synthesize_findings_node(self, state: ResearchState) -> Dict[str, Any]:
        """Synthesize final research report"""
        log.info("Synthesizing research findings")
        
        # Collect citations from actual results (not just findings summary)
        citations = self._extract_citations_from_results(
            web_results=state.get("web_search_results", []),
            financial_results=state.get("financial_data_results", [])
        )
        
        # Use enhanced Phase 8 synthesizer with financial calculations and citations
        report = await self.synthesizer.synthesize_report(
            original_query=state["query"],
            sector=state["sector"],
            findings=state["findings"],
            accumulated_knowledge=state["accumulated_knowledge"],
            citations=citations
        )
        
        return {
            "status": "completed",
            "completed_at": timezone.now(),
            "report": report
        }
    
    def _extract_insights(
        self,
        web_results: List[Dict[str, Any]],
        financial_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract key insights from results"""
        insights = []
        
        # Extract from web results
        for result in web_results:
            data = result.get("data") or {}
            if not isinstance(data, dict):
                continue
                
            if "answer" in data and data["answer"]:
                insights.append(str(data["answer"])[:200])
            elif "results" in data and isinstance(data["results"], list):
                for res in data["results"][:2]:
                    if isinstance(res, dict) and "content" in res and res["content"]:
                        insights.append(str(res["content"])[:200])
        
        # Extract from financial results
        for result in financial_results:
            data = result.get("data") or {}
            if not isinstance(data, dict):
                continue
                
            if "data" in data and isinstance(data["data"], dict):
                fin_data = data["data"]
                if "current_price" in fin_data and fin_data["current_price"]:
                    insights.append(f"Current price: {fin_data['current_price']}")
                if "revenue" in fin_data and fin_data["revenue"]:
                    insights.append(f"Revenue: {fin_data['revenue']}")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _extract_citations_from_results(
        self,
        web_results: List[Dict[str, Any]],
        financial_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract citations with URLs from actual results"""
        citations = []
        seen_urls = set()
        accessed_at = timezone.now().isoformat()
        
        # Extract from web search results
        for result in web_results:
            data = result.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # Extract from web search answer (Tavily provides answer with sources)
            if "answer" in data and data["answer"]:
                # Tavily answer might reference sources, but we need actual results
                pass
            
            # Extract from web search results list
            if "results" in data and isinstance(data["results"], list):
                for res in data["results"]:
                    if isinstance(res, dict):
                        url = res.get("url", "")
                        if url and url not in seen_urls and url.startswith(("http://", "https://")):
                            citations.append({
                                "title": res.get("title", "Web Source"),
                                "url": url,
                                "type": "web",
                                "domain": self._extract_domain(url),
                                "published_date": res.get("published_date"),
                                "accessed_at": accessed_at,
                            })
                            seen_urls.add(url)
        
        # Extract from financial data results
        for result in financial_results:
            data = result.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # Extract symbol from financial data
            if "data" in data and isinstance(data["data"], dict):
                fin_data = data["data"]
                symbol = fin_data.get("symbol", "")
                if symbol:
                    yfinance_url = f"https://finance.yahoo.com/quote/{symbol}"
                    if yfinance_url not in seen_urls:
                        citations.append({
                            "title": f"Financial Data: {symbol}",
                            "url": yfinance_url,
                            "type": "financial",
                            "domain": "finance.yahoo.com",
                            "symbol": symbol,
                            "accessed_at": accessed_at,
                        })
                        seen_urls.add(yfinance_url)
        
        return citations
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
                return domain.replace("www.", "").replace("m.", "")
            return "Unknown"
        except (IndexError, AttributeError):
            return "Unknown"