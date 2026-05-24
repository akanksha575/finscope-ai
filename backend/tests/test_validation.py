from research.validation import extract_numeric_claims, merge_claim_evidence, unvalidated_claims


def test_extract_numeric_claims_finds_percent_and_currency():
    text = "Operating margin improved to 24.1% and revenue reached $7.5B in Q3."
    claims = extract_numeric_claims(text)
    assert any("%" in c["value"] for c in claims)
    assert any("$" in c["value"] or "B" in c["value"].upper() for c in claims)


def test_merge_claim_evidence_validates_on_two_domains():
    registry = {}
    claims = extract_numeric_claims("Market cap is $100B.")
    registry = merge_claim_evidence(registry, claims, domain="example.com", url="https://example.com/a")
    assert unvalidated_claims(registry)
    registry = merge_claim_evidence(registry, claims, domain="example2.com", url="https://example2.com/b")
    assert not unvalidated_claims(registry)

