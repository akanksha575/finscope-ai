from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
from utils.logger import log
import math

class CalculatorTool(BaseTool):
    """Financial calculator for programmatic calculations"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description=(
                "Perform precise financial calculations programmatically (bypasses LLM math errors). "
                "Supports 12 operations: revenue_growth, profit_margin, P/E ratio, P/B ratio, "
                "debt-to-equity, ROE, ROA, current_ratio, gross_margin, operating_margin, CAGR, "
                "and compound_interest. Returns exact computed values with formulas for validation. "
                "Essential for accurate financial analysis and metric calculation."
            )
        )
    
    async def execute(
        self,
        operation: str,
        values: Dict[str, float],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute calculation
        
        Args:
            operation: Calculation operation (e.g., "revenue_growth", "profit_margin", "pe_ratio")
            values: Dictionary of values needed for calculation
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with calculation result
        """
        try:
            # Validate input
            is_valid, error = self.validate_input(operation=operation, values=values)
            if not is_valid:
                return {"error": error, "operation": operation, "result": None}
            
            log.info(f"Calculating: {operation} with values: {values}")
            
            # Perform calculation
            result = self._calculate(operation, values)
            
            return {
                "operation": operation,
                "values": values,
                "result": result,
                "formula": self._get_formula(operation),
            }
            
        except Exception as e:
            log.error(f"Calculation failed: {e}")
            return {
                "error": str(e),
                "operation": operation,
                "result": None,
            }
    
    def _calculate(self, operation: str, values: Dict[str, float]) -> float:
        """Perform the actual calculation"""
        operations = {
            "revenue_growth": lambda v: ((v.get("current_revenue", 0) - v.get("previous_revenue", 0)) / v.get("previous_revenue", 1)) * 100,
            "profit_margin": lambda v: (v.get("net_profit", 0) / v.get("revenue", 1)) * 100,
            "pe_ratio": lambda v: v.get("price", 0) / v.get("earnings_per_share", 1),
            "pb_ratio": lambda v: v.get("price", 0) / v.get("book_value_per_share", 1),
            "debt_to_equity": lambda v: v.get("total_debt", 0) / v.get("total_equity", 1),
            "roe": lambda v: (v.get("net_income", 0) / v.get("shareholders_equity", 1)) * 100,
            "roa": lambda v: (v.get("net_income", 0) / v.get("total_assets", 1)) * 100,
            "current_ratio": lambda v: v.get("current_assets", 0) / v.get("current_liabilities", 1),
            "gross_margin": lambda v: ((v.get("revenue", 0) - v.get("cost_of_goods_sold", 0)) / v.get("revenue", 1)) * 100,
            "operating_margin": lambda v: (v.get("operating_income", 0) / v.get("revenue", 1)) * 100,
            "cagr": lambda v: ((v.get("ending_value", 0) / v.get("beginning_value", 1)) ** (1 / v.get("years", 1))) - 1,
            "compound_interest": lambda v: v.get("principal", 0) * ((1 + v.get("rate", 0) / 100) ** v.get("years", 1)),
        }
        
        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")
        
        result = operations[operation](values)
        
        # Handle division by zero and invalid results
        if math.isnan(result) or math.isinf(result):
            raise ValueError(f"Invalid calculation result for {operation}")
        
        return round(result, 4)
    
    def _get_formula(self, operation: str) -> str:
        """Get formula description for operation"""
        formulas = {
            "revenue_growth": "(Current Revenue - Previous Revenue) / Previous Revenue × 100",
            "profit_margin": "Net Profit / Revenue × 100",
            "pe_ratio": "Price / Earnings Per Share",
            "pb_ratio": "Price / Book Value Per Share",
            "debt_to_equity": "Total Debt / Total Equity",
            "roe": "Net Income / Shareholders' Equity × 100",
            "roa": "Net Income / Total Assets × 100",
            "current_ratio": "Current Assets / Current Liabilities",
            "gross_margin": "(Revenue - COGS) / Revenue × 100",
            "operating_margin": "Operating Income / Revenue × 100",
            "cagr": "((Ending Value / Beginning Value) ^ (1 / Years)) - 1",
            "compound_interest": "Principal × (1 + Rate/100) ^ Years",
        }
        return formulas.get(operation, "N/A")
    
    def validate_input(self, operation: str, values: Dict[str, float], **kwargs) -> tuple[bool, Optional[str]]:
        """Validate calculation input"""
        if not operation:
            return False, "Operation cannot be empty"
        
        valid_operations = [
            "revenue_growth", "profit_margin", "pe_ratio", "pb_ratio",
            "debt_to_equity", "roe", "roa", "current_ratio",
            "gross_margin", "operating_margin", "cagr", "compound_interest"
        ]
        
        if operation not in valid_operations:
            return False, f"Operation must be one of: {', '.join(valid_operations)}"
        
        if not values or not isinstance(values, dict):
            return False, "Values must be a dictionary"
        
        return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "revenue_growth", "profit_margin", "pe_ratio", "pb_ratio",
                            "debt_to_equity", "roe", "roa", "current_ratio",
                            "gross_margin", "operating_margin", "cagr", "compound_interest"
                        ],
                        "description": "Calculation operation to perform"
                    },
                    "values": {
                        "type": "object",
                        "description": "Dictionary of values needed for calculation"
                    }
                },
                "required": ["operation", "values"]
            }
        }