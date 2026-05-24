import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime, timedelta
from tools.base_tool import BaseTool
from utils.logger import log

class WebScraperTool(BaseTool):
    """Enhanced web scraper using Jina AI Reader with BeautifulSoup fallback"""
    
    def __init__(self):
        super().__init__(
            name="web_scraper",
            description="Scrape and extract content from web pages using Jina AI (handles JS) with BeautifulSoup fallback."
        )
        self.timeout = 30
        self.max_content_length = 50000  # Max characters to extract
        
        # Jina AI configuration
        self.jina_api_key = os.getenv("JINA_AI_API_KEY")  # Optional: get from .env
        self.jina_base_url = "https://r.jina.ai/"
        
        # Rate limiting
        self.last_request_time = {}  # {domain: datetime}
        self.min_delay_seconds = 3  # Minimum delay between requests to same domain
        self.blocked_domains = {}  # {domain: blocked_until_datetime}
        
        # Cache for repeated requests
        self.cache = {}  # {url: (result, timestamp)}
        self.cache_duration = timedelta(minutes=30)
        
        log.info(f"Initialized WebScraperTool with Jina AI {'(authenticated)' if self.jina_api_key else '(anonymous)'}")
    
    async def execute(
        self,
        url: str,
        extract_text: bool = True,
        extract_links: bool = False,
        max_length: Optional[int] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute web scraping with Jina AI (primary) and BeautifulSoup (fallback)
        
        Args:
            url: URL to scrape
            extract_text: Whether to extract text content (default: True)
            extract_links: Whether to extract links (default: False)
            max_length: Maximum content length in characters (default: 50000)
            use_cache: Whether to use cached results (default: True)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with scraped content
        """
        try:
            # Validate input
            is_valid, error = self.validate_input(url=url)
            if not is_valid:
                return {"error": error, "url": url, "content": ""}
            
            max_length = max_length or self.max_content_length
            
            # Check cache first
            if use_cache and url in self.cache:
                cached_result, timestamp = self.cache[url]
                if datetime.now() - timestamp < self.cache_duration:
                    log.info(f"Using cached content for: {url[:60]}")
                    return cached_result
            
            log.info(f"Scraping URL: {url[:80]}...")
            
            # Apply rate limiting
            await self._rate_limit_check(url)
            
            # Try Jina AI first (handles JavaScript, bypasses anti-bot)
            result = await self._jina_ai_scrape(url, max_length)
            
            # If Jina AI fails or returns error, fallback to BeautifulSoup
            if "error" in result:
                log.warning(f"Jina AI failed, using BeautifulSoup fallback: {result.get('error', '')[:100]}")
                result = await self._beautifulsoup_scrape(url, extract_text, extract_links, max_length)
            
            # Cache successful results
            if "error" not in result and use_cache:
                self.cache[url] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            log.error(f"Web scraping failed: {e}")
            return {
                "error": str(e),
                "url": url,
                "content": "",
            }
    
    async def _rate_limit_check(self, url: str):
        """Enforce rate limiting per domain"""
        domain = urlparse(url).netloc
        
        # Check if domain is temporarily blocked
        if domain in self.blocked_domains:
            blocked_until = self.blocked_domains[domain]
            if datetime.now() < blocked_until:
                wait_seconds = (blocked_until - datetime.now()).total_seconds()
                log.warning(f"Domain {domain} is blocked for {wait_seconds:.0f} more seconds")
                raise ValueError(f"Domain temporarily blocked: {domain} (retry after {wait_seconds:.0f}s)")
            else:
                # Unblock if time has passed
                del self.blocked_domains[domain]
        
        # Enforce minimum delay between requests to same domain
        if domain in self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time[domain]).total_seconds()
            if elapsed < self.min_delay_seconds:
                wait_time = self.min_delay_seconds - elapsed
                log.info(f"Rate limiting: waiting {wait_time:.1f}s for {domain}")
                await asyncio.sleep(wait_time)
        
        # Update last request time
        self.last_request_time[domain] = datetime.now()
    
    async def _jina_ai_scrape(self, url: str, max_length: int) -> Dict[str, Any]:
        """
        Scrape using Jina AI Reader API
        Handles JavaScript rendering and bypasses many anti-bot measures
        """
        try:
            # Construct Jina AI URL
            jina_url = f"{self.jina_base_url}{url}"
            
            # Prepare headers
            headers = {
                "User-Agent": "FinScope-AI/1.0",
                "X-Return-Format": "markdown",  # Get clean markdown
                "X-Timeout": "20000",  # 20 second timeout
            }
            
            # Add API key if available (higher rate limits)
            if self.jina_api_key:
                headers["Authorization"] = f"Bearer {self.jina_api_key}"
            
            log.info(f"Using Jina AI to scrape: {url[:60]}...")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(jina_url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Truncate if needed
                        if len(content) > max_length:
                            content = content[:max_length] + "..."
                        
                        # Extract title from markdown (first # heading)
                        title = self._extract_title_from_markdown(content)
                        
                        return {
                            "url": url,
                            "data": {
                                "title": title,
                                "content": content,
                                "format": "markdown",
                                "source": "jina_ai"
                            },
                            "source": "web_scraper",
                        }
                    
                    elif response.status == 429 or response.status == 451:
                        # Rate limit or security block
                        error_text = await response.text()
                        log.warning(f"Jina AI rate limit/block: {error_text[:200]}")
                        
                        # Block domain temporarily (5 minutes)
                        domain = urlparse(url).netloc
                        self.blocked_domains[domain] = datetime.now() + timedelta(minutes=5)
                        
                        return {
                            "error": f"Rate limited (status {response.status})",
                            "url": url
                        }
                    
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"HTTP {response.status}: {error_text[:200]}",
                            "url": url
                        }
        
        except asyncio.TimeoutError:
            log.error(f"Jina AI timeout for: {url}")
            return {"error": "Timeout", "url": url}
        
        except Exception as e:
            log.error(f"Jina AI scraping failed: {e}")
            return {"error": str(e), "url": url}
    
    async def _beautifulsoup_scrape(
        self,
        url: str,
        extract_text: bool = True,
        extract_links: bool = False,
        max_length: int = None
    ) -> Dict[str, Any]:
        """
        Fallback scraper using BeautifulSoup (for simple static sites)
        """
        try:
            log.info(f"Using BeautifulSoup fallback for: {url[:60]}...")
            max_length = max_length or self.max_content_length
            
            # Fetch page content
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return {
                            "error": f"HTTP {response.status}",
                            "url": url,
                            "content": "",
                        }
                    
                    html_content = await response.text()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "lxml")
            
            result = {
                "url": url,
                "title": "",
                "content": "",
                "links": [],
            }
            
            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text().strip()
            
            # Extract main content
            if extract_text:
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Try to find main content areas
                main_content = None
                for selector in ["main", "article", "[role='main']", ".content", "#content"]:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                if main_content:
                    text = main_content.get_text(separator=" ", strip=True)
                else:
                    # Fallback to body
                    body = soup.find("body")
                    text = body.get_text(separator=" ", strip=True) if body else ""
                
                # Clean and truncate text
                text = " ".join(text.split())
                if len(text) > max_length:
                    text = text[:max_length].rsplit(" ", 1)[0] + "..."
                
                result["content"] = text
            
            # Extract links if requested
            if extract_links:
                links = []
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text().strip()
                    if href and text:
                        # Resolve relative URLs
                        parsed_url = urlparse(url)
                        if href.startswith("/"):
                            href = f"{parsed_url.scheme}://{parsed_url.netloc}{href}"
                        elif not href.startswith("http"):
                            href = f"{parsed_url.scheme}://{parsed_url.netloc}/{href}"
                        
                        links.append({"url": href, "text": text})
                
                result["links"] = links[:50]  # Limit to 50 links
            
            return {
                "url": url,
                "data": result,
                "source": "web_scraper",
            }
            
        except aiohttp.ClientError as e:
            log.error(f"BeautifulSoup scraping failed (network error): {e}")
            return {
                "error": f"Network error: {str(e)}",
                "url": url,
                "content": "",
            }
        except Exception as e:
            log.error(f"BeautifulSoup scraping failed: {e}")
            return {
                "error": str(e),
                "url": url,
                "content": "",
            }
    
    def _extract_title_from_markdown(self, markdown_content: str) -> str:
        """Extract title from markdown content (first # heading)"""
        lines = markdown_content.split("\n")
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"
    
    def validate_input(self, url: str, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate scraping input"""
        if not url or not url.strip():
            return False, "URL cannot be empty"
        
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format"
        
        if parsed.scheme not in ["http", "https"]:
            return False, "URL must use http or https"
        
        return True, None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to scrape"
                    },
                    "extract_text": {
                        "type": "boolean",
                        "description": "Extract text content",
                        "default": True
                    },
                    "extract_links": {
                        "type": "boolean",
                        "description": "Extract links from page (BeautifulSoup only)",
                        "default": False
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum content length in characters",
                        "default": 50000
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Use cached results if available (30 min cache)",
                        "default": True
                    }
                },
                "required": ["url"]
            }
        }