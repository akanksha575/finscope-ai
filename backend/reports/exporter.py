"""Report exporter for PDF, HTML, and Markdown files"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reports.formatter import ReportFormatter
from reports.graph_generator import GraphGenerator
from utils.logger import log

class ReportExporter:
    """Exports reports to various file formats"""
    
    def __init__(self):
        self.formatter = ReportFormatter()
        self.graph_generator = GraphGenerator()
        self.output_dir = Path("outputs/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        log.info("Initialized ReportExporter")
    
    def export_html(
        self,
        report_data: Dict[str, Any],
        query_id: str,
        query: str,
        sector: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export report as HTML file"""
        # Ensure report_data has correct structure
        if "report" not in report_data:
            report_data["report"] = report_data
        
        # Extract graphs from web sources (not generate)
        graphs = self._generate_graphs_for_report(report_data, query_id)
        log.info(f"Extracted {len(graphs)} graphs from web sources for HTML export: {[g.get('type') for g in graphs]}")
        
        # Add graphs to report_data if not already present
        existing_graphs = report_data["report"].get("images_and_graphs", [])
        log.info(f"Existing graphs in report_data: {len(existing_graphs)}")
        
        if graphs:
            # Add extracted graphs to existing ones (use URL directly, not base64)
            for graph in graphs:
                graph_url = graph.get('url', '')
                if graph_url:
                    # Check if this graph is already in existing_graphs
                    if not any(existing.get('url') == graph_url for existing in existing_graphs):
                        graph_entry = {
                            "url": graph_url,  # Use web URL directly
                            "title": graph.get("title", "Chart"),
                            "type": "chart",
                            "description": graph.get("description", ""),
                            "file_path": graph.get("file_path", "")
                        }
                        existing_graphs.append(graph_entry)
                        log.info(f"Added graph from web source: {graph_entry['title']}, URL: {graph_url[:100]}")
                else:
                    log.warning(f"Graph {graph.get('title')} has no URL, skipping")
        
        # Always set images_and_graphs, even if empty
        report_data["report"]["images_and_graphs"] = existing_graphs
        log.info(f"Total graphs in report_data after adding: {len(existing_graphs)}")
        
        if not graphs and len(existing_graphs) == 0:
            log.warning(f"No graphs extracted from web sources for query_id={query_id}")
        
        html_content = self.formatter.format_html(report_data, query, sector, metadata)
        
        filename = f"{query_id}_report.html"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        log.info(f"Exported HTML report: {filepath}")
        return str(filepath)
    
    def export_markdown(
        self,
        report_data: Dict[str, Any],
        query_id: str,
        query: str,
        sector: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export report as Markdown file"""
        # Ensure report_data has correct structure
        if "report" not in report_data:
            report_data["report"] = report_data
        
        # Extract graphs from web sources (not generate)
        graphs = self._generate_graphs_for_report(report_data, query_id)
        log.info(f"Extracted {len(graphs)} graphs from web sources for Markdown export: {[g.get('type') for g in graphs]}")
        
        # Add graphs to report_data if not already present
        existing_graphs = report_data["report"].get("images_and_graphs", [])
        log.info(f"Existing graphs in report_data: {len(existing_graphs)}")
        
        if graphs:
            for graph in graphs:
                graph_url = graph.get('url', '')
                if graph_url:
                    # Check if this graph is already in existing_graphs
                    if not any(existing.get('url') == graph_url for existing in existing_graphs):
                        graph_entry = {
                            "url": graph_url,  # Use web URL directly
                            "title": graph.get("title", "Chart"),
                            "type": "chart",
                            "description": graph.get("description", "")
                        }
                        existing_graphs.append(graph_entry)
                        log.info(f"Added graph from web source: {graph_entry['title']}")
        
        # Always set images_and_graphs, even if empty
        report_data["report"]["images_and_graphs"] = existing_graphs
        log.info(f"Total graphs in report_data after adding: {len(existing_graphs)}")
        
        if not graphs and len(existing_graphs) == 0:
            log.warning(f"No graphs extracted from web sources for query_id={query_id}")
        
        markdown_content = self.formatter.format_markdown(report_data, query, sector, metadata)
        
        filename = f"{query_id}_report.md"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        log.info(f"Exported Markdown report: {filepath}")
        return str(filepath)
    
    def export_pdf(
        self,
        report_data: Dict[str, Any],
        query_id: str,
        query: str,
        sector: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Export report as PDF file"""
        content = self.formatter.format_pdf_content(report_data, query, sector, metadata)
        
        filename = f"{query_id}_report.pdf"
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=15,
            backColor=colors.HexColor('#f8f9fa'),
            borderPadding=10
        )
        
        # Title
        elements.append(Paragraph(content["title"], title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Metadata
        metadata_text = f"""
        <b>Sector:</b> {sector} | 
        <b>Generated:</b> {content["generated_at"]} | 
        <b>Duration:</b> {metadata.get('duration_seconds', 0):.1f}s | 
        <b>Steps:</b> {metadata.get('total_steps', 0)}
        """
        elements.append(Paragraph(metadata_text, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Paragraph(content["executive_summary"], summary_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Extract and add graphs from web sources
        graphs = self._generate_graphs_for_report(report_data, query_id)
        if graphs:
            elements.append(Paragraph("Charts and Visualizations", heading_style))
            for graph in graphs:
                graph_url = graph.get("url", "")
                graph_path = graph.get("file_path", "")
                
                # Try to use file path if available, otherwise note that it's a web URL
                if graph_path and Path(graph_path).exists():
                    try:
                        img = Image(graph_path, width=6*inch, height=4*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 0.1*inch))
                        # Add caption
                        caption = graph.get("title", "Chart")
                        if graph.get("description"):
                            caption += f": {graph.get('description')}"
                        elements.append(Paragraph(f"<i>{caption}</i>", styles['Normal']))
                        elements.append(Spacer(1, 0.2*inch))
                    except Exception as e:
                        log.warning(f"Could not add graph to PDF: {e}")
                elif graph_url:
                    # For web URLs, add a note in PDF (can't embed external images directly)
                    caption = graph.get("title", "Chart")
                    if graph.get("description"):
                        caption += f": {graph.get('description')}"
                    elements.append(Paragraph(f"<b>{caption}</b>", body_style))
                    elements.append(Paragraph(f"<i>Chart available at: {graph_url}</i>", styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))
                    log.info(f"Added web graph reference to PDF: {caption}")
        
        # Detailed Analysis
        elements.append(Paragraph("Detailed Analysis", heading_style))
        
        # Split analysis into paragraphs
        analysis_paragraphs = content["analysis"].split("\n\n")
        for para in analysis_paragraphs:
            if para.strip():
                # Handle markdown headers
                if para.startswith("###"):
                    header_text = para.replace("###", "").strip()
                    elements.append(Paragraph(f"<b>{header_text}</b>", body_style))
                elif para.startswith("**") and para.endswith("**"):
                    # Bold text
                    elements.append(Paragraph(para, body_style))
                else:
                    elements.append(Paragraph(para, body_style))
                elements.append(Spacer(1, 0.1*inch))
        
        elements.append(PageBreak())
        
        # Key Findings
        elements.append(Paragraph("Key Findings", heading_style))
        for i, finding in enumerate(content["key_findings"], 1):
            finding_text = f"<b>{i}.</b> {finding}"
            elements.append(Paragraph(finding_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Recommendations
        elements.append(Paragraph("Recommendations", heading_style))
        for i, rec in enumerate(content["recommendations"], 1):
            rec_text = f"<b>{i}.</b> {rec}"
            elements.append(Paragraph(rec_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_text = f"""
        <i>Generated by FinScope AI Research Engine</i><br/>
        <i>Query: {query[:80]}{"..." if len(query) > 80 else ""}</i>
        """
        elements.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        log.info(f"Exported PDF report: {filepath}")
        return str(filepath)
    
    def _generate_graphs_for_report(
        self,
        report_data: Dict[str, Any],
        query_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract graphs from web sources instead of generating them.
        Uses images_and_graphs from report data which are extracted from web search results.
        
        Args:
            report_data: Full report data dictionary
            query_id: Query ID for file naming
            
        Returns:
            List of graph info dicts (extracted from web sources)
        """
        graphs = []
        
        try:
            report = report_data.get("report", {})
            images_and_graphs = report.get("images_and_graphs", [])
            
            log.info(f"Extracting graphs from web sources for query_id={query_id}: found {len(images_and_graphs)} images/graphs")
            
            # Use graphs/images extracted from web sources
            # Be more inclusive - include all images that might be charts
            for img in images_and_graphs:
                img_type = img.get("type", "image")
                img_url = img.get("url", "")
                img_title = img.get("title", "").lower()
                
                # Include if it's explicitly marked as chart
                if img_type == "chart":
                    graphs.append({
                        "url": img_url,
                        "title": img.get("title", "Chart/Graph"),
                        "type": "chart",
                        "description": img.get("description", "Extracted from web source"),
                        "file_path": "",
                        "base64_data": ""
                    })
                # Include if URL or title suggests it's a chart/graph
                elif img_url and ("chart" in img_url.lower() or "graph" in img_url.lower() or 
                                 "chart" in img_title or "graph" in img_title or
                                 "financial" in img_url.lower() or "yahoo" in img_url.lower() or
                                 "visualization" in img_url.lower() or "data" in img_url.lower()):
                    graphs.append({
                        "url": img_url,
                        "title": img.get("title", "Chart/Graph"),
                        "type": "chart",
                        "description": img.get("description", "Chart from web source"),
                        "file_path": "",
                        "base64_data": ""
                    })
                # If no charts found, include any valid image URLs as potential charts
                elif img_url and len(graphs) == 0 and self._is_valid_url(img_url):
                    log.info(f"Including image as potential chart (no charts found yet): {img_url[:100]}")
                    graphs.append({
                        "url": img_url,
                        "title": img.get("title", "Chart/Graph"),
                        "type": "chart",
                        "description": img.get("description", "Image from web source"),
                        "file_path": "",
                        "base64_data": ""
                    })
            
            # If no graphs found, try to get from metadata
            if not graphs:
                metadata = report_data.get("metadata", {})
                metadata_graphs = metadata.get("images_and_graphs", [])
                for img in metadata_graphs:
                    if img.get("type") == "chart" or "chart" in img.get("url", "").lower():
                        graphs.append({
                            "url": img.get("url", ""),
                            "title": img.get("title", "Chart"),
                            "type": "chart",
                            "description": img.get("description", ""),
                            "file_path": "",
                            "base64_data": ""
                        })
            
            log.info(f"Extracted {len(graphs)} graphs from web sources")
            
            # If still no graphs, log a detailed warning
            if len(graphs) == 0:
                log.warning(f"No graphs extracted for query_id={query_id}. Report data keys: {list(report_data.keys())}")
                if "report" in report_data:
                    report = report_data.get("report", {})
                    log.warning(f"Report keys: {list(report.keys())}")
                    log.warning(f"images_and_graphs in report: {report.get('images_and_graphs', [])}")
        
        except Exception as e:
            log.error(f"Error extracting graphs from web sources: {e}", exc_info=True)
        
        return graphs
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        if not url or not isinstance(url, str):
            return False
        return url.startswith(("http://", "https://", "data:image"))