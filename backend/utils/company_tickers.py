import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CompanyMatch:
    canonical_name: str
    ticker: str
    start: int  # start index in normalized text for ordering


def _normalize_text(text: str) -> str:
    """
    Normalize free text for robust substring matching:
    - lowercase
    - replace punctuation with spaces
    - collapse whitespace
    """
    if not text:
        return ""
    t = text.lower()
    # Keep dots for patterns like "dr." but treat everything else as separators.
    t = re.sub(r"[^a-z0-9\.\s]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # Also add a "no dots" variant behavior by normalizing "dr." -> "dr"
    t = t.replace("dr.", "dr")
    return t


# Canonical mapping: alias -> (canonical_name, yfinance_ticker)
# Keep aliases lowercase + normalized-ish; matching is done on normalized query text.
COMPANY_TICKER_MAP: Dict[str, Tuple[str, str]] = {
    # IT (India / global)
    "tcs": ("Tata Consultancy Services", "TCS.NS"),
    "tata consultancy": ("Tata Consultancy Services", "TCS.NS"),
    "tata consultancy services": ("Tata Consultancy Services", "TCS.NS"),
    "infosys": ("Infosys", "INFY.NS"),
    "wipro": ("Wipro", "WIPRO.NS"),
    "hcl": ("HCL Technologies", "HCLTECH.NS"),
    "hcltech": ("HCL Technologies", "HCLTECH.NS"),
    "hcl technologies": ("HCL Technologies", "HCLTECH.NS"),
    "tech mahindra": ("Tech Mahindra", "TECHM.NS"),
    "microsoft": ("Microsoft", "MSFT"),
    "msft": ("Microsoft", "MSFT"),
    "nvidia": ("Nvidia", "NVDA"),
    "nvda": ("Nvidia", "NVDA"),
    "amazon": ("Amazon", "AMZN"),
    "amzn": ("Amazon", "AMZN"),
    "google": ("Alphabet", "GOOGL"),
    "alphabet": ("Alphabet", "GOOGL"),
    "googl": ("Alphabet", "GOOGL"),
    "apple": ("Apple", "AAPL"),
    "aapl": ("Apple", "AAPL"),

    # Pharma (Global)
    "pfizer": ("Pfizer", "PFE"),
    "pfe": ("Pfizer", "PFE"),
    "merck": ("Merck", "MRK"),
    "mrk": ("Merck", "MRK"),
    "bristol myers": ("Bristol Myers Squibb", "BMY"),
    "bristol myers squibb": ("Bristol Myers Squibb", "BMY"),
    "bmy": ("Bristol Myers Squibb", "BMY"),
    "johnson": ("Johnson & Johnson", "JNJ"),
    "johnson & johnson": ("Johnson & Johnson", "JNJ"),
    "jnj": ("Johnson & Johnson", "JNJ"),
    "eli lilly": ("Eli Lilly", "LLY"),
    "lilly": ("Eli Lilly", "LLY"),
    "lly": ("Eli Lilly", "LLY"),
    "gsk": ("GSK", "GSK"),
    "glaxosmithkline": ("GSK", "GSK"),
    "astrazeneca": ("AstraZeneca", "AZN"),
    "azn": ("AstraZeneca", "AZN"),
    
    # Pharma (India)
    "dr reddy": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "dr reddys": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "dr reddys laboratories": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "dr reddy laboratories": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "dr reddy's": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "dr reddy's laboratories": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "dr. reddy's laboratories": ("Dr. Reddy's Laboratories", "DRREDDY.NS"),
    "sun pharma": ("Sun Pharmaceutical Industries", "SUNPHARMA.NS"),
    "sun pharmaceutical": ("Sun Pharmaceutical Industries", "SUNPHARMA.NS"),
    "sun pharmaceutical industries": ("Sun Pharmaceutical Industries", "SUNPHARMA.NS"),
    "biocon": ("Biocon", "BIOCON.NS"),
    "cipla": ("Cipla", "CIPLA.NS"),
    "lupin": ("Lupin", "LUPIN.NS"),
}


def find_companies(text: str) -> List[CompanyMatch]:
    """
    Return all recognized companies in the text, ordered by first appearance.
    Matching is substring-based on normalized text.
    """
    n = _normalize_text(text)
    if not n:
        return []

    matches: List[CompanyMatch] = []
    for alias, (canonical_name, ticker) in COMPANY_TICKER_MAP.items():
        alias_n = _normalize_text(alias)
        if not alias_n:
            continue
        idx = n.find(alias_n)
        if idx >= 0:
            matches.append(CompanyMatch(canonical_name=canonical_name, ticker=ticker, start=idx))

    # Order by first appearance; dedupe by ticker while preserving order.
    matches.sort(key=lambda m: m.start)
    seen = set()
    ordered: List[CompanyMatch] = []
    for m in matches:
        if m.ticker in seen:
            continue
        ordered.append(m)
        seen.add(m.ticker)
    return ordered


def extract_primary_company_name(text: str) -> Optional[str]:
    """Best-effort: return the first recognized company's canonical name."""
    matches = find_companies(text)
    return matches[0].canonical_name if matches else None


def extract_tickers(text: str, max_companies: int = 3) -> List[str]:
    """Return up to N tickers found in the text, ordered by mention."""
    matches = find_companies(text)
    return [m.ticker for m in matches[:max_companies]]

