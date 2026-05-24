from typing import List
from agents.base_agent import BaseAgent
from utils.logger import log

class QueryExpander(BaseAgent):
    """Expand queries using HyDE (Hypothetical Document Embeddings)"""
    
    def __init__(self):
        super().__init__(model="gpt-4o-mini", temperature=0.3)
        log.info("Initialized QueryExpander")
    
    async def expand_query(self, query: str, sector: str) -> str:
        """
        Generate hypothetical document answer to expand query
        
        Args:
            query: Original query
            sector: Sector context (IT/Pharma)
            
        Returns:
            Expanded query text (hypothetical answer)
        """
        prompt = f"""You are an expert financial research analyst specializing in the {sector} sector. Your task is to generate a comprehensive hypothetical document that would answer the user's query.

Query: "{query}"

Generate a detailed hypothetical answer document that:
1. Directly addresses the query with specific, factual-sounding information
2. Includes relevant financial metrics, KPIs, and performance indicators
3. Mentions specific company names, products, technologies, or market segments relevant to the {sector} sector
4. Incorporates industry terminology, jargon, and technical terms commonly used in {sector} sector research
5. Provides context about market trends, competitive landscape, and business strategies
6. Uses the same language style and structure as professional financial research reports

Write this as if you were drafting a section of a comprehensive research report. Be specific and detailed, but focus on information that would help retrieve the most relevant documents.

Hypothetical Answer Document:"""
        
        system_prompt = (
            "You are a specialized financial research assistant generating hypothetical documents for query expansion (HyDE technique). "
            "Your goal is to create a detailed, sector-specific answer that mirrors the language and content structure of real financial research documents. "
            "This hypothetical document will be used to improve semantic search by matching against similar language patterns in the knowledge base. "
            "Focus on accuracy, relevance, and using authentic financial terminology and company names from the specified sector."
        )
        
        try:
            hypothetical_answer = await self._call_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Combine original query with hypothetical answer
            expanded_query = f"{query}\n\n{hypothetical_answer[:500]}"  # Limit length
            
            log.info(f"Expanded query from {len(query)} to {len(expanded_query)} characters")
            return expanded_query
            
        except Exception as e:
            log.warning(f"Query expansion failed: {e}, using original query")
            return query
    
    async def process(self, query: str, sector: str) -> dict:
        """Process query expansion (implements BaseAgent interface)"""
        expanded = await self.expand_query(query, sector)
        return {"original": query, "expanded": expanded}