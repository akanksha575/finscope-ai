from research.complexity import QueryType
from research.dimensions import get_dimensions, get_dimension_keywords, update_dimension_coverage


def test_it_company_dimensions_present():
    dims = get_dimensions("IT", QueryType.COMPANY_DEEP_DIVE)
    assert "Financial Performance" in dims
    assert "Operational Metrics" in dims


def test_pharma_company_dimensions_present():
    dims = get_dimensions("Pharma", QueryType.COMPANY_DEEP_DIVE)
    assert "Pipeline Analysis" in dims
    assert "Patent Landscape" in dims


def test_dimension_coverage_updates_from_text():
    kws = get_dimension_keywords("IT", QueryType.COMPANY_DEEP_DIVE)
    covered = {k: False for k in kws.keys()}
    updated = update_dimension_coverage(covered, kws, "Latest revenue growth and operating margin guidance")
    assert updated["Financial Performance"] is True

