from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from utils.logger import log

class PharmaSectorAgent(BaseAgent):
    """Specialized agent for Pharma sector research with domain-specific knowledge"""

    # Deep-research dimension framework (aligned with product requirements)
    DIMENSIONS_FRAMEWORK = [
        "Financial Performance",
        "Product Portfolio",
        "Drug Pipeline",
        "Market Position",
        "Regulatory Status",
        "Manufacturing & Distribution",
        "Recent Developments",
        "R&D Innovation",
        "Future Outlook",
        "Competitive Comparison",
    ]

    QUERY_TEMPLATES = {
        "financial_deep_dive": "{company} {area} revenue margins 2025 2026",
        "pipeline_analysis": "{company} {drug} clinical trial status phase 2025 2026",
        "competitive": "{company} vs {competitor} {area} market share comparison 2025 2026",
        "regulatory": "{company} {drug} FDA approval patent expiry timeline 2024 2026",
        "portfolio_mix": "{company} generic vs branded mix {area} 2025 2026",
        "market_dynamics": "India {area} market size growth drivers 2026",
    }
    
    # Pharma Sector Focus Areas with canonical keywords for matching
    FOCUS_AREAS = [
        "Drug pipeline (clinical trials)",
        "R&D spending",
        "Patent expirations",
        "Regulatory approvals",
        "Generic vs branded drug mix",
        "Market exclusivity periods",
        "Biosimilar development",
        "Therapeutic areas focus",
        "Geographic market presence",
        "Manufacturing capabilities"
    ]
    
    # Canonical keywords per focus area for precise matching
    FOCUS_AREA_KEYWORDS = {
        "Drug pipeline (clinical trials)": ["pipeline", "clinical trial", "clinical", "phase", "trial", "drug development"],
        "R&D spending": ["r&d", "research and development", "research", "development", "rd spending"],
        "Patent expirations": ["patent", "patent expiration", "patent expiry", "patent cliff", "exclusivity"],
        "Regulatory approvals": ["regulatory", "approval", "fda", "ema", "regulatory approval", "drug approval"],
        "Generic vs branded drug mix": ["generic", "branded", "generic drug", "branded drug", "generic vs branded"],
        "Market exclusivity periods": ["exclusivity", "market exclusivity", "exclusive", "exclusivity period"],
        "Biosimilar development": ["biosimilar", "biosimilar development", "biologic", "biologics"],
        "Therapeutic areas focus": ["therapeutic", "therapeutic area", "therapeutic focus", "indication"],
        "Geographic market presence": ["geographic", "geography", "region", "international", "domestic", "market presence"],
        "Manufacturing capabilities": ["manufacturing", "manufacturing capability", "production", "facility", "capacity"]
    }
    
    # Pharma Sector Key Metrics
    KEY_METRICS = [
        "R&D as % of revenue",
        "Success rate in clinical trials",
        "Time to market for new drugs",
        "Patent cliff impact",
        "Generic competition exposure",
        "Pipeline value",
        "Number of drugs in Phase I/II/III",
        "FDA approvals (recent)",
        "Market share by therapeutic area",
        "Revenue from top 5 products"
    ]
    
    # Pharma Sector Keywords for relevance scoring and filtering
    KEYWORDS = [
        "drug", "medicine", "clinical", "FDA", "pharmaceutical", "Sun Pharma",
        "Dr. Reddy's", "Cipla", "Lupin", "Aurobindo", "clinical trial",
        "patent", "generic", "biosimilar", "therapeutic", "regulatory",
        "approval", "pipeline", "R&D", "research and development", "formulation"
    ]
    
    # Common pharma companies
    PHARMA_COMPANIES = [
        "Sun Pharma", "Dr. Reddy's", "Cipla", "Lupin", "Aurobindo",
        "Pfizer", "Novartis", "Roche", "GSK", "Merck"
    ]
    
    # Indian pharma companies (for focused analysis)
    INDIAN_PHARMA_COMPANIES = ["Sun Pharma", "Dr. Reddy's", "Cipla", "Lupin", "Aurobindo"]
    
    # Therapeutic areas
    THERAPEUTIC_AREAS = [
        "oncology", "cardiovascular", "diabetes", "respiratory",
        "CNS", "gastrointestinal", "dermatology", "ophthalmology"
    ]
    
    def __init__(self):
        super().__init__(model="gpt-4o", temperature=0.3)
        log.info("Initialized PharmaSectorAgent")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for keyword matching (lowercase, single space)
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        return " ".join(text.lower().split())
    
    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        Check if text contains any of the given keywords (word-boundary aware)
        
        Args:
            text: Text to search in
            keywords: List of keywords to match
            
        Returns:
            True if any keyword is found
        """
        normalized_text = self._normalize_text(text)
        for keyword in keywords:
            normalized_keyword = keyword.lower()
            # Check for whole word or phrase match
            if normalized_keyword in normalized_text:
                return True
        return False
    
    async def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Enhance query with Pharma sector-specific context
        
        Args:
            query: Original query
            context: Optional context from previous research
            
        Returns:
            Enhanced query with Pharma sector focus
        """
        context_str = ""
        if context:
            findings = context.get("findings", [])
            if findings:
                context_str = f"\nPrevious findings: {findings[-1].get('key_insights', [])[:2]}"
        
        # Use KEYWORDS to detect relevant pharma terms in query
        query_lower = self._normalize_text(query)
        detected_keywords = [kw for kw in self.KEYWORDS if kw.lower() in query_lower]
        
        if detected_keywords:
            focus_note = f"Pharma Sector Focus: {', '.join(detected_keywords[:3])}"
        else:
            focus_note = "Pharma Sector Focus: drug pipeline, R&D investments, regulatory approvals, patent landscape, generic/branded mix"
        
        # Add recent date filter to prioritize 2024-2025 sources
        date_filter = " (2024 OR 2025 OR recent OR latest)"
        
        enhanced = f"{query}{date_filter} [{focus_note}]"
        if context_str:
            enhanced += context_str
        return enhanced

    def build_dimension_query(
        self,
        *,
        company: str,
        dimension: str,
        competitor: Optional[str] = None,
        topic: Optional[str] = None,
        therapeutic_area: Optional[str] = None,
        drug: Optional[str] = None,
    ) -> str:
        dim = (dimension or "").lower()
        area = therapeutic_area or topic or "respiratory"
        if "competitive" in dim and competitor:
            return self.QUERY_TEMPLATES["competitive"].format(company=company, competitor=competitor, area=area)
        if "pipeline" in dim:
            return self.QUERY_TEMPLATES["pipeline_analysis"].format(company=company, drug=drug or (topic or "pipeline"))
        if "regulatory" in dim:
            return self.QUERY_TEMPLATES["regulatory"].format(company=company, drug=drug or (topic or "product"))
        if "financial" in dim:
            return self.QUERY_TEMPLATES["financial_deep_dive"].format(company=company, area=area)
        if "portfolio" in dim:
            return self.QUERY_TEMPLATES["portfolio_mix"].format(company=company, area=area)
        if "manufacturing" in dim:
            return f"{company} manufacturing facilities capacity quality compliance 2025 2026"
        if "outlook" in dim or "future" in dim:
            return f"{company} outlook guidance risks pipeline catalysts 2026 2028"
        return f"{company} {dimension} 2026"
    
    def _extract_focus_areas(self, normalized_text: str) -> List[str]:
        """Extract covered focus areas from normalized text"""
        covered_areas = []
        for area in self.FOCUS_AREAS:
            area_keywords = self.FOCUS_AREA_KEYWORDS.get(area, [area.lower()])
            if self._matches_keywords(normalized_text, area_keywords):
                covered_areas.append(area)
        return covered_areas
    
    def _extract_companies(self, normalized_text: str) -> List[str]:
        """Extract mentioned companies from normalized text"""
        mentioned = []
        for company in self.PHARMA_COMPANIES:
            if company.lower() in normalized_text:
                mentioned.append(company)
        return mentioned
    
    def _extract_therapeutic_areas(self, normalized_text: str) -> List[str]:
        """Extract mentioned therapeutic areas from normalized text"""
        mentioned = []
        for area in self.THERAPEUTIC_AREAS:
            if area.lower() in normalized_text:
                mentioned.append(area)
        return mentioned
    
    def _extract_key_metrics(self, normalized_text: str) -> List[str]:
        """Extract key metrics mentions from normalized text"""
        metrics_found = []
        if "patent" in normalized_text:
            metrics_found.append("Patent information")
        if "clinical trial" in normalized_text or "clinical" in normalized_text:
            metrics_found.append("Clinical trial data")
        if "r&d" in normalized_text or "research" in normalized_text:
            metrics_found.append("R&D spending")
        return metrics_found
    
    async def extract_metrics(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract Pharma sector-specific metrics from findings
        
        Args:
            findings: Research findings
            
        Returns:
            Dictionary of Pharma-specific metrics
        """
        metrics = {
            "focus_areas_covered": [],
            "key_metrics_found": [],
            "companies_mentioned": [],
            "therapeutic_areas": [],
            "drugs_mentioned": [],
            "keyword_relevance_score": 0.0
        }
        
        # Normalize all insights once for efficiency
        all_text = []
        for finding in findings:
            insights = finding.get("key_insights", [])
            query = finding.get("query", "")
            combined_text = f"{query} {' '.join(str(insight) for insight in insights)}"
            all_text.append(combined_text)
        
        combined_normalized = self._normalize_text(" ".join(all_text))
        
        # Extract metrics using helper methods
        metrics["focus_areas_covered"] = self._extract_focus_areas(combined_normalized)
        metrics["companies_mentioned"] = self._extract_companies(combined_normalized)
        metrics["therapeutic_areas"] = self._extract_therapeutic_areas(combined_normalized)
        metrics["key_metrics_found"] = self._extract_key_metrics(combined_normalized)
        
        # Calculate keyword relevance score using KEYWORDS
        matched_keywords = sum(1 for kw in self.KEYWORDS if kw.lower() in combined_normalized)
        metrics["keyword_relevance_score"] = min(matched_keywords / len(self.KEYWORDS), 1.0)
        
        return metrics
    
    async def generate_follow_up_query(
        self,
        original_query: str,
        previous_findings: List[Dict[str, Any]],
        accumulated_knowledge: str = ""
    ) -> Optional[str]:
        """
        Generate next research query based on previous findings (iterative intelligence)
        Uses prioritization by frequency, novelty, and coverage gaps
        
        Args:
            original_query: Original user query
            previous_findings: Findings from previous research steps
            accumulated_knowledge: Accumulated knowledge so far (reserved for future use)
            
        Returns:
            Next query to research, or None if research is complete
        """
        # Use accumulated_knowledge if provided (future enhancement)
        _ = accumulated_knowledge  # Reserved for future use
        
        if not previous_findings:
            # First query - broad overview with recent date emphasis
            return f"{original_query} - pharmaceutical sector overview and recent developments (2024-2025)"
        
        # Analyze all previous findings to identify patterns
        all_insights_text = " ".join(
            " ".join(str(insight) for insight in finding.get("key_insights", []))
            for finding in previous_findings
        )
        normalized_insights = self._normalize_text(all_insights_text)
        
        # Get coverage to identify gaps
        coverage = await self.validate_coverage(previous_findings)
        missing_areas = coverage.get("missing_areas", [])
        
        # Thread candidates with priority scores
        thread_candidates = []
        
        # Priority 1: Coverage gaps (highest priority - fill missing areas)
        for area in missing_areas[:2]:  # Top 2 missing areas
            thread_candidates.append({
                "thread": f"{area.lower()} - detailed analysis",
                "priority": 10,
                "reason": "coverage_gap"
            })
        
        # Priority 2: High-frequency interesting threads (mentioned multiple times)
        thread_patterns = {
            "Pipeline": {
                "keywords": ["pipeline", "clinical trial", "clinical", "phase", "trial"],
                "thread": "drug pipeline and clinical trial progress, pipeline value and success rates"
            },
            "R&D": {
                "keywords": ["r&d", "research", "development", "research and development"],
                "thread": "R&D spending as percentage of revenue, R&D efficiency and productivity"
            },
            "Patent": {
                "keywords": ["patent", "exclusivity", "patent expiration", "patent cliff"],
                "thread": "patent expirations and patent cliff impact, generic competition timeline"
            },
            "Biosimilar": {
                "keywords": ["biosimilar", "biologic", "biologics"],
                "thread": "biosimilar market opportunities and competition"
            },
            "Generic": {
                "keywords": ["generic", "generic drug", "generic vs branded"],
                "thread": "generic drug portfolio and market share, generic vs branded revenue mix"
            }
        }
        
        for pattern_name, pattern_data in thread_patterns.items():
            mention_count = sum(1 for kw in pattern_data["keywords"] if kw in normalized_insights)
            if mention_count >= 2:  # Mentioned at least twice
                thread_candidates.append({
                    "thread": pattern_data["thread"],
                    "priority": 5 + mention_count,  # Higher frequency = higher priority
                    "reason": "high_frequency"
                })
        
        # Priority 3: Company-specific deep dives
        for company in self.INDIAN_PHARMA_COMPANIES:
            if company.lower() in normalized_insights:
                # Check if we already have deep coverage
                company_mentions = sum(1 for finding in previous_findings 
                                     if company.lower() in self._normalize_text(finding.get("query", "")))
                if company_mentions < 2:  # Not deeply covered yet
                    thread_candidates.append({
                        "thread": f"{company} drug pipeline and R&D strategy, regulatory approvals and FDA status",
                        "priority": 3,
                        "reason": "company_deep_dive"
                    })
        
        # Sort by priority (highest first) and select top candidate
        if thread_candidates:
            thread_candidates.sort(key=lambda x: x["priority"], reverse=True)
            selected_thread = thread_candidates[0]["thread"]
            next_query = f"{original_query} - {selected_thread}"
        else:
            # Generic follow-up based on original query
            next_query = f"{original_query} - detailed financial analysis and drug pipeline"
        
        return next_query
    
    async def validate_coverage(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate if research has covered key Pharma sector dimensions
        
        Args:
            findings: All research findings
            
        Returns:
            Coverage assessment with missing areas
        """
        covered_areas = set()
        all_insights = []
        
        # Normalize all findings text once
        all_text = []
        for finding in findings:
            query = finding.get("query", "")
            insights = finding.get("key_insights", [])
            all_insights.extend(insights)
            combined = f"{query} {' '.join(str(insight) for insight in insights)}"
            all_text.append(combined)
        
        combined_normalized = self._normalize_text(" ".join(all_text))
        
        # Check coverage using canonical keywords
        for area in self.FOCUS_AREAS:
            area_keywords = self.FOCUS_AREA_KEYWORDS.get(area, [area.lower()])
            if self._matches_keywords(combined_normalized, area_keywords):
                covered_areas.add(area)
        
        missing_areas = [area for area in self.FOCUS_AREAS if area not in covered_areas]
        
        return {
            "coverage_percentage": (len(covered_areas) / len(self.FOCUS_AREAS)) * 100,
            "covered_areas": list(covered_areas),
            "missing_areas": missing_areas,
            "total_findings": len(findings),
            "is_comprehensive": len(missing_areas) <= 2  # Allow 2 missing areas
        }
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Process Pharma sector query (implements BaseAgent interface)
        
        Args:
            query: Research query
            context: Optional context
            **kwargs: Additional parameters
            
        Returns:
            Processed result with Pharma sector enhancements
        """
        enhanced_query = await self.enhance_query(query, context)
        
        findings = context.get("findings", []) if context else []
        metrics = await self.extract_metrics(findings)
        coverage = await self.validate_coverage(findings)
        
        return {
            "enhanced_query": enhanced_query,
            "sector": "Pharma",
            "metrics": metrics,
            "coverage": coverage,
            "focus_areas": self.FOCUS_AREAS,
            "key_metrics": self.KEY_METRICS
        }


