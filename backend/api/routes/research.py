import json
import re
import uuid
from datetime import datetime
from typing import Optional
import asyncio
from django.utils import timezone
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request, File, UploadFile, Form
from pathlib import Path
import os
from api.schemas.research import ResearchAnalysisRequest, ResearchAnalysisResponse, ResearchSource
from api.schemas.research_engine import ResearchRequest, ResearchResponse
from rag.retriever import HybridRetriever
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingGenerator
from rag.query_expansion import QueryExpander
from rag.reranker import Reranker
from tools.mcp_tools import mcp_tools
from agents.base_agent import BaseAgent
from guardrails.safety_checker import safety_checker
from utils.logger import log
from utils.helpers import sanitize_query, validate_query
from utils.cache import get_cache_manager, generate_cache_key, CACHE_TTL

router = APIRouter()

# Initialize components
_retriever = None
_research_agent = None

def get_retriever():
    """Get or initialize hybrid retriever"""
    global _retriever
    
    if _retriever is None:
        vector_store = VectorStore()
        embedding_gen = EmbeddingGenerator()
        query_expander = QueryExpander()
        reranker = Reranker()
        
        _retriever = HybridRetriever(
            vector_store=vector_store,
            embedding_generator=embedding_gen,
            query_expander=query_expander,
            reranker=reranker
        )
    
    return _retriever

class ResearchAnalyst(BaseAgent):
    """Agent for synthesizing comprehensive research analysis"""
    
    def __init__(self):
        super().__init__(model="gpt-4o-mini", temperature=0.3)
        log.info("Initialized ResearchAnalyst")
    
    async def process(self, query: str, document_context: str, web_context: str, sector: str) -> dict:
        """Process research analysis (implements BaseAgent interface)"""
        return await self.synthesize_analysis(query, document_context, web_context, sector)
    
    async def synthesize_analysis(
        self,
        query: str,
        document_context: str,
        web_context: str,
        sector: str
    ) -> dict:
        """
        Synthesize comprehensive research analysis from multiple sources
        
        Args:
            query: Research query
            document_context: Retrieved document chunks
            web_context: Web search results
            sector: Sector context
            
        Returns:
            Dictionary with analysis, summary, and key findings
        """
        prompt = f"""You are a senior financial research analyst specializing in comprehensive, data-driven analysis. Your task is to synthesize information from multiple sources into a cohesive, insightful research report.

RESEARCH QUERY:
{query}

SECTOR CONTEXT:
{sector}

DOCUMENT SOURCES (from ingested documents):
{document_context}

WEB SOURCES (from internet search):
{web_context}

ANALYSIS REQUIREMENTS:

1. **Direct Query Response**: Address the research query directly and comprehensively. Do not provide generic information.

2. **Source Synthesis**: 
   - Integrate information from BOTH document and web sources
   - When sources conflict, acknowledge both perspectives
   - Cite specific sources when referencing data (e.g., "According to [Document 1]" or "[Web Source 2] reports...")

3. **Data-Driven Analysis**:
   - Include specific numbers, percentages, dates, and metrics
   - Use exact figures from sources (e.g., "$2.5B revenue", "15% growth", "Q3 2024")
   - If data is unavailable, state this explicitly rather than making assumptions

4. **Comprehensive Coverage**:
   - Financial performance: revenue, growth, profitability, market share
   - Strategic initiatives: new products, partnerships, expansions
   - Competitive positioning: market position, differentiation, threats
   - Risks and opportunities: specific challenges and growth potential
   - Future outlook: trends, projections, strategic direction

5. **Key Findings**:
   - Extract 5-10 most important insights
   - Each finding should be specific and actionable
   - Include supporting data points for each finding

OUTPUT FORMAT (STRICT JSON - NO MARKDOWN, NO CODE BLOCKS):
{{
    "executive_summary": "2-3 sentence high-level summary capturing the most critical findings and implications",
    "analysis": "Comprehensive analysis (1000-2000 words) that thoroughly addresses the query. Structure with clear paragraphs covering: context, current state, key developments, financial metrics, strategic analysis, competitive landscape, risks, opportunities, and future outlook. Include specific data points throughout.",
    "key_findings": [
        "Finding 1: [Specific insight with supporting data/metrics]",
        "Finding 2: [Another key insight with numbers or facts]",
        "Finding 3: [Continue with 5-10 total findings]"
    ]
}}

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON. No markdown formatting, no code blocks, no explanatory text outside the JSON.
- Ensure all JSON strings are properly escaped.
- The "analysis" field must be comprehensive (1000-2000 words) with specific details.
- Every key finding must include concrete data or metrics.
- If a source is unavailable or data is missing, state this explicitly in the analysis."""

        system_prompt = (
            "You are an expert financial research analyst specializing in deep, comprehensive analysis. "
            "Your analysis should be thorough, well-structured, and based on the provided sources. "
            "Always include specific data points, numbers, and facts. Be objective and analytical."
        )
        
        try:
            # Request JSON format (works with gpt-4o-mini)
            response = await self._call_llm(
                prompt=prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no additional text.",
                system_prompt=system_prompt + " You must return valid JSON only."
            )
            
            # Extract JSON from response (handle cases where LLM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Try parsing entire response
                result = json.loads(response)
            
            return {
                "analysis": result.get("analysis", ""),
                "executive_summary": result.get("executive_summary", ""),
                "key_findings": result.get("key_findings", [])
            }
            
        except json.JSONDecodeError as e:
            log.warning(f"JSON parsing failed, using text response: {e}")
            # Fallback: parse text response manually
            return {
                "analysis": response if response else f"Comprehensive analysis of: {query}\n\nBased on document and web sources provided.",
                "executive_summary": "Analysis generated from available sources. See detailed analysis below.",
                "key_findings": [f"Analysis completed for: {query}"]
            }
        except Exception as e:
            log.error(f"Analysis synthesis failed: {e}")
            # Fallback to simple analysis
            return {
                "analysis": f"Comprehensive analysis based on query: {query}\n\nDocument Context:\n{document_context[:1000]}...\n\nWeb Context:\n{web_context[:1000]}...",
                "executive_summary": "Analysis generated from available sources",
                "key_findings": ["Analysis completed with available information"]
            }

