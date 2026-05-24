import json
import re
from enum import Enum
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.prompts import get_classification_prompt
from utils.logger import log
from utils.cache import get_cache_manager, generate_cache_key, CACHE_TTL, cached_call

from guardrails.validators import validate_query_safety

class Sector(str, Enum):
    """Supported sectors for query classification"""
    IT = "IT"
    PHARMA = "Pharma"
    ARCHITECTURE = "Architecture"
    ENERGY = "Energy"
    UNKNOWN = "Unknown"


class QueryRouter(BaseAgent):
    """Routes queries to appropriate sector agents"""
    
    # Valid sectors for validation
    VALID_SECTORS = [sector.value for sector in Sector]
    
    def __init__(self):
        super().__init__(model="gpt-4o-mini", temperature=0.1)
    
    @staticmethod
    def _normalize_confidence(confidence: float) -> float:
        """
        Normalize confidence score to valid range [0.0, 1.0]
        
        Args:
            confidence: Raw confidence value
            
        Returns:
            Clamped confidence value
        """
        return max(0.0, min(1.0, float(confidence)))
    
    async def process(self, query: str) -> Dict[str, Any]:
        """
        Process query (alias for classify)
        
        Args:
            query: User query to process
            
        Returns:
            Classification result
        """
        return await self.classify(query)
    
    async def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify query into sector (with caching)
        
        Args:
            query: User query to classify
            
        Returns:
            Classification result with sector, confidence, reasoning
        """
        log.info(f"Classifying query: {query[:100]}...")
        
        # Safety validation (not cached - must always check)
        is_safe, error = validate_query_safety(query)
        if not is_safe:
            return {
                "sector": Sector.UNKNOWN.value,
                "confidence": 1.0,
                "reasoning": "Query failed safety validation",
                "decline_message": error,
                "error": error
            }
        
        # Generate cache key
        cache_key = generate_cache_key("classify", query)
        
        # Try cache first
        cache = await get_cache_manager()
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            log.info(f"Cache hit for classification: {query[:60]}...")
            return cached_result
        
        # Cache miss - execute classification
        log.debug(f"Cache miss for classification, executing LLM call")
        result = await self._classify_uncached(query)
        
        # Cache successful results only
        if result.get("error") is None:
            await cache.set(cache_key, result, ttl=CACHE_TTL["classification"])
            log.info(f"Cached classification result for: {query[:60]}...")
        
        return result
    
    async def _classify_uncached(self, query: str) -> Dict[str, Any]:
        """
        Internal method to perform actual classification (without cache)
        
        Args:
            query: User query to classify
            
        Returns:
            Classification result
        """
        try:
            # Get classification prompt
            prompt = get_classification_prompt(query)
            
            # Call LLM with enhanced system prompt emphasizing all sectors
            system_prompt = """You are a financial research query classifier for FinScope AI. 

You MUST classify queries into one of these sectors:
- IT: Information Technology (software, cloud, SaaS, tech companies)
- Pharma: Pharmaceutical (drugs, clinical trials, pharma companies)
- Architecture: Architecture and construction (building design, construction firms, infrastructure)
- Energy: Energy sector (oil, gas, renewable energy, utilities, energy companies)
- Unknown: Only if query is clearly not financial/company research

CRITICAL: Architecture and Energy are valid sectors. Do NOT classify them as Unknown.
- Architecture keywords: architecture, architectural, building design, construction, infrastructure, Gensler, AECOM, HOK
- Energy keywords: energy, oil, gas, petroleum, renewable, solar, wind, refinery, utilities, Reliance, Exxon, Shell

Always respond with valid JSON only, no additional text. 
Format: {"sector": "IT"|"Pharma"|"Architecture"|"Energy"|"Unknown", "confidence": 0.0-1.0, "reasoning": "..."}"""
            response = await self._call_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            log.debug(f"LLM classification response: {response[:500]}")
            
            # Parse response
            result = self._parse_response(response)
            
            # Validate and normalize result
            if result["sector"] not in self.VALID_SECTORS:
                log.warning(f"Invalid sector returned: {result['sector']}, defaulting to Unknown. Full response: {response[:200]}")
                result["sector"] = Sector.UNKNOWN.value
            
            # Normalize confidence to valid range
            result["confidence"] = self._normalize_confidence(result.get("confidence", 0.5))
            
            log.info(f"Classification result for query '{query[:60]}...': {result['sector']} (confidence: {result['confidence']}, reasoning: {result.get('reasoning', 'N/A')[:100]})")
            return result
            
        except Exception as e:
            log.error(f"Classification failed: {e}")
            return {
                "sector": Sector.UNKNOWN.value,
                "confidence": 0.0,
                "reasoning": f"Classification error: {str(e)}",
                "decline_message": "We encountered an error processing your query. Please try rephrasing it.",
                "error": str(e)
            }
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format
        
        Uses a layered defensive approach with multiple fallback strategies:
        1. Direct JSON parsing
        2. Regex-based JSON extraction (handles nested objects)
        3. Heuristic text-based extraction
        
        This complexity is intentional to handle LLM unpredictability and ensure
        the system never fails due to parsing issues.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed classification result
        """
        # First, try to parse the entire response as JSON
        try:
            result = json.loads(response.strip())
            # Validate and ensure all required fields
            if "sector" in result:
                result.setdefault("confidence", 0.5)
                result["confidence"] = self._normalize_confidence(result["confidence"])
                result.setdefault("reasoning", "No reasoning provided")
                result.setdefault("decline_message", None)
                return result
        except json.JSONDecodeError:
            pass
        
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested objects (handles simple nesting)
            r'\{.*?"sector".*?\}',  # Object with "sector" key
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    # Ensure all required fields
                    if "sector" in result:
                        result.setdefault("confidence", 0.5)
                        result["confidence"] = self._normalize_confidence(result["confidence"])
                        result.setdefault("reasoning", "No reasoning provided")
                        result.setdefault("decline_message", None)
                        return result
                except json.JSONDecodeError:
                    continue
        
        # Fallback: try to extract sector from text using heuristic patterns
        sector = Sector.UNKNOWN.value
        confidence = 0.5
        reasoning = "Parsed from text response"
        
        # Look for sector indicators in the response
        response_upper = response.upper()
        response_lower = response.lower()
        
        # Check for IT sector
        if any(indicator in response_upper for indicator in ["\"IT\"", "'IT'", '"sector": "IT"', "'sector': 'IT'", "SECTOR.*IT"]):
            sector = Sector.IT.value
            confidence = 0.7
        elif "information technology" in response_lower or ("it" in response_lower and "sector" in response_lower):
            sector = Sector.IT.value
            confidence = 0.6
        
        # Check for Pharma sector
        elif any(indicator in response_upper for indicator in ["\"PHARMA\"", "'PHARMA'", '"sector": "Pharma"', "'sector': 'Pharma'", "SECTOR.*PHARMA"]):
            sector = Sector.PHARMA.value
            confidence = 0.7
        elif "pharmaceutical" in response_lower or ("pharma" in response_lower and "sector" in response_lower):
            sector = Sector.PHARMA.value
            confidence = 0.6
        
        # Check for Architecture sector (check BEFORE Energy to avoid conflicts)
        architecture_keywords = [
            "architecture", "architectural", "building design", "construction", "infrastructure",
            "gensler", "aecom", "hok", "skidmore", "som", "bim", "urban planning", 
            "sustainable design", "green building", "architect", "architects"
        ]
        if any(indicator in response_upper for indicator in ["\"ARCHITECTURE\"", "'ARCHITECTURE'", '"sector": "Architecture"', "'sector': 'Architecture'", "SECTOR.*ARCHITECTURE"]):
            sector = Sector.ARCHITECTURE.value
            confidence = 0.8
        elif any(keyword in response_lower for keyword in architecture_keywords):
            sector = Sector.ARCHITECTURE.value
            confidence = 0.7
        
        # Check for Energy sector
        energy_keywords = [
            "energy", "oil", "gas", "petroleum", "renewable", "solar", "wind", 
            "refinery", "utilities", "reliance", "exxon", "shell", "chevron",
            "bp", "total", "crude", "drilling", "exploration", "power generation"
        ]
        if any(indicator in response_upper for indicator in ["\"ENERGY\"", "'ENERGY'", '"sector": "Energy"', "'sector': 'Energy'", "SECTOR.*ENERGY"]):
            sector = Sector.ENERGY.value
            confidence = 0.8
        elif any(keyword in response_lower for keyword in energy_keywords):
            sector = Sector.ENERGY.value
            confidence = 0.7
        
        # Normalize confidence before returning
        confidence = self._normalize_confidence(confidence)
        
        log.warning(f"Could not parse JSON from classification response, using fallback: {sector}")
        log.debug(f"Response was: {response[:200]}...")
        
        return {
            "sector": sector,
            "confidence": confidence,
            "reasoning": reasoning,
            "decline_message": None
        }