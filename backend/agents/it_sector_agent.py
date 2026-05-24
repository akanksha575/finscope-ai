from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from utils.logger import log


class ITSectorAgent(BaseAgent):
    """Specialized agent for IT sector research with domain-specific knowledge"""

    # Deep-research dimension framework (aligned with product requirements)
    DIMENSIONS_FRAMEWORK = [
        "Financial Performance",
        "Market Position",
        "Product/Service Portfolio",
        "Client Base",
        "Talent & Operations",
        "Recent Developments",
        "Technology Innovation",
        "Future Outlook",
        "Competitive Comparison",
    ]

    # Query templates by dimension (use these for deterministic, progressive query planning)
    QUERY_TEMPLATES = {
        "financial_deep_dive": "{company} {metric} quarterly trends 2024 2026",
        "competitive": "{company} vs {competitor} {aspect} comparison India 2025 2026",
        "product_analysis": "{company} {product} revenue contribution market adoption 2025 2026",
        "client_portfolio": "{company} major clients wins {industry} 2026",
        "innovation": "{company} {technology} investments R&D spending 2025 2026",
        "market_dynamics": "India IT services {trend} impact analysis 2026",
    }
    
    # IT Sector Focus Areas with canonical keywords for matching
    FOCUS_AREAS = [
        "Cloud computing adoption",
        "Digital transformation services",
        "AI/ML integration",
        "Cybersecurity",
        "Talent acquisition and attrition",
        "Client concentration",
        "Geographic revenue mix",
        "SaaS and platform services",
        "DevOps and automation",
        "Data analytics and insights"
    ]
    
    # Canonical keywords per focus area for precise matching
    FOCUS_AREA_KEYWORDS = {
        "Cloud computing adoption": ["cloud", "aws", "azure", "gcp", "cloud computing", "cloud services"],
        "Digital transformation services": ["digital transformation", "digital", "transformation", "modernization"],
        "AI/ML integration": ["ai", "artificial intelligence", "machine learning", "ml", "neural", "deep learning"],
        "Cybersecurity": ["cybersecurity", "security", "cyber", "data protection", "encryption"],
        "Talent acquisition and attrition": ["talent", "attrition", "retention", "hiring", "employee", "workforce"],
        "Client concentration": ["client concentration", "customer concentration", "client mix", "diversification"],
        "Geographic revenue mix": ["geographic", "region", "geography", "international", "domestic"],
        "SaaS and platform services": ["saas", "platform", "software as a service", "subscription"],
        "DevOps and automation": ["devops", "automation", "ci/cd", "continuous integration", "deployment"],
        "Data analytics and insights": ["analytics", "data analytics", "insights", "business intelligence", "bi"]
    }
    
    # IT Sector Key Metrics
    KEY_METRICS = [
        "Revenue per employee",
        "Client addition rate",
        "Deal pipeline size",
        "Utilization rates",
        "Attrition rate",
        "Billable hours",
        "Average deal size",
        "Client retention rate",
        "Geographic revenue distribution",
        "Service mix (cloud vs traditional)"
    ]
    
    # IT Sector Keywords for relevance scoring and filtering
    KEYWORDS = [
        "software", "cloud", "SaaS", "technology", "Infosys", "TCS", "Wipro",
        "HCL", "Tech Mahindra", "digital transformation", "AI", "machine learning",
        "cybersecurity", "DevOps", "automation", "IT services", "consulting",
        "enterprise software", "platform", "API", "microservices", "containerization"
    ]
    
    # Common IT companies
    IT_COMPANIES = ["Infosys", "TCS", "Wipro", "HCL", "Tech Mahindra", "Microsoft", "Google", "Amazon", "IBM"]
    
    # Technology keywords for extraction
    TECH_KEYWORDS = ["cloud", "ai", "machine learning", "cybersecurity", "saas", "devops", "automation"]
    
    def __init__(self):
        super().__init__(model="gpt-4o", temperature=0.3)
        log.info("Initialized ITSectorAgent")
    
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
        Enhance query with IT sector-specific context
        
        Args:
            query: Original query
            context: Optional context from previous research
            
        Returns:
            Enhanced query with IT sector focus
        """
        context_str = ""
        if context:
            findings = context.get("findings", [])
            if findings:
                context_str = f"\nPrevious findings: {findings[-1].get('key_insights', [])[:2]}"
        
        # Use KEYWORDS to detect relevant IT terms in query
        query_lower = self._normalize_text(query)
        detected_keywords = [kw for kw in self.KEYWORDS if kw.lower() in query_lower]
        
        if detected_keywords:
            focus_note = f"IT Sector Focus: {', '.join(detected_keywords[:3])}"
        else:
            focus_note = "IT Sector Focus: cloud services, digital transformation, AI/ML capabilities, cybersecurity, talent management"
        
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
        metric: Optional[str] = None,
    ) -> str:
        """
        Minimal helper to construct focused queries without reusing the full original prompt.
        """
        dim = (dimension or "").lower()
        if "competitive" in dim and competitor:
            return self.QUERY_TEMPLATES["competitive"].format(company=company, competitor=competitor, aspect=topic or "cloud AI services")
        if "financial" in dim:
            return self.QUERY_TEMPLATES["financial_deep_dive"].format(company=company, metric=metric or "revenue profit margin")
        if "portfolio" in dim:
            return self.QUERY_TEMPLATES["product_analysis"].format(company=company, product=topic or "cloud AI services")
        if "client" in dim:
            return self.QUERY_TEMPLATES["client_portfolio"].format(company=company, industry=topic or "BFSI retail")
        if "talent" in dim or "operations" in dim:
            return f"{company} attrition utilization headcount trend FY2025 FY2026"
        if "innovation" in dim or "technology" in dim:
            return self.QUERY_TEMPLATES["innovation"].format(company=company, technology=topic or "GenAI cloud")
        if "outlook" in dim or "future" in dim:
            return f"{company} management guidance risks opportunities outlook 2026 2028"
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
        for company in self.IT_COMPANIES:
            if company.lower() in normalized_text:
                mentioned.append(company)
        return mentioned
    
    def _extract_technologies(self, normalized_text: str) -> List[str]:
        """Extract mentioned technologies from normalized text"""
        mentioned = []
        for tech in self.TECH_KEYWORDS:
            if tech in normalized_text:
                mentioned.append(tech)
        return mentioned
    
    async def extract_metrics(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract IT sector-specific metrics from findings
        
        Args:
            findings: Research findings
            
        Returns:
            Dictionary of IT-specific metrics
        """
        metrics = {
            "focus_areas_covered": [],
            "key_metrics_found": [],
            "companies_mentioned": [],
            "technologies_mentioned": [],
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
        metrics["technologies_mentioned"] = self._extract_technologies(combined_normalized)
        
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
            return f"{original_query} - IT sector overview and recent developments (2024-2025)"
        
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
            "AI/ML": {
                "keywords": ["ai", "artificial intelligence", "machine learning", "ml"],
                "thread": "AI services revenue, growth trajectory, and competitive differentiation"
            },
            "Cloud": {
                "keywords": ["cloud", "aws", "azure", "gcp", "cloud computing"],
                "thread": "cloud services adoption, market share, and migration trends"
            },
            "Cybersecurity": {
                "keywords": ["cybersecurity", "security", "cyber", "data protection"],
                "thread": "cybersecurity services, investments, and threat landscape"
            },
            "Talent": {
                "keywords": ["talent", "attrition", "retention", "employee", "workforce"],
                "thread": "talent acquisition, retention strategies, and workforce dynamics"
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
        
        # Priority 3: Company-specific deep dives (focus on Indian IT companies)
        indian_it_companies = [c for c in self.IT_COMPANIES if c in ["Infosys", "TCS", "Wipro", "HCL", "Tech Mahindra"]]
        for company in indian_it_companies:
            if company.lower() in normalized_insights:
                # Check if we already have deep coverage
                company_mentions = sum(1 for finding in previous_findings 
                                     if company.lower() in self._normalize_text(finding.get("query", "")))
                if company_mentions < 2:  # Not deeply covered yet
                    thread_candidates.append({
                        "thread": f"{company} competitive positioning, financial performance, and growth metrics",
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
            next_query = f"{original_query} - detailed financial analysis and market position"
        
        return next_query
    
    async def validate_coverage(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate if research has covered key IT sector dimensions
        
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
        Process IT sector query (implements BaseAgent interface)
        
        Args:
            query: Research query
            context: Optional context
            **kwargs: Additional parameters
            
        Returns:
            Processed result with IT sector enhancements
        """
        enhanced_query = await self.enhance_query(query, context)
        
        findings = context.get("findings", []) if context else []
        metrics = await self.extract_metrics(findings)
        coverage = await self.validate_coverage(findings)
        
        return {
            "enhanced_query": enhanced_query,
            "sector": "IT",
            "metrics": metrics,
            "coverage": coverage,
            "focus_areas": self.FOCUS_AREAS,
            "key_metrics": self.KEY_METRICS
        }