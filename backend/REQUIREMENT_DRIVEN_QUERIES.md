# Requirement-Driven Query Generation System

## Overview

The FinScope AI query generation system has been completely rewritten to generate **precise, requirement-driven queries** instead of generic templates.

## Critical Non-Negotiable Rules

### 1. NEVER Generate Self-Comparisons ❌

**Invalid:**
```
"Eli Lilly vs Eli Lilly market share"
"Pfizer vs Pfizer revenue comparison"
```

**Valid:**
```
"Eli Lilly vs Novo Nordisk market share"  (uses primary competitor)
"Pfizer vs Merck revenue comparison"      (uses primary competitor)
```

**Implementation:**
- Primary competitor mapping in `requirement_driven_planner.py`
- Validation layer rejects any "X vs X" queries
- Single-company comparisons automatically use mapped competitor

### 2. Queries MUST Target User Requirements ✅

**User Query:**
```
"Analyze Eli Lilly's GLP-1 franchise (Mounjaro, Zepbound), 
manufacturing capacity, and revenue growth 2023-2025"
```

**Generated Queries:**
```
✅ "Eli Lilly GLP-1 Mounjaro Zepbound revenue sales 2023 2024 2025"
✅ "Eli Lilly manufacturing capacity expansion facilities supply constraints"
✅ "Eli Lilly revenue 2023 annual quarterly earnings fiscal"
✅ "Eli Lilly revenue 2024 annual quarterly earnings fiscal"
✅ "Eli Lilly revenue 2025 annual quarterly earnings fiscal"
```

**NOT Generated:**
```
❌ "drug portfolio pipeline"  (too generic, missing product names)
❌ "Pharma market overview"   (not company-specific)
```

### 3. Financial Time-Series Data is MANDATORY 📊

For ANY equity research request, the system MUST generate:

**Revenue Queries (for each year):**
```
"{company} revenue {year} annual quarterly earnings fiscal"
```

**Margin Queries (for each year):**
```
"{company} operating margin {year} profitability EBITDA"
```

**Trend Queries (if multiple years):**
```
"{company} revenue growth rate {start_year}-{end_year} CAGR YoY trend"
"{company} operating margin trend {start_year}-{end_year} profitability"
```

**Guidance Queries (for future years):**
```
"{company} revenue {future_year} guidance forecast analyst estimates"
```

## Architecture

### 1. Requirement Extractor

**File:** `research/requirement_driven_planner.py`

**Extracts:**
- **Companies**: All company names mentioned
- **Products**: Specific products/drugs/services (GLP-1, Mounjaro, Azure, etc.)
- **Metrics**: revenue, operating_margin, profit_margin, cash_flow, market_share
- **Years**: All years mentioned (2023, 2024, 2025)
- **Calculations**: YoY, CAGR, trend
- **Aspects**: pipeline, manufacturing, R&D, risks, competition, guidance

**Example:**
```python
query = "Analyze Eli Lilly's GLP-1 franchise (Mounjaro, Zepbound) revenue 2023-2025"

extracted = {
    "companies": ["Eli Lilly"],
    "products": ["GLP-1", "Mounjaro", "Zepbound"],
    "metrics": {"revenue"},
    "years": [2023, 2024, 2025],
    "aspects": set()
}
```

### 2. Requirement-Driven Planner

**File:** `research/requirement_driven_planner.py`

**Query Generation Logic:**

1. **Product-Specific Queries** (if products mentioned)
   - Include product names explicitly
   - Target revenue, market share, performance

2. **Financial Time-Series Queries** (mandatory for equity research)
   - Revenue for EACH year
   - Margins for EACH year
   - Trend queries if multiple years
   - Guidance for future years

3. **Aspect-Specific Queries** (if aspects mentioned)
   - Pipeline: "drug pipeline clinical trials phase 3"
   - Manufacturing: "manufacturing capacity expansion facilities"
   - R&D: "R&D spending investment research development"
   - Risks: "key risks challenges threats headwinds"

