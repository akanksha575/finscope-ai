"""
Tests for query intelligence system
"""

import pytest
from research.query_intelligence import (
    CoverageTracker,
    QueryHistory,
    SimilarityChecker,
    ThreadExtractor,
    QueryConstructor,
    PhaseManager,
    ResearchPhase,
    get_dimension_framework
)


class TestDimensionFramework:
    """Test dimension framework"""
    
    def test_it_dimensions(self):
        """Test IT dimension framework"""
        dims = get_dimension_framework("IT")
        assert "Financial Performance" in dims
        assert "Business Segments" in dims
        assert "Market Position" in dims
        assert len(dims) == 9
    
    def test_pharma_dimensions(self):
        """Test Pharma dimension framework"""
        dims = get_dimension_framework("Pharma")
        assert "Financial Performance" in dims
        assert "Drug Pipeline" in dims
        assert "Regulatory & Patents" in dims
        assert len(dims) == 9


class TestCoverageTracker:
    """Test coverage tracker"""
    
    def test_initialization(self):
        """Test tracker initialization"""
        tracker = CoverageTracker(sector="IT")
        assert tracker.sector == "IT"
        assert len(tracker.dimensions) == 9
        assert all(not d.covered for d in tracker.dimensions.values())
    
    def test_update_from_text(self):
        """Test updating coverage from text"""
        tracker = CoverageTracker(sector="IT")
        text = "Microsoft reported strong revenue growth of 15% with cloud services leading"
        updated = tracker.update_from_text(text)
        
        assert "Financial Performance" in updated
        assert tracker.dimensions["Financial Performance"].covered
    
    def test_coverage_percentage(self):
        """Test coverage percentage calculation"""
        tracker = CoverageTracker(sector="IT")
        assert tracker.get_coverage_percentage() == 0.0
        
        # Update with comprehensive text
        text = """
        Microsoft reported revenue of $77B with strong profit margins.
        Their cloud segment Azure is growing rapidly.
        Market share increased to 30% in enterprise software.
        AI and machine learning investments are paying off.
        Employee count reached 200,000 with low attrition.
        R&D spending increased to $25B for innovation.
        Competing strongly against AWS and Google Cloud.
        Key risks include regulatory challenges.
        Future outlook is positive with strong growth projections.
        """
        tracker.update_from_text(text)
        
        coverage = tracker.get_coverage_percentage()
        assert coverage > 70.0  # Should cover most dimensions


class TestSimilarityChecker:
    """Test semantic similarity checker"""
    
    def test_exact_match(self):
        """Test exact match detection"""
        checker = SimilarityChecker(threshold=0.7)
        q1 = "Microsoft cloud revenue growth 2026"
        q2 = "Microsoft cloud revenue growth 2026"
        
        similarity = checker.calculate_similarity(q1, q2)
        assert similarity == 1.0
    
    def test_similar_queries(self):
        """Test similar query detection"""
        checker = SimilarityChecker(threshold=0.7)
        q1 = "Microsoft cloud revenue growth 2026"
        q2 = "Microsoft cloud revenue increase 2026"
        
        similarity = checker.calculate_similarity(q1, q2)
        assert similarity > 0.5  # Should be moderately similar (0.6)
    
    def test_different_queries(self):
        """Test different query detection"""
        checker = SimilarityChecker(threshold=0.7)
        q1 = "Microsoft cloud revenue growth 2026"
        q2 = "Apple iPhone sales market share India"
        
        similarity = checker.calculate_similarity(q1, q2)
        assert similarity < 0.3  # Should be different
    
    def test_is_too_similar(self):
        """Test repetition detection"""
        checker = SimilarityChecker(threshold=0.7)
        previous = [
            "Microsoft cloud revenue 2026",
            "Microsoft AI investments analysis",
            "Microsoft market position competitive landscape"
        ]
        
        # Similar query
        is_similar, _ = checker.is_too_similar("Microsoft cloud revenue growth 2026", previous)
        assert is_similar
        
        # Different query
        is_similar, _ = checker.is_too_similar("Microsoft employee attrition rate 2026", previous)
        assert not is_similar


