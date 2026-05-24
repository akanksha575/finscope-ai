import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from tools.mcp_tools import mcp_tools
from utils.logger import log
from utils.company_tickers import extract_tickers
from rag.retriever import HybridRetriever
from rag.vector_store import VectorStore
from rag.embeddings import EmbeddingGenerator
from rag.query_expansion import QueryExpander
from rag.reranker import Reranker


class ToolExecutor:
    """Execute research tools in parallel or sequentially"""
    
    def __init__(self):
        # Yahoo Finance (yfinance) is extremely sensitive to parallelism.
        # Limit concurrency across the entire process to avoid 429s.
        self._financial_semaphore = asyncio.Semaphore(1)
        # Simple TTL cache to dedupe repeated symbol fetches across queries/batches.
        self._financial_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._financial_cache_ts: Dict[Tuple[str, str], float] = {}
        self._financial_cache_ttl_s = 5 * 60  # 5 minutes
        
        # RAG retriever for PDF mode
        self._rag_retriever = None
        log.info("Initialized ToolExecutor")
    
    def _get_rag_retriever(self) -> HybridRetriever:
        """Get or initialize RAG retriever"""
        if self._rag_retriever is None:
            vector_store = VectorStore()
            embedding_gen = EmbeddingGenerator()
            query_expander = QueryExpander()
            reranker = Reranker()
            
            self._rag_retriever = HybridRetriever(
                vector_store=vector_store,
                embedding_generator=embedding_gen,
                query_expander=query_expander,
                reranker=reranker
            )
        return self._rag_retriever
    
    def _get_cached_financial(self, symbol: str, period: str) -> Optional[Dict[str, Any]]:
        key = (symbol, period)
        ts = self._financial_cache_ts.get(key)
        if ts is None:
            return None
        if time.time() - ts > self._financial_cache_ttl_s:
            # Expired; drop
            self._financial_cache.pop(key, None)
            self._financial_cache_ts.pop(key, None)
            return None
        return self._financial_cache.get(key)
    
    def _set_cached_financial(self, symbol: str, period: str, value: Dict[str, Any]) -> None:
        key = (symbol, period)
        self._financial_cache[key] = value
        self._financial_cache_ts[key] = time.time()
    
    async def execute_sequential(
        self,
        query: str,
        sector: str,
        tools: List[str] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None,
        query_idx: int = 0,
        total_queries: int = 1,
        use_pdf_only: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute a single query with multiple tools SEQUENTIALLY
        
        This is used for iterative research where each query is executed
        one at a time, allowing findings to inform the next query.
        
        Args:
            query: Single research query
            sector: Sector context
            tools: List of tool names to use (default: web_search, financial_data)
            progress_callback: Optional callback for progress updates
            query_idx: Current query index
            total_queries: Total number of queries
            
        Returns:
            Dictionary mapping tool names to results
        """
        tools = tools or ["web_search", "financial_data"]
        tool_params = tool_params or {}
        
        log.info(f"Executing query sequentially: {query[:60]}...")
        
        results = {
            "web_search": [],
            "financial_data": [],
            "web_scraper": []
        }
        
        # Execute tools sequentially for this query
        for tool_name in tools:
            try:
                if tool_name == "web_search":
                    # Use RAG if PDF-only mode, otherwise use web search
                    if use_pdf_only:
                        result = await self._execute_rag_search(
                            query,
                            sector,
                            progress_callback,
                            query_idx,
                            total_queries,
                            top_k=int(tool_params.get("rag_top_k", 10))
                        )
                    else:
                        result = await self._execute_web_search(
                            query,
                            sector,
                            progress_callback,
                            query_idx,
                            total_queries,
                            max_results=int(tool_params.get("web_search_max_results", 5)),
                            search_depth=str(tool_params.get("web_search_depth", "advanced")),
                            include_answer=bool(tool_params.get("web_search_include_answer", True)),
                        )
                    if result:
                        results["web_search"].append({
                            "query": query,
                            "data": result
                        })
                
                elif tool_name == "financial_data":
                    result = await self._execute_financial_data(
                        query, sector, progress_callback, query_idx, total_queries
                    )
                    if result:
                        results["financial_data"].append({
                            "query": query,
                            "data": result
                        })
                
                elif tool_name == "web_scraper":
                    # Skip scraper for now (needs URLs)
                    continue
                    
            except Exception as e:
                log.error(f"Tool {tool_name} failed for query '{query}': {e}")
                results[tool_name].append({
                    "query": query,
                    "error": str(e),
                    "data": {}
                })
        
        return results
    
    async def execute_parallel(
        self,
        queries: List[str],
        sector: str,
        tools: List[str] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute multiple queries in parallel using specified tools
        
        Args:
            queries: List of research queries
            sector: Sector context
            tools: List of tool names to use (default: all available)
            
        Returns:
            Dictionary mapping tool names to results
        """
        if not queries:
            return {}
        
        tools = tools or ["web_search", "financial_data", "web_scraper"]
        tool_params = tool_params or {}
        
        log.info(f"Executing {len(queries)} queries in parallel using {len(tools)} tools")
        
        # Create tasks for parallel execution
        tasks = []
        
        for query_idx, query in enumerate(queries):
            for tool_name in tools:
                if tool_name == "web_search":
                    task = self._execute_web_search(
                        query,
                        sector,
                        progress_callback,
                        query_idx,
                        len(queries),
                        max_results=int(tool_params.get("web_search_max_results", 5)),
                        search_depth=str(tool_params.get("web_search_depth", "advanced")),
                        include_answer=bool(tool_params.get("web_search_include_answer", True)),
                    )
                elif tool_name == "financial_data":
                    task = self._execute_financial_data(query, sector, progress_callback, query_idx, len(queries))
                elif tool_name == "web_scraper":
                    # Skip scraper for now (needs URLs)
                    continue
                else:
                    continue
                
                tasks.append((tool_name, query, task))
        
        # Execute all tasks in parallel
        results = {
            "web_search": [],
            "financial_data": [],
            "web_scraper": []
        }
        
        if tasks:
            # Run tasks concurrently
            task_results = await asyncio.gather(
                *[task for _, _, task in tasks],
                return_exceptions=True
            )
            
            # Organize results
            for i, (tool_name, query, _) in enumerate(tasks):
                result = task_results[i]
                if isinstance(result, Exception):
                    log.error(f"Tool {tool_name} failed for query '{query}': {result}")
                    results[tool_name].append({
                        "query": query,
                        "error": str(result),
                        "data": {}
                    })
                else:
                    results[tool_name].append({
                        "query": query,
                        "data": result
                    })
        
        log.info(f"Completed parallel execution: {sum(len(v) for v in results.values())} results")
        return results
    
    async def _execute_web_search(
        self, 
        query: str, 
        sector: str,
        progress_callback: Optional[callable] = None,
        query_idx: int = 0,
        total_queries: int = 1,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_answer: bool = True,
    ) -> Dict[str, Any]:
        """Execute web search for a query"""
        try:
            # Hard limit to avoid provider/tool failures (Tavily rejects >400 chars).
            # Keep a buffer because the downstream tool may add a small "recency" hint.
            MAX_QUERY_LEN = 380

            def _simplify(q: str) -> str:
                if not q:
                    return ""
                # Remove common instruction-y words that bloat LLM-generated prompts.
                filler = {
                    "analyze", "evaluate", "assess", "research", "discuss",
                    "strategic", "positioning", "whether", "delivering",
                    "sustainable", "growth", "market", "their", "and", "or",
                    "the", "a", "an", "to", "from", "of", "in", "on", "for",
                }
                words = [w for w in q.replace("\n", " ").split() if w.lower() not in filler]
                out: List[str] = []
                for w in words:
                    candidate = (" ".join(out + [w])).strip()
                    if len(candidate) > MAX_QUERY_LEN:
                        break
                    out.append(w)
                simplified = " ".join(out).strip()
                return simplified or " ".join(q.split()[:15])

            query = " ".join((query or "").split())
            if len(query) > MAX_QUERY_LEN:
                query = _simplify(query)

            # Anchor searches to 2026 unless caller already includes an explicit year,
            # but never exceed our max length.
            if query and not any(str(y) in query for y in range(1990, 2031)):
                anchored = f"{query} 2026"
                query = anchored if len(anchored) <= MAX_QUERY_LEN else query

            if progress_callback:
                await progress_callback({
                    "type": "tool_start",
                    "tool": "web_search",
                    "query": query,
                    "message": f"Searching web for: {query[:60]}...",
                    "progress": query_idx / total_queries if total_queries > 0 else 0
                })
            
            result = await mcp_tools.execute_tool(
                "web_search",
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=include_answer,
                topic="finance" if sector in ["IT", "Pharma"] else "general"
            )
            
            # Extract URLs from results for real-time updates
            if progress_callback and "results" in result:
                urls = [r.get("url", "") for r in result.get("results", []) if r.get("url")]
                for url in urls[:3]:  # Show first 3 URLs
                    await progress_callback({
                        "type": "url_accessed",
                        "url": url,
                        "tool": "web_search",
                        "query": query,
                        "message": f"Accessing: {url[:60]}..."
                    })
            
            if progress_callback:
                await progress_callback({
                    "type": "tool_complete",
                    "tool": "web_search",
                    "query": query,
                    "message": f"Found {len(result.get('results', []))} results",
                    "progress": (query_idx + 1) / total_queries if total_queries > 0 else 1
                })
            
            return result
        except Exception as e:
            log.error(f"Web search failed: {e}")
            if progress_callback:
                await progress_callback({
                    "type": "tool_error",
                    "tool": "web_search",
                    "query": query,
                    "error": str(e),
                    "message": f"Web search failed: {str(e)[:60]}"
                })
            return {"error": str(e), "results": []}
    
    async def _execute_rag_search(
        self,
        query: str,
        sector: str,
        progress_callback: Optional[callable] = None,
        query_idx: int = 0,
        total_queries: int = 1,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """Execute RAG search from PDF documents"""
        try:
            if progress_callback:
                await progress_callback({
                    "type": "tool_start",
                    "tool": "rag_search",
                    "query": query,
                    "message": f"Searching PDF documents for: {query[:60]}...",
                    "progress": query_idx / total_queries if total_queries > 0 else 0
                })
            
            retriever = self._get_rag_retriever()
            
            # Retrieve documents from RAG
            rag_results = await retriever.retrieve(
                query=query,
                sector=sector,
                top_k=top_k,
                use_hyde=True,
                use_reranking=True
            )
            
            if not rag_results:
                log.warning(f"No RAG results found for query: {query}")
                return {"results": [], "answer": ""}
            
            # Format results to match web search format
            formatted_results = []
            for i, result in enumerate(rag_results[:top_k], 1):
                text = result.get("text", "")
                metadata = result.get("metadata", {})
                source_name = metadata.get("source_name", "PDF Document")
                
                formatted_results.append({
                    "title": f"[PDF Document {i}] {source_name}",
                    "content": text,
                    "url": "",  # PDFs don't have URLs
                    "metadata": metadata
                })
                
                if progress_callback:
                    await progress_callback({
                        "type": "data_received",
                        "tool": "rag_search",
                        "query": query,
                        "source": source_name,
                        "message": f"Retrieved chunk {i}/{len(rag_results)} from {source_name}"
                    })
            
            # Combine text for answer synthesis
            combined_text = "\n\n".join([r["content"] for r in formatted_results[:5]])
            answer = combined_text[:1000] + "..." if len(combined_text) > 1000 else combined_text
            
            if progress_callback:
                await progress_callback({
                    "type": "tool_complete",
                    "tool": "rag_search",
                    "query": query,
                    "message": f"Found {len(formatted_results)} relevant chunks from PDF",
                    "progress": (query_idx + 1) / total_queries if total_queries > 0 else 1
                })
            
            return {
                "results": formatted_results,
                "answer": answer,
                "source": "pdf_rag"
            }
        except Exception as e:
            log.error(f"RAG search failed: {e}")
            if progress_callback:
                await progress_callback({
                    "type": "tool_error",
                    "tool": "rag_search",
                    "query": query,
                    "error": str(e),
                    "message": f"RAG search failed: {str(e)[:60]}"
                })
            return {"error": str(e), "results": [], "answer": ""}
    
    async def _execute_financial_data(
        self, 
        query: str, 
        sector: str,
        progress_callback: Optional[callable] = None,
        query_idx: int = 0,
        total_queries: int = 1
    ) -> Dict[str, Any]:
        """Extract and execute financial data queries"""
        # Try to extract stock symbols from query
        # This is a simple implementation - could be enhanced with NER
        symbols = self._extract_symbols(query, sector)
        # Dedupe while preserving order
        symbols = list(dict.fromkeys(symbols))
        
        if progress_callback:
            await progress_callback({
                "type": "tool_start",
                "tool": "financial_data",
                "query": query,
                "symbols": symbols,
                "message": f"Fetching financial data for: {', '.join(symbols) if symbols else 'query'}",
                "progress": query_idx / total_queries if total_queries > 0 else 0
            })
        
        results = []
        period = "1y"
        for symbol in symbols[:2]:  # Limit to 2 symbols per query
            try:
                cached = self._get_cached_financial(symbol, period)
                if cached is not None:
                    results.append(cached)
                    if progress_callback:
                        await progress_callback({
                            "type": "data_received",
                            "tool": "financial_data",
                            "symbol": symbol,
                            "message": f"Using cached financial data for {symbol}"
                        })
                    continue

                yfinance_url = f"https://finance.yahoo.com/quote/{symbol}"
                if progress_callback:
                    await progress_callback({
                        "type": "url_accessed",
                        "url": yfinance_url,
                        "tool": "financial_data",
                        "symbol": symbol,
                        "message": f"Fetching data from Yahoo Finance: {symbol}"
                    })

                # Limit concurrency + retry/backoff on rate limiting.
                attempt = 0
                result: Dict[str, Any] = {}
                while attempt < 3:
                    async with self._financial_semaphore:
                        result = await mcp_tools.execute_tool(
                            "financial_data",
                            symbol=symbol,
                            period=period
                        )
                    err = (result.get("error") or "").lower()
                    if "429" in err or "too many requests" in err or "rate limit" in err:
                        # Backoff and retry
                        sleep_s = 1.5 * (attempt + 1)
                        log.warning(f"Rate limited fetching {symbol}. Retrying in {sleep_s:.1f}s (attempt {attempt+1}/3)")
                        await asyncio.sleep(sleep_s)
                        attempt += 1
                        continue
                    break

                results.append(result)
                # Cache even partial data to avoid hammering for the next query in the same run.
                self._set_cached_financial(symbol, period, result)
                
                if progress_callback:
                    await progress_callback({
                        "type": "data_received",
                        "tool": "financial_data",
                        "symbol": symbol,
                        "message": f"Received financial data for {symbol}"
                    })
            except Exception as e:
                log.warning(f"Financial data fetch failed for {symbol}: {e}")
                if progress_callback:
                    await progress_callback({
                        "type": "tool_error",
                        "tool": "financial_data",
                        "symbol": symbol,
                        "error": str(e),
                        "message": f"Failed to fetch data for {symbol}: {str(e)[:60]}"
                    })
        
        if progress_callback:
            await progress_callback({
                "type": "tool_complete",
                "tool": "financial_data",
                "query": query,
                "message": f"Fetched data for {len(results)} symbols",
                "progress": (query_idx + 1) / total_queries if total_queries > 0 else 1
            })
        
        return {"symbols": symbols, "results": results}
    
    def _extract_symbols(self, query: str, sector: str) -> List[str]:
        """Extract potential stock symbols from query"""
        # Prefer normalized, mapping-based extraction (handles punctuation like "Dr. Reddy's").
        symbols: List[str] = []

        # Pull known tickers in order of mention.
        mapped = extract_tickers(query, max_companies=3)
        if mapped:
            symbols.extend(mapped)

        # Sector-specific minimal fallbacks (keep for robustness if mapping misses something).
        ql = (query or "").lower()
        if sector == "IT":
            if ("microsoft" in ql or "msft" in ql) and "MSFT" not in symbols:
                symbols.append("MSFT")
        elif sector == "Pharma":
            # Handle variations like "Dr. Reddy's" explicitly
            if ("dr reddy" in ql or "dr. reddy" in ql or "dr reddy's" in ql) and "DRREDDY.NS" not in symbols:
                symbols.append("DRREDDY.NS")

        # Dedupe while preserving order
        return list(dict.fromkeys(symbols))