4. **Comparative Queries** (only if valid)
   - Single company: Use primary competitor
   - Multiple companies: Compare distinct companies
   - Validation: Reject self-comparisons

### 3. Primary Competitor Mapping

**File:** `research/requirement_driven_planner.py`

```python
PRIMARY_COMPETITORS = {
    # Pharma
    "Eli Lilly": "Novo Nordisk",
    "Novo Nordisk": "Eli Lilly",
    "Pfizer": "Merck",
    "Merck": "Pfizer",
    "Bristol Myers Squibb": "Merck",
    "Sun Pharma": "Cipla",
    "Dr. Reddy's Laboratories": "Lupin",
    
    # Tech
    "Microsoft": "Amazon",
    "Amazon": "Microsoft",
    "Apple": "Microsoft",
    "Nvidia": "AMD",
}
```

### 4. Query Validation

**File:** `research/requirement_driven_planner.py`

**Validates:**
- ❌ Self-comparisons ("X vs X")
- ❌ Missing company name
- ✅ Company name present
- ✅ Requirement-specific keywords

## Examples

### Example 1: Comprehensive Pharma Query

**User Query:**
```
"Create an equity research memo on Eli Lilly focusing on their GLP-1 
franchise (Mounjaro, Zepbound), manufacturing capacity constraints, 
and revenue growth 2023-2025"
```

**Generated Queries:**
```
1. Eli Lilly GLP-1 Mounjaro Zepbound revenue sales 2023 2024 2025
2. Eli Lilly Mounjaro market share adoption rate performance
3. Eli Lilly Zepbound market share adoption rate performance
4. Eli Lilly revenue 2023 annual quarterly earnings fiscal
5. Eli Lilly revenue 2024 annual quarterly earnings fiscal
6. Eli Lilly revenue 2025 annual quarterly earnings fiscal
7. Eli Lilly revenue growth rate 2023-2025 CAGR YoY trend
8. Eli Lilly operating margin 2023 profitability EBITDA
9. Eli Lilly operating margin 2024 profitability EBITDA
10. Eli Lilly operating margin 2025 profitability EBITDA
11. Eli Lilly manufacturing capacity expansion facilities supply constraints
```

**Coverage:**
- ✅ Product names (GLP-1, Mounjaro, Zepbound)
- ✅ Revenue for each year (2023, 2024, 2025)
- ✅ Operating margins for each year
- ✅ Manufacturing capacity
- ✅ No self-comparisons
- ✅ All queries contain "Eli Lilly"

### Example 2: Comparative Query (3 Companies)

**User Query:**
```
"Compare Nvidia vs Microsoft vs Amazon revenue growth 2023-2025"
```

**Generated Queries:**
```
1. Nvidia revenue 2023 annual quarterly earnings fiscal
2. Nvidia revenue 2024 annual quarterly earnings fiscal
3. Nvidia revenue 2025 annual quarterly earnings fiscal
4. Nvidia revenue growth rate 2023-2025 CAGR YoY trend
5. Microsoft revenue 2023 annual quarterly earnings fiscal
6. Microsoft revenue 2024 annual quarterly earnings fiscal
7. Microsoft revenue 2025 annual quarterly earnings fiscal
8. Microsoft revenue growth rate 2023-2025 CAGR YoY trend
9. Amazon revenue 2023 annual quarterly earnings fiscal
10. Amazon revenue 2024 annual quarterly earnings fiscal
11. Amazon revenue 2025 annual quarterly earnings fiscal
12. Amazon revenue growth rate 2023-2025 CAGR YoY trend
13. Nvidia vs Microsoft revenue comparison
14. Nvidia vs Amazon revenue comparison
15. Nvidia vs Microsoft vs Amazon market share comparison
```

**Coverage:**
- ✅ Revenue for each company, each year
- ✅ Comparative queries
- ✅ No self-comparisons
- ✅ All queries contain company names

### Example 3: Single Company Comparison

**User Query:**
```
"Compare Eli Lilly's market position"
```

