"""
Query Intent Parser

Extracts structured intent from user queries:
- Companies mentioned
- Report type and requirements
- Timeframe and constraints
- Separates instructions from content

This prevents instruction prefix pollution and ensures company-centric research.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from utils.company_tickers import find_companies
from utils.logger import log


@dataclass
class QueryIntent:
    """Structured representation of user query intent"""
    # Core entities
    companies: List[str] = field(default_factory=list)
    sector: Optional[str] = None
    
    # Report specifications
    report_type: Optional[str] = None  # equity_research, investment_analysis, comparative_analysis
    requirements: List[str] = field(default_factory=list)
    
    # Temporal context
    timeframe: Dict[str, Any] = field(default_factory=dict)
    
    # Constraints
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Cleaned query (instruction stripped)
    cleaned_query: str = ""
    
    # Original for reference
    original_query: str = ""


class QueryIntentParser:
    """Parse user queries to extract structured intent"""
    
    # Instruction prefixes to strip
    INSTRUCTION_PREFIXES = [
        r"^create\s+(an?|the)\s+",
        r"^generate\s+(an?|the)\s+",
        r"^produce\s+(an?|the)\s+",
        r"^write\s+(an?|the)\s+",
        r"^make\s+(an?|the)\s+",
        r"^build\s+(an?|the)\s+",
        r"^prepare\s+(an?|the)\s+",
        r"^draft\s+(an?|the)\s+",
    ]
    
    # Report types
    REPORT_TYPES = {
        "equity research": "equity_research",
        "investment analysis": "investment_analysis",
        "investment memo": "investment_analysis",
        "research report": "research_report",
        "research memo": "research_memo",
        "comparative analysis": "comparative_analysis",
        "comparison": "comparative_analysis",
        "financial analysis": "financial_analysis",
    }
    
    # Requirement keywords
    REQUIREMENT_KEYWORDS = {
        "business highlights": ["business highlights", "core business", "key products", "main operations"],
        "revenue_trend": ["revenue trend", "revenue growth", "revenue 20", "sales growth", "top line"],
        "operating_margin": ["operating margin", "operating income", "EBIT", "profitability", "margins"],
        "profit_margin": ["profit margin", "net margin", "net income", "bottom line"],
        "cash_flow": ["cash flow", "free cash flow", "FCF", "operating cash"],
        "risks": ["risks", "challenges", "threats", "headwinds", "concerns"],
        "opportunities": ["opportunities", "growth drivers", "tailwinds", "catalysts"],
        "recommendation": ["recommendation", "buy", "hold", "sell", "rating", "target price"],
        "pipeline": ["pipeline", "clinical trials", "drug development", "phase"],
        "patent": ["patent", "exclusivity", "LOE", "loss of exclusivity", "patent cliff"],
        "competitive": ["competitive", "competition", "competitors", "market share", "vs"],
        "strategy": ["strategy", "strategic", "initiatives", "transformation"],
        "guidance": ["guidance", "forecast", "outlook", "projections"],
    }
    
    def parse(self, query: str, sector: Optional[str] = None) -> QueryIntent:
        """
        Parse user query into structured intent.
        
        Args:
            query: Raw user query
            sector: Optional sector hint (IT/Pharma)
            
        Returns:
            QueryIntent object with extracted information
        """
        intent = QueryIntent(original_query=query, sector=sector)
        
        # Step 1: Strip instruction prefixes
        cleaned = self._strip_instruction_prefix(query)
        intent.cleaned_query = cleaned
        
        # Step 2: Extract companies
        intent.companies = self._extract_companies(cleaned)
        
        # Step 3: Extract report type
        intent.report_type = self._extract_report_type(cleaned)
        
        # Step 4: Extract requirements
        intent.requirements = self._extract_requirements(cleaned)
        
        # Step 5: Extract timeframe
        intent.timeframe = self._extract_timeframe(cleaned)
        
        # Step 6: Extract constraints
        intent.constraints = self._extract_constraints(cleaned)
        
        log.info(f"Parsed intent: companies={intent.companies}, report_type={intent.report_type}, requirements={len(intent.requirements)}")
        
        return intent
    
    def _strip_instruction_prefix(self, query: str) -> str:
        """Remove instruction prefixes from query"""
        query_lower = query.lower()
        
        for pattern in self.INSTRUCTION_PREFIXES:
            match = re.match(pattern, query_lower, re.IGNORECASE)
            if match:
                # Remove the matched prefix
                stripped = query[match.end():]
                log.info(f"Stripped instruction prefix: '{match.group()}' from query")
                return stripped.strip()
        
        return query
    
    def _extract_companies(self, query: str) -> List[str]:
        """Extract all company names from query"""
        # Use existing company extraction
        matches = find_companies(query)
        companies = [m.canonical_name for m in matches]
        
        if companies:
            log.info(f"Extracted companies: {companies}")
        
        return companies
    
    def _extract_report_type(self, query: str) -> Optional[str]:
        """Extract report type from query"""
        query_lower = query.lower()
        
        for keyword, report_type in self.REPORT_TYPES.items():
            if keyword in query_lower:
                log.info(f"Detected report type: {report_type}")
                return report_type
        
        # Check for comparison patterns
        if any(word in query_lower for word in ["compare", "vs", "versus", "comparison"]):
            return "comparative_analysis"
        
        return None
    
    def _extract_requirements(self, query: str) -> List[str]:
        """Extract data requirements from query"""
        query_lower = query.lower()
        requirements = []
        
        for req_name, keywords in self.REQUIREMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if req_name not in requirements:
                        requirements.append(req_name)
                    break
        
        if requirements:
            log.info(f"Extracted requirements: {requirements}")
        
        return requirements
    
    def _extract_timeframe(self, query: str) -> Dict[str, Any]:
        """Extract temporal context from query"""
        timeframe = {}
        
        # Extract year ranges (e.g., "2023-2025", "2023–2025")
        year_range_pattern = r'(20\d{2})\s*[-–]\s*(20\d{2})'
        match = re.search(year_range_pattern, query)
        if match:
            timeframe["start"] = int(match.group(1))
            timeframe["end"] = int(match.group(2))
            log.info(f"Extracted timeframe: {timeframe['start']}-{timeframe['end']}")
        else:
            # Extract individual years
            years = re.findall(r'\b(20\d{2})\b', query)
            if years:
                years = sorted([int(y) for y in set(years)])
                if len(years) == 1:
                    timeframe["year"] = years[0]
                else:
                    timeframe["start"] = years[0]
                    timeframe["end"] = years[-1]
                log.info(f"Extracted years: {years}")
        
        # Extract quarters
        quarters = re.findall(r'\bQ([1-4])\b', query, re.IGNORECASE)
        if quarters:
            timeframe["quarters"] = [f"Q{q}" for q in quarters]
        
        # Extract fiscal year references
        if "fy" in query.lower() or "fiscal year" in query.lower():
            timeframe["fiscal_year"] = True
        
        return timeframe
    
    def _extract_constraints(self, query: str) -> Dict[str, Any]:
        """Extract constraints and preferences"""
        query_lower = query.lower()
        constraints = {}
        
        # Source constraints
        if "using only pdf" in query_lower or "pdf only" in query_lower:
            constraints["pdf_only"] = True
            constraints["sources"] = "pdf"
        elif "public sources" in query_lower or "publicly available" in query_lower:
            constraints["sources"] = "public"
        
        # Link requirements
        if "include links" in query_lower or "with links" in query_lower or "provide links" in query_lower:
            constraints["include_links"] = True
        
        # Focus areas
        focus_patterns = [
            (r"focus(?:ing)? on ([^,\.]+)", "focus"),
            (r"emphasiz(?:e|ing) ([^,\.]+)", "emphasis"),
            (r"specifically ([^,\.]+)", "specific"),
        ]
        
        for pattern, key in focus_patterns:
            match = re.search(pattern, query_lower)
            if match:
                constraints[key] = match.group(1).strip()
                break
        
        if constraints:
            log.info(f"Extracted constraints: {constraints}")
        
        return constraints


# Global parser instance
_parser = QueryIntentParser()


def parse_query_intent(query: str, sector: Optional[str] = None) -> QueryIntent:
    """
    Parse user query into structured intent.
    
    Convenience function that uses the global parser instance.
    """
    return _parser.parse(query, sector)
