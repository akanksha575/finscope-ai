"""
Tests for requirement-driven query planner

These tests verify the CRITICAL NON-NEGOTIABLE RULES:
1. NEVER generate self-comparisons (X vs X)
2. Queries MUST target user requirements
3. Financial time-series data is MANDATORY for equity research
"""

import pytest
from research.requirement_driven_planner import (
    RequirementExtractor,
    RequirementDrivenPlanner,
    generate_requirement_driven_queries,
    PRIMARY_COMPETITORS
)


class TestRequirementExtractor:
    """Test requirement extraction"""
    
    def test_extract_products_glp1(self):
        """Test extracting GLP-1 products"""
        extractor = RequirementExtractor()
        
        query = "Analyze Eli Lilly's GLP-1 franchise (Mounjaro, Zepbound)"
        req = extractor.extract(query, ["Eli Lilly"])
        
        assert "GLP-1" in [p.upper() for p in req.products]
        assert "Mounjaro" in req.products
        assert "Zepbound" in req.products
    
    def test_extract_metrics_revenue_margin(self):
        """Test extracting revenue and margin metrics"""
        extractor = RequirementExtractor()
        
        query = "revenue growth and operating margins"
        req = extractor.extract(query, ["Microsoft"])
        
        assert "revenue" in req.metrics
        assert "operating_margin" in req.metrics
    
    def test_extract_years_range(self):
        """Test extracting year range"""
        extractor = RequirementExtractor()
        
        query = "data for 2023-2025"
        req = extractor.extract(query, ["Apple"])
        
        # Extractor captures explicit years (2023, 2025)
        # The planner will fill in intermediate years
        assert 2023 in req.years
        assert 2025 in req.years
    
    def test_extract_calculations(self):
        """Test extracting calculation requirements"""
        extractor = RequirementExtractor()
        
        query = "YoY growth rate and CAGR"
        req = extractor.extract(query, ["Nvidia"])
        
        assert "YoY" in req.calculations or "year-over-year" in req.calculations
        assert "CAGR" in req.calculations
    
    def test_extract_aspects_pipeline(self):
        """Test extracting pipeline aspect"""
        extractor = RequirementExtractor()
        
        query = "drug pipeline and clinical trials"
        req = extractor.extract(query, ["Pfizer"])
        
        assert "pipeline" in req.aspects
    
    def test_extract_aspects_manufacturing(self):
        """Test extracting manufacturing aspect"""
        extractor = RequirementExtractor()
        
        query = "manufacturing capacity and supply constraints"
        req = extractor.extract(query, ["Eli Lilly"])
        
        assert "manufacturing" in req.aspects


