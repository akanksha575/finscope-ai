"""
Deep Research Query Intelligence System

This module implements the core intelligence for progressive, non-repetitive research:
- Dimension framework and coverage tracking
- Semantic similarity checking to prevent repetition
- Thread extraction from findings
- Natural language query construction
- Research phase management
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import Counter


# ============================================================================
# DIMENSION FRAMEWORKS
# ============================================================================

IT_DIMENSIONS = {
    "Financial Performance": [
        "revenue", "profit", "margin", "growth", "earnings", "cash flow",
        "quarterly", "annual", "guidance", "cagr", "ebitda"
    ],
    "Business Segments": [
        "cloud", "infrastructure", "software", "services", "consulting",
        "segment", "revenue mix", "geographic", "breakdown"
    ],
    "Market Position": [
        "market share", "ranking", "leader", "position", "competitive",
        "customer base", "client", "concentration"
    ],
    "Strategic Initiatives": [
        "ai", "ml", "artificial intelligence", "machine learning", "digital transformation",
        "acquisition", "partnership", "investment", "strategy"
    ],
    "Operational Metrics": [
        "employee", "attrition", "utilization", "headcount", "workforce",
        "deal pipeline", "bookings", "revenue per employee"
    ],
    "Innovation & R&D": [
        "r&d", "research", "development", "innovation", "product launch",
        "technology", "platform", "differentiation"
    ],
    "Competitive Landscape": [
        "competitor", "competition", "vs", "compared to", "advantage",
        "vulnerability", "market dynamics", "peer"
    ],
    "Risks & Challenges": [
        "risk", "challenge", "threat", "regulatory", "disruption",
        "economic", "headwind", "vulnerability"
    ],
    "Future Outlook": [
        "outlook", "forecast", "projection", "guidance", "future",
        "2026", "2027", "2028", "growth driver", "opportunity"
    ]
}

PHARMA_DIMENSIONS = {
    "Financial Performance": [
        "revenue", "profit", "margin", "cash flow", "r&d spending",
        "ebitda", "quarterly", "annual", "growth"
    ],
    "Product Portfolio": [
        "branded", "generic", "product", "portfolio", "therapeutic area",
        "drug", "medicine", "top selling", "revenue breakdown"
    ],
    "Drug Pipeline": [
        "pipeline", "clinical trial", "phase i", "phase ii", "phase iii",
        "nda", "bla", "trial", "development", "candidate"
    ],
    "Regulatory & Patents": [
        "fda", "ema", "approval", "regulatory", "patent", "exclusivity",
        "expiration", "patent cliff", "generic competition"
    ],
    "Market Position": [
        "market share", "leader", "position", "competitive", "ranking",
        "geographic presence", "market"
    ],
    "Manufacturing & Distribution": [
        "manufacturing", "facility", "capacity", "plant", "production",
        "supply chain", "quality", "gmp", "distribution"
    ],
    "R&D Innovation": [
        "r&d", "research", "innovation", "clinical trial", "success rate",
        "time to market", "therapeutic focus", "collaboration"
    ],
    "Competitive Landscape": [
        "competitor", "competition", "vs", "biosimilar", "peer",
        "competitive advantage", "market dynamics"
    ],
    "Risks & Opportunities": [
        "risk", "patent cliff", "regulatory challenge", "pricing pressure",
        "opportunity", "market expansion", "growth driver"
    ]
}


def get_dimension_framework(sector: str) -> Dict[str, List[str]]:
    """Get dimension framework for sector"""
    if sector == "IT":
        return IT_DIMENSIONS
    elif sector == "Pharma":
        return PHARMA_DIMENSIONS
    else:
        # Unknown sector: combine both
        return {**IT_DIMENSIONS, **PHARMA_DIMENSIONS}


# ============================================================================
# DIMENSION COVERAGE TRACKER
# ============================================================================

@dataclass
class DimensionCoverage:
    """Track coverage of a single dimension"""
    dimension: str
    covered: bool = False
    confidence: str = "none"  # none, low, medium, high
    queries_used: int = 0
    gaps: List[str] = field(default_factory=list)
    evidence_snippets: List[str] = field(default_factory=list)
    
    def update(self, text: str, keywords: List[str]) -> bool:
        """
        Update coverage based on text containing dimension keywords.
        Returns True if coverage improved.
        """
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        
        if matches == 0:
            return False
        
        # Store evidence snippet
        snippet = text[:200] if len(text) > 200 else text
        if snippet not in self.evidence_snippets:
            self.evidence_snippets.append(snippet)
        
        # Update confidence based on evidence
        evidence_count = len(self.evidence_snippets)
        if evidence_count >= 3:
            self.confidence = "high"
        elif evidence_count >= 2:
            self.confidence = "medium"
        elif evidence_count >= 1:
            self.confidence = "low"
        
        self.covered = True
        return True


@dataclass
class CoverageTracker:
    """Track coverage across all dimensions"""
    sector: str
    dimensions: Dict[str, DimensionCoverage] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize dimension coverage"""
        framework = get_dimension_framework(self.sector)
        for dim_name in framework.keys():
            self.dimensions[dim_name] = DimensionCoverage(dimension=dim_name)
    
    def update_from_text(self, text: str) -> List[str]:
        """
        Update coverage from text. Returns list of dimensions that were updated.
        """
        framework = get_dimension_framework(self.sector)
        updated_dims = []
        
        for dim_name, keywords in framework.items():
            if self.dimensions[dim_name].update(text, keywords):
                updated_dims.append(dim_name)
        
        return updated_dims
    
    def get_uncovered_dimensions(self) -> List[str]:
        """Get dimensions that haven't been covered"""
        return [
            dim for dim, coverage in self.dimensions.items()
            if not coverage.covered
        ]
    
    def get_low_confidence_dimensions(self) -> List[str]:
        """Get dimensions with low confidence that need more depth"""
        return [
            dim for dim, coverage in self.dimensions.items()
            if coverage.covered and coverage.confidence == "low"
        ]
    
    def get_coverage_percentage(self) -> float:
        """Get overall coverage percentage"""
        total = len(self.dimensions)
        covered = sum(1 for d in self.dimensions.values() if d.covered)
        return (covered / total * 100) if total > 0 else 0.0
    
    def is_comprehensive(self) -> bool:
        """Check if coverage is comprehensive (allow 2 missing dimensions)"""
        uncovered = len(self.get_uncovered_dimensions())
        return uncovered <= 2


