from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Tuple


class QueryType(str, Enum):
    COMPANY_DEEP_DIVE = "company_deep_dive"
    SECTOR_TREND = "sector_trend"
    COMPETITIVE_COMPARISON = "competitive_comparison"
    STRATEGIC_IMPACT = "strategic_impact"


class QueryComplexity(str, Enum):
    SIMPLE = "simple"          # 5-7 steps
    MEDIUM = "medium"          # 8-12 steps
    COMPLEX = "complex"        # 13-18 steps
    DEEP = "deep"              # 18-25+ steps (we cap at max_steps)


@dataclass(frozen=True)
class ComplexityPlan:
    query_type: QueryType
    complexity: QueryComplexity
    min_steps: int
    max_steps: int


_RE_COMPARE = re.compile(r"\b(compare|vs\.?|versus|comparison|compared to)\b", re.I)
_RE_TREND = re.compile(r"\b(trend|trends|sector|industry|market size|cagr|outlook|forecast|drivers)\b", re.I)
_RE_IMPACT = re.compile(r"\b(impact|transformation|disruption|scenario|future of|roadmap)\b", re.I)
_RE_METRIC_LOOKUP = re.compile(r"\b(market cap|market capitalization|pe ratio|p/e|price|stock price|revenue|profit|margin)\b", re.I)


def assess_query_type(query: str) -> QueryType:
    q = (query or "").strip()
    if not q:
        return QueryType.COMPANY_DEEP_DIVE

    if _RE_COMPARE.search(q):
        return QueryType.COMPETITIVE_COMPARISON
    if _RE_IMPACT.search(q):
        return QueryType.STRATEGIC_IMPACT
    if _RE_TREND.search(q):
        return QueryType.SECTOR_TREND
    return QueryType.COMPANY_DEEP_DIVE


def assess_complexity(query: str, query_type: QueryType) -> QueryComplexity:
    """
    Heuristic complexity assessment.
    - We intentionally bias toward deeper research for IT/Pharma strategy/sector queries.
    """
    q = (query or "").strip()
    length = len(q)

    # Simple: explicit single-metric lookup style.
    if _RE_METRIC_LOOKUP.search(q) and length < 80 and query_type == QueryType.COMPANY_DEEP_DIVE:
        return QueryComplexity.SIMPLE

    # Deep: impact/market transformation questions tend to be multi-dimensional.
    if query_type == QueryType.STRATEGIC_IMPACT:
        return QueryComplexity.DEEP

    # Competitive comparisons are typically complex.
    if query_type == QueryType.COMPETITIVE_COMPARISON:
        return QueryComplexity.COMPLEX

    # Sector trends usually medium-to-deep depending on specificity/length.
    if query_type == QueryType.SECTOR_TREND:
        return QueryComplexity.DEEP if length >= 80 else QueryComplexity.COMPLEX

    # Default company deep dive: medium or complex depending on query breadth.
    if length >= 120:
        return QueryComplexity.COMPLEX
    return QueryComplexity.MEDIUM


def plan_for_query(query: str) -> ComplexityPlan:
    qtype = assess_query_type(query)
    complexity = assess_complexity(query, qtype)

    if complexity == QueryComplexity.SIMPLE:
        return ComplexityPlan(qtype, complexity, min_steps=5, max_steps=12)
    if complexity == QueryComplexity.MEDIUM:
        return ComplexityPlan(qtype, complexity, min_steps=8, max_steps=18)
    if complexity == QueryComplexity.COMPLEX:
        return ComplexityPlan(qtype, complexity, min_steps=13, max_steps=22)
    # DEEP - ensure 18-20 steps for comprehensive research
    return ComplexityPlan(qtype, complexity, min_steps=18, max_steps=25)


def summarize_plan(plan: ComplexityPlan) -> Tuple[str, int, int]:
    """Convenience for logging/UI."""
    return plan.complexity.value, plan.min_steps, plan.max_steps

