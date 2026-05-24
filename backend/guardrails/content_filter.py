import re
from typing import List, Dict, Any, Optional
from utils.logger import log

class ContentFilter:
    """Filter sensitive topics and inappropriate content"""
    
    # Sensitive topics that should be blocked
    SENSITIVE_TOPICS = [
        r'\b(terrorism|bomb|attack|violence|weapon|gun|shooting)\b',
        r'\b(narcotic|illegal substance|marijuana|cannabis|cocaine|heroin|meth)\b',  # Removed generic "drug" to allow pharma context
        r'\b(porn|adult content|explicit|nsfw)\b',
        r'\b(hack|cyber attack|malware|virus|exploit)\b',
        r'\b(suicide|self-harm|depression|mental health crisis)\b',
    ]
    
    # Financial scope keywords (queries should contain at least one)
    FINANCIAL_KEYWORDS = [
        r'\b(company|companies|stock|stocks|share|shares|equity|equities|corporation)\b',
        r'\b(revenue|profit|earnings|financial|finance|investment|invest|sales)\b',
        r'\b(market|markets|trading|trade|sector|industry|business|enterprise)\b',
        r'\b(analysis|analyze|analyse|compare|comparison|performance|growth|research)\b',
        r'\b(quarterly|annual|report|reports|financials|balance sheet|results)\b',
        r'\b(merger|acquisition|ipo|dividend|valuation|competitive|strategy)\b',
        # IT sector companies
        r'\b(TCS|Infosys|Wipro|Microsoft|Apple|Google|Amazon|Oracle|IBM|Accenture|Capgemini|HCL|Tech Mahindra)\b',
        # Pharma sector companies and terms
        r'\b(Sun Pharma|Dr Reddy|Cipla|Lupin|Biocon|Pfizer|Novartis|Roche|GSK|Merck|AstraZeneca|Eli Lilly|Johnson)\b',
        r'\b(Zydus|Cadila|Aurobindo|Torrent|Alkem|Glenmark|Mankind|Abbott)\b',
        r'\b(pharma|pharmaceutical|drug|medicine|vaccine|biosimilar|biologic|therapeutic)\b',
        r'\b(clinical|trial|FDA|approval|pipeline|R&D|development|innovation|patent)\b',
        # General business terms
        r'\b(operating|operational|margin|EBITDA|cash flow|capex|expansion)\b',
    ]
    
    def __init__(self):
        self.sensitive_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SENSITIVE_TOPICS]
        self.financial_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.FINANCIAL_KEYWORDS]
        log.info("Initialized ContentFilter")
    
    def check_sensitive_content(self, text: str) -> Dict[str, Any]:
        """
        Check if text contains sensitive or inappropriate content
        
        Returns:
            Dict with 'blocked' (bool) and 'reason' (str)
        """
        for pattern in self.sensitive_patterns:
            if pattern.search(text):
                matched = pattern.pattern
                log.warning(f"Sensitive content detected: {matched}")
                return {
                    "blocked": True,
                    "reason": f"Query contains sensitive topic: {matched}",
                    "category": "sensitive_content"
                }
        
        return {"blocked": False, "reason": None}
    
    def check_financial_scope(self, text: str) -> Dict[str, Any]:
        """
        Check if query is within financial research scope
        
        Returns:
            Dict with 'in_scope' (bool) and 'reason' (str)
        """
        # Check if query contains financial keywords
        for pattern in self.financial_patterns:
            if pattern.search(text):
                return {
                    "in_scope": True,
                    "reason": "Query contains financial/business keywords"
                }
        
        # If no financial keywords found, it's out of scope
        log.warning(f"Query out of scope (no financial keywords): {text[:100]}")
        return {
            "in_scope": False,
            "reason": "Query does not appear to be related to financial research. Please ask questions about companies, stocks, markets, or financial analysis."
        }
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Returns:
            Sanitized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limit length (prevent DoS)
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length]
            log.warning(f"Input truncated to {max_length} characters")
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Comprehensive query validation
        
        Returns:
            Dict with validation results
        """
        if not query or not isinstance(query, str):
            return {
                "valid": False,
                "reason": "Query is empty or invalid",
                "category": "validation_error"
            }
        
        # Sanitize input
        sanitized = self.sanitize_input(query)
        
        if not sanitized:
            return {
                "valid": False,
                "reason": "Query is empty after sanitization",
                "category": "validation_error"
            }
        
        # Check sensitive content
        sensitive_check = self.check_sensitive_content(sanitized)
        if sensitive_check["blocked"]:
            return {
                "valid": False,
                "reason": sensitive_check["reason"],
                "category": sensitive_check["category"],
                "sanitized_query": sanitized
            }
        
        # Check financial scope
        scope_check = self.check_financial_scope(sanitized)
        if not scope_check["in_scope"]:
            return {
                "valid": False,
                "reason": scope_check["reason"],
                "category": "out_of_scope",
                "sanitized_query": sanitized
            }
        
        return {
            "valid": True,
            "sanitized_query": sanitized,
            "reason": "Query validated successfully"
        }


# Global instance
content_filter = ContentFilter()