def get_research_agent():
    """Get or initialize research analyst"""
    global _research_agent
    
    if _research_agent is None:
        _research_agent = ResearchAnalyst()
    
    return _research_agent

@router.post("/research/analyze", response_model=ResearchAnalysisResponse)
async def conduct_research_analysis(request: ResearchAnalysisRequest) -> ResearchAnalysisResponse:
    """
    Conduct comprehensive in-depth research analysis
    
    Combines:
    - RAG document retrieval (from ingested documents)
    - Web search (for additional context)
    - LLM synthesis (for comprehensive analysis)
    """
    try:
        # Validate query
        is_valid, error_msg = validate_query(request.query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        sanitized_query = sanitize_query(request.query)
        log.info(f"Starting deep research analysis for query: {sanitized_query[:80]}...")
        
        sources = []
        document_context = ""
        web_context = ""
        
        # Step 1: RAG Document Retrieval
        if request.use_rag:
            log.info("Retrieving documents from RAG system...")
            retriever = get_retriever()
            
            rag_results = await retriever.retrieve(
                query=sanitized_query,
                sector=request.sector,
                top_k=request.rag_top_k,
                use_hyde=True,
                use_reranking=True
            )
            
            if rag_results:
                # Combine top document chunks
                doc_texts = []
                for i, result in enumerate(rag_results[:request.rag_top_k], 1):
                    text = result.get("text", "")
                    metadata = result.get("metadata", {})
                    source_name = metadata.get("source_name", "Unknown")
                    
                    doc_texts.append(f"[Document {i} - {source_name}]\n{text}\n")
                    sources.append(ResearchSource(
                        type="document",
                        content=text[:500] + "..." if len(text) > 500 else text,
                        metadata=metadata
                    ))
                
                document_context = "\n\n".join(doc_texts)
                log.info(f"Retrieved {len(rag_results)} document chunks")
            else:
                log.warning("No documents found in RAG system")
        
        # Step 2: Web Search
        if request.use_web_search:
            log.info("Searching web for additional context...")
            try:
                web_results = await mcp_tools.execute_tool(
                    "web_search",
                    query=sanitized_query,
                    max_results=request.max_web_results,
                    search_depth="advanced",
                    topic="finance" if request.sector in ["IT", "Pharma", "Architecture", "Energy"] else "general"
                )
                
                if "error" not in web_results and web_results.get("results"):
                    # Combine web search results
                    web_texts = []
                    for i, result in enumerate(web_results["results"][:request.max_web_results], 1):
                        title = result.get("title", "Unknown")
                        content = result.get("content", "")
                        url = result.get("url", "")
                        
                        web_texts.append(f"[Web Source {i} - {title}]\nURL: {url}\nContent: {content}\n")
                        sources.append(ResearchSource(
                            type="web",
                            content=content[:500] + "..." if len(content) > 500 else content,
                            url=url,
                            metadata={"title": title}
                        ))
                    
                    web_context = "\n\n".join(web_texts)
                    log.info(f"Retrieved {len(web_results.get('results', []))} web results")
                else:
                    log.warning(f"Web search failed or returned no results: {web_results.get('error', 'Unknown error')}")
            except Exception as e:
                log.error(f"Web search error: {e}")
                web_context = ""
        
        # Step 3: Synthesize comprehensive analysis
        log.info("Synthesizing comprehensive analysis...")
        research_agent = get_research_agent()
        
        analysis_result = await research_agent.synthesize_analysis(
            query=sanitized_query,
            document_context=document_context or "No document sources available.",
            web_context=web_context or "No web sources available.",
            sector=request.sector
        )
        
        log.info("Research analysis completed successfully")
        
        return ResearchAnalysisResponse(
            query=sanitized_query,
            sector=request.sector,
            analysis=analysis_result["analysis"],
            executive_summary=analysis_result["executive_summary"],
            key_findings=analysis_result["key_findings"],
            sources=sources,
            total_sources=len(sources)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Research analysis failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during research analysis: {str(e)}"
        )

@router.post("/research/start/pdf", response_model=ResearchResponse)
async def start_research_with_pdf(
    query: str = Form(..., min_length=3, max_length=1000),
    sector: str = Form(..., regex="^(IT|Pharma|Architecture|Energy|Unknown)$"),
    pdf_file: UploadFile = File(...),
    selected_questions: Optional[str] = Form(default="[]"),
    http_request: Request = None
) -> ResearchResponse:
    """
    Start deep research workflow with PDF file upload
    
    The report will be based on the uploaded PDF document instead of web search.
    """
    import json
    
    try:
        # Validate PDF file
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF (.pdf)")
        
        # Parse selected questions
        try:
            questions = json.loads(selected_questions) if selected_questions else []
        except json.JSONDecodeError:
            questions = []
        
        # Save uploaded PDF
        upload_dir = Path("./data/uploads/research")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{uuid.uuid4()}_{pdf_file.filename}"
        content = await pdf_file.read()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: file_path.write_bytes(content)
        )
        
        log.info(f"PDF uploaded: {file_path}, size: {len(content)} bytes")
        
        # Ingest PDF into RAG system
        from api.routes.ingest import get_rag_components
        from api.schemas.rag import IngestRequest as IngestReq
        from rag.document_processor import DocumentProcessor
        
        vector_store, doc_processor, embedding_gen = get_rag_components()
        
        # Process PDF
        max_pages = int(os.getenv("PDF_MAX_PAGES", default="0")) or None
        chunks = await loop.run_in_executor(
            None,
            doc_processor.process_pdf,
            str(file_path),
            max_pages
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No content extracted from PDF")
        
        # Add to vector store
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadata = chunk["metadata"].copy()
            metadata["source_name"] = pdf_file.filename
            metadatas.append(metadata)
        
        await loop.run_in_executor(
            None,
            vector_store.add_documents,
            sector,
            documents,
            metadatas,
            ids
        )
        
        log.info(f"Ingested {len(chunks)} chunks from PDF into {sector} collection")
        
        # Create ResearchRequest and proceed with research
        request = ResearchRequest(
            query=query,
            sector=sector,
            selected_questions=questions,
            use_rag=True  # Force RAG usage
        )
        
        # Import helper function
        from api.routes.research_pdf_helper import start_research_with_pdf_flag
        
        # Call start_research with PDF flag
        return await start_research_with_pdf_flag(request, http_request, str(file_path))
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"PDF upload research failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/research/start", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, http_request: Request) -> ResearchResponse:
    """
    Start deep research workflow (Phase 6)
    
    This is independent of RAG - uses web search, financial data, and tools
    to conduct comprehensive research without requiring document ingestion.
    """
    from asgiref.sync import sync_to_async
    from core.models import Query as QueryModel, ResearchStep as ResearchStepModel
    from research.orchestrator import ResearchOrchestrator
    from research.state import ResearchState
    
    try:
        # Phase 10: Safety checks (guardrails)
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
        
        # Use sanitized query from safety checker
        sanitized_query = safety_result["sanitized_query"]
        
        # Additional validation
        is_valid, error_msg = validate_query(sanitized_query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        log.info(f"Starting Phase 6 research: {sanitized_query[:80]}...")
        
        # Check cache for research results (cache key based on query, sector, and selected questions)
        cache = await get_cache_manager()
        cache_key = generate_cache_key(
            "research_result",
            sanitized_query,
            request.sector,
            request.selected_questions
        )
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            log.info(f"Cache hit for research result: {sanitized_query[:60]}...")
            # Still create query record for history
            query_obj = await sync_to_async(QueryModel.objects.create)(
                query_text=sanitized_query,
                sector=request.sector,
                status="completed",
                plan_type="deep",
                completed_at=timezone.now()
            )
            # Return cached result
            return ResearchResponse(
                query_id=str(query_obj.id),
                query=sanitized_query,
                sector=request.sector,
                plan_type="deep",
                status="completed",
                report=cached_result.get("report", {}),
                total_steps=cached_result.get("total_steps", 0),
                duration_seconds=cached_result.get("duration_seconds", 0),
                sources_used=cached_result.get("sources_used", [])
            )
        
        # Cache miss - proceed with research
        log.debug(f"Cache miss for research, executing workflow")
        
        # Create query record (async wrapper)
        query_obj = await sync_to_async(QueryModel.objects.create)(
            query_text=sanitized_query,
            sector=request.sector,
            status="researching",
            plan_type="deep"  # Always deep research now
        )
        
        start_time = timezone.now()
        
        # Initialize orchestrator
        orchestrator = ResearchOrchestrator()
        workflow = orchestrator.build_workflow()
        
        # Initialize state
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
            "pdf_file_path": None,
            "use_pdf_only": request.use_rag,  # Use PDF/RAG if requested
            "started_at": start_time,
            "completed_at": None,
            "error": None
        }
        
        # Execute workflow
        final_state = await workflow.ainvoke(initial_state)
        
        # Save research steps to database (async wrapper)
        for i, finding in enumerate(final_state.get("findings", []), 1):
            await sync_to_async(ResearchStepModel.objects.create)(
                query=query_obj,
                step_number=i,
                action=finding.get("query", "Research step"),
                source="Tavily",
                query_text=finding.get("query", ""),
                finding=json.dumps(finding.get("key_insights", [])),
                raw_data=finding,
                status="completed",
                started_at=start_time,
                completed_at=timezone.now()
            )
        
        # Update query status (async wrapper)
        completed_time = timezone.now()
        query_obj.status = "completed"
        query_obj.completed_at = completed_time
        await sync_to_async(query_obj.save)()
        
        # Calculate duration
        duration = (completed_time - start_time).total_seconds()
        
        # Extract sources used
        sources_used = []
        if final_state.get("web_search_results"):
            sources_used.append("web_search")
        if final_state.get("financial_data_results"):
            sources_used.append("financial_data")
        
        log.info(f"Research completed in {duration:.2f} seconds")
        
        # Cache research result (only if successful)
        cache = await get_cache_manager()
        if report_data:
            cache_key = generate_cache_key(
                "research_result",
                sanitized_query,
                request.sector,
                request.selected_questions
            )
            result_to_cache = {
                "report": report_data,
                "total_steps": final_state.get("total_steps", 0),
                "duration_seconds": duration,
                "sources_used": sources_used
            }
            await cache.set(cache_key, result_to_cache, ttl=CACHE_TTL["research_result"])
            log.info(f"Cached research result for: {sanitized_query[:60]}...")
        
        # Save report to database (Phase 7 & 8)
        report_data = final_state.get("report", {})
        if report_data:
            from core.models import Report
            
            # Extract citations with URLs (Phase 8)
            citations = report_data.get("citations", [])  # Filtered citations for report
            all_citations = report_data.get("all_citations", citations)  # All citations for Sources panel
            if not citations:
                # Fallback: create citations from sources_used
                citations = [{"type": source, "url": "", "title": source} for source in sources_used]
                all_citations = citations
            
            # Extract financial calculations (Phase 8)
            financial_calculations = report_data.get("financial_calculations", [])
            # Extract financial data for graph generation
            financial_data = report_data.get("financial_data", {})
            images_and_graphs = report_data.get("images_and_graphs", [])
            
            # Create or update report
            report_obj, created = await sync_to_async(Report.objects.update_or_create)(
                query=query_obj,
                defaults={
                    "title": report_data.get("title", "Research Report"),
                    "content": report_data.get("analysis", ""),
                    "executive_summary": report_data.get("executive_summary", ""),
                    "total_steps": final_state.get("total_steps", 0),
                    "duration_seconds": duration,
                    "citations": citations,  # Phase 8: Filtered citations with URLs (for report)
                    "metadata": {
                        "key_findings": report_data.get("key_findings", []),
                        "recommendations": report_data.get("recommendations", []),
                        "financial_highlights": report_data.get("financial_highlights", []),
                        "financial_calculations": financial_calculations,  # Phase 8: Financial calculations
                        "financial_data": financial_data,  # Financial data for graph generation
                        "images_and_graphs": images_and_graphs,  # Images and graphs
                        "sources_used": sources_used,
                        "plan_type": "deep",  # Always deep research
                        "sections": report_data.get("sections", {}),  # Phase 8: Section validation
                        "all_citations": all_citations  # All citations for Sources panel
                    }
                }
            )
            log.info(f"Report {'created' if created else 'updated'} in database: {report_obj.id} with {len(citations)} citations")
        
        return ResearchResponse(
            query_id=str(query_obj.id),
            query=sanitized_query,
            sector=request.sector,
            plan_type="deep",  # Always deep research
            status="completed",
            report=report_data,
            total_steps=final_state.get("total_steps", 0),
            duration_seconds=duration,
            sources_used=sources_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Research workflow failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during research: {str(e)}"
        )