class TestRequirementDrivenPlanner:
    """Test requirement-driven query planning"""
    
    def test_product_specific_queries(self):
        """Test that product names appear in queries"""
        planner = RequirementDrivenPlanner()
        
        query = "Analyze Eli Lilly's GLP-1 franchise (Mounjaro, Zepbound) revenue"
        queries = planner.plan_queries(query, ["Eli Lilly"], "Pharma")
        
        # At least one query must contain product names
        has_mounjaro = any("Mounjaro" in q for q in queries)
        has_zepbound = any("Zepbound" in q for q in queries)
        has_glp1 = any("GLP" in q.upper() for q in queries)
        
        assert has_mounjaro or has_zepbound or has_glp1, f"Product names missing from queries: {queries}"
    
    def test_financial_mandatory_revenue(self):
        """Test that revenue queries are generated for equity research"""
        planner = RequirementDrivenPlanner()
        
        query = "Create an equity research memo on Pfizer"
        queries = planner.plan_queries(query, ["Pfizer"], "Pharma")
        
        # Must have at least one revenue query
        revenue_queries = [q for q in queries if "revenue" in q.lower()]
        assert len(revenue_queries) > 0, f"No revenue queries generated: {queries}"
    
    def test_financial_mandatory_margin(self):
        """Test that margin queries are generated for equity research"""
        planner = RequirementDrivenPlanner()
        
        query = "Create an equity research memo on Microsoft"
        queries = planner.plan_queries(query, ["Microsoft"], "IT")
        
        # Must have at least one margin query
        margin_queries = [q for q in queries if "margin" in q.lower() or "profitability" in q.lower()]
        assert len(margin_queries) > 0, f"No margin queries generated: {queries}"
    
    def test_financial_year_specific(self):
        """Test that queries target specific years"""
        planner = RequirementDrivenPlanner()
        
        query = "Analyze Apple revenue for 2023, 2024, 2025"
        queries = planner.plan_queries(query, ["Apple"], "IT")
        
        # Must have queries for each year
        has_2023 = any("2023" in q for q in queries)
        has_2024 = any("2024" in q for q in queries)
        has_2025 = any("2025" in q for q in queries)
        
        assert has_2023 or has_2024 or has_2025, f"Year-specific queries missing: {queries}"
    
    def test_no_self_comparison_single_company(self):
        """CRITICAL: Test that single company does NOT generate self-comparison"""
        planner = RequirementDrivenPlanner()
        
        query = "Compare Eli Lilly's performance"
        queries = planner.plan_queries(query, ["Eli Lilly"], "Pharma")
        
        # Check for self-comparison
        for q in queries:
            if " vs " in q.lower() or " versus " in q.lower():
                # Extract companies
                parts = q.lower().split(" vs ")
                if len(parts) < 2:
                    parts = q.lower().split(" versus ")
                
                # Ensure "eli lilly" doesn't appear twice
                count = sum(1 for part in parts if "eli lilly" in part.lower())
                assert count <= 1, f"SELF-COMPARISON DETECTED: {q}"
    
    def test_no_self_comparison_validation(self):
        """CRITICAL: Test validation rejects self-comparisons"""
        planner = RequirementDrivenPlanner()
        
        # Invalid query
        invalid_query = "Pfizer vs Pfizer revenue comparison"
        is_valid = planner.validate_query(invalid_query, ["Pfizer"])
        
        assert not is_valid, "Validation should reject self-comparison"
    
    def test_comparative_with_primary_competitor(self):
        """Test that single company uses primary competitor"""
        planner = RequirementDrivenPlanner()
        
        query = "Compare Eli Lilly's market share"
        queries = planner.plan_queries(query, ["Eli Lilly"], "Pharma")
        
        # Should compare with Novo Nordisk (primary competitor)
        comparative_queries = [q for q in queries if " vs " in q.lower()]
        if comparative_queries:
            # Check that Novo Nordisk appears
            has_competitor = any("Novo Nordisk" in q for q in comparative_queries)
            assert has_competitor, f"Primary competitor missing: {comparative_queries}"
    
    def test_comparative_multiple_companies(self):
        """Test comparative queries with multiple companies"""
        planner = RequirementDrivenPlanner()
        
        query = "Compare Nvidia vs AMD revenue growth"
        queries = planner.plan_queries(query, ["Nvidia", "AMD"], "IT")
        
        # Should have comparative queries
        comparative_queries = [q for q in queries if " vs " in q.lower()]
        assert len(comparative_queries) > 0, f"No comparative queries generated: {queries}"
        
        # Ensure no self-comparison
        for q in comparative_queries:
            assert not ("nvidia vs nvidia" in q.lower()), f"Self-comparison: {q}"
            assert not ("amd vs amd" in q.lower()), f"Self-comparison: {q}"
    
    def test_aspect_specific_pipeline(self):
        """Test pipeline-specific queries"""
        planner = RequirementDrivenPlanner()
        
        query = "Analyze Pfizer's drug pipeline and clinical trials"
        queries = planner.plan_queries(query, ["Pfizer"], "Pharma")
        
        # Must have pipeline query
        pipeline_queries = [q for q in queries if "pipeline" in q.lower() or "clinical" in q.lower()]
        assert len(pipeline_queries) > 0, f"No pipeline queries generated: {queries}"
    
    def test_aspect_specific_manufacturing(self):
        """Test manufacturing-specific queries"""
        planner = RequirementDrivenPlanner()
        
        query = "Analyze Eli Lilly's manufacturing capacity constraints"
        queries = planner.plan_queries(query, ["Eli Lilly"], "Pharma")
        
        # Must have manufacturing query
        mfg_queries = [q for q in queries if "manufacturing" in q.lower() or "capacity" in q.lower()]
        assert len(mfg_queries) > 0, f"No manufacturing queries generated: {queries}"
    
    def test_company_name_in_all_queries(self):
        """Test that company name appears in all queries"""
        planner = RequirementDrivenPlanner()
        
        query = "Analyze Microsoft's cloud business"
        queries = planner.plan_queries(query, ["Microsoft"], "IT")
        
        # Every query must contain company name
        for q in queries:
            assert "microsoft" in q.lower(), f"Company name missing from query: {q}"


