from datetime import datetime
from typing import Dict, Any, Optional
import markdown
from utils.logger import log

class ReportFormatter:
    """Formats research reports into HTML, Markdown, and PDF content structures"""
    
    def __init__(self):
        log.info("Initialized ReportFormatter")
    
    def format_html(
        self,
        report_data: Dict[str, Any],
        query: str,
        sector: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format report as HTML"""
        report = report_data.get("report", {})
        title = report.get("title", "Research Report")
        executive_summary = report.get("executive_summary", "")
        analysis = report.get("analysis", "")
        key_findings = report.get("key_findings", [])
        recommendations = report.get("recommendations", [])
        # Use all_citations for references section (all citations, not just filtered ones)
        all_citations = report.get("all_citations", report.get("citations", []))
        
        # Convert markdown analysis to HTML
        analysis_html = markdown.markdown(analysis, extensions=['extra', 'nl2br'])
        
        # Format findings and recommendations
        findings_html = "".join([
            f'<li class="finding-item">{finding}</li>'
            for finding in key_findings
        ])
        
        recommendations_html = "".join([
            f'<li class="recommendation-item">{rec}</li>'
            for rec in recommendations
        ])
        
        # Get metadata
        duration = metadata.get("duration_seconds", 0) if metadata else 0
        total_steps = metadata.get("total_steps", 0) if metadata else 0
        sources = metadata.get("sources_used", []) if metadata else []
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .metadata {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
            font-size: 0.9em;
            color: #666;
        }}
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        .section h3 {{
            color: #34495e;
            font-size: 1.4em;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        .executive-summary {{
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid #3498db;
            margin-bottom: 30px;
            font-size: 1.1em;
            line-height: 1.8;
        }}
        .analysis-content {{
            text-align: justify;
            line-height: 1.8;
        }}
        .analysis-content p {{
            margin-bottom: 15px;
        }}
        .analysis-content h3 {{
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        .analysis-content ul, .analysis-content ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        .analysis-content li {{
            margin-bottom: 8px;
        }}
        .findings-list, .recommendations-list {{
            list-style: none;
            padding: 0;
        }}
        .finding-item, .recommendation-item {{
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid #3498db;
            background: #f8f9fa;
        }}
        .recommendation-item {{
            border-left-color: #27ae60;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-sector {{
            background: #3498db;
            color: white;
        }}
        .badge-it {{
            background: #9b59b6;
            color: white;
        }}
        .badge-pharma {{
            background: #e74c3c;
            color: white;
        }}
        .badge-architecture {{
            background: #e67e22;
            color: white;
        }}
        .badge-energy {{
            background: #16a085;
            color: white;
        }}
        .citations-list {{
            list-style: none;
            padding: 0;
        }}
        .citations-list li {{
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid #3498db;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .citations-list li a {{
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }}
        .citations-list li a:hover {{
            text-decoration: underline;
        }}
        .pub-date {{
            color: #666;
            font-size: 0.9em;
        }}
        .citation-type {{
            color: #27ae60;
            font-size: 0.85em;
            font-weight: 500;
            margin-left: 8px;
        }}
        .images-section {{
            margin: 30px 0;
        }}
        .image-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .image-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 10px 0;
        }}
        .image-caption {{
            margin-top: 10px;
            font-style: italic;
            color: #666;
            font-size: 0.9em;
        }}
        .chart-container {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .chart-container iframe {{
            width: 100%;
            height: 400px;
            border: none;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="metadata">
                <div class="metadata-item">
                    <strong>Sector:</strong>
                    <span class="badge badge-sector badge-{sector.lower()}">{sector}</span>
                </div>
                <div class="metadata-item">
                    <strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                </div>
                <div class="metadata-item">
                    <strong>Duration:</strong> {duration:.1f}s
                </div>
                <div class="metadata-item">
                    <strong>Steps:</strong> {total_steps}
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="executive-summary">
                {executive_summary}
            </div>
        </div>
        
        <div class="section">
            <h2>Detailed Analysis</h2>
            <div class="analysis-content">
                {analysis_html}
            </div>
        </div>
        
        <div class="section">
            <h2>Key Findings</h2>
            <ul class="findings-list">
                {findings_html}
            </ul>
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ul class="recommendations-list">
                {recommendations_html}
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by FinScope AI Research Engine</p>
            <p>Query: {query[:100]}{"..." if len(query) > 100 else ""}</p>
            <p>Sources: {", ".join(sources) if sources else "N/A"}</p>
        </div>
    </div>
</body>
</html>"""
        
        # Add images and graphs section if available
        images_and_graphs = report.get("images_and_graphs", [])
        log.info(f"Formatting HTML: Found {len(images_and_graphs)} images/graphs in report")
        
        # Debug: log what we found
        if images_and_graphs:
            for idx, img in enumerate(images_and_graphs[:3]):  # Log first 3
                log.info(f"Image {idx+1}: type={img.get('type')}, url={img.get('url', '')[:100]}, title={img.get('title', '')[:50]}")
        
        if images_and_graphs:
            images_html = "<div class='section images-section'><h2>Charts and Visualizations</h2>"
            images_added = 0
            for img in images_and_graphs:
                img_url = img.get("url", "")
                img_title = img.get("title", "Chart/Graph")
                img_type = img.get("type", "image")
                description = img.get("description", "")
                
                if not img_url:
                    log.warning(f"Skipping image with no URL: {img_title}")
                    continue
                
                if img_type == "chart" and "yahoo.com" in img_url:
                    # Financial chart - use iframe
                    images_html += f"""
                    <div class="chart-container">
                        <h3>{img_title}</h3>
                        <iframe src="{img_url}" title="{img_title}" width="100%" height="400px"></iframe>
                        {f'<p class="image-caption">{description}</p>' if description else ''}
                    </div>
                    """
                    images_added += 1
                    log.info(f"Added Yahoo chart: {img_title}")
                elif img_url and (self._is_valid_url(img_url) or img_url.startswith("data:image")):
                    # Regular image or base64 encoded image
                    images_html += f"""
                    <div class="image-container">
                        <img src="{img_url}" alt="{img_title}" style="max-width: 100%; height: auto;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                        <p style="display:none; color: #999;">Image could not be loaded: <a href="{img_url if img_url.startswith('http') else '#'}" target="_blank">{img_title}</a></p>
                        {f'<p class="image-caption"><strong>{img_title}</strong>{": " + description if description else ""}</p>' if img_title or description else ''}
                    </div>
                    """
                    images_added += 1
                    log.info(f"Added image: {img_title}, URL: {img_url[:100]}")
                else:
                    log.warning(f"Skipping invalid image URL: {img_url[:100]}")
            
            images_html += "</div>"
            log.info(f"Added {images_added} images to HTML report")
            
            # Insert after analysis section
            if images_added > 0:
                html_content = html_content.replace(
                    '</div>\n        </div>\n        \n        <div class="section">\n            <h2>Key Findings</h2>',
                    '</div>\n        </div>\n        ' + images_html + '\n        <div class="section">\n            <h2>Key Findings</h2>'
                )
            else:
                log.warning("No valid images were added to HTML despite images_and_graphs being present")
        else:
            log.warning("No images_and_graphs found in report for HTML formatting")
        
        # Add references section with ALL citations at the end
        if all_citations:
            citations_html = "<div class='section'><h2>References</h2><ul class='citations-list'>"
            for i, citation in enumerate(all_citations, 1):
                citation_title = citation.get("title", "Source")
                url = citation.get("url", "")
                domain = citation.get("domain", "Unknown")
                pub_date = citation.get("published_date", "")
                citation_type = citation.get("type", "web")
                
                if url and self._is_valid_url(url):
                    citations_html += f'<li><a href="{url}" target="_blank">{citation_title}</a> - {domain}'
                else:
                    citations_html += f'<li>{citation_title} - {domain}'
                
                if pub_date:
                    citations_html += f' <span class="pub-date">({pub_date})</span>'
                
                if citation_type:
                    citations_html += f' <span class="citation-type">[{citation_type}]</span>'
                
                citations_html += "</li>"
            citations_html += "</ul></div>"
            
            # Insert before footer
            html_content = html_content.replace(
                '<div class="footer">',
                citations_html + '<div class="footer">'
            )
        
        return html_content
    
    def format_markdown(
        self,
        report_data: Dict[str, Any],
        query: str,
        sector: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format report as Markdown with citations and financial calculations"""
        report = report_data.get("report", {})
        title = report.get("title", "Research Report")
        executive_summary = report.get("executive_summary", "")
        analysis = report.get("analysis", "")
        key_findings = report.get("key_findings", [])
        recommendations = report.get("recommendations", [])
        financial_highlights = report.get("financial_highlights", [])
        # Use all_citations for references section (all citations, not just filtered ones)
        all_citations = report.get("all_citations", report.get("citations", []))
        financial_calculations = report.get("financial_calculations", [])
        
        # Get metadata
        duration = metadata.get("duration_seconds", 0) if metadata else 0
        total_steps = metadata.get("total_steps", 0) if metadata else 0
        sources = metadata.get("sources_used", []) if metadata else []
        
        markdown_content = f"""# {title}

**Sector:** {sector}  
**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}  
**Duration:** {duration:.1f} seconds  
**Research Steps:** {total_steps}  
**Sources Used:** {", ".join(sources) if sources else "N/A"}

---

## Executive Summary

{executive_summary}

---

## Detailed Analysis

{analysis}

---

## Key Findings

"""
        
        for i, finding in enumerate(key_findings, 1):
            markdown_content += f"{i}. {finding}\n"
        
        # Add Financial Highlights section if available
        if financial_highlights:
            markdown_content += "\n---\n\n## Financial Highlights\n\n"
            for i, highlight in enumerate(financial_highlights, 1):
                markdown_content += f"{i}. {highlight}\n"
        
        # Add Financial Calculations section if available
        if financial_calculations:
            markdown_content += "\n---\n\n## Programmatic Financial Calculations\n\n"
            markdown_content += "The following metrics were calculated programmatically to ensure accuracy:\n\n"
            
            # Group by symbol if available
            by_symbol = {}
            general = []
            
            for calc in financial_calculations:
                symbol = calc.get("symbol")
                if symbol:
                    if symbol not in by_symbol:
                        by_symbol[symbol] = []
                    by_symbol[symbol].append(calc)
                else:
                    general.append(calc)
            
            # Format by symbol
            for symbol, calcs in by_symbol.items():
                markdown_content += f"\n### {symbol}\n\n"
                for calc in calcs:
                    metric = calc.get("metric", "")
                    value = calc.get("value", "")
                    formula = calc.get("formula", "")
                    markdown_content += f"- **{metric}**: {value}"
                    if formula:
                        markdown_content += f" (Formula: {formula})"
                    markdown_content += "\n"
            
            # Format general calculations
            for calc in general:
                metric = calc.get("metric", "")
                value = calc.get("value", "")
                formula = calc.get("formula", "")
                markdown_content += f"- **{metric}**: {value}"
                if formula:
                    markdown_content += f" (Formula: {formula})"
                markdown_content += "\n"
        
        markdown_content += "\n---\n\n## Recommendations\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            markdown_content += f"{i}. {rec}\n"
        
        # Add Images and Graphs section if available
        images_and_graphs = report.get("images_and_graphs", [])
        log.info(f"Formatting Markdown: Found {len(images_and_graphs)} images/graphs in report")
        if images_and_graphs:
            markdown_content += "\n---\n\n## Charts and Visualizations\n\n"
            for img in images_and_graphs:
                img_url = img.get("url", "")
                img_title = img.get("title", "Chart/Graph")
                img_type = img.get("type", "image")
                description = img.get("description", "")
                
                if img_type == "chart" and "yahoo.com" in img_url:
                    # Financial chart - provide link and description
                    markdown_content += f"### {img_title}\n\n"
                    if description:
                        markdown_content += f"{description}\n\n"
                    markdown_content += f"[View Chart: {img_title}]({img_url})\n\n"
                elif img_url and (self._is_valid_url(img_url) or img_url.startswith("data:image")):
                    # Regular image or base64 encoded image
                    markdown_content += f"### {img_title}\n\n"
                    if description:
                        markdown_content += f"{description}\n\n"
                    if img_url.startswith("data:image"):
                        # For base64 images, use HTML img tag in markdown (some renderers support it)
                        markdown_content += f'<img src="{img_url}" alt="{img_title}" />\n\n'
                    else:
                        markdown_content += f"![{img_title}]({img_url})\n\n"
        
        # Add References section with ALL citations at the end
        if all_citations:
            markdown_content += "\n---\n\n## References\n\n"
            markdown_content += f"All sources used in this research ({len(all_citations)} total):\n\n"
            
            for i, citation in enumerate(all_citations, 1):
                citation_title = citation.get("title", "Source")
                url = citation.get("url", "")
                domain = citation.get("domain", "Unknown")
                pub_date = citation.get("published_date", "")
                citation_type = citation.get("type", "web")
                
                if url and self._is_valid_url(url):
                    markdown_content += f"{i}. **{citation_title}** - [{domain}]({url})"
                else:
                    markdown_content += f"{i}. **{citation_title}** - {domain}"
                
                if pub_date:
                    markdown_content += f" (Published: {pub_date})"
                
                if citation_type:
                    markdown_content += f" [{citation_type}]"
                
                markdown_content += "\n"
        
        markdown_content += f"\n---\n\n*Generated by FinScope AI Research Engine*\n*Query: {query}*\n"
        
        return markdown_content
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        return url.startswith(("http://", "https://"))
    
    def format_pdf_content(
        self,
        report_data: Dict[str, Any],
        query: str,
        sector: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare content for PDF generation (returns structured data)"""
        report = report_data.get("report", {})
        
        return {
            "title": report.get("title", "Research Report"),
            "executive_summary": report.get("executive_summary", ""),
            "analysis": report.get("analysis", ""),
            "key_findings": report.get("key_findings", []),
            "recommendations": report.get("recommendations", []),
            "query": query,
            "sector": sector,
            "metadata": metadata or {},
            "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p")
        }