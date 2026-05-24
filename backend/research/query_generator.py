"""
Intelligent Query Generator with Phased Research Progression

This module generates progressive, non-repetitive research queries using:
- Phase-based state machine (overview → deep dive → comparative → forward → validation)
- Dimension coverage tracking
- Semantic similarity checking
- Thread extraction and following
- Natural language query construction
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from agents.it_sector_agent import ITSectorAgent
from agents.pharma_sector_agent import PharmaSectorAgent
from utils.logger import log
from utils.company_tickers import extract_primary_company_name, find_companies
from research.complexity import QueryType
from research.query_intelligence import (
    CoverageTracker,
    QueryHistory,
    ThreadExtractor,
    QueryConstructor,
    PhaseManager,
    ResearchPhase,
    SimilarityChecker
)
from research.requirement_driven_planner import (
    generate_requirement_driven_queries,
    RequirementDrivenPlanner
)


class QueryGenerator(BaseAgent):
    """Generates intelligent, progressive research queries"""
    
    def __init__(self):
        super().__init__(model="gpt-4o", temperature=0.4)
        self.it_agent = ITSectorAgent()
        self.pharma_agent = PharmaSectorAgent()
        self.similarity_checker = SimilarityChecker(threshold=0.7)
        self.thread_extractor = ThreadExtractor()
        self.query_constructor = QueryConstructor()
        self.requirement_planner = RequirementDrivenPlanner()
        log.info("Initialized QueryGenerator with requirement-driven system")
    
    def _extract_company_name(self, query: str) -> str:
        """Extract primary company name from query"""
        company = extract_primary_company_name(query)
        if company:
            return company
        
        # Fallback: extract first capitalized phrase
        words = query.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Take up to 3 words
                return " ".join(words[i:min(i+3, len(words))])
        
        return "Company"
    
    def _extract_all_companies(self, query: str) -> List[str]:
        """Extract all companies mentioned in query (for comparative queries)"""
        matches = find_companies(query)
        return [m.canonical_name for m in matches]
    
    def _is_comparative_query(self, query: str) -> bool:
        """Check if query is asking for comparison of multiple companies"""
        query_lower = query.lower()
        comparative_patterns = [
            "compare", "vs", "versus", "comparison", "compared to",
            " and ", " or ", "between"
        ]
        return any(pattern in query_lower for pattern in comparative_patterns)
    
    def _clean_query(self, query: str, primary_company: str, all_companies: List[str]) -> str:
        """
        EMERGENCY PATCH: Clean query to remove instruction prefixes and ensure company name.
        
        This prevents:
        1. Instruction prefix pollution ("Create an equity...")
        2. Missing company names in queries
        3. Truncated queries
        """
        if not query:
            return query
        
        # Strip instruction prefixes
        instruction_prefixes = [
            "create an equity", "create a", "create the",
            "generate an", "generate a", "generate the",
            "produce an", "produce a", "produce the",
            "write an", "write a", "write the",
            "make an", "make a", "make the",
            "build an", "build a", "build the"
        ]
        
        query_lower = query.lower()
        for prefix in instruction_prefixes:
            if query_lower.startswith(prefix):
                # Remove prefix and clean up
                query = query[len(prefix):].strip()
                log.warning(f"Stripped instruction prefix '{prefix}' from query")
                break
        
        # Ensure company name is present (unless it's a pure comparative query with "vs")
        has_company = any(comp.lower() in query.lower() for comp in all_companies)
        is_vs_query = " vs " in query.lower() or " versus " in query.lower()
        
        if not has_company and not is_vs_query:
            # Prepend primary company name
            query = f"{primary_company} {query}"
            log.info(f"Prepended company name to query: {primary_company}")
        
        # Fix truncation (ends with "...")
        if query.endswith("..."):
            query = query[:-3].strip()
            log.warning(f"Removed truncation from query")
        
        # Fix truncated last word (< 3 chars and not a known abbreviation)
        words = query.split()
        if words and len(words[-1]) < 3 and words[-1].lower() not in ["ai", "ml", "r&d", "us", "eu", "uk", "q1", "q2", "q3", "q4"]:
            # Likely truncated, remove last word
            query = " ".join(words[:-1])
            log.warning(f"Removed likely truncated word: {words[-1]}")
        
        return query.strip()
    
    def _extract_competitors_from_findings(self, findings: List[Dict[str, Any]], sector: str) -> List[str]:
        """Extract competitor names mentioned in findings"""
        competitors = set()
        
        # Get company lists from thread extractor
        if sector == "IT":
            company_list = self.thread_extractor.IT_COMPANIES
        else:
            company_list = self.thread_extractor.PHARMA_COMPANIES
        
        # Search findings for company mentions
        for finding in findings:
            text = str(finding.get("key_insights", "")).lower()
            for company in company_list:
                if company in text:
                    competitors.add(company.title())
        
        return list(competitors)[:3]  # Return top 3
    
    async def generate_next_query(
        self,
        original_query: str,
        sector: str,
        previous_findings: List[Dict[str, Any]],
        accumulated_knowledge: str,
        selected_questions: List[str] = None,
        query_type: Optional[QueryType] = None,
        dimensions_not_covered: Optional[List[str]] = None,
        unvalidated_claims: Optional[List[Dict[str, Any]]] = None,
        citations_count: int = 0,
        query_history: Optional[QueryHistory] = None,
        coverage_tracker: Optional[CoverageTracker] = None,
        phase_manager: Optional[PhaseManager] = None,
    ) -> Optional[str]:
        """
        Generate next research query using intelligent phased approach.
        
        This is the CORE intelligence function that implements:
        1. Phase-based progression (overview → deep → compare → validate)
        2. Dimension coverage tracking
        3. Semantic similarity checking
        4. Thread extraction and following
        5. Natural language query construction
        """
        # Initialize tracking objects if not provided
        if query_history is None:
            query_history = QueryHistory()
        
        if coverage_tracker is None:
            coverage_tracker = CoverageTracker(sector=sector)
        
        if phase_manager is None:
            phase_manager = PhaseManager()
        
        # Extract company names (may be multiple for comparative queries)
        all_companies = self._extract_all_companies(original_query)
        is_comparative = self._is_comparative_query(original_query) and len(all_companies) > 1
        company = all_companies[0] if all_companies else self._extract_company_name(original_query)
        
        log.info(f"Query analysis: companies={all_companies}, is_comparative={is_comparative}")
        
        # Update coverage from latest findings
        if previous_findings:
            latest_finding = previous_findings[-1]
            text = f"{latest_finding.get('query', '')} {' '.join(str(i) for i in latest_finding.get('key_insights', []))}"
            coverage_tracker.update_from_text(text)
        
        # Check if should advance phase
        if phase_manager.should_advance_phase(coverage_tracker, previous_findings):
            new_phase = phase_manager.advance_phase()
            log.info(f"Advanced to research phase: {new_phase}")
        
        current_phase = phase_manager.current_phase
        log.info(f"Generating query for phase: {current_phase}, step {len(previous_findings) + 1}")
        
        # Generate query based on current phase
        candidate_query = None
        
        # ===== PHASE 1: OVERVIEW =====
        if current_phase == ResearchPhase.OVERVIEW:
            if len(previous_findings) == 0:
                # First query: broad overview
                if is_comparative and len(all_companies) > 1:
                    # For comparative queries, start with first company
                    candidate_query = self.query_constructor.construct_overview_query(all_companies[0], sector)
                else:
                    candidate_query = self.query_constructor.construct_overview_query(company, sector)
            else:
                # Second overview query
                if is_comparative and len(all_companies) > 1:
                    # Cycle through companies for overview
                    company_idx = len(previous_findings) % len(all_companies)
                    if company_idx < len(all_companies):
                        target_company = all_companies[company_idx]
                        candidate_query = self.query_constructor.construct_overview_query(target_company, sector)
                    else:
                        # All companies covered, move to deep dive
                        candidate_query = f"{all_companies[0]} financial performance detailed analysis 2023-2025"
                else:
                    # Single company: focus on key aspect
                    if sector == "IT":
                        candidate_query = f"{company} cloud AI digital transformation revenue breakdown 2025-2026"
                    else:
                        candidate_query = f"{company} drug portfolio pipeline R&D spending breakdown 2025-2026"
        
        # ===== PHASE 2: DEEP DIVE =====
        elif current_phase == ResearchPhase.DEEP_DIVE:
            # For comparative queries, cycle through companies for deep dives
            if is_comparative and len(all_companies) > 1:
                # Determine which company to focus on
                company_idx = phase_manager.steps_in_phase % len(all_companies)
                target_company = all_companies[company_idx]
                
                # Deep dive on key metrics for this company
                if sector == "IT":
                    aspects = ["revenue growth 2023-2025", "operating margins", "key business segments", "competitive positioning"]
                else:
                    aspects = ["revenue growth 2023-2025", "profit margins", "drug pipeline", "market position"]
                
                aspect_idx = (phase_manager.steps_in_phase // len(all_companies)) % len(aspects)
                aspect = aspects[aspect_idx]
                candidate_query = f"{target_company} {aspect} detailed analysis"
            else:
                # Single company: extract threads and follow them
                threads = self.thread_extractor.extract_threads(previous_findings, sector)
                
                # Prioritize uncovered dimensions
                uncovered = coverage_tracker.get_uncovered_dimensions()
                low_confidence = coverage_tracker.get_low_confidence_dimensions()
                
                if uncovered:
                    # Focus on uncovered dimension
                    dimension = uncovered[0]
                    aspect = dimension.lower().replace(" & ", " ").replace(" ", " ")
                    candidate_query = self.query_constructor.construct_deep_dive_query(company, aspect, sector)
                
                elif low_confidence:
                    # Deepen low confidence dimension
                    dimension = low_confidence[0]
                    aspect = dimension.lower()
                    candidate_query = self.query_constructor.construct_deep_dive_query(company, aspect, sector)
                
                elif threads:
                    # Follow interesting thread
                    thread = threads[0]
                    if thread.thread_type == "entity":
                        # Research mentioned entity
                        candidate_query = f"{company} {thread.content} partnership collaboration details 2026"
                    elif thread.thread_type == "metric":
                        # Deep dive on metric
                        metric_text = thread.content.split("(")[0].strip()
                        candidate_query = f"{company} {metric_text} breakdown trend analysis 2024-2026"
                    else:
                        # Follow claim
                        candidate_query = f"{company} {thread.content[:50]} quantify latest data"
                
                else:
                    # Fallback: financial deep dive
                    candidate_query = f"{company} quarterly revenue profit margin trend Q1-Q3 2025"
        
        # ===== PHASE 3: COMPARATIVE =====
        elif current_phase == ResearchPhase.COMPARATIVE:
            if is_comparative and len(all_companies) > 1:
                # Direct comparison between the companies mentioned in query
                if sector == "IT":
                    aspects = ["revenue growth 2023-2025", "operating margins", "market share", "stock performance"]
                else:
                    aspects = ["revenue growth", "profit margins", "market share", "pipeline strength"]
                
                aspect_idx = phase_manager.steps_in_phase % len(aspects)
                aspect = aspects[aspect_idx]
                
                # Compare all companies
                companies_str = " vs ".join(all_companies)
                candidate_query = f"{companies_str} {aspect} comparison"
            else:
                # Single company: extract competitors from findings
                competitors = self._extract_competitors_from_findings(previous_findings, sector)
                
                if competitors:
                    competitor = competitors[0]
                    # Compare on key dimension
                    if sector == "IT":
                        aspects = ["cloud revenue", "AI capabilities", "market share", "growth rate"]
                    else:
                        aspects = ["drug pipeline", "R&D spending", "market share", "patent portfolio"]
                    
                    aspect = aspects[phase_manager.steps_in_phase % len(aspects)]
                    candidate_query = self.query_constructor.construct_comparative_query(
                        company, competitor, aspect, sector
                    )
                else:
                    # No competitors found, do sector comparison
                    if sector == "IT":
                        candidate_query = f"{company} vs TCS Infosys Wipro market position India 2026"
                    else:
                        candidate_query = f"{company} vs Sun Pharma Cipla Lupin market share comparison 2026"
        
        # ===== PHASE 4: FORWARD-LOOKING =====
        elif current_phase == ResearchPhase.FORWARD:
            if phase_manager.steps_in_phase == 0:
                # First forward query: outlook and projections
                candidate_query = self.query_constructor.construct_forward_query(company, sector)
            else:
                # Second forward query: risks and challenges
                candidate_query = f"{company} key risks challenges regulatory competition {sector} 2026"
        
        # ===== PHASE 5: VALIDATION =====
        elif current_phase == ResearchPhase.VALIDATION:
            # Validate key metrics or fill gaps
            uncovered = coverage_tracker.get_uncovered_dimensions()
            
            if uncovered:
                # Fill remaining gaps
                dimension = uncovered[0]
                candidate_query = f"{company} {dimension.lower()} latest data verification 2026"
            elif unvalidated_claims:
                # Validate unvalidated claims
                claim = unvalidated_claims[0]
                value = claim.get("value_examples", [""])[0]
                candidate_query = f"{company} {value} verification latest quarter 2025"
            else:
                # Final validation: financial metrics
                candidate_query = f"{company} latest quarterly earnings financial results Q3 2025"
        
        # Fallback if no query generated
        if not candidate_query:
            log.warning("No candidate query generated, using fallback")
            candidate_query = f"{company} {sector} latest developments 2026"
        
        # EMERGENCY PATCH: Clean instruction prefixes and ensure company name
        candidate_query = self._clean_query(candidate_query, company, all_companies if is_comparative else [company])
        
        # Validate query quality
        is_valid, error = self.query_constructor.validate_query_quality(candidate_query)
        if not is_valid:
            log.warning(f"Query quality check failed: {error}. Query: {candidate_query}")
            # Try to fix
            candidate_query = f"{company} {sector} overview 2026"
        
        # Check for repetition
        is_repetitive, similar_query = query_history.is_repetitive(candidate_query)
        if is_repetitive:
            log.warning(f"Query too similar to previous: {similar_query}")
            # Generate alternative by switching dimension
            uncovered = coverage_tracker.get_uncovered_dimensions()
            if uncovered:
                alt_dimension = uncovered[0]
                candidate_query = f"{company} {alt_dimension.lower()} analysis 2026"
            else:
                # Force a different angle
                candidate_query = f"{company} {sector} competitive landscape analysis 2026"
            
            # Check again
            is_repetitive, _ = query_history.is_repetitive(candidate_query)
            if is_repetitive:
                # Give up, return None to signal stopping
                log.warning("Unable to generate non-repetitive query, suggesting stop")
                return None
        
        # Add to history
        query_history.add_query(candidate_query)
        
        # Record step in phase
        phase_manager.record_step()
        
        log.info(f"Generated query (phase={current_phase}, similarity_ok=True): {candidate_query}")
        return candidate_query
    
    async def generate_research_queries(
        self,
        original_query: str,
        sector: str,
        selected_questions: List[str] = None,
        current_findings: List[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate initial batch of research queries using REQUIREMENT-DRIVEN PLANNING.
        
        This replaces template-based generation with precise, targeted queries
        derived from user requirements.
        """
        # Extract all companies from query
        company_matches = find_companies(original_query)
        companies = [m.canonical_name for m in company_matches]
        
        if not companies:
            # Fallback: try basic extraction
            company = self._extract_company_name(original_query)
            if company:
                companies = [company]
        
        if not companies:
            log.warning("No companies found in query, using generic overview")
            return [f"{sector} sector overview 2025 2026"]
        
        # Use requirement-driven planner
        queries = self.requirement_planner.plan_queries(
            original_query=original_query,
            companies=companies,
            sector=sector
        )
        
        # Validate all queries (prevent self-comparisons)
        valid_queries = []
        for q in queries:
            if self.requirement_planner.validate_query(q, companies):
                valid_queries.append(q)
            else:
                log.error(f"REJECTED INVALID QUERY: {q}")
        
        log.info(f"Generated {len(valid_queries)} requirement-driven queries")
        # Return 18-20 queries for deep research
        target_count = 18
        min_count = 18  # Minimum required
        
        if len(valid_queries) < min_count:
            # If we don't have enough, generate additional queries using OpenAI
            needed = min_count - len(valid_queries)
            log.info(f"Only {len(valid_queries)} queries generated, generating {needed} additional queries to reach minimum {min_count}")
            additional_queries = await self._generate_additional_queries(
                original_query, companies, sector, valid_queries, needed
            )
            valid_queries.extend(additional_queries)
            log.info(f"After OpenAI generation: {len(valid_queries)} total queries")
        
        # If still not enough, generate more until we reach target
        if len(valid_queries) < target_count:
            needed = target_count - len(valid_queries)
            log.info(f"Still need {needed} more queries, generating additional batch")
            more_queries = await self._generate_additional_queries(
                original_query, companies, sector, valid_queries, needed
            )
            valid_queries.extend(more_queries)
            log.info(f"Final query count: {len(valid_queries)}")
        
        # Ensure we return at least 18, up to 20
        final_queries = valid_queries[:20] if len(valid_queries) >= 18 else valid_queries
        log.info(f"Returning {len(final_queries)} queries for research (target: 18-20)")
        return final_queries
    
    async def process(self, original_query: str, sector: str, selected_questions: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Process query generation (implements BaseAgent interface)"""
        queries = await self.generate_research_queries(
            original_query,
            sector,
            selected_questions or [],
            kwargs.get("current_findings", [])
        )
        return {"queries": queries}
    
    async def _generate_additional_queries(
        self,
        original_query: str,
        companies: List[str],
        sector: str,
        existing_queries: List[str],
        count: int
    ) -> List[str]:
        """Generate additional research queries using OpenAI to reach target count"""
        try:
            # Ensure we generate at least the requested count, maybe a bit more to account for filtering
            generate_count = max(count, 5)  # Generate at least 5, or more if needed
            
            prompt = f"""Generate {generate_count} additional research queries for deep financial analysis.

Original Query: {original_query}
Sector: {sector}
Companies: {', '.join(companies) if companies else 'General sector analysis'}

Existing Queries (avoid repetition):
{chr(10).join(f"- {q}" for q in existing_queries[:15])}

Generate {generate_count} NEW, specific research queries that:
1. Cover different dimensions (financial performance, market position, strategy, risks, outlook, competitive analysis)
2. Are specific to the companies/sector mentioned
3. Focus on recent data (2024-2025)
4. Are actionable and will provide valuable insights
5. Do NOT repeat existing queries
6. Cover various aspects: revenue, profitability, market share, growth, risks, strategy, outlookReturn ONLY a JSON array of query strings. No additional text.
Format: ["Query 1", "Query 2", "Query 3", ...]"""
            
            response = await self._call_llm(
                prompt=prompt,
                system_prompt="You are a financial research query generator. Always return valid JSON array only. Generate exactly the number of queries requested."
            )
            
            # Parse JSON response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                additional = json.loads(json_match.group())
                # Validate and clean queries
                valid_additional = []
                seen_lower = {q.lower() for q in existing_queries}
                for q in additional:
                    if isinstance(q, str) and len(q.strip()) > 10:
                        cleaned = self._clean_query(q.strip(), companies[0] if companies else "Company", companies)
                        if cleaned and cleaned.lower() not in seen_lower:
                            valid_additional.append(cleaned)
                            seen_lower.add(cleaned.lower())
                log.info(f"Generated {len(valid_additional)} additional queries via OpenAI (requested {count})")
                return valid_additional[:count * 2]  # Return up to 2x requested to ensure we have enough after filtering
        except Exception as e:
            log.error(f"Error generating additional queries: {e}", exc_info=True)
        
        return []
