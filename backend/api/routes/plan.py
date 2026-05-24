from fastapi import APIRouter, HTTPException

from api.schemas.plan import PlanRequest, PlanResponse
from agents.research_planner import ResearchPlanner
from guardrails.safety_checker import safety_checker
from utils.helpers import sanitize_query, validate_query
from utils.logger import log

router = APIRouter()
planner = ResearchPlanner()

@router.post("/plan", response_model=PlanResponse)
async def create_research_plan(request: PlanRequest) -> PlanResponse:
    """
    Generate deep research plan for a query.

    This endpoint is typically called after classification so `sector`
    will already be IT / Pharma / Architecture / Energy / Unknown.
    """
    try:
        # Basic validation
        is_valid, error_msg = validate_query(request.query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Phase 10: Safety & scope guardrails
        safety_result = await safety_checker.validate_request(
            query=request.query,
            request=None  # Plan endpoint doesn't need rate limiting
        )
        
        if not safety_result["allowed"]:
            raise HTTPException(
                status_code=400,
                detail=safety_result["reason"]
            )
        
        # Use sanitized query
        request.query = safety_result["sanitized_query"]

        sanitized_query = sanitize_query(request.query)
        sector = request.sector

        log.info(
            f"Generating research plan for sector={sector}, "
            f"query='{sanitized_query[:80]}...'"
        )

        plan = await planner.generate_plan(sanitized_query, sector)

        return PlanResponse(query=sanitized_query, sector=sector, plan=plan)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Planning endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during plan generation: {str(e)}",
        )