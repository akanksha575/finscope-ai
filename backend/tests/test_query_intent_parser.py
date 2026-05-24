"""
Tests for query intent parser
"""

import pytest
from research.query_intent_parser import QueryIntentParser, parse_query_intent


class TestQueryIntentParser:
    """Test query intent parsing"""
    
    def test_strip_instruction_prefix_create(self):
        """Test stripping 'Create' prefix"""
        parser = QueryIntentParser()
        
        query = "Create an equity research memo on Pfizer"
        cleaned = parser._strip_instruction_prefix(query)
        
        assert "Create" not in cleaned
        assert "equity research memo on Pfizer" in cleaned
    
    def test_strip_instruction_prefix_generate(self):
        """Test stripping 'Generate' prefix"""
        parser = QueryIntentParser()
        
        query = "Generate a financial analysis of Apple"
        cleaned = parser._strip_instruction_prefix(query)
        
        assert "Generate" not in cleaned
        assert "financial analysis of Apple" in cleaned
    
    def test_extract_single_company(self):
        """Test extracting single company"""
        parser = QueryIntentParser()
        
        query = "equity research memo on Pfizer"
        companies = parser._extract_companies(query)
        
        assert "Pfizer" in [c for c in companies if "Pfizer" in c]
    
    def test_extract_multiple_companies(self):
        """Test extracting multiple companies"""
        parser = QueryIntentParser()
        
        query = "Compare Nvidia vs Microsoft vs Amazon"
        companies = parser._extract_companies(query)
        
        assert len(companies) == 3
        company_names = " ".join(companies)
        assert "Nvidia" in company_names
        assert "Microsoft" in company_names
        assert "Amazon" in company_names
    
    def test_extract_report_type_equity_research(self):
        """Test extracting equity research report type"""
        parser = QueryIntentParser()
        
        query = "equity research memo on Pfizer"
        report_type = parser._extract_report_type(query)
        
        # "equity research" matches first, so returns "equity_research"
        assert report_type == "equity_research"
    
    def test_extract_report_type_comparative(self):
        """Test extracting comparative analysis type"""
        parser = QueryIntentParser()
        
        query = "Compare Apple vs Microsoft"
        report_type = parser._extract_report_type(query)
        
        assert report_type == "comparative_analysis"
    
    def test_extract_requirements(self):
        """Test extracting data requirements"""
        parser = QueryIntentParser()
        
        query = "revenue growth, operating margins, and risks"
        requirements = parser._extract_requirements(query)
        
        assert "revenue_trend" in requirements
        assert "operating_margin" in requirements
        assert "risks" in requirements
    
    def test_extract_timeframe_range(self):
        """Test extracting year range"""
        parser = QueryIntentParser()
        
        query = "revenue trend 2023-2025"
        timeframe = parser._extract_timeframe(query)
        
        assert timeframe.get("start") == 2023
        assert timeframe.get("end") == 2025
    
    def test_extract_timeframe_individual_years(self):
        """Test extracting individual years"""
        parser = QueryIntentParser()
        
        query = "data for 2023 2024 2025"
        timeframe = parser._extract_timeframe(query)
        
        assert timeframe.get("start") == 2023
        assert timeframe.get("end") == 2025
    
    def test_extract_constraints_pdf_only(self):
        """Test extracting PDF-only constraint"""
        parser = QueryIntentParser()
        
        query = "using only PDFs for Apple"
        constraints = parser._extract_constraints(query)
        
        assert constraints.get("pdf_only") == True
        assert constraints.get("sources") == "pdf"
    
    def test_extract_constraints_include_links(self):
        """Test extracting include links constraint"""
        parser = QueryIntentParser()
        
        query = "analysis with links to sources"
        constraints = parser._extract_constraints(query)
        
        assert constraints.get("include_links") == True
    
    def test_full_parse_instruction_query(self):
        """Test full parsing of instruction-style query"""
        intent = parse_query_intent("Create an equity research memo on Pfizer (pharma)", "Pharma")
        
        # Should strip instruction
        assert "Create" not in intent.cleaned_query
        
        # Should extract company
        assert any("Pfizer" in c for c in intent.companies)
        
        # Should detect report type
        assert intent.report_type in ["research_memo", "equity_research"]
        
        # Should preserve sector
        assert intent.sector == "Pharma"
    
    def test_full_parse_comparative_query(self):
        """Test full parsing of comparative query"""
        intent = parse_query_intent(
            "Compare Nvidia vs Microsoft vs Amazon over 2023-2025: revenue growth, operating margins",
            "IT"
        )
        
        # Should extract all companies
        assert len(intent.companies) == 3
        
        # Should detect comparative type
        assert intent.report_type == "comparative_analysis"
        
        # Should extract timeframe
        assert intent.timeframe.get("start") == 2023
        assert intent.timeframe.get("end") == 2025
        
        # Should extract requirements
        assert "revenue_trend" in intent.requirements
        assert "operating_margin" in intent.requirements
    
    def test_full_parse_simple_query(self):
        """Test full parsing of simple information query"""
        intent = parse_query_intent("Analyze Microsoft's cloud services revenue growth", "IT")
        
        # Should extract company
        assert any("Microsoft" in c for c in intent.companies)
        
        # Should extract requirements
        assert "revenue_trend" in intent.requirements
        
        # No instruction to strip
        assert "Microsoft" in intent.cleaned_query
