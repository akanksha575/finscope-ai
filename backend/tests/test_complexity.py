from research.complexity import assess_query_type, plan_for_query, QueryType


def test_query_type_company_default():
    assert assess_query_type("Analyze Infosys profitability") == QueryType.COMPANY_DEEP_DIVE


def test_query_type_comparison():
    assert assess_query_type("Compare TCS vs Infosys AI capabilities") == QueryType.COMPETITIVE_COMPARISON


def test_query_type_sector_trend():
    assert assess_query_type("Emerging trends in Indian IT services market") == QueryType.SECTOR_TREND


def test_query_type_strategic_impact():
    assert assess_query_type("Impact of AI on Indian IT sector margins") == QueryType.STRATEGIC_IMPACT


def test_plan_for_query_bounds():
    p = plan_for_query("What is TCS market cap?")
    assert 5 <= p.min_steps <= p.max_steps <= 25