**Generated Queries:**
```
1. Eli Lilly revenue 2023 annual quarterly earnings fiscal
2. Eli Lilly revenue 2024 annual quarterly earnings fiscal
3. Eli Lilly revenue 2025 annual quarterly earnings fiscal
4. Eli Lilly operating margin 2023 profitability EBITDA
5. Eli Lilly operating margin 2024 profitability EBITDA
6. Eli Lilly vs Novo Nordisk market share comparison  ← Uses primary competitor
7. Eli Lilly vs Novo Nordisk revenue comparison
```

**Coverage:**
- ✅ Uses primary competitor (Novo Nordisk)
- ✅ No self-comparison
- ✅ Financial data included

## Testing

### Unit Tests

**File:** `tests/test_requirement_driven_planner.py`

- ✅ Requirement extraction (products, metrics, years, aspects)
- ✅ Product-specific query generation
- ✅ Financial mandatory queries
- ✅ No self-comparison validation
- ✅ Primary competitor usage
- ✅ Company name in all queries

**Run:**
```bash
pytest tests/test_requirement_driven_planner.py -v
```

### Integration Tests

**File:** `tests/test_query_generator_integration.py`

- ✅ End-to-end query generation
- ✅ Real user queries
- ✅ No instruction prefix pollution
- ✅ No self-comparisons

**Run (requires OPENAI_API_KEY):**
```bash
pytest tests/test_query_generator_integration.py -v -s
```

## Failure Conditions

The system is considered **BROKEN** if:

1. ❌ Any "X vs X" query is generated
2. ❌ A named product/drug is missing from queries
3. ❌ Revenue or margin data is reported as "not available"
4. ❌ Queries ignore requested years or calculations
5. ❌ Queries do not materially change based on user input

## Success Metrics

The system is **WORKING CORRECTLY** if:

1. ✅ Zero self-comparisons generated
2. ✅ All product names appear in queries
3. ✅ Revenue queries for each year mentioned
4. ✅ Margin queries for equity research
5. ✅ Queries target user requirements
6. ✅ Company name in all queries
7. ✅ No instruction prefix pollution

## Migration Notes

### Before (Template-Based)

```python
# Old system generated generic queries
queries = [
    f"{company} {sector} overview financial performance 2025-2026",
    f"{company} revenue growth 2023-2025",
    f"{company} operating margin profitability"
]
```

**Problems:**
- ❌ Ignored user requirements
- ❌ Generic templates
- ❌ No product-specific queries
- ❌ Self-comparisons possible

### After (Requirement-Driven)

```python
# New system extracts requirements and generates targeted queries
req = extractor.extract(user_query, companies)
queries = planner.plan_queries(user_query, companies, sector)
```

**Benefits:**
- ✅ Targets user requirements
- ✅ Product-specific queries
- ✅ Year-specific financial data
- ✅ No self-comparisons (validated)
- ✅ Primary competitor mapping

## Files Modified

1. **`research/requirement_driven_planner.py`** (NEW)
   - Requirement extraction
   - Requirement-driven query planning
   - Primary competitor mapping
   - Query validation

2. **`research/query_generator.py`** (MODIFIED)
   - Uses requirement-driven planner
   - Validates all queries
   - Rejects invalid queries

3. **`research/query_intent_parser.py`** (NEW)
   - Strips instruction prefixes
   - Extracts companies, requirements, constraints

4. **`research/orchestrator.py`** (MODIFIED)
   - Parses intent at start
   - Uses cleaned query for planning

5. **`utils/company_tickers.py`** (MODIFIED)
   - Added pharma companies (Pfizer, Merck, Eli Lilly, etc.)

## Summary

The query generation system now:

1. **Extracts requirements** from user queries
2. **Generates targeted queries** for each requirement
3. **Validates queries** to prevent self-comparisons
4. **Ensures financial data** for equity research
5. **Uses primary competitors** for single-company comparisons

**Result:** Precise, requirement-driven queries that deliver the exact data requested by users.
