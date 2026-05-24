import yfinance as yf
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from tools.base_tool import BaseTool
from utils.logger import log

class FinancialDataTool(BaseTool):
    """yfinance tool for fetching financial data"""
    
    # Module-level concurrency limit + TTL cache to reduce Yahoo 429s.
    _semaphore = asyncio.Semaphore(1)
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_ts: Dict[str, datetime] = {}
    _cache_ttl = timedelta(minutes=5)
    
    def __init__(self):
        super().__init__(
            name="financial_data",
            description=(
                "Fetch real-time and historical financial data for stocks using Yahoo Finance (yfinance). "
                "Provides: stock prices, market cap, P/E ratio, profit margins, revenue, dividend yield, "
                "52-week highs/lows, trading volume, and company fundamentals. "
                "Supports global markets (US: MSFT, India: INFY.NS, etc.). "
                "Returns programmatic data for accurate financial calculations."
            )
        )
    
    async def execute(
        self,
        symbol: str,
        metrics: Optional[List[str]] = None,
        period: str = "1y",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute financial data fetch
        
        Args:
            symbol: Stock symbol (e.g., "INFY.NS" for Infosys NSE, "MSFT" for Microsoft)
            metrics: List of metrics to fetch (e.g., ["revenue", "profit_margin", "pe_ratio"])
                    If None, fetches all available metrics
            period: Time period - "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with financial data
        """
        try:
            # Validate input
            is_valid, error = self.validate_input(symbol=symbol, period=period)
            if not is_valid:
                return {"error": error, "symbol": symbol, "data": {}}
            
            cache_key = f"{symbol}|{period}|{','.join(metrics or [])}"
            now = datetime.now(timezone.utc)
            ts = self._cache_ts.get(cache_key)
            if ts and (now - ts) < self._cache_ttl:
                return self._cache.get(cache_key, {"symbol": symbol, "data": {}, "source": "yfinance", "cached": True})

            log.info(f"Fetching financial data for: {symbol}")
            
            async with self._semaphore:
                # Fetch ticker data with retry logic for rate limiting
                ticker = yf.Ticker(symbol)

                # Add small delay to avoid rate limiting (still helpful even with semaphore)
                await asyncio.sleep(0.25)

                # Try to fetch info with error handling for rate limiting
                try:
                    info = ticker.info
                except Exception as e:
                    # Check if it's a rate limit error (429)
                    error_str = str(e).lower()
                    if "429" in error_str or "too many requests" in error_str or "rate limit" in error_str:
                        log.warning(f"Rate limited by yfinance API for {symbol}, using minimal data")
                    else:
                        log.warning(f"Failed to fetch ticker info: {e}, using minimal data")
                    info = {}

                # Fetch historical data
                try:
                    hist = ticker.history(period=period)
                except Exception as e:
                    log.warning(f"Failed to fetch historical data: {e}")
                    hist = None
            
            # Build response data
            data = {
                "symbol": symbol,
                "company_name": info.get("longName", info.get("shortName", "")),
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
            }
            
            # Add requested metrics or all common metrics
            if metrics:
                for metric in metrics:
                    data[metric] = self._get_metric(info, metric)
            else:
                # Fetch common financial metrics
                common_metrics = [
                    "current_price", "market_cap", "revenue", "profit_margin",
                    "pe_ratio", "pb_ratio", "dividend_yield", "52_week_high",
                    "52_week_low", "volume", "avg_volume",
                    # Expanded fundamentals for programmatic calculations
                    "net_profit", "earnings_per_share", "book_value_per_share",
                    "total_debt", "total_equity", "shareholders_equity",
                    "total_assets", "current_assets", "current_liabilities",
                    "operating_income", "cost_of_goods_sold",
                ]
                for metric in common_metrics:
                    value = self._get_metric(info, metric)
                    if value is not None:
                        data[metric] = value
            
            # Add historical price data summary
            if hist is not None and not hist.empty:
                data["price_history"] = {
                    "current": float(hist["Close"].iloc[-1]) if len(hist) > 0 else None,
                    "52_week_high": float(hist["High"].max()) if len(hist) > 0 else None,
                    "52_week_low": float(hist["Low"].min()) if len(hist) > 0 else None,
                    "avg_volume": float(hist["Volume"].mean()) if len(hist) > 0 else None,
                    "period": period,
                }
            
            result = {
                "symbol": symbol,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "yfinance",
            }
            self._cache[cache_key] = result
            self._cache_ts[cache_key] = now
            return result
            
        except Exception as e:
            error_msg = str(e)
            log.error(f"Financial data fetch failed for {symbol}: {e}")
            
            # Check if it's a rate limit error
            if "429" in error_msg or "Too Many Requests" in error_msg:
                error_msg = "Rate limit exceeded. Please wait a moment and try again, or use a different symbol."
            
            return {
                "error": error_msg,
                "symbol": symbol,
                "data": {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "yfinance",
                "note": "Yahoo Finance API may have rate limits. Try again after a few seconds."
            }
    
    def _get_metric(self, info: Dict, metric: str) -> Optional[Any]:
        """Get specific metric from yfinance data"""
        metric_map = {
            "current_price": lambda: info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": lambda: info.get("marketCap"),
            "revenue": lambda: info.get("totalRevenue") or info.get("revenue"),
            "profit_margin": lambda: info.get("profitMargins"),
            "pe_ratio": lambda: info.get("trailingPE") or info.get("forwardPE"),
            "pb_ratio": lambda: info.get("priceToBook"),
            "dividend_yield": lambda: info.get("dividendYield"),
            "52_week_high": lambda: info.get("fiftyTwoWeekHigh"),
            "52_week_low": lambda: info.get("fiftyTwoWeekLow"),
            "volume": lambda: info.get("volume"),
            "avg_volume": lambda: info.get("averageVolume"),
            "revenue_growth": lambda: info.get("revenueGrowth"),
            "earnings_growth": lambda: info.get("earningsGrowth"),
            "debt_to_equity": lambda: info.get("debtToEquity"),
            "roe": lambda: info.get("returnOnEquity"),
            "roa": lambda: info.get("returnOnAssets"),
            # Additional fields to enable programmatic calculations in ReportSynthesizer
            "net_profit": lambda: info.get("netIncomeToCommon") or info.get("netIncome") or info.get("netIncomeApplicableToCommonShares"),
            "earnings_per_share": lambda: info.get("trailingEps") or info.get("forwardEps"),
            "book_value_per_share": lambda: info.get("bookValue"),
            "total_debt": lambda: info.get("totalDebt"),
            "total_equity": lambda: info.get("totalStockholderEquity") or info.get("totalEquity"),
            "shareholders_equity": lambda: info.get("totalStockholderEquity") or info.get("totalEquity"),
            "total_assets": lambda: info.get("totalAssets"),
            "current_assets": lambda: info.get("totalCurrentAssets"),
            "current_liabilities": lambda: info.get("totalCurrentLiabilities"),
            "operating_income": lambda: info.get("operatingIncome"),
            "cost_of_goods_sold": lambda: info.get("costOfRevenue"),
        }
        
        if metric in metric_map:
            try:
                return metric_map[metric]()
            except (KeyError, TypeError, AttributeError):
                return None
        
        # Try direct access
        return info.get(metric)
    
    def validate_input(self, symbol: str, period: str = "1y", **kwargs) -> tuple[bool, Optional[str]]:
        """Validate financial data input"""
        if not symbol or not symbol.strip():
            return False, "Symbol cannot be empty"
        
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        if period not in valid_periods:
            return False, f"Period must be one of: {', '.join(valid_periods)}"
        
        return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., 'INFY.NS' for Infosys NSE, 'MSFT' for Microsoft)"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of metrics to fetch (optional, fetches all if not specified)"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                        "description": "Time period for historical data",
                        "default": "1y"
                    }
                },
                "required": ["symbol"]
            }
        }