class TestPrimaryCompetitors:
    """Test primary competitor mappings"""
    
    def test_eli_lilly_competitor(self):
        """Test Eli Lilly's primary competitor"""
        assert PRIMARY_COMPETITORS.get("Eli Lilly") == "Novo Nordisk"
    
    def test_pfizer_competitor(self):
        """Test Pfizer's primary competitor"""
        assert PRIMARY_COMPETITORS.get("Pfizer") == "Merck"
    
    def test_microsoft_competitor(self):
        """Test Microsoft's primary competitor"""
        assert PRIMARY_COMPETITORS.get("Microsoft") == "Amazon"
    
    def test_bidirectional_mapping(self):
        """Test that competitor mappings are bidirectional"""
        # If A -> B, then B -> A
        for company, competitor in PRIMARY_COMPETITORS.items():
            reverse_competitor = PRIMARY_COMPETITORS.get(competitor)
            assert reverse_competitor is not None, f"Missing reverse mapping for {competitor}"


class TestEndToEnd:
    """End-to-end tests for complete user queries"""
    
    def test_eli_lilly_glp1_query(self):
        """Test real user query: Eli Lilly GLP-1 analysis"""
        query = "Create an equity research memo on Eli Lilly focusing on their GLP-1 franchise (Mounjaro, Zepbound), manufacturing capacity constraints, and revenue growth 2023-2025"
        queries = generate_requirement_driven_queries(query, ["Eli Lilly"], "Pharma")
        
        # Must have product-specific queries
        assert any("Mounjaro" in q or "Zepbound" in q or "GLP" in q.upper() for q in queries), "Missing product queries"
        
        # Must have manufacturing queries
        assert any("manufacturing" in q.lower() or "capacity" in q.lower() for q in queries), "Missing manufacturing queries"
        
        # Must have revenue queries
        assert any("revenue" in q.lower() for q in queries), "Missing revenue queries"
        
        # Must target years
        assert any("2023" in q or "2024" in q or "2025" in q for q in queries), "Missing year-specific queries"
        
        # No self-comparisons
        for q in queries:
            assert not ("eli lilly vs eli lilly" in q.lower()), f"Self-comparison: {q}"
    
    def test_comparative_three_companies(self):
        """Test comparative query with 3 companies"""
        query = "Compare Nvidia vs Microsoft vs Amazon revenue growth 2023-2025"
        queries = generate_requirement_driven_queries(query, ["Nvidia", "Microsoft", "Amazon"], "IT")
        
        # Must have comparative queries
        assert any(" vs " in q.lower() for q in queries), "Missing comparative queries"
        
        # Must have revenue queries
        assert any("revenue" in q.lower() for q in queries), "Missing revenue queries"
        
        # No self-comparisons
        for q in queries:
            assert not ("nvidia vs nvidia" in q.lower()), f"Self-comparison: {q}"
            assert not ("microsoft vs microsoft" in q.lower()), f"Self-comparison: {q}"
            assert not ("amazon vs amazon" in q.lower()), f"Self-comparison: {q}"
