"""
Deep Research Engine with iterative intelligence
Uses LangGraph for workflow orchestration and iterative research
"""
from typing import TYPE_CHECKING

# IMPORTANT:
# Avoid importing modules with side effects (e.g., tool initialization requiring API keys)
# at package import time. This keeps `import research.*` safe in environments like pytest
# where secrets may not be configured.
if TYPE_CHECKING:
    from research.state import ResearchState  # noqa: F401
    from research.query_generator import QueryGenerator  # noqa: F401
    from research.tool_executor import ToolExecutor  # noqa: F401
    from research.orchestrator import ResearchOrchestrator  # noqa: F401

__all__ = [
    "ResearchState",
    "QueryGenerator",
    "ToolExecutor",
    "ResearchOrchestrator",
]




