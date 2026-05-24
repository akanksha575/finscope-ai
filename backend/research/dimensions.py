from __future__ import annotations

from typing import Dict, List

from research.complexity import QueryType


# Canonical dimension frameworks (user-facing names) + keywords for matching.
# We keep keywords intentionally redundant; the goal is recall for coverage tracking.

IT_COMPANY_DIMENSIONS: Dict[str, List[str]] = {
    "Financial Performance": ["revenue", "profit", "margin", "growth", "guidance", "cash flow", "cagr", "q1", "q2", "q3", "q4", "fy"],
    "Market Position": ["market share", "ranking", "leader", "positioning", "competitive", "top", "client base"],
    "Service Portfolio": ["services", "offerings", "portfolio", "revenue mix", "segment", "cloud", "digital", "bpo", "infrastructure"],
    "Technology Capabilities": ["ai", "genai", "machine learning", "platform", "cloud", "cybersecurity", "proprietary", "automation"],
    "Operational Metrics": ["utilization", "attrition", "headcount", "employee", "revenue per employee", "offshore", "onsite", "productivity"],
    "Recent Developments": ["deal", "tcv", "partnership", "acquisition", "leadership", "launch", "announcement", "recent", "latest"],
    "Strategic Direction": ["strategy", "investment", "capex", "focus", "vertical", "geography", "expansion", "roadmap"],
    "Future Outlook": ["outlook", "forecast", "projection", "risks", "opportunities", "scenario", "2026", "2027", "2028"],
}

IT_SECTOR_DIMENSIONS: Dict[str, List[str]] = {
    "Market Size & Growth": ["market size", "cagr", "growth", "forecast", "projection"],
    "Key Drivers": ["drivers", "demand", "spending", "macro", "regulatory", "policy"],
    "Major Players": ["top players", "ranking", "market share", "leaders", "competitive landscape"],
    "Emerging Technologies": ["genai", "ai", "cloud", "zero trust", "data", "automation", "platform engineering"],
    "Client Behavior": ["client spending", "budget", "priorities", "vertical", "bFSI", "manufacturing", "retail", "healthcare"],
    "Competitive Dynamics": ["pricing", "rate card", "consolidation", "new entrants", "hyperscalers", "disruption"],
    "Regulatory Environment": ["compliance", "data protection", "gdpr", "sox", "ai act", "regulation"],
    "Talent Landscape": ["talent", "attrition", "wage", "hiring", "skill", "compensation"],
}

PHARMA_COMPANY_DIMENSIONS: Dict[str, List[str]] = {
    "Financial Performance": ["revenue", "profit", "margin", "cash flow", "r&d", "r and d", "ebitda", "fy", "q1", "q2", "q3", "q4"],
    "Drug Portfolio": ["portfolio", "products", "top drugs", "branded", "generic", "mix", "revenue breakdown"],
    "Pipeline Analysis": ["pipeline", "clinical trial", "phase i", "phase ii", "phase iii", "nda", "bla", "trial"],
    "R&D Strategy": ["r&d strategy", "partnership", "licensing", "collaboration", "therapeutic area", "investment"],
    "Regulatory Status": ["fda", "ema", "approval", "inspection", "warning letter", "compliance", "pending"],
    "Market Position": ["market share", "leader", "competition", "positioning"],
    "Manufacturing Capabilities": ["manufacturing", "facility", "capacity", "plant", "quality", "gmp"],
    "Patent Landscape": ["patent", "exclusivity", "patent cliff", "expiration", "litigation"],
    "Future Outlook": ["outlook", "forecast", "risks", "opportunities", "guidance", "2026", "2027", "2028"],
}

