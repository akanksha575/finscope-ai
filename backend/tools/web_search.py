import os
from typing import Dict, Any, Optional, List
from tavily import TavilyClient
from tools.base_tool import BaseTool
from utils.logger import log

class WebSearchTool(BaseTool):
    """Tavily web search tool for intelligent research queries"""
    
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        
        self.client = TavilyClient(api_key=api_key)
        super().__init__(
            name="web_search",
            description=(
                "Search the web for financial information, news, and market data using Tavily AI. "
                "Provides AI-generated summaries with source citations. Prioritizes recent sources (2024-2025). "
                "Best for: recent news, market trends, company announcements, industry analysis, and competitive intelligence. "
                "Returns top 5 results with relevance scores and optional AI-synthesized answer."
            )
        )
    
    async def execute(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        topic: Optional[str] = None,
        include_answer: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute web search
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 5)
            search_depth: Search depth - "basic", "advanced", "fast", "ultra-fast" (default: "advanced")
            topic: Topic filter - "general", "news", "finance" (optional)
            include_answer: Whether to include AI-generated answer (default: True)
            **kwargs: Additional Tavily parameters
            
        Returns:
            Dictionary with search results
        """
        try:
            # Validate input
            is_valid, error = self.validate_input(query=query, max_results=max_results)
            if not is_valid:
                return {"error": error, "results": []}
            
            log.info(f"Searching web for: {query[:80]}...")
            
            # Enhance query to prioritize recent sources, but keep it short.
            # Tavily rejects queries > 400 chars, so we must respect that limit.
            MAX_QUERY_LENGTH = 400
            query = " ".join((query or "").split())
            query_lower = query.lower()

            need_recency_hint = (
                "2024" not in query_lower
                and "2025" not in query_lower
                and "2026" not in query_lower
                and "recent" not in query_lower
                and "latest" not in query_lower
            )

            # Keep the hint minimal (no parentheses/OR) to avoid blowing length.
            recency_hint = "2024 2025 latest"
            enhanced_query = f"{query} {recency_hint}" if need_recency_hint else query

            if len(enhanced_query) > MAX_QUERY_LENGTH:
                # Drop hint first; if still too long, hard-truncate.
                enhanced_query = query
            if len(enhanced_query) > MAX_QUERY_LENGTH:
                enhanced_query = enhanced_query[: MAX_QUERY_LENGTH - 1].rstrip()
            
            # Prepare search parameters
            search_params = {
                "query": enhanced_query,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": include_answer,
            }
            
            if topic:
                search_params["topic"] = topic
            
            # Add any additional kwargs
            search_params.update(kwargs)
            
            # Execute search (Tavily client is synchronous, but we wrap in async)
            # For true async, we'd need to use httpx or aiohttp
            response = self.client.search(**search_params)
            
            # Format results
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date"),
                })
            
            answer = response.get("answer", "")
            
            return {
                "query": query,
                "results": results,
                "answer": answer,
                "total_results": len(results),
                "source": "Tavily",
            }
            
        except Exception as e:
            log.error(f"Web search failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "answer": "",
                "total_results": 0,
                "source": "Tavily",
            }
    
    def validate_input(self, query: str, max_results: int = 5, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate search input"""
        if not query or not query.strip():
            return False, "Query cannot be empty"

        # Tavily max query length guard to prevent repeated tool failures.
        # Keep the limit aligned with provider constraints.
        if len(query) > 400:
            return False, f"Query is too long. Max query length is 400 characters."
        
        if max_results < 1 or max_results > 20:
            return False, "max_results must be between 1 and 20"
        
        return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (1-20)",
                        "default": 5
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced", "fast", "ultra-fast"],
                        "description": "Search depth",
                        "default": "advanced"
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["general", "news", "finance"],
                        "description": "Topic filter (optional)"
                    },
                    "include_answer": {
                        "type": "boolean",
                        "description": "Include AI-generated answer",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        }