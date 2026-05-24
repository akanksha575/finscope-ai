from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Dict, List, Optional, Tuple


_RE_NUMBER = re.compile(
    r"(?P<value>(?:₹|\$)?\s?\d[\d,]*(?:\.\d+)?\s?(?:billion|million|bn|mn|cr|crore|%)?)",
    re.I,
)


def _normalize_context(text: str) -> str:
    t = " ".join((text or "").lower().split())
    # remove most punctuation for stable keys
    t = re.sub(r"[^a-z0-9\s%₹$]", " ", t)
    t = " ".join(t.split())
    return t


def extract_numeric_claims(text: str, window: int = 60) -> List[Dict[str, str]]:
    """
    Extract crude numeric claims from text.
    Returns list of dicts: {value, context, key}.

    This is intentionally heuristic. The goal is to drive validation searches
    and detect when multiple independent sources support the same quantitative statement.
    """
    if not text:
        return []

    claims: List[Dict[str, str]] = []
    for m in _RE_NUMBER.finditer(text):
        value = m.group("value").strip()
        if len(value) < 2:
            continue
        start = max(m.start() - window, 0)
        end = min(m.end() + window, len(text))
        context = text[start:end].strip()
        norm = _normalize_context(context)
        key = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]
        claims.append({"value": value, "context": context, "key": key})
    return claims


def merge_claim_evidence(
    claim_registry: Dict[str, Dict],
    new_claims: List[Dict[str, str]],
    domain: str,
    url: Optional[str] = None,
) -> Dict[str, Dict]:
    """
    Merge extracted claims into a registry keyed by claim.key.
    Registry entry shape:
      {
        "key": str,
        "value_examples": [str],
        "contexts": [str],
        "evidence_domains": [str],
        "evidence_urls": [str],
        "validated": bool,
      }
    """
    updated = dict(claim_registry or {})
    for c in new_claims:
        key = c.get("key")
        if not key:
            continue
        entry = updated.get(key) or {
            "key": key,
            "value_examples": [],
            "contexts": [],
            "evidence_domains": [],
            "evidence_urls": [],
            "validated": False,
        }
        v = c.get("value")
        ctx = c.get("context")
        if v and v not in entry["value_examples"]:
            entry["value_examples"].append(v)
        if ctx and ctx not in entry["contexts"]:
            entry["contexts"].append(ctx)
        if domain and domain not in entry["evidence_domains"]:
            entry["evidence_domains"].append(domain)
        if url and url not in entry["evidence_urls"]:
            entry["evidence_urls"].append(url)

        # Validate if we have >=2 independent domains.
        if len(entry["evidence_domains"]) >= 2:
            entry["validated"] = True

        updated[key] = entry
    return updated


def unvalidated_claims(claim_registry: Dict[str, Dict], limit: int = 5) -> List[Dict]:
    if not claim_registry:
        return []
    items = [v for v in claim_registry.values() if not v.get("validated")]
    # prioritize "high impact" claims first, then those with more evidence.
    critical_terms = [
        "market cap", "revenue", "profit", "margin", "cagr", "market share",
        "guidance", "operating", "ebitda", "r&d", "pipeline", "approval",
        "patent", "deal", "tcv",
    ]

    def score(item: Dict) -> int:
        ctx = " ".join(item.get("contexts", [])).lower()
        term_hits = sum(1 for t in critical_terms if t in ctx)
        evidence = len(item.get("evidence_domains", []))
        return term_hits * 10 + evidence

    items.sort(key=score, reverse=True)
    return items[:limit]