PHARMA_SECTOR_DIMENSIONS: Dict[str, List[str]] = {
    "Market Dynamics": ["market size", "growth", "pricing pressure", "competition", "access"],
    "Innovation Trends": ["biosimilar", "gene therapy", "cell therapy", "new modalities", "ai drug discovery"],
    "R&D Landscape": ["r&d spending", "success rate", "time to market", "trial success"],
    "Regulatory Environment": ["approval timeline", "fda", "ema", "policy", "guidance"],
    "Patent Developments": ["patent cliff", "expiration", "evergreening", "exclusivity"],
    "Competitive Evolution": ["m&a", "consolidation", "new entrants", "competition"],
    "Pricing & Access": ["pricing", "reimbursement", "price control", "market access"],
    "Global Expansion": ["exports", "us market", "eu market", "regulatory approvals", "partnerships"],
}

ARCHITECTURE_COMPANY_DIMENSIONS: Dict[str, List[str]] = {
    "Financial Performance": ["revenue", "profit", "margin", "net income", "earnings", "ebitda", "cash flow", "q1", "q2", "q3", "q4", "fy"],
    "Project Portfolio": ["projects", "portfolio", "design", "construction", "infrastructure", "building", "major projects", "backlog"],
    "Service Mix": ["service mix", "segment", "architectural design", "planning", "urban design", "consulting", "engineering", "revenue breakdown"],
    "Design Capabilities": ["sustainable design", "green building", "bim", "technology", "innovation", "awards", "certification", "leed"],
    "Market Position": ["market share", "ranking", "leader", "positioning", "competitive", "reputation", "awards", "recognition"],
    "Geographic Presence": ["geographic", "locations", "international", "domestic", "global", "regional", "expansion"],
    "Recent Developments": ["merger", "acquisition", "partnership", "launch", "announcement", "deal", "major project", "contract"],
    "Strategic Direction": ["strategy", "investment", "focus", "expansion", "vertical", "geography", "roadmap"],
    "Future Outlook": ["outlook", "forecast", "risks", "opportunities", "guidance", "pipeline", "2026", "2027", "2028"],
}

ARCHITECTURE_SECTOR_DIMENSIONS: Dict[str, List[str]] = {
    "Market Size & Growth": ["market size", "cagr", "growth", "forecast", "projection", "construction spending", "infrastructure investment"],
    "Key Drivers": ["urbanization", "population growth", "infrastructure spending", "regulatory", "policy", "sustainability", "government projects"],
    "Major Players": ["top firms", "ranking", "market share", "leaders", "competitive landscape", "architecture firms"],
    "Design Trends": ["sustainable design", "green building", "smart buildings", "biophilic design", "modular construction", "resilience"],
    "Regulatory Environment": ["building codes", "zoning", "permits", "regulation", "compliance", "environmental", "safety standards"],
    "Technology Trends": ["bim", "3d printing", "vr", "ar", "digital twin", "automation", "ai in design", "prefabrication"],
    "Competitive Dynamics": ["consolidation", "m&a", "new entrants", "disruption", "pricing", "fees", "bidding"],
    "Infrastructure Investment": ["infrastructure", "public works", "government spending", "transportation", "utilities", "renewable infrastructure"],
}

ENERGY_COMPANY_DIMENSIONS: Dict[str, List[str]] = {
    "Financial Performance": ["revenue", "profit", "margin", "cash flow", "ebitda", "capex", "operating income", "q1", "q2", "q3", "q4", "fy"],
    "Production Metrics": ["production", "output", "reserves", "refining", "capacity", "utilization", "throughput"],
    "Portfolio Mix": ["upstream", "downstream", "renewable", "oil", "gas", "renewable energy", "segment mix"],
    "Reserve Analysis": ["proven reserves", "probable reserves", "exploration", "discovery", "depletion"],
    "Refining & Processing": ["refining capacity", "refinery", "petrochemicals", "crude processing", "distillation"],
    "Market Position": ["market share", "ranking", "leader", "competitive", "positioning", "supply chain"],
    "Environmental & ESG": ["emissions", "carbon", "renewable", "solar", "wind", "sustainability", "esg", "net zero"],
    "Strategic Direction": ["strategy", "investment", "capex", "divestiture", "partnership", "joint venture"],
    "Future Outlook": ["outlook", "forecast", "risks", "opportunities", "guidance", "energy transition", "2026", "2027", "2028"],
}

