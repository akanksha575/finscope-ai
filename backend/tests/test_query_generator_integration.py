"""
Integration tests for QueryGenerator with requirement-driven planning

Tests verify the complete flow from user query to generated search queries.

NOTE: These tests require OPENAI_API_KEY to be set.
Run with: pytest tests/test_query_generator_integration.py -v -s
"""

import pytest
import os
from research.query_generator import QueryGenerator


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)


class TestQueryGeneratorIntegration:
    """Integration tests for requirement-driven query generation"""
    
    @pytest.mark.asyncio
    async def test_eli_lilly_glp1_comprehensive(self):
        """Test comprehensive Eli Lilly GLP-1 query"""
        generator = QueryGenerator()
        
        query = "Create an equity research memo on Eli Lilly focusing on their GLP-1 franchise (Mounjaro, Zepbound), manufacturing capacity constraints, and revenue growth 2023-2025"
        queries = await generator.generate_research_queries(query, "Pharma")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # CRITICAL: No self-comparisons
        for q in queries:
            assert not ("eli lilly vs eli lilly" in q.lower()), f"SELF-COMPARISON: {q}"
        
        # Must have product-specific queries
        product_queries = [q for q in queries if "Mounjaro" in q or "Zepbound" in q or "GLP" in q.upper()]
        assert len(product_queries) > 0, f"Missing product queries. Got: {queries}"
        
        # Must have revenue queries
        revenue_queries = [q for q in queries if "revenue" in q.lower()]
        assert len(revenue_queries) > 0, f"Missing revenue queries. Got: {queries}"
        
        # Must have manufacturing queries
        mfg_queries = [q for q in queries if "manufacturing" in q.lower() or "capacity" in q.lower()]
        assert len(mfg_queries) > 0, f"Missing manufacturing queries. Got: {queries}"
        
        # Must target years
        year_queries = [q for q in queries if "2023" in q or "2024" in q or "2025" in q]
        assert len(year_queries) > 0, f"Missing year-specific queries. Got: {queries}"
    
    @pytest.mark.asyncio
    async def test_pfizer_simple_equity_research(self):
        """Test simple equity research query"""
        generator = QueryGenerator()
        
        query = "Create an equity research memo on Pfizer"
        queries = await generator.generate_research_queries(query, "Pharma")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # CRITICAL: No self-comparisons
        for q in queries:
            assert not ("pfizer vs pfizer" in q.lower()), f"SELF-COMPARISON: {q}"
        
        # Must have revenue queries (mandatory for equity research)
        revenue_queries = [q for q in queries if "revenue" in q.lower()]
        assert len(revenue_queries) > 0, f"Missing revenue queries. Got: {queries}"
        
        # Must have margin queries (mandatory for equity research)
        margin_queries = [q for q in queries if "margin" in q.lower() or "profitability" in q.lower()]
        assert len(margin_queries) > 0, f"Missing margin queries. Got: {queries}"
        
        # All queries must contain company name
        for q in queries:
            assert "pfizer" in q.lower(), f"Company name missing: {q}"
    
    @pytest.mark.asyncio
    async def test_comparative_three_companies(self):
        """Test comparative query with 3 companies"""
        generator = QueryGenerator()
        
        query = "Compare Nvidia vs Microsoft vs Amazon revenue growth 2023-2025"
        queries = await generator.generate_research_queries(query, "IT")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # CRITICAL: No self-comparisons
        for q in queries:
            assert not ("nvidia vs nvidia" in q.lower()), f"SELF-COMPARISON: {q}"
            assert not ("microsoft vs microsoft" in q.lower()), f"SELF-COMPARISON: {q}"
            assert not ("amazon vs amazon" in q.lower()), f"SELF-COMPARISON: {q}"
        
        # Must have revenue queries
        revenue_queries = [q for q in queries if "revenue" in q.lower()]
        assert len(revenue_queries) > 0, f"Missing revenue queries. Got: {queries}"
        
        # Must have comparative queries
        comparative_queries = [q for q in queries if " vs " in q.lower()]
        assert len(comparative_queries) > 0, f"Missing comparative queries. Got: {queries}"
        
        # Must target years
        year_queries = [q for q in queries if "2023" in q or "2024" in q or "2025" in q]
        assert len(year_queries) > 0, f"Missing year-specific queries. Got: {queries}"
    
    @pytest.mark.asyncio
    async def test_single_company_comparison_uses_competitor(self):
        """Test that single company comparison uses primary competitor"""
        generator = QueryGenerator()
        
        query = "Compare Eli Lilly's market position"
        queries = await generator.generate_research_queries(query, "Pharma")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # CRITICAL: No self-comparisons
        for q in queries:
            assert not ("eli lilly vs eli lilly" in q.lower()), f"SELF-COMPARISON: {q}"
        
        # Should use primary competitor (Novo Nordisk)
        comparative_queries = [q for q in queries if " vs " in q.lower()]
        if comparative_queries:
            # At least one should mention Novo Nordisk
            has_competitor = any("novo nordisk" in q.lower() for q in comparative_queries)
            assert has_competitor, f"Primary competitor missing. Got: {comparative_queries}"
    
    @pytest.mark.asyncio
    async def test_microsoft_cloud_specific(self):
        """Test product-specific query (Microsoft cloud)"""
        generator = QueryGenerator()
        
        query = "Analyze Microsoft's Azure cloud services revenue growth"
        queries = await generator.generate_research_queries(query, "IT")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # CRITICAL: No self-comparisons
        for q in queries:
            assert not ("microsoft vs microsoft" in q.lower()), f"SELF-COMPARISON: {q}"
        
        # Must have Azure-specific queries
        azure_queries = [q for q in queries if "azure" in q.lower() or "cloud" in q.lower()]
        assert len(azure_queries) > 0, f"Missing Azure/cloud queries. Got: {queries}"
        
        # Must have revenue queries
        revenue_queries = [q for q in queries if "revenue" in q.lower()]
        assert len(revenue_queries) > 0, f"Missing revenue queries. Got: {queries}"
    
    @pytest.mark.asyncio
    async def test_no_instruction_prefix_pollution(self):
        """Test that instruction prefixes are stripped"""
        generator = QueryGenerator()
        
        query = "Create an equity research memo on Apple"
        queries = await generator.generate_research_queries(query, "IT")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # No query should start with instruction prefixes
        for q in queries:
            q_lower = q.lower()
            assert not q_lower.startswith("create"), f"Instruction prefix: {q}"
            assert not q_lower.startswith("generate"), f"Instruction prefix: {q}"
            assert not q_lower.startswith("produce"), f"Instruction prefix: {q}"
    
    @pytest.mark.asyncio
    async def test_all_queries_have_company_name(self):
        """Test that all queries contain company name"""
        generator = QueryGenerator()
        
        query = "Analyze Nvidia's GPU business and AI chip revenue"
        queries = await generator.generate_research_queries(query, "IT")
        
        print(f"\n=== Generated {len(queries)} queries ===")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        
        # Every query must contain company name
        for q in queries:
            assert "nvidia" in q.lower(), f"Company name missing: {q}"
