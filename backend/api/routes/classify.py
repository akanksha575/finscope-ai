from fastapi import APIRouter, HTTPException
from api.schemas.query import QueryRequest, ClassificationResponse
from agents.query_router import QueryRouter
from utils.helpers import sanitize_query, validate_query
from utils.logger import log

router = APIRouter()

# Initialize query router lazily to handle potential initialization errors
_query_router = None

def get_query_router():
    """Get or initialize query router"""
    global _query_router
    if _query_router is None:
        try:
            _query_router = QueryRouter()
        except Exception as e:
            log.error(f"Failed to initialize QueryRouter: {e}")
            raise
    return _query_router

@router.post("/classify", response_model=ClassificationResponse)
async def classify_query(request: QueryRequest) -> ClassificationResponse:
    """
    Classify a user query to determine the appropriate sector (IT/Pharma/Architecture/Energy)
    
    Args:
        request: Query request with user query text
        
    Returns:
        Classification result with sector, confidence, and reasoning
    """
    try:
        # Validate query
        is_valid, error_msg = validate_query(request.query)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Sanitize query
        sanitized_query = sanitize_query(request.query)
        
        log.info(f"Classifying query: {sanitized_query[:100]}...")
        
        # Get query router (lazy initialization)
        query_router = get_query_router()
        
        # Classify using query router
        result = await query_router.classify(sanitized_query)
        
        # Log the result for debugging
        log.info(f"Classification result: sector={result.get('sector')}, confidence={result.get('confidence')}, error={result.get('error')}")
        
        # Ensure sector is always one of the valid values
        sector = result.get("sector", "Unknown")
        if sector not in ["IT", "Pharma", "Architecture", "Energy", "Unknown"]:
            log.warning(f"Invalid sector '{sector}' returned, defaulting to 'Unknown'")
            sector = "Unknown"
        
        # Return classification response
        return ClassificationResponse(
            sector=sector,
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Classification completed"),
            decline_message=result.get("decline_message"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Classification endpoint error: {e}", exc_info=True)
        import traceback
        log.error(f"Traceback: {traceback.format_exc()}")
        # Return a safe fallback response instead of raising
        return ClassificationResponse(
            sector="Unknown",
            confidence=0.0,
            reasoning=f"Classification error: {str(e)}",
            decline_message="We encountered an error processing your query. Please try again.",
            error=str(e)
        )