ENERGY_SECTOR_DIMENSIONS: Dict[str, List[str]] = {
    "Market Dynamics": ["oil prices", "gas prices", "supply", "demand", "inventory", "opec", "geopolitical"],
    "Energy Transition": ["renewable energy", "solar", "wind", "clean energy", "decarbonization", "energy transition"],
    "Technology Trends": ["exploration technology", "drilling", "fracking", "renewable tech", "battery storage"],
    "Regulatory Environment": ["policy", "regulation", "subsidies", "carbon tax", "environmental", "climate"],
    "Geopolitical Factors": ["geopolitical", "sanctions", "trade", "supply chain", "security"],
    "Competitive Evolution": ["consolidation", "m&a", "new entrants", "market share", "competition"],
    "Infrastructure": ["pipeline", "refinery", "storage", "grid", "renewable infrastructure", "transmission"],
    "Investment Trends": ["capex", "investment", "funding", "venture capital", "green bonds"],
}


def get_dimension_keywords(sector: str, query_type: QueryType) -> Dict[str, List[str]]:
    if sector == "IT":
        if query_type in (QueryType.SECTOR_TREND, QueryType.STRATEGIC_IMPACT):
            return {**IT_SECTOR_DIMENSIONS, **IT_COMPANY_DIMENSIONS}
        return IT_COMPANY_DIMENSIONS
    if sector == "Pharma":
        if query_type in (QueryType.SECTOR_TREND, QueryType.STRATEGIC_IMPACT):
            return {**PHARMA_SECTOR_DIMENSIONS, **PHARMA_COMPANY_DIMENSIONS}
        return PHARMA_COMPANY_DIMENSIONS
    if sector == "Architecture":
        if query_type in (QueryType.SECTOR_TREND, QueryType.STRATEGIC_IMPACT):
            return {**ARCHITECTURE_SECTOR_DIMENSIONS, **ARCHITECTURE_COMPANY_DIMENSIONS}
        return ARCHITECTURE_COMPANY_DIMENSIONS
    if sector == "Energy":
        if query_type in (QueryType.SECTOR_TREND, QueryType.STRATEGIC_IMPACT):
            return {**ENERGY_SECTOR_DIMENSIONS, **ENERGY_COMPANY_DIMENSIONS}
        return ENERGY_COMPANY_DIMENSIONS
    # Unknown: include all frameworks to avoid missing coverage.
    return {
        **IT_COMPANY_DIMENSIONS, **IT_SECTOR_DIMENSIONS,
        **PHARMA_COMPANY_DIMENSIONS, **PHARMA_SECTOR_DIMENSIONS,
        **ARCHITECTURE_COMPANY_DIMENSIONS, **ARCHITECTURE_SECTOR_DIMENSIONS,
        **ENERGY_COMPANY_DIMENSIONS, **ENERGY_SECTOR_DIMENSIONS
    }


def get_dimensions(sector: str, query_type: QueryType) -> List[str]:
    return list(get_dimension_keywords(sector, query_type).keys())


def update_dimension_coverage(
    dimensions_covered: Dict[str, bool],
    dimension_keywords: Dict[str, List[str]],
    text: str,
) -> Dict[str, bool]:
    """
    Keyword-based coverage update. Returns a NEW dict (no in-place mutation) to make state updates safer.
    """
    normalized = (text or "").lower()
    updated = dict(dimensions_covered)
    for dim, kws in dimension_keywords.items():
        if updated.get(dim):
            continue
        for kw in kws:
            if kw.lower() in normalized:
                updated[dim] = True
                break
        updated.setdefault(dim, False)
    return updated