class TestQueryHistory:
    """Test query history"""
    
    def test_add_query(self):
        """Test adding queries"""
        history = QueryHistory()
        assert len(history.queries) == 0
        
        history.add_query("Test query 1")
        assert len(history.queries) == 1
        
        history.add_query("Test query 2")
        assert len(history.queries) == 2
    
    def test_is_repetitive(self):
        """Test repetition checking"""
        history = QueryHistory()
        history.add_query("Microsoft cloud revenue 2026")
        history.add_query("Microsoft AI strategy analysis")
        
        # Similar query
        is_rep, _ = history.is_repetitive("Microsoft cloud revenue growth 2026")
        assert is_rep
        
        # Different query
        is_rep, _ = history.is_repetitive("Apple iPhone sales India")
        assert not is_rep


class TestThreadExtractor:
    """Test thread extraction"""
    
    def test_extract_entities_it(self):
        """Test entity extraction for IT"""
        extractor = ThreadExtractor()
        text = "Microsoft and Google are competing in cloud services with AWS"
        threads = extractor.extract_entities(text, "IT")
        
        entity_contents = [t.content for t in threads]
        assert "Microsoft" in entity_contents
        assert "Google" in entity_contents
    
    def test_extract_entities_pharma(self):
        """Test entity extraction for Pharma"""
        extractor = ThreadExtractor()
        text = "Pfizer and GSK are developing new vaccines while Sun Pharma focuses on generics"
        threads = extractor.extract_entities(text, "Pharma")
        
        entity_contents = [t.content for t in threads]
        assert "Pfizer" in entity_contents
        assert "Gsk" in entity_contents
    
    def test_extract_metrics(self):
        """Test metric extraction"""
        extractor = ThreadExtractor()
        text = "Revenue reached $77 billion with 15% growth and 41% operating margin"
        threads = extractor.extract_metrics(text)
        
        assert len(threads) > 0
        assert any("$77" in t.content for t in threads)


class TestQueryConstructor:
    """Test query constructor"""
    
    def test_overview_query(self):
        """Test overview query construction"""
        constructor = QueryConstructor()
        query = constructor.construct_overview_query("Microsoft", "IT")
        
        assert "Microsoft" in query
        assert "2026" in query
        assert len(query) > 10
    
    def test_deep_dive_query(self):
        """Test deep dive query construction"""
        constructor = QueryConstructor()
        query = constructor.construct_deep_dive_query("Microsoft", "cloud revenue", "IT")
        
        assert "Microsoft" in query
        assert "cloud revenue" in query or "cloud" in query
    
    def test_comparative_query(self):
        """Test comparative query construction"""
        constructor = QueryConstructor()
        query = constructor.construct_comparative_query("Microsoft", "Google", "cloud market share", "IT")
        
        assert "Microsoft" in query
        assert "Google" in query or "vs" in query
    
    def test_validate_query_quality(self):
        """Test query quality validation"""
        constructor = QueryConstructor()
        
        # Good query
        is_valid, _ = constructor.validate_query_quality("Microsoft cloud revenue growth 2026")
        assert is_valid
        
        # Too short
        is_valid, error = constructor.validate_query_quality("test")
        assert not is_valid
        
        # Malformed
        is_valid, error = constructor.validate_query_quality("validate $75.49 billion ghlights")
        assert not is_valid


class TestPhaseManager:
    """Test phase manager"""
    
    def test_initialization(self):
        """Test phase manager initialization"""
        manager = PhaseManager()
        assert manager.current_phase == ResearchPhase.OVERVIEW
        assert manager.steps_in_phase == 0
        assert manager.total_steps == 0
    
    def test_phase_advancement(self):
        """Test phase advancement"""
        manager = PhaseManager()
        tracker = CoverageTracker(sector="IT")
        
        # Advance from overview
        manager.steps_in_phase = 2
        assert manager.should_advance_phase(tracker, [])
        
        new_phase = manager.advance_phase()
        assert new_phase == ResearchPhase.DEEP_DIVE
        assert manager.steps_in_phase == 0
    
    def test_record_step(self):
        """Test step recording"""
        manager = PhaseManager()
        assert manager.steps_in_phase == 0
        assert manager.total_steps == 0
        
        manager.record_step()
        assert manager.steps_in_phase == 1
        assert manager.total_steps == 1
        
        manager.record_step()
        assert manager.steps_in_phase == 2
        assert manager.total_steps == 2
