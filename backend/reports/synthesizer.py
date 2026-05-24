import json
import re
import os
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin
from openai import AsyncOpenAI
from tools.calculator import CalculatorTool
from tools.web_scraper import WebScraperTool
from bs4 import BeautifulSoup
import httpx
from utils.logger import log

class ReportSynthesizer:
    """Enhanced report synthesizer with financial calculations and citation management"""
    
    def __init__(self):
        # Use OpenAI client directly instead of BaseAgent to avoid abstract class issue
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
        self.temperature = 0.3
        self.calculator = CalculatorTool()
        self.web_scraper = WebScraperTool()
        log.info("Initialized ReportSynthesizer with web scraper for image extraction")
    
    async def synthesize_report(
        self,
        original_query: str,
        sector: str,
        findings: List[Dict[str, Any]],
        accumulated_knowledge: str,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize comprehensive research report with:
        - GPT-4o generation
        - Financial calculations
        - Citation management
        - Structured markdown
        """
        # Extract financial data for calculations (with AI enhancement if needed)
        financial_metrics = await self._extract_financial_data_with_ai(findings, accumulated_knowledge)
        
        # Perform programmatic financial calculations
        calculated_metrics = await self._calculate_financial_metrics(financial_metrics)
        
        # Extract and format citations with URLs
        formatted_citations = self._format_citations(citations or [], findings)
        
        # Build enhanced prompt with financial calculations
        prompt = self._build_synthesis_prompt(
            original_query=original_query,
            sector=sector,
            findings=findings,
            accumulated_knowledge=accumulated_knowledge,
            calculated_metrics=calculated_metrics,
            citations=formatted_citations
        )
        
        system_prompt = (
            "You are a senior financial analyst at Goldman Sachs with 15+ years of experience. "
            "Your reports are known for precision, depth, and actionable insights. "
            "You always use exact data from calculations, never estimate, and structure "
            "information in a clear, digestible format. Your analysis drives multi-million dollar decisions.\n\n"
            "CRITICAL REQUIREMENTS FOR DEEP RESEARCH:\n"
            "- Generate 7-10 KEY FINDINGS (not just 1-2). If numeric data is missing, say 'Data not available' (do NOT invent numbers)\n"
            "- Write comprehensive analysis (1500-2500 words minimum) with deep insights\n"
            "- Include SCENARIO ANALYSIS section (best case, base case, worst case scenarios)\n"
            "- Provide detailed LONG-TERM OUTLOOK (3-5 year projections and strategic implications)\n"
            "- Reference citations explicitly in the analysis text (mention sources by domain/name)\n"
            "- Ensure all sections are thoroughly developed with supporting data; never fabricate facts or metrics"
        )
        
        try:
            response = await self._call_llm(prompt=prompt, system_prompt=system_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                report = json.loads(json_match.group())
            else:
                report = json.loads(response)
            
            # Filter citations to only include those referenced in the analysis
            analysis_text = report.get("analysis", "")
            relevant_citations = self._filter_relevant_citations(formatted_citations, analysis_text)
            
            # Extract images and graphs from findings (using OpenAI to identify charts)
            images_and_graphs = await self._extract_images_and_graphs(findings)
            
            # Enhance report with filtered citations, calculations, and images
            # Store all citations separately for Sources panel display
            report["citations"] = relevant_citations  # Filtered citations for report
            report["all_citations"] = formatted_citations  # All citations for Sources panel
            report["financial_calculations"] = calculated_metrics
            report["images_and_graphs"] = images_and_graphs
            report["sections"] = self._ensure_required_sections(report)
            # Include financial data for graph generation
            report["financial_data"] = financial_metrics
            
            return report
            
        except Exception as e:
            log.error(f"Report synthesis failed: {e}")
            return await self._create_fallback_report(
                original_query=original_query,
                accumulated_knowledge=accumulated_knowledge,
                citations=formatted_citations,
                calculated_metrics=calculated_metrics,
                findings=findings
            )
    
    def _extract_financial_data(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract financial data from findings for calculations"""
        financial_data = {}
        
        for finding in findings:
            data = finding.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # Extract from financial_data tool results
            if "data" in data and isinstance(data["data"], dict):
                fin_data = data["data"]
                symbol = fin_data.get("symbol", "")
                
                if symbol and symbol not in financial_data:
                    financial_data[symbol] = {}
                
                # Extract key metrics
                metrics = [
                    "revenue", "current_price", "market_cap", "net_profit",
                    "earnings_per_share", "book_value_per_share", "total_debt",
                    "total_equity", "shareholders_equity", "total_assets",
                    "current_assets", "current_liabilities", "operating_income",
                    "cost_of_goods_sold", "previous_revenue"
                ]
                
                for metric in metrics:
                    if metric in fin_data and fin_data[metric] is not None:
                        if symbol:
                            financial_data[symbol][metric] = fin_data[metric]
                        else:
                            financial_data[metric] = fin_data[metric]
        
        return financial_data
    
    async def _extract_financial_data_with_ai(
        self,
        findings: List[Dict[str, Any]],
        accumulated_knowledge: str
    ) -> Dict[str, Any]:
        """
        Use OpenAI to extract and structure financial data from findings
        when explicit financial data is missing or incomplete
        """
        try:
            # First, try standard extraction
            financial_data = self._extract_financial_data(findings)
            
            # If we have good financial data, return it
            if financial_data and len(financial_data) > 0:
                # Check if we have actual numeric values
                has_values = False
                for key, value in financial_data.items():
                    if isinstance(value, dict):
                        if any(isinstance(v, (int, float)) for v in value.values() if v is not None):
                            has_values = True
                            break
                    elif isinstance(value, (int, float)):
                        has_values = True
                        break
                
                if has_values:
                    return financial_data
            
            # Use OpenAI to extract financial metrics from findings and knowledge
            log.info("Using OpenAI to extract financial data from findings")
            
            # Prepare context from findings
            findings_text = []
            for finding in findings[:10]:  # Limit to recent findings
                insights = finding.get("key_insights", [])
                query = finding.get("query", "")
                if insights:
                    findings_text.append(f"Query: {query}\nInsights: {'; '.join(str(i)[:200] for i in insights[:3])}")
            
            context = "\n\n".join(findings_text[:5])  # Last 5 findings
            if accumulated_knowledge:
                context += f"\n\nAccumulated Knowledge:\n{accumulated_knowledge[:2000]}"
            
            prompt = f"""Extract financial metrics and numerical data from the following research findings.

Findings Context:
{context[:3000]}

Extract any financial metrics, revenue numbers, market cap, profit margins, growth rates, or other numerical financial data mentioned in the findings.

Return a JSON object with this structure:
{{
  "symbol1": {{
    "revenue": <number in millions/billions>,
    "market_cap": <number in millions/billions>,
    "net_profit": <number in millions/billions>,
    "profit_margin": <percentage as decimal, e.g., 0.15 for 15%>,
    "pe_ratio": <number>,
    "pb_ratio": <number>
  }},
  "symbol2": {{ ... }}
}}

If no specific symbols are mentioned, use a generic key like "General" or "Company".

ONLY return valid JSON. If no financial data can be extracted, return {{}}."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial data extractor. Always return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    ai_extracted = json.loads(json_match.group())
                    log.info(f"OpenAI extracted financial data with {len(ai_extracted)} symbols/keys")
                    
                    # Merge with existing financial data
                    if ai_extracted:
                        for key, value in ai_extracted.items():
                            if key not in financial_data:
                                financial_data[key] = {}
                            if isinstance(value, dict):
                                financial_data[key].update(value)
                    
                    return financial_data
            except json.JSONDecodeError as e:
                log.warning(f"Failed to parse OpenAI financial data extraction: {e}")
                log.debug(f"Response was: {response_text[:500]}")
        
        except Exception as e:
            log.error(f"Error in AI financial data extraction: {e}", exc_info=True)
        
        # Fallback to standard extraction
        return financial_data
    
    async def _calculate_financial_metrics(
        self,
        financial_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform programmatic financial calculations"""
        calculations = []
        
        for symbol, metrics in financial_data.items():
            if not isinstance(metrics, dict):
                continue
            
            symbol_calcs = []
            
            # Revenue growth
            if "revenue" in metrics and "previous_revenue" in metrics:
                try:
                    result = await self.calculator.execute(
                        operation="revenue_growth",
                        values={
                            "current_revenue": float(metrics.get("revenue", 0)),
                            "previous_revenue": float(metrics.get("previous_revenue", 0))
                        }
                    )
                    if "result" in result and result["result"] is not None:
                        symbol_calcs.append({
                            "metric": "Revenue Growth",
                            "value": f"{result['result']:.2f}%",
                            "formula": result.get("formula", ""),
                            "symbol": symbol
                        })
                except Exception as e:
                    log.warning(f"Revenue growth calculation failed: {e}")
            
            # Profit margin
            if "net_profit" in metrics and "revenue" in metrics:
                try:
                    result = await self.calculator.execute(
                        operation="profit_margin",
                        values={
                            "net_profit": float(metrics.get("net_profit", 0)),
                            "revenue": float(metrics.get("revenue", 1))
                        }
                    )
                    if "result" in result and result["result"] is not None:
                        symbol_calcs.append({
                            "metric": "Profit Margin",
                            "value": f"{result['result']:.2f}%",
                            "formula": result.get("formula", ""),
                            "symbol": symbol
                        })
                except Exception as e:
                    log.warning(f"Profit margin calculation failed: {e}")
            
            # P/E Ratio
            if "current_price" in metrics and "earnings_per_share" in metrics:
                try:
                    result = await self.calculator.execute(
                        operation="pe_ratio",
                        values={
                            "price": float(metrics.get("current_price", 0)),
                            "earnings_per_share": float(metrics.get("earnings_per_share", 1))
                        }
                    )
                    if "result" in result and result["result"] is not None:
                        symbol_calcs.append({
                            "metric": "P/E Ratio",
                            "value": f"{result['result']:.2f}",
                            "formula": result.get("formula", ""),
                            "symbol": symbol
                        })
                except Exception as e:
                    log.warning(f"P/E ratio calculation failed: {e}")
            
            # ROE
            if "net_profit" in metrics and "shareholders_equity" in metrics:
                try:
                    result = await self.calculator.execute(
                        operation="roe",
                        values={
                            "net_income": float(metrics.get("net_profit", 0)),
                            "shareholders_equity": float(metrics.get("shareholders_equity", 1))
                        }
                    )
                    if "result" in result and result["result"] is not None:
                        symbol_calcs.append({
                            "metric": "Return on Equity (ROE)",
                            "value": f"{result['result']:.2f}%",
                            "formula": result.get("formula", ""),
                            "symbol": symbol
                        })
                except Exception as e:
                    log.warning(f"ROE calculation failed: {e}")
            
            # Debt-to-Equity
            if "total_debt" in metrics and "total_equity" in metrics:
                try:
                    result = await self.calculator.execute(
                        operation="debt_to_equity",
                        values={
                            "total_debt": float(metrics.get("total_debt", 0)),
                            "total_equity": float(metrics.get("total_equity", 1))
                        }
                    )
                    if "result" in result and result["result"] is not None:
                        symbol_calcs.append({
                            "metric": "Debt-to-Equity Ratio",
                            "value": f"{result['result']:.2f}",
                            "formula": result.get("formula", ""),
                            "symbol": symbol
                        })
                except Exception as e:
                    log.warning(f"Debt-to-equity calculation failed: {e}")
            
            calculations.extend(symbol_calcs)
        
        return calculations
    
    def _format_citations(
        self,
        citations: List[Dict[str, Any]],
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract and format citations with URLs from all sources"""
        formatted = []
        seen_urls = set()
        
        # Process explicit citations
        for citation in citations:
            if isinstance(citation, dict):
                url = citation.get("url") or citation.get("source_url")
                if url and url not in seen_urls and self._is_valid_url(url):
                    formatted.append({
                        "title": citation.get("title", "Source"),
                        "url": url,
                        "type": citation.get("type", "web"),
                        "domain": self._extract_domain(url),
                        "published_date": citation.get("published_date")
                    })
                    seen_urls.add(url)
        
        # Extract citations from findings
        for finding in findings:
            data = finding.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # Extract from web search results
            if "results" in data and isinstance(data["results"], list):
                for result in data["results"]:
                    if isinstance(result, dict):
                        url = result.get("url", "")
                        if url and url not in seen_urls and self._is_valid_url(url):
                            formatted.append({
                                "title": result.get("title", "Web Source"),
                                "url": url,
                                "type": "web",
                                "domain": self._extract_domain(url),
                                "published_date": result.get("published_date")
                            })
                            seen_urls.add(url)
            
            # Extract from financial data (yfinance sources)
            if "data" in data and isinstance(data["data"], dict):
                fin_data = data["data"]
                symbol = fin_data.get("symbol", "")
                if symbol:
                    yfinance_url = f"https://finance.yahoo.com/quote/{symbol}"
                    if yfinance_url not in seen_urls:
                        formatted.append({
                            "title": f"Financial Data: {symbol}",
                            "url": yfinance_url,
                            "type": "financial",
                            "domain": "finance.yahoo.com",
                            "symbol": symbol
                        })
                        seen_urls.add(yfinance_url)
        
        return formatted
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        return url.startswith(("http://", "https://"))
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
                return domain.replace("www.", "").replace("m.", "")
            return "Unknown"
        except (IndexError, AttributeError):
            return "Unknown"
    
    def _filter_relevant_citations(
        self,
        citations: List[Dict[str, Any]],
        analysis_text: str
    ) -> List[Dict[str, Any]]:
        """
        Filter citations to only include those that are actually referenced in the analysis.
        Checks if domain, title, or URL appears in the analysis text.
        """
        if not analysis_text or not citations:
            return citations
        
        analysis_lower = analysis_text.lower()
        relevant = []
        
        for citation in citations:
            # Check if citation is referenced in analysis
            domain = citation.get("domain", "").lower()
            title = citation.get("title", "").lower()
            url = citation.get("url", "").lower()
            
            # Check if domain, title keywords, or URL appears in analysis
            is_referenced = False
            
            # Check domain (e.g., "yahoo.com", "bloomberg.com")
            if domain and domain in analysis_lower:
                is_referenced = True
            
            # Check title keywords (extract key words from title)
            if title:
                title_words = [w for w in title.split() if len(w) > 3]  # Words longer than 3 chars
                if any(word in analysis_lower for word in title_words[:3]):  # Check first 3 significant words
                    is_referenced = True
            
            # Check if URL is mentioned (common patterns)
            if url:
                # Extract key parts of URL
                url_parts = url.replace("https://", "").replace("http://", "").split("/")
                if url_parts and url_parts[0] in analysis_lower:
                    is_referenced = True
            
            # Always include financial data citations (they're usually relevant)
            if citation.get("type") == "financial":
                is_referenced = True
            
            if is_referenced:
                relevant.append(citation)
        
        # If no citations match, return top 5 most important ones
        if not relevant and citations:
            # Prioritize financial data and unique domains
            financial = [c for c in citations if c.get("type") == "financial"]
            web = [c for c in citations if c.get("type") == "web"]
            relevant = financial[:2] + web[:3]
        
        return relevant
    
    async def _extract_images_and_graphs(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract images and graphs from findings by scraping web pages.
        Uses web scraper to fetch HTML and extract image URLs, then uses OpenAI to identify charts/graphs.
        """
        images = []
        seen_urls = set()
        potential_graph_urls = []  # URLs that might be graphs
        urls_to_scrape = []  # Web page URLs to scrape for images
        
        # First pass: collect URLs from web search results
        for finding in findings:
            data = finding.get("data", {})
            if not isinstance(data, dict):
                continue
            
            # Extract from web search results
            if "results" in data and isinstance(data["results"], list):
                for result in data["results"]:
                    if not isinstance(result, dict):
                        continue
                    
                    url = result.get("url", "")
                    title = result.get("title", "")
                    content = result.get("content", "")
                    description = result.get("description", "")
                    
                    if url and self._is_valid_url(url) and url not in seen_urls:
                        urls_to_scrape.append({
                            "url": url,
                            "title": title,
                            "description": description
                        })
                        seen_urls.add(url)
                    
                    # Also check content for direct image URLs (some may be embedded)
                    if content:
                        img_patterns = [
                            r'!\[.*?\]\((https?://[^\s\)]+\.(?:jpg|jpeg|png|gif|svg|webp))\)',
                            r'<img[^>]+src=["\'](https?://[^\s"\']+\.(?:jpg|jpeg|png|gif|svg|webp))["\']',
                            r'(https?://[^\s\)]+\.(?:jpg|jpeg|png|gif|svg|webp))'
                        ]
                        
                        for pattern in img_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                img_url = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else match
                                if img_url not in seen_urls and self._is_valid_url(img_url):
                                    potential_graph_urls.append({
                                        "url": img_url,
                                        "title": title,
                                        "description": description,
                                        "source_url": url
                                    })
                                    seen_urls.add(img_url)
            
            # Extract from financial data (generate chart URLs for financial symbols)
            if "data" in data and isinstance(data["data"], dict):
                fin_data = data["data"]
                symbol = fin_data.get("symbol", "")
                if symbol:
                    # Generate chart URL for financial symbol
                    chart_url = f"https://chart.yahoo.com/t?s={symbol}"
                    if chart_url not in seen_urls:
                        images.append({
                            "url": chart_url,
                            "title": f"Price Chart: {symbol}",
                            "type": "chart",
                            "source": "financial_data",
                            "symbol": symbol,
                            "description": f"Stock price chart for {symbol}"
                        })
                        seen_urls.add(chart_url)
        
        # Second pass: scrape web pages to extract images
        log.info(f"Scraping {len(urls_to_scrape)} web pages to extract images...")
        for page_info in urls_to_scrape[:10]:  # Limit to 10 pages to avoid timeout
            try:
                url = page_info["url"]
                title = page_info.get("title", "")
                
                # Use web scraper to get HTML content
                scrape_result = await self.web_scraper.execute(
                    url=url,
                    extract_text=False,
                    extract_links=False,
                    max_length=50000  # Get enough content to find images
                )
                
                if "error" in scrape_result:
                    log.warning(f"Failed to scrape {url}: {scrape_result.get('error', 'Unknown error')}")
                    continue
                
                # Extract images from scraped HTML
                html_content = scrape_result.get("content", "")
                if html_content:
                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(html_content, "lxml")
                    
                    # Find all img tags
                    for img_tag in soup.find_all("img"):
                        img_src = img_tag.get("src", "")
                        if not img_src:
                            continue
                        
                        # Convert relative URLs to absolute
                        if img_src.startswith("//"):
                            img_src = "https:" + img_src
                        elif img_src.startswith("/"):
                            img_src = urljoin(url, img_src)
                        elif not img_src.startswith("http"):
                            img_src = urljoin(url, img_src)
                        
                        if img_src not in seen_urls and self._is_valid_url(img_src):
                            img_alt = img_tag.get("alt", "")
                            img_title_attr = img_tag.get("title", "")
                            
                            potential_graph_urls.append({
                                "url": img_src,
                                "title": img_title_attr or img_alt or title,
                                "description": f"Image from {url}",
                                "source_url": url
                            })
                            seen_urls.add(img_src)
                    
                    # Also check for Open Graph images and other meta tags
                    og_image = soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        og_img_url = og_image.get("content")
                        if og_img_url not in seen_urls and self._is_valid_url(og_img_url):
                            potential_graph_urls.append({
                                "url": og_img_url,
                                "title": title,
                                "description": f"Open Graph image from {url}",
                                "source_url": url
                            })
                            seen_urls.add(og_img_url)
                
            except Exception as e:
                log.error(f"Error scraping {page_info.get('url', 'unknown')} for images: {e}", exc_info=True)
                continue
        
        # Third pass: Use OpenAI to identify which URLs are actually charts/graphs
        if potential_graph_urls:
            try:
                log.info(f"Using OpenAI to identify charts/graphs from {len(potential_graph_urls)} potential image URLs")
                
                # Prepare context for OpenAI
                url_contexts = []
                for item in potential_graph_urls[:20]:  # Limit to 20 for token efficiency
                    url_contexts.append(f"URL: {item['url']}\nTitle: {item['title']}\nDescription: {item.get('description', '')[:200]}")
                
                prompt = f"""Identify which of these image URLs are financial charts, graphs, or data visualizations (not just regular photos or logos).

Image URLs and Context:
{chr(10).join(f"{i+1}. {ctx}" for i, ctx in enumerate(url_contexts))}

Return a JSON object mapping URL indices (1-based) to whether they are charts/graphs.
Format: {{"1": true, "2": false, "3": true, ...}}

Consider a URL a chart/graph if:
- It's from financial websites (yahoo.com, bloomberg.com, reuters.com, etc.)
- Title/description mentions "chart", "graph", "visualization", "data", "trend", "analysis"
- It's likely showing financial metrics, trends, or comparisons
- It's from a data/analytics source
- URL contains words like "chart", "graph", "visualization"

Return ONLY valid JSON. If unsure, mark as false."""
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a financial data analyzer. Always return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                response_text = response.choices[0].message.content.strip()
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    chart_identifications = json.loads(json_match.group())
                    
                    # Add identified charts to images list
                    for idx, item in enumerate(potential_graph_urls[:20], 1):
                        if str(idx) in chart_identifications and chart_identifications[str(idx)]:
                            images.append({
                                "url": item["url"],
                                "title": item["title"] or "Financial Chart",
                                "type": "chart",
                                "source": "web_search",
                                "description": item.get("description", "Chart extracted from web source")
                            })
                            log.info(f"Identified as chart: {item['url'][:100]}")
                
            except Exception as e:
                log.error(f"Error using OpenAI to identify charts: {e}", exc_info=True)
                # Fallback: add images from financial domains or with chart-related keywords
                for item in potential_graph_urls[:10]:
                    img_url = item["url"].lower()
                    if any(domain in img_url for domain in ["yahoo.com", "bloomberg.com", "reuters.com", "chart", "graph", "visualization"]):
                        images.append({
                            "url": item["url"],
                            "title": item["title"] or "Chart/Graph",
                            "type": "chart",
                            "source": "web_search",
                            "description": item.get("description", "Extracted from web source")
                        })
        
        # Final fallback: if still no images, include first few potential images as charts
        if len(images) == 0 and len(potential_graph_urls) > 0:
            log.warning("No charts identified by OpenAI, including first few potential images as fallback")
            for item in potential_graph_urls[:5]:  # Include first 5 as fallback
                images.append({
                    "url": item["url"],
                    "title": item["title"] or "Chart/Graph",
                    "type": "chart",
                    "source": "web_search",
                    "description": item.get("description", "Image from web source")
                })
                log.info(f"Added fallback image: {item['url'][:100]}")
        
        log.info(f"Extracted {len(images)} charts/graphs from web sources")
        
        # If no images found, try a more aggressive extraction from content
        if len(images) == 0:
            log.warning("No images extracted, trying aggressive extraction from content")
            for finding in findings:
                data = finding.get("data", {})
                if not isinstance(data, dict):
                    continue
                
                # Check web search results more thoroughly
                if "results" in data and isinstance(data["results"], list):
                    for result in data["results"]:
                        content = result.get("content", "")
                        url = result.get("url", "")
                        
                        if content:
                            # More aggressive pattern matching
                            img_patterns = [
                                r'https?://[^\s\)]+\.(?:jpg|jpeg|png|gif|svg|webp)',
                                r'https?://[^\s"\']+chart[^\s"\']*\.(?:jpg|jpeg|png|gif|svg|webp)',
                                r'https?://[^\s"\']+graph[^\s"\']*\.(?:jpg|jpeg|png|gif|svg|webp)',
                                r'https?://[^\s"\']+image[^\s"\']*\.(?:jpg|jpeg|png|gif|svg|webp)',
                            ]
                            
                            for pattern in img_patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    if match not in seen_urls and self._is_valid_url(match):
                                        images.append({
                                            "url": match,
                                            "title": result.get("title", "Chart/Graph"),
                                            "type": "chart",
                                            "source": "web_search",
                                            "description": f"Extracted from {url}"
                                        })
                                        seen_urls.add(match)
                                        log.info(f"Found image via aggressive extraction: {match[:100]}")
        
        log.info(f"Final count: {len(images)} charts/graphs extracted from web sources")
        return images
    
    def _build_synthesis_prompt(
        self,
        original_query: str,
        sector: str,
        findings: List[Dict[str, Any]],
        accumulated_knowledge: str,
        calculated_metrics: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> str:
        """Build enhanced synthesis prompt with financial calculations"""
        
        # Format calculated metrics for better readability
        metrics_text = "None available"
        if calculated_metrics:
            metrics_lines = []
            for calc in calculated_metrics:
                symbol = calc.get('symbol', 'N/A')
                metric = calc.get('metric', 'Unknown')
                value = calc.get('value', 'N/A')
                metrics_lines.append(f"  - {symbol}: {metric} = {value}")
            metrics_text = "\n".join(metrics_lines)
        
        # Format citations for better context
        citations_text = "None available"
        if citations:
            citations_lines = []
            for i, cit in enumerate(citations[:10], 1):  # Limit to top 10
                title = cit.get('title', 'Unknown')
                domain = cit.get('domain', 'Unknown')
                accessed_at = cit.get("accessed_at", "")
                accessed_str = f" (accessed {accessed_at})" if accessed_at else ""
                citations_lines.append(f"  [{i}] {title} - {domain}{accessed_str}")
            citations_text = "\n".join(citations_lines)
        
        # Research steps (methodology) – keep concise but explicit.
        step_lines = []
        for f in findings[:25]:
            q = f.get("query", "")
            n = f.get("step_number", "")
            if q:
                step_lines.append(f"  - Step {n}: {q}")
        steps_text = "\n".join(step_lines) or "  - (no steps captured)"

        prompt = f"""You are an elite financial research analyst at a top-tier investment firm. Your task is to synthesize a comprehensive, data-driven research report that directly answers the client's query with precision and depth.

═══════════════════════════════════════════════════════════════════════════════
CLIENT QUERY: {original_query}
SECTOR: {sector.upper()}
═══════════════════════════════════════════════════════════════════════════════

RESEARCH FINDINGS SUMMARY:
{accumulated_knowledge[:3000]}

PROGRAMMATIC FINANCIAL CALCULATIONS (Use these exact values):
{metrics_text}

AVAILABLE CITATIONS (Top Sources):
{citations_text}

RESEARCH METHODOLOGY (Steps taken):
{steps_text}

RAW DATA EXTRACT (for additional context):
{json.dumps(findings, indent=2, default=str)[:4000]}

═══════════════════════════════════════════════════════════════════════════════
REPORT GENERATION INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════════════

1. ACCURACY FIRST:
   - Use ONLY the programmatic financial calculations provided above for derived metrics (growth, margins, ratios).
   - Do NOT invent, estimate, extrapolate, or assume any numbers, percentages, market caps, stock moves, or approvals.
   - If a specific number is not present in the provided calculations OR explicitly present in the findings, write "Data not available".

2. STRUCTURE YOUR ANALYSIS (1500-2500 words minimum):
   - Start with market context and overview (200-300 words)
   - Present key financial metrics with exact values from calculations (300-400 words)
   - Analyze competitive positioning and trends in depth (300-400 words)
   - Include ### Research Methodology (brief, but explicit):
     * Numbered steps you took (high level)
     * Number of unique sources consulted (must be **8+** if available)
     * Date range / recency emphasis
     * Validation approach for key claims
   - Include ### Limitations & Gaps:
     * Any dimensions you couldn't fully validate
     * Any single-source claims
   - Include SCENARIO ANALYSIS section (200-300 words):
     * Best Case Scenario: Optimistic outcomes and their implications
     * Base Case Scenario: Most likely outcomes based on current trends
     * Worst Case Scenario: Risk factors and potential negative impacts
   - Discuss risks, opportunities, and strategic implications (200-300 words)
   - Provide detailed LONG-TERM OUTLOOK (300-400 words):
     * 3-5 year projections based on current trends
     * Strategic implications for stakeholders
     * Market evolution and competitive dynamics
     * Investment and growth opportunities
   - Support all claims with specific data points and cite sources

3. MARKDOWN FORMATTING REQUIREMENTS:
   - Use ### for main section headers (e.g., ### Market Overview)
   - Use #### for subsections
   - **Bold** all numeric metrics and company names
   - Create tables for comparing multiple data points
   - Use bullet points for lists of factors/risks/opportunities
   - Keep paragraphs focused (3-5 sentences max)

4. DATA INTEGRATION & CITATIONS:
   - Quote exact values from programmatic calculations (e.g., "**P/E Ratio: 24.35**")
   - Reference multiple sources to validate claims
   - Explicitly mention sources in the analysis text (e.g., "According to Yahoo Finance", "Bloomberg reports", "As cited in [Source Name]")
   - Include citation references in parentheses when using specific data points
   - Highlight year-over-year trends when available
   - Note any data limitations or gaps
   - Ensure **8+ unique, relevant sources** are cited when citations are provided; otherwise, explain why sources are limited.

5. BUSINESS INSIGHTS:
   - Explain what the numbers mean for investors/stakeholders
   - Compare to industry benchmarks when relevant
   - Identify cause-and-effect relationships
   - Address both short-term and long-term implications

6. EXECUTIVE SUMMARY: Write a compelling 2-3 sentence summary that captures the most critical finding and actionable insight.

7. KEY FINDINGS: List 7-10 specific discoveries (not vague observations)
   - If you have the data, include it with the source context (e.g., mention the domain/provider)
   - If you do NOT have the data for a finding the client asked for, explicitly write: "Data not available (not found in research findings)"
   - Cover multiple dimensions: financial performance, competitive positioning, market trends, strategic initiatives, risks/opportunities

8. RECOMMENDATIONS: Provide 3-5 actionable, specific recommendations
   ✓ Good: "Monitor debt-to-equity ratio quarterly as it rose to 1.8x"
   ✗ Bad: "Keep an eye on financial health"

OUTPUT FORMAT (Return ONLY this JSON structure, no other text):
{{
    "title": "Concise, descriptive report title (max 80 chars)",
    "executive_summary": "2-3 compelling sentences highlighting the key finding and insight",
    "analysis": "Comprehensive markdown-formatted analysis (1500-2500 words minimum) with clear sections, specific data points, and business implications. Use the structure: Market Overview → Financial Performance → Competitive Analysis → Scenario Analysis (Best/Base/Worst Case) → Risks & Opportunities → Long-Term Outlook (3-5 year projections) → Strategic Implications. Include explicit source citations throughout the text.",
    "key_findings": [
        "Specific finding with data point (financial performance)",
        "Another discovery with metrics (competitive positioning)",
        "Trend or pattern identified with numbers (market dynamics)",
        "Competitive insight with comparison (peer analysis)",
        "Risk or opportunity with quantification (strategic assessment)",
        "Additional finding with supporting data (operational metrics)",
        "Market trend with specific evidence (industry analysis)",
        "Strategic initiative impact with metrics (growth drivers)"
    ],
    "recommendations": [
        "Actionable recommendation with clear rationale",
        "Strategic suggestion with specific focus area",
        "Monitoring guideline with specific metric"
    ],
    "financial_highlights": [
        "Key metric 1 with value and trend",
        "Key metric 2 with value and context",
        "Key metric 3 with value and implication"
    ]
}}

CRITICAL: Ensure all JSON is properly formatted with escaped quotes. Validate before returning."""

        return prompt
    
    def _ensure_required_sections(self, report: Dict[str, Any]) -> Dict[str, bool]:
        """Ensure report has all required sections"""
        required = {
            "title": bool(report.get("title")),
            "executive_summary": bool(report.get("executive_summary")),
            "analysis": bool(report.get("analysis")),
            "key_findings": bool(report.get("key_findings")),
            "recommendations": bool(report.get("recommendations"))
        }
        return required
    
    async def _create_fallback_report(
        self,
        original_query: str,
        accumulated_knowledge: str,
        citations: List[Dict[str, Any]],
        calculated_metrics: List[Dict[str, Any]],
        findings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create fallback report if synthesis fails"""
        # Extract images from findings if available
        images = []
        if findings:
            images = await self._extract_images_and_graphs(findings)
        
        # Filter citations for fallback
        filtered_citations = self._filter_relevant_citations(citations, accumulated_knowledge[:2000])
        
        # Create structured fallback content
        fallback_analysis = f"""### Research Summary

{accumulated_knowledge[:1500]}

### Financial Metrics Calculated

"""
        if calculated_metrics:
            fallback_analysis += "\n".join([
                f"- **{calc.get('metric', 'Unknown')}**: {calc.get('value', 'N/A')} "
                f"({calc.get('symbol', '')})"
                for calc in calculated_metrics[:8]
            ])
        else:
            fallback_analysis += "No financial calculations available for this query.\n"
        
        fallback_analysis += "\n\n### Data Sources\n\n"
        fallback_analysis += f"This report synthesizes information from {len(citations)} sources including "
        fallback_analysis += "financial databases, news articles, and market data providers.\n"
        
        return {
            "title": f"Research Analysis: {original_query[:60]}{'...' if len(original_query) > 60 else ''}",
            "executive_summary": (
                "Research completed with available data sources. "
                "This report provides key insights based on market data, financial metrics, and industry analysis. "
                "Additional synthesis may be required for deeper insights."
            ),
            "analysis": fallback_analysis,
            "key_findings": [
                "Data collection completed from multiple sources",
                f"Analyzed {len(findings or [])} data points across various sources",
                f"Generated {len(calculated_metrics)} programmatic financial calculations"
            ] if findings else [
                "Research phase completed",
                "Financial data extracted and processed",
                "Multiple sources consulted for comprehensive coverage"
            ],
            "recommendations": [
                "Review detailed metrics in the financial calculations section",
                "Cross-reference findings with latest market data",
                "Consider conducting follow-up analysis on specific areas of interest"
            ],
            "financial_highlights": [
                f"{calc.get('metric', 'Metric')}: {calc.get('value', 'N/A')}"
                for calc in calculated_metrics[:5]
            ] if calculated_metrics else [],
            "citations": filtered_citations,
            "all_citations": citations,
            "financial_calculations": calculated_metrics,
            "images_and_graphs": images,
            "sections": {
                "title": True,
                "executive_summary": True,
                "analysis": True,
                "key_findings": True,
                "recommendations": True
            }
        }
    
    async def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Call OpenAI LLM asynchronously
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            LLM response text
        """
        # Standard chat.completions.create for all models
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            log.error(f"LLM call failed: {e}")
            raise