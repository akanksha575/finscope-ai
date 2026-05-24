from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime

class ResearchState(TypedDict):
    """State for research workflow"""
    # Input
    query: str
    sector: Literal["IT", "Pharma", "Unknown"]
    selected_questions: List[str]  # Selected clarification questions
    query_id: str  # UUID from database
    
    # Research progress
    current_step: int
    total_steps: int
    status: Literal["planning", "researching", "synthesizing", "completed", "failed"]
    
    # Generated queries
    research_queries: List[str]  # Dynamically generated sub-queries
    
    # Tool execution results
    web_search_results: List[Dict[str, Any]]
    financial_data_results: List[Dict[str, Any]]
    web_scraper_results: List[Dict[str, Any]]
    calculator_results: List[Dict[str, Any]]
    
    # Findings and analysis
    findings: List[Dict[str, Any]]  # Key findings from each step
    accumulated_knowledge: str  # Combined knowledge from all steps
    
    # Intelligence markers
    intelligence_markers: Dict[str, Any]  # Tracks what's been covered
    
    # Real-time updates
    progress_updates: List[Dict[str, Any]]  # Real-time progress updates
    
    # Final report
    report: Optional[Dict[str, Any]]  # Generated research report
    
    # PDF mode
    pdf_file_path: Optional[str]  # Path to uploaded PDF file
    use_pdf_only: bool  # If True, use RAG from PDF instead of web search
    
    # Metadata
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]