# ============================================================================
# SEMANTIC SIMILARITY CHECKER
# ============================================================================

@dataclass
class SimilarityChecker:
    """Check semantic similarity between queries to prevent repetition"""
    threshold: float = 0.7  # 70% similarity = too similar
    
    def normalize_query(self, query: str) -> str:
        """Normalize query for comparison"""
        # Lowercase
        q = query.lower()
        # Remove common filler words
        fillers = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"]
        words = q.split()
        words = [w for w in words if w not in fillers]
        # Remove punctuation
        q = " ".join(words)
        q = re.sub(r'[^\w\s]', '', q)
        return q
    
    def extract_key_terms(self, query: str) -> Set[str]:
        """Extract key terms from query"""
        normalized = self.normalize_query(query)
        # Remove very common words
        stop_words = {"overview", "latest", "recent", "2024", "2025", "2026", "2027", "india", "sector"}
        words = set(normalized.split())
        return words - stop_words
    
    def calculate_similarity(self, query1: str, query2: str) -> float:
        """
        Calculate similarity between two queries.
        Returns value between 0.0 (completely different) and 1.0 (identical).
        """
        # Exact match
        if query1.lower().strip() == query2.lower().strip():
            return 1.0
        
        # Extract key terms
        terms1 = self.extract_key_terms(query1)
        terms2 = self.extract_key_terms(query2)
        
        if not terms1 or not terms2:
            return 0.0
        
        # Jaccard similarity (intersection over union)
        intersection = len(terms1 & terms2)
        union = len(terms1 | terms2)
        
        return intersection / union if union > 0 else 0.0
    
    def is_too_similar(self, new_query: str, previous_queries: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if new query is too similar to any previous query.
        Returns (is_similar, most_similar_query).
        """
        max_similarity = 0.0
        most_similar = None
        
        for prev_query in previous_queries:
            similarity = self.calculate_similarity(new_query, prev_query)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = prev_query
        
        is_similar = max_similarity >= self.threshold
        return is_similar, most_similar if is_similar else None


# ============================================================================
# THREAD EXTRACTION
# ============================================================================

@dataclass
class ResearchThread:
    """A thread to follow in research"""
    thread_type: str  # entity, metric, claim, gap
    content: str
    priority: int  # 1-10, higher = more important
    source: str  # where it came from
    
    def __hash__(self):
        return hash((self.thread_type, self.content.lower()))
    
    def __eq__(self, other):
        if not isinstance(other, ResearchThread):
            return False
        return self.thread_type == other.thread_type and self.content.lower() == other.content.lower()


class ThreadExtractor:
    """Extract interesting threads to follow from research findings"""
    
    # Company patterns (IT)
    IT_COMPANIES = ["microsoft", "google", "amazon", "ibm", "oracle", "salesforce", "sap",
                    "tcs", "infosys", "wipro", "hcl", "tech mahindra", "capgemini", "accenture"]
    
    # Company patterns (Pharma)
    PHARMA_COMPANIES = ["pfizer", "novartis", "roche", "gsk", "merck", "j&j", "johnson",
                        "sun pharma", "cipla", "dr reddy", "dr. reddy's", "lupin", "aurobindo",
                        "astrazeneca", "eli lilly"]
    
    # Number pattern
    NUMBER_PATTERN = re.compile(
        r'(?:₹|\$|€|£)?\s?\d+(?:,\d{3})*(?:\.\d+)?\s?(?:billion|million|bn|mn|cr|crore|%|percent)?',
        re.IGNORECASE
    )
    
    def extract_entities(self, text: str, sector: str) -> List[ResearchThread]:
        """Extract named entities (companies, products, etc.)"""
        threads = []
        text_lower = text.lower()
        
        # Extract companies
        companies = self.IT_COMPANIES if sector == "IT" else self.PHARMA_COMPANIES
        for company in companies:
            if company in text_lower:
                threads.append(ResearchThread(
                    thread_type="entity",
                    content=company.title(),
                    priority=7,  # Companies are high priority
                    source="entity_extraction"
                ))
        
        return threads
    
    def extract_metrics(self, text: str) -> List[ResearchThread]:
        """Extract numerical metrics"""
        threads = []
        matches = self.NUMBER_PATTERN.findall(text)
        
        for match in matches[:5]:  # Limit to top 5 numbers
            # Get context around the number
            idx = text.find(match)
            if idx != -1:
                start = max(0, idx - 50)
                end = min(len(text), idx + len(match) + 50)
                context = text[start:end].strip()
                
                threads.append(ResearchThread(
                    thread_type="metric",
                    content=f"{match} ({context[:60]}...)",
                    priority=8,  # Metrics are high priority
                    source="metric_extraction"
                ))
        
        return threads
    
    def extract_claims(self, text: str) -> List[ResearchThread]:
        """Extract qualitative claims that need quantification"""
        threads = []
        
        # Patterns that indicate claims needing quantification
        claim_patterns = [
            (r'strong\s+(?:growth|performance|position)', "strong claim", 6),
            (r'market\s+leader', "leadership claim", 7),
            (r'facing\s+(?:challenges|headwinds|pressure)', "challenge claim", 6),
            (r'recently\s+(?:launched|announced|acquired)', "recent event", 7),
            (r'expected\s+(?:to|in)\s+\d{4}', "future event", 6),
        ]
        
        for pattern, description, priority in claim_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                threads.append(ResearchThread(
                    thread_type="claim",
                    content=context,
                    priority=priority,
                    source="claim_extraction"
                ))
        
        return threads
    
    def extract_threads(self, findings: List[Dict[str, Any]], sector: str) -> List[ResearchThread]:
        """
        Extract all threads from findings.
        Returns deduplicated, prioritized list of threads.
        """
        all_threads = set()
        
        for finding in findings[-3:]:  # Focus on last 3 findings
            # Combine query and insights
            query = finding.get("query", "")
            insights = finding.get("key_insights", [])
            text = f"{query} {' '.join(str(i) for i in insights)}"
            
            # Extract different types of threads
            all_threads.update(self.extract_entities(text, sector))
            all_threads.update(self.extract_metrics(text))
            all_threads.update(self.extract_claims(text))
        
        # Sort by priority (highest first)
        sorted_threads = sorted(all_threads, key=lambda t: t.priority, reverse=True)
        return sorted_threads[:10]  # Return top 10


# ============================================================================
# QUERY CONSTRUCTION
# ============================================================================

class QueryConstructor:
    """Construct well-formed natural language queries"""
    
    # Query templates by research phase
    OVERVIEW_TEMPLATES = [
        "{company} overview financial performance {sector} 2026",
        "{topic} market landscape key players trends 2026",
        "{company} {sector} business highlights recent developments 2025-2026"
    ]
    
    DEEP_DIVE_TEMPLATES = [
        "{company} {aspect} detailed breakdown 2025-2026",
        "{entity} revenue contribution market share adoption rate",
        "{company} {segment} growth rate year-over-year comparison",
        "{company} {metric} trend analysis 2023-2026"
    ]
    
    COMPARATIVE_TEMPLATES = [
        "{company} vs {competitor} {aspect} comparison {sector}",
        "{company} market position competitive advantages vs {competitor}",
        "{company} {competitor} {metric} comparison India 2026"
    ]
    
    FORWARD_TEMPLATES = [
        "{company} future outlook growth projections 2026-2028",
        "{company} key risks challenges {sector} latest analysis",
        "{sector} trends impact on {company} opportunities 2026"
    ]
    
    VALIDATION_TEMPLATES = [
        "{company} Q{quarter} {year} earnings financial results verification",
        "{metric} {company} latest official data 2026",
        "{company} {aspect} validation latest quarter"
    ]
    
    def construct_overview_query(self, company: str, sector: str) -> str:
        """Construct overview query"""
        import random
        template = random.choice(self.OVERVIEW_TEMPLATES)
        return template.format(company=company, sector=sector, topic=f"{company} {sector}")
    
    def construct_deep_dive_query(self, company: str, aspect: str, sector: str) -> str:
        """Construct deep dive query"""
        import random
        template = random.choice(self.DEEP_DIVE_TEMPLATES)
        return template.format(
            company=company,
            aspect=aspect,
            entity=aspect,
            segment=aspect,
            metric=aspect,
            sector=sector
        )
    
    def construct_comparative_query(self, company: str, competitor: str, aspect: str, sector: str) -> str:
        """Construct comparative query"""
        import random
        template = random.choice(self.COMPARATIVE_TEMPLATES)
        return template.format(
            company=company,
            competitor=competitor,
            aspect=aspect,
            metric=aspect,
            sector=sector
        )
    
    def construct_forward_query(self, company: str, sector: str) -> str:
        """Construct forward-looking query"""
        import random
        template = random.choice(self.FORWARD_TEMPLATES)
        return template.format(company=company, sector=sector)
    
    def construct_validation_query(self, company: str, metric: str) -> str:
        """Construct validation query"""
        import random
        template = random.choice(self.VALIDATION_TEMPLATES)
        return template.format(
            company=company,
            metric=metric,
            aspect=metric,
            quarter="Q3",  # Default to latest quarter
            year="2025"
        )
    
    def validate_query_quality(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate query quality.
        Returns (is_valid, error_message).
        """
        # Check length
        if len(query) < 10:
            return False, "Query too short"
        
        if len(query) > 200:
            return False, "Query too long"
        
        # Check for fragments
        if query.startswith("validate ") and len(query.split()) < 4:
            return False, "Query is a fragment"
        
        # Check for malformed patterns
        malformed_patterns = [
            r'\$\d+.*ghlights',  # "$75.49 billion ghlights..."
            r'\{.*\}',  # JSON-like
            r'^[^a-zA-Z]+',  # Starts with non-letters
        ]
        
        for pattern in malformed_patterns:
            if re.search(pattern, query):
                return False, "Query is malformed"
        
        # Check word count
        words = query.split()
        if len(words) < 3:
            return False, "Query too few words"
        
        return True, None


# ============================================================================
# QUERY HISTORY
# ============================================================================

@dataclass
class QueryHistory:
    """Track query history and prevent repetition"""
    queries: List[str] = field(default_factory=list)
    similarity_checker: SimilarityChecker = field(default_factory=SimilarityChecker)
    
    def add_query(self, query: str) -> None:
        """Add query to history"""
        self.queries.append(query)
    
    def is_repetitive(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query is repetitive.
        Returns (is_repetitive, similar_query).
        """
        return self.similarity_checker.is_too_similar(query, self.queries)
    
    def get_recent_queries(self, n: int = 5) -> List[str]:
        """Get n most recent queries"""
        return self.queries[-n:] if self.queries else []


# ============================================================================
# RESEARCH PHASE MANAGER
# ============================================================================

class ResearchPhase:
    """Research phase enum"""
    OVERVIEW = "overview"
    DEEP_DIVE = "deep_dive"
    COMPARATIVE = "comparative"
    FORWARD = "forward"
    VALIDATION = "validation"


def findings_similarity(finding1: Dict[str, Any], finding2: Dict[str, Any]) -> float:
    """
    Calculate similarity between two findings to detect diminishing returns.
    Returns value between 0.0 (completely different) and 1.0 (identical).
    """
    # Extract insights from both findings
    insights1 = finding1.get("key_insights", [])
    insights2 = finding2.get("key_insights", [])
    
    if not insights1 or not insights2:
        return 0.0
    
    # Combine insights into text
    text1 = " ".join(str(i) for i in insights1).lower()
    text2 = " ".join(str(i) for i in insights2).lower()
    
    # Extract words (simple tokenization)
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


@dataclass
class PhaseManager:
    """Manage research phase transitions"""
    current_phase: str = ResearchPhase.OVERVIEW
    steps_in_phase: int = 0
    total_steps: int = 0
    
    def should_advance_phase(self, coverage_tracker: CoverageTracker, findings: List[Dict]) -> bool:
        """Determine if should advance to next phase"""
        # Phase-specific advancement logic
        if self.current_phase == ResearchPhase.OVERVIEW:
            # Advance after 1-2 overview queries
            return self.steps_in_phase >= 2
        
        elif self.current_phase == ResearchPhase.DEEP_DIVE:
            # Advance after 3-5 deep dives OR coverage >50%
            return self.steps_in_phase >= 5 or coverage_tracker.get_coverage_percentage() > 50
        
        elif self.current_phase == ResearchPhase.COMPARATIVE:
            # Advance after 2-3 comparisons
            return self.steps_in_phase >= 3
        
        elif self.current_phase == ResearchPhase.FORWARD:
            # Advance after 2 forward-looking queries
            return self.steps_in_phase >= 2
        
        elif self.current_phase == ResearchPhase.VALIDATION:
            # Validation is final phase
            return self.steps_in_phase >= 2
        
        return False
    
    def advance_phase(self) -> str:
        """Advance to next phase"""
        phase_order = [
            ResearchPhase.OVERVIEW,
            ResearchPhase.DEEP_DIVE,
            ResearchPhase.COMPARATIVE,
            ResearchPhase.FORWARD,
            ResearchPhase.VALIDATION
        ]
        
        current_idx = phase_order.index(self.current_phase)
        if current_idx < len(phase_order) - 1:
            self.current_phase = phase_order[current_idx + 1]
            self.steps_in_phase = 0
        
        return self.current_phase
    
    def record_step(self) -> None:
        """Record a step in current phase"""
        self.steps_in_phase += 1
        self.total_steps += 1
