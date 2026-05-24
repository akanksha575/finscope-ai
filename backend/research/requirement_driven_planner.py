"""
Requirement-Driven Query Planner

Generates precise, targeted queries based on extracted user requirements.
NO generic templates - every query must target specific data requested by user.

Critical Rules:
1. NEVER generate self-comparisons (X vs X)
2. Queries MUST target user requirements explicitly
3. Financial time-series data is MANDATORY for equity research
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from utils.logger import log


# Primary competitor mappings (for single-company comparative queries)
PRIMARY_COMPETITORS = {
    # Pharma
    "Eli Lilly": "Novo Nordisk",
    "Novo Nordisk": "Eli Lilly",
    "Pfizer": "Merck",
    "Merck": "Pfizer",
    "Bristol Myers Squibb": "Merck",
    "Johnson & Johnson": "Pfizer",
    "GSK": "AstraZeneca",
    "AstraZeneca": "GSK",
    "Sun Pharma": "Cipla",
    "Cipla": "Sun Pharma",
    "Dr. Reddy's Laboratories": "Lupin",
    "Lupin": "Dr. Reddy's Laboratories",
    
    # Tech
    "Microsoft": "Amazon",
    "Amazon": "Microsoft",
    "Apple": "Microsoft",
    "Nvidia": "AMD",
    "AMD": "Nvidia",
    "Google": "Microsoft",
    "Alphabet": "Microsoft",
}


@dataclass
class ExtractedRequirements:
    """Comprehensive extraction of user requirements"""
    # Entities
    companies: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)  # Drugs, services, product lines
    
    # Financial metrics
    metrics: Set[str] = field(default_factory=set)  # revenue, margin, EBITDA, etc.
    
    # Time periods
    years: List[int] = field(default_factory=list)
    quarters: List[str] = field(default_factory=list)
    
    # Calculations
    calculations: Set[str] = field(default_factory=set)  # YoY, CAGR, trend
    
    # Aspects
    aspects: Set[str] = field(default_factory=set)  # pipeline, R&D, risks, etc.
    
    # Report type
    is_equity_research: bool = False
    is_comparative: bool = False


class RequirementExtractor:
    """Extract detailed requirements from user query"""
    
    # Product/Drug patterns (case-insensitive)
    PRODUCT_PATTERNS = [
        r'\b(GLP-1|GLP1)\b',
        r'\b(Mounjaro|Zepbound|Trulicity)\b',
        r'\b(Azure|AWS|Google Cloud)\b',
        r'\b(iPhone|iPad|Mac)\b',
        r'\b(Eliquis|Ibrance|Prevnar)\b',
        r'\b(Keytruda|Opdivo)\b',
    ]
    
    # Metric keywords
    METRIC_KEYWORDS = {
        'revenue': ['revenue', 'sales', 'top line', 'top-line'],
        'operating_margin': ['operating margin', 'operating income', 'EBIT', 'EBITDA'],
        'profit_margin': ['profit margin', 'net margin', 'net income', 'bottom line'],
        'cash_flow': ['cash flow', 'free cash flow', 'FCF', 'operating cash'],
        'market_share': ['market share', 'market position'],
        'growth_rate': ['growth rate', 'growth', 'CAGR'],
    }
    
    # Calculation keywords
    CALCULATION_KEYWORDS = ['YoY', 'year-over-year', 'CAGR', 'trend', 'growth rate']
    
    # Aspect keywords
    ASPECT_KEYWORDS = {
        'pipeline': ['pipeline', 'clinical trials', 'drug development', 'phase'],
        'manufacturing': ['manufacturing', 'capacity', 'facilities', 'supply', 'production'],
        'rd': ['R&D', 'research', 'development', 'innovation'],
        'risks': ['risks', 'challenges', 'threats', 'headwinds'],
        'competition': ['competition', 'competitive', 'competitors', 'vs'],
        'guidance': ['guidance', 'forecast', 'outlook', 'projections'],
    }
    
    def extract(self, query: str, companies: List[str]) -> ExtractedRequirements:
        """Extract all requirements from query"""
        req = ExtractedRequirements()
        req.companies = companies
        
        # Extract products/drugs
        req.products = self._extract_products(query)
        
        # Extract metrics
        req.metrics = self._extract_metrics(query)
        
        # Extract time periods
        req.years = self._extract_years(query)
        req.quarters = self._extract_quarters(query)
        
        # Extract calculations
        req.calculations = self._extract_calculations(query)
        
        # Extract aspects
        req.aspects = self._extract_aspects(query)
        
        # Determine report type
        req.is_equity_research = any(word in query.lower() for word in ['equity', 'research', 'memo', 'report'])
        req.is_comparative = any(word in query.lower() for word in ['compare', 'vs', 'versus', 'comparison'])
        
        log.info(f"Extracted requirements: products={req.products}, metrics={req.metrics}, years={req.years}")
        
        return req
    
    def _extract_products(self, query: str) -> List[str]:
        """Extract product/drug names"""
        products = []
        for pattern in self.PRODUCT_PATTERNS:
            matches = re.findall(pattern, query, re.IGNORECASE)
            products.extend(matches)
        return list(set(products))
    
    def _extract_metrics(self, query: str) -> Set[str]:
        """Extract financial metrics"""
        query_lower = query.lower()
        metrics = set()
        
        for metric, keywords in self.METRIC_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                metrics.add(metric)
        
        return metrics
    
    def _extract_years(self, query: str) -> List[int]:
        """Extract years"""
        years = re.findall(r'\b(20\d{2})\b', query)
        return sorted([int(y) for y in set(years)])
    
    def _extract_quarters(self, query: str) -> List[str]:
        """Extract quarters"""
        quarters = re.findall(r'\b(Q[1-4])\b', query, re.IGNORECASE)
        return [q.upper() for q in quarters]
    
    def _extract_calculations(self, query: str) -> Set[str]:
        """Extract calculation requirements"""
        calcs = set()
        query_lower = query.lower()
        
        for calc in self.CALCULATION_KEYWORDS:
            if calc.lower() in query_lower:
                calcs.add(calc)
        
        return calcs
    
    def _extract_aspects(self, query: str) -> Set[str]:
        """Extract research aspects"""
        query_lower = query.lower()
        aspects = set()
        
        for aspect, keywords in self.ASPECT_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                aspects.add(aspect)
        
        return aspects


class RequirementDrivenPlanner:
    """Generate queries driven by extracted requirements"""
    
    def __init__(self):
        self.extractor = RequirementExtractor()
    
    def plan_queries(
        self,
        original_query: str,
        companies: List[str],
        sector: str
    ) -> List[str]:
        """
        Generate requirement-driven queries.
        
        Returns list of precise queries targeting user requirements.
        """
        # Extract requirements
        req = self.extractor.extract(original_query, companies)
        
        queries = []
        
        # 1. PRODUCT-SPECIFIC QUERIES (if products mentioned)
        if req.products:
            queries.extend(self._generate_product_queries(req, sector))
        
        # 2. FINANCIAL TIME-SERIES QUERIES (mandatory for equity research)
        # Always generate financial queries for comprehensive research
        queries.extend(self._generate_financial_queries(req, sector))
        
        # 3. ASPECT-SPECIFIC QUERIES (pipeline, manufacturing, etc.)
        if req.aspects:
            queries.extend(self._generate_aspect_queries(req, sector))
        else:
            # Generate default aspect queries if none specified
            queries.extend(self._generate_default_aspect_queries(req, sector))
        
        # 4. COMPARATIVE QUERIES (only if valid)
        if req.is_comparative and len(req.companies) > 0:
            queries.extend(self._generate_comparative_queries(req, sector))
        
        # 5. MARKET & SECTOR QUERIES (always add for comprehensive research)
        queries.extend(self._generate_market_sector_queries(req, sector))
        
        # 6. OVERVIEW QUERY (always add at least one)
        if not queries:
            # Fallback: basic overview
            for company in req.companies[:1]:  # Just first company
                queries.append(f"{company} {sector} overview financial performance 2025-2026")
        
        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        log.info(f"Generated {len(unique_queries)} requirement-driven queries")
        # Return up to 20 queries for deep research
        return unique_queries[:20]
    
    def _generate_product_queries(self, req: ExtractedRequirements, sector: str) -> List[str]:
        """Generate queries for specific products/drugs"""
        queries = []
        
        for company in req.companies:
            for product in req.products:
                # Revenue query
                if req.years:
                    year_str = " ".join(str(y) for y in req.years)
                    queries.append(f"{company} {product} revenue sales {year_str}")
                else:
                    queries.append(f"{company} {product} revenue sales growth 2024 2025")
                
                # Market performance
                queries.append(f"{company} {product} market share adoption rate performance")
        
        return queries
    
    def _generate_financial_queries(self, req: ExtractedRequirements, sector: str) -> List[str]:
        """Generate financial time-series queries (MANDATORY) - Always generates comprehensive queries"""
        queries = []
        
        # Determine years to query
        years = req.years if req.years else [2023, 2024, 2025]
        
        for company in req.companies:
            # Revenue queries for EACH year (always generate for equity research)
            for year in years:
                queries.append(f"{company} revenue {year} annual quarterly earnings fiscal")
            
            # Revenue trend query
            if len(years) > 1:
                year_range = f"{min(years)}-{max(years)}"
                queries.append(f"{company} revenue growth rate {year_range} CAGR YoY trend")
            
            # Operating margin queries for each year
            for year in years:
                queries.append(f"{company} operating margin {year} profitability EBITDA")
            
            # Operating margin trend
            if len(years) > 1:
                year_range = f"{min(years)}-{max(years)}"
                queries.append(f"{company} operating margin trend {year_range} profitability")
            
            # Profit margin queries
            for year in years:
                queries.append(f"{company} profit margin net income {year}")
            
            # Market cap and valuation
            queries.append(f"{company} market capitalization valuation 2024 2025")
            
            # Cash flow
            queries.append(f"{company} cash flow free cash flow FCF 2024 2025")
            
            # Guidance/forecast (always add)
            queries.append(f"{company} revenue {max(years)} guidance forecast analyst estimates")
            
            # Stock performance
            queries.append(f"{company} stock price performance 52 week high low 2024 2025")
        
        return queries
    
    def _generate_aspect_queries(self, req: ExtractedRequirements, sector: str) -> List[str]:
        """Generate aspect-specific queries"""
        queries = []
        
        for company in req.companies:
            # Pipeline (Pharma)
            if 'pipeline' in req.aspects and sector == "Pharma":
                queries.append(f"{company} drug pipeline clinical trials phase 3 late stage 2025 2026")
            
            # Manufacturing/Capacity
            if 'manufacturing' in req.aspects:
                queries.append(f"{company} manufacturing capacity expansion facilities supply constraints")
            
            # R&D
            if 'rd' in req.aspects:
                year_str = str(max(req.years)) if req.years else "2024 2025"
                queries.append(f"{company} R&D spending investment {year_str} research development")
            
            # Risks
            if 'risks' in req.aspects:
                queries.append(f"{company} key risks challenges threats headwinds 2025 2026")
            
            # Competition (general competitive landscape)
            if 'competition' in req.aspects and not req.is_comparative:
                queries.append(f"{company} competitive position market share competitors {sector}")
        
        return queries
    
    def _generate_comparative_queries(self, req: ExtractedRequirements, sector: str) -> List[str]:
        """Generate comparative queries (NO SELF-COMPARISONS)"""
        queries = []
        
        if len(req.companies) == 1:
            # Single company: compare with primary competitor
            company = req.companies[0]
            competitor = PRIMARY_COMPETITORS.get(company)
            
            if competitor:
                # Compare on requested metrics
                if req.metrics:
                    for metric in list(req.metrics)[:2]:  # Top 2 metrics
                        queries.append(f"{company} vs {competitor} {metric.replace('_', ' ')} comparison")
                else:
                    # Default comparison
                    queries.append(f"{company} vs {competitor} market share revenue comparison")
            else:
                log.warning(f"No primary competitor found for {company}, skipping comparative queries")
        
        elif len(req.companies) >= 2:
            # Multiple companies: compare them
            company1 = req.companies[0]
            company2 = req.companies[1]
            
            # CRITICAL: Ensure no self-comparison
            if company1.lower() == company2.lower():
                log.error(f"PREVENTED SELF-COMPARISON: {company1} vs {company2}")
                return []
            
            # Compare on requested metrics
            if req.metrics:
                for metric in list(req.metrics)[:3]:  # Top 3 metrics
                    queries.append(f"{company1} vs {company2} {metric.replace('_', ' ')} comparison")
            else:
                # Default comparisons
                queries.append(f"{company1} vs {company2} revenue growth comparison")
                queries.append(f"{company1} vs {company2} market position competitive analysis")
            
            # If 3+ companies, add third
            if len(req.companies) >= 3:
                company3 = req.companies[2]
                if company3.lower() != company1.lower() and company3.lower() != company2.lower():
                    queries.append(f"{company1} vs {company2} vs {company3} market share comparison")
        
        return queries
    
    def _generate_default_aspect_queries(self, req: ExtractedRequirements, sector: str) -> List[str]:
        """Generate default aspect queries when none are specified"""
        queries = []
        
        for company in req.companies:
            # Market position
            queries.append(f"{company} market position competitive landscape {sector} 2025")
            
            # Growth strategy
            queries.append(f"{company} growth strategy expansion plans 2025 2026")
            
            # Risk factors
            queries.append(f"{company} key risks challenges {sector} 2025")
            
            # Financial outlook
            queries.append(f"{company} financial outlook forecast analyst expectations 2025")
            
            # Recent developments
            queries.append(f"{company} recent developments news announcements 2024 2025")
        
        return queries
    
    def _generate_market_sector_queries(self, req: ExtractedRequirements, sector: str) -> List[str]:
        """Generate market and sector-level queries"""
        queries = []
        
        for company in req.companies:
            # Industry trends
            queries.append(f"{sector} industry trends market dynamics 2025")
            
            # Regulatory environment
            queries.append(f"{company} regulatory environment compliance {sector} 2025")
            
            # Technology/Innovation
            queries.append(f"{company} innovation technology R&D investments {sector} 2025")
            
            # Supply chain
            queries.append(f"{company} supply chain operations efficiency {sector}")
            
            # ESG factors
            queries.append(f"{company} ESG sustainability environmental social governance")
        
        return queries
    
    def validate_query(self, query: str, companies: List[str]) -> bool:
        """
        Validate query for critical failures.
        
        Returns False if query is invalid (self-comparison, etc.)
        """
        query_lower = query.lower()
        
        # Check for self-comparison
        if ' vs ' in query_lower or ' versus ' in query_lower:
            # Extract companies around "vs"
            parts = re.split(r'\s+vs\s+|\s+versus\s+', query_lower)
            if len(parts) >= 2:
                # Check if same company appears multiple times
                for company in companies:
                    company_lower = company.lower()
                    count = sum(1 for part in parts if company_lower in part)
                    if count > 1:
                        log.error(f"INVALID QUERY - Self-comparison detected: {query}")
                        return False
        
        # Check for company name presence
        has_company = any(company.lower() in query_lower for company in companies)
        if not has_company:
            log.warning(f"Query missing company name: {query}")
            return False
        
        return True


# Global planner instance
_planner = RequirementDrivenPlanner()


def generate_requirement_driven_queries(
    original_query: str,
    companies: List[str],
    sector: str
) -> List[str]:
    """
    Generate requirement-driven queries.
    
    Convenience function using global planner instance.
    """
    queries = _planner.plan_queries(original_query, companies, sector)
    
    # Validate all queries
    valid_queries = []
    for q in queries:
        if _planner.validate_query(q, companies):
            valid_queries.append(q)
    
    return valid_queries