@router.websocket("/research/stream")
async def research_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time research progress streaming
    
    Client sends: {"query": "...", "sector": "IT", "selected_questions": ["q1", "q2"]}
    Server streams: Real-time progress updates including URLs, tools, and findings
    """
    await websocket.accept()
    
    try:
        # Receive initial request
        data = await websocket.receive_json()
        query = data.get("query")
        sector = data.get("sector", "Unknown")
        selected_questions = data.get("selected_questions", [])
        
        if not query:
            await websocket.send_json({"error": "Query is required"})
            await websocket.close()
            return
        
        # Phase 10: Safety checks (guardrails) - Note: WebSocket doesn't have Request object
        # We'll use a mock request for rate limiting
        class MockRequest:
            def __init__(self, client_host):
                self.client = type('obj', (object,), {'host': client_host})()
                self.headers = {}
        
        client_ip = websocket.client.host if hasattr(websocket, 'client') and websocket.client else "websocket"
        mock_request = MockRequest(client_ip)
        
        safety_result = await safety_checker.validate_request(
            query=query,
            request=mock_request
        )
        
        if not safety_result["allowed"]:
            await websocket.send_json({
                "type": "error",
                "error": safety_result["reason"],
                "category": safety_result.get("category", "validation_error")
            })
            await websocket.close()
            return
        
        # Use sanitized query
        query = safety_result["sanitized_query"]
        
        log.info(f"WebSocket research started: {query[:80]}...")
        
        # Create QueryModel in database
        from core.models import Query as QueryModel
        from asgiref.sync import sync_to_async
        
        # Query already sanitized by safety_checker above
        sanitized_query = query[:500]  # Just truncate if needed
        
        start_time = timezone.now()
        query_obj = await sync_to_async(QueryModel.objects.create)(
            query_text=sanitized_query,
            sector=sector,
            status="researching",
            plan_type="deep"
        )
        query_id = str(query_obj.id)
        
        # Send initial acknowledgment with query_id
        await websocket.send_json({
            "type": "status",
            "status": "planning",
            "message": "Starting deep research workflow...",
            "query_id": query_id,
            "progress": 0.0
        })
        
        # Initialize orchestrator
        from research.orchestrator import ResearchOrchestrator
        from research.state import ResearchState
        orchestrator = ResearchOrchestrator()
        workflow = orchestrator.build_workflow()
        
        # Initialize state
        initial_state: ResearchState = {
            "query": sanitized_query,
            "sector": sector,
            "selected_questions": selected_questions,
            "query_id": query_id,
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
            "started_at": start_time,
            "completed_at": None,
            "error": None
        }
        
        # Track final state for report saving
        final_state = initial_state
        
        # Track progress state
        last_progress = 0.0
        last_status = "planning"
        sent_progress_updates = 0
        
        # Helper function to calculate overall progress
        def calculate_overall_progress(status: str, current_step: int, total_steps: int, findings_count: int) -> float:
            """Calculate overall progress (0-1) based on workflow stage"""
            nonlocal last_progress, last_status
            
            if status == "planning":
                progress = 0.05  # Planning is quick, 5%
            elif status == "researching":
                # Research stage: 10% to 90%
                # Use findings count as proxy for progress (max 25 steps expected)
                max_expected_steps = max(1, total_steps or 25)
                research_progress = min(findings_count / max_expected_steps, 1.0)
                progress = 0.1 + (research_progress * 0.8)  # 10% to 90%
            elif status == "synthesizing":
                progress = 0.95  # Synthesizing is quick, 95%
            elif status == "completed":
                progress = 1.0
            else:
                progress = last_progress  # Keep last progress if status unknown
            
            # Ensure progress only increases (don't go backwards)
            if status == last_status or status == "researching":
                progress = max(progress, last_progress)
            
            last_progress = progress
            last_status = status
            return progress
        
        # Execute workflow with streaming and increased recursion limit
        # LangGraph 0.0.20 may not support config parameter or uses different format
        try:
            # Try with config first (for newer LangGraph versions)
            config = {"recursion_limit": 50}
            workflow_stream = workflow.astream(initial_state, config=config)
        except (KeyError, TypeError, ValueError) as e:
            # LangGraph 0.0.20 might not support config or uses different format
            # Fallback: execute without config (uses default recursion limit)
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
        
        async for state_update in workflow_stream:
            # Update final_state with latest state - filter out invalid keys
            for node_name, node_state in state_update.items():
                # Filter out _should_stop if it exists (it's now in intelligence_markers)
                # LangGraph validates against ResearchState TypedDict, so remove invalid keys
                filtered_state = {k: v for k, v in node_state.items() 
                                 if k in ResearchState.__annotations__}
                
                # Update final_state - LangGraph handles accumulation automatically
                final_state.update(filtered_state)
            # Send progress updates
            for node_name, node_state in state_update.items():
                if node_name == "plan_queries":
                    overall_progress = calculate_overall_progress("planning", 0, 0, 0)
                    await websocket.send_json({
                        "type": "progress",
                        "status": "planning",
                        "message": f"Generated {len(node_state.get('research_queries', []))} research queries",
                        "queries": node_state.get("research_queries", []),
                        "progress": overall_progress
                    })
                
                elif node_name == "execute_research":
                    # Send real-time progress updates
                    progress_updates = node_state.get("progress_updates", [])
                    findings = node_state.get("findings", [])
                    current_step = node_state.get("current_step", 0)
                    total_steps = node_state.get("total_steps", 25)  # Default to 25 if not set
                    
                    # Calculate overall progress for this stage
                    overall_progress = calculate_overall_progress("researching", current_step, total_steps, len(findings))
                    
                    # Send only NEW progress updates to avoid duplicates.
                    new_updates = progress_updates[sent_progress_updates:]
                    sent_progress_updates = len(progress_updates)
                    for update in new_updates:
                        # Use overall progress instead of per-query progress
                        await websocket.send_json({
                            "type": update.get("type", "progress"),
                            "tool": update.get("tool"),
                            "url": update.get("url"),
                            "message": update.get("message"),
                            "progress": overall_progress,  # Use overall progress
                            "status": "researching",
                            "timestamp": timezone.now().isoformat()
                        })
                    
                    # Send summary update with overall progress
                    await websocket.send_json({
                        "type": "progress",
                        "status": "researching",
                        "message": f"Completed {len(findings)} research steps",
                        "progress": overall_progress,
                        "findings": findings  # Send all findings, not just last 3
                    })
                
                elif node_name == "synthesize_findings":
                    overall_progress = calculate_overall_progress("synthesizing", 0, 0, 0)
                    await websocket.send_json({
                        "type": "progress",
                        "status": "synthesizing",
                        "message": "Synthesizing final report with financial calculations and citations...",
                        "progress": overall_progress
                    })
        
        # Workflow complete - check final_state for report
        log.info("Workflow stream completed, checking final state for report...")
        
        if "report" in final_state and final_state["report"]:
            # Save report to database
            report_data = final_state["report"]
            from core.models import Report
            from asgiref.sync import sync_to_async
            
            log.info("Report found in final state, saving to database...")
            
            # Extract citations with URLs
            citations = report_data.get("citations", [])  # Filtered citations for report
            all_citations = report_data.get("all_citations", citations)  # All citations for Sources panel
            if not citations:
                sources_used = []
                if final_state.get("web_search_results"):
                    sources_used.append("web_search")
                if final_state.get("financial_data_results"):
                    sources_used.append("financial_data")
                citations = [{"type": source, "url": "", "title": source} for source in sources_used]
                all_citations = citations
            
            # Extract financial calculations
            financial_calculations = report_data.get("financial_calculations", [])
            
            # Calculate duration
            completed_time = timezone.now()
            duration = (completed_time - start_time).total_seconds()
            
            # Update query status
            query_obj.status = "completed"
            query_obj.completed_at = completed_time
            await sync_to_async(query_obj.save)()
            
            # Extract sources used
            sources_used = []
            if final_state.get("web_search_results"):
                sources_used.append("web_search")
            if final_state.get("financial_data_results"):
                sources_used.append("financial_data")
            
            # Create or update report
            report_obj, created = await sync_to_async(Report.objects.update_or_create)(
                query=query_obj,
                defaults={
                    "title": report_data.get("title", "Research Report"),
                    "content": report_data.get("analysis", ""),
                    "executive_summary": report_data.get("executive_summary", ""),
                    "total_steps": final_state.get("total_steps", 0),
                    "duration_seconds": duration,
                    "citations": citations,  # Filtered citations for report
                    "metadata": {
                        "key_findings": report_data.get("key_findings", []),
                        "recommendations": report_data.get("recommendations", []),
                        "financial_highlights": report_data.get("financial_highlights", []),
                        "financial_calculations": financial_calculations,
                        "sources_used": sources_used,
                        "plan_type": "deep",
                        "sections": report_data.get("sections", {}),
                        "all_citations": all_citations  # All citations for Sources panel
                    }
                }
            )
            
            log.info(f"Report saved successfully: {report_obj.id}")
            
            await websocket.send_json({
                "type": "complete",
                "status": "completed",
                "query_id": query_id,
                "report": report_data,
                "message": "Research completed successfully",
                "progress": 1.0
            })
            log.info("Final report sent to client via WebSocket")
        else:
            log.error("Workflow completed but no report found in final state!")
            await websocket.send_json({
                "type": "error",
                "error": "Report generation failed - no report in final state"
            })
        
        await websocket.close()
        log.info("WebSocket connection closed")
        
    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    except asyncio.CancelledError:
        # This commonly happens when the client disconnects while background tasks are still running.
        # It has an empty message by default, so treat it as a normal disconnect.
        log.info("WebSocket research cancelled (client likely disconnected)")
    except Exception as e:
        # Log full traceback for debugging
        log.exception("WebSocket research error")
        # Best-effort notify client; socket may already be closed.
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e) or e.__class__.__name__
            })
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass