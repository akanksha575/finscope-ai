import json
import re
from typing import Any, Dict, List, Literal

from agents.base_agent import BaseAgent
from utils.logger import log
from utils.prompts import get_planning_prompt

SectorLiteral = Literal["IT", "Pharma", "Unknown"]

class ResearchPlanner(BaseAgent):
    """Create deep research plans with dynamically generated clarification questions."""

    # Common fallback questions
    COMMON_QUESTIONS = {
        "region": "Are you interested in global market data or a specific region?",
        "timeframe": "Do you want the most recent data, or should I include historical trends?",
    }

    # Deep plan configuration
    DEEP_PLAN_CONFIG = {
        "steps": 18,
        "estimated_time": "3-5 minutes",
        "description": (
            "Exhaustive plan designed for deep-dive research. "
            "Includes comprehensive analysis, competitive positioning, scenario analysis, and long-term outlook."
        ),
        "max_questions": 7,
    }

    def __init__(self) -> None:
        super().__init__(model="gpt-4o", temperature=0.4)
        log.info("Initialized ResearchPlanner")

    async def generate_plan(self, query: str, sector: SectorLiteral) -> Dict[str, Any]:
        """
        Generate deep research plan with dynamically generated clarification questions.

        Args:
            query: User research query
            sector: Classified sector ("IT", "Pharma", or "Unknown")

        Returns:
            Deep plan dict with type, steps, questions, estimated_time, description
        """
        log.info(f"Generating deep research plan for sector={sector}, query='{query[:80]}...'")

        # Generate deep plan with questions
        deep_plan = await self._build_plan_with_questions(query, sector)

        return deep_plan

    async def process(self, query: str, sector: SectorLiteral) -> Dict[str, Any]:
        """Process query and return deep plan (implements BaseAgent interface)"""
        plan = await self.generate_plan(query, sector)
        return {"plan": plan}

    async def _build_plan_with_questions(
        self, query: str, sector: SectorLiteral
    ) -> Dict[str, Any]:
        """Build a deep plan with dynamically generated questions using LLM."""
        try:
            # Generate questions using LLM
            questions = await self._generate_questions(query, sector)
            
            # Get plan configuration
            config = self.DEEP_PLAN_CONFIG
            questions = questions[:config["max_questions"]]
            
            return {
                "type": "deep",
                "steps": config["steps"],
                "questions": questions,
                "estimated_time": config["estimated_time"],
                "description": config["description"],
            }
            
        except Exception as e:
            log.error(f"Error generating deep plan: {e}")
            # Fallback to basic questions
            return self._fallback_plan(query, sector)

    async def _generate_questions(
        self, query: str, sector: SectorLiteral
    ) -> List[str]:
        """Generate clarification questions using LLM."""
        prompt = get_planning_prompt(query, sector, "deep")
        
        system_prompt = (
            "You are an expert financial research assistant specializing in generating "
            "high-quality clarification questions for deep financial research.\n\n"
            "Your role:\n"
            "- Generate 6-7 precise, actionable clarification questions\n"
            "- Questions must be specific to the user's query (mention companies, topics, or themes)\n"
            "- Questions should help refine research scope, timeframe, geography, and metrics\n"
            "- Questions must be relevant to the sector context (IT or Pharma)\n\n"
            "Output requirements:\n"
            "- Return ONLY a valid JSON array of question strings\n"
            "- No additional text, explanations, or markdown formatting\n"
            "- Each question must end with a question mark (?)\n"
            "- Questions should be 10-80 words each\n"
            "- Format: [\"Question 1?\", \"Question 2?\", \"Question 3?\"]\n\n"
            "Quality criteria:\n"
            "- Avoid generic questions (e.g., 'What do you want to know?')\n"
            "- Avoid yes/no questions unless necessary\n"
            "- Focus on actionable clarifications that improve research quality\n"
            "- Prioritize questions that reveal scope, depth, and focus areas"
        )
        
        try:
            response = await self._call_llm(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Parse JSON response
            questions = self._parse_questions(response)
            return questions if questions else self._fallback_questions(query, sector)
            
        except Exception as e:
            log.warning(f"LLM question generation failed: {e}, using fallback")
            return self._fallback_questions(query, sector)

    def _parse_questions(self, response: str) -> List[str]:
        """Parse questions from LLM response."""
        # Try to extract JSON array (using negated character class for better performance)
        json_match = re.search(r'\[[^\]]*\]', response, re.DOTALL)
        if json_match:
            try:
                questions = json.loads(json_match.group())
                if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
                    # Normalize whitespace for all questions
                    return [q.strip() for q in questions if q.strip()]
            except json.JSONDecodeError:
                pass
        
        questions = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            match = re.match(r'^\s*(?:\d+[\.\)]|[-*])\s+(.+)$', line)
            if match:
                question = match.group(1).strip()
                if question.endswith('?') or len(question) > 10:
                    questions.append(question)
        
        return questions if questions else []

    def _fallback_questions(
        self, _query: str, sector: SectorLiteral
    ) -> List[str]:
        """
        Fallback questions if LLM generation fails.
        
        Args:
            _query: User query (unused in fallback, kept for interface consistency)
            sector: Classified sector
        """
        base_questions = []
        
        if sector == "IT":
            base_questions = [
                self.COMMON_QUESTIONS["region"],
                "Do you want the most recent data (2024-2025), or should I include historical trends?",
                "Should the analysis focus on specific segments (cloud, AI, digital services) or the entire portfolio?",
            ]
        elif sector == "Pharma":
            base_questions = [
                self.COMMON_QUESTIONS["region"],
                "Do you want the most recent data (2024-2025), or should I include historical trends?",
                "Should the analysis focus on branded drugs, generics, biosimilars, or the entire portfolio?",
            ]
        else:
            base_questions = [
                "Could you clarify which sector or company you'd like me to focus on?",
                self.COMMON_QUESTIONS["region"],
                self.COMMON_QUESTIONS["timeframe"],
            ]
        
        # Limit to max questions for deep plan
        max_questions = self.DEEP_PLAN_CONFIG["max_questions"]
        return base_questions[:max_questions]

    def _fallback_plan(
        self, query: str, sector: SectorLiteral
    ) -> Dict[str, Any]:
        """Fallback plan if generation fails."""
        questions = self._fallback_questions(query, sector)
        
        # Use deep plan configuration
        config = self.DEEP_PLAN_CONFIG
        return {
            "type": "deep",
            "steps": config["steps"],
            "questions": questions,
            "estimated_time": config["estimated_time"],
            "description": config["description"],
        }

__all__ = ["ResearchPlanner"]