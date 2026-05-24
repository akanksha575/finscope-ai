"""Graph generator for financial reports"""
import os
import io
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import numpy as np
from utils.logger import log

class GraphGenerator:
    """Generates graphs and charts for financial reports"""
    
    def __init__(self):
        self.output_dir = Path("outputs/reports/graphs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Set style - try seaborn, fallback to default
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            try:
                plt.style.use('seaborn-darkgrid')
            except:
                plt.style.use('default')
        log.info("Initialized GraphGenerator")
    
    def generate_financial_metrics_chart(
        self,
        financial_data: Dict[str, Dict[str, Any]],
        query_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a bar chart comparing financial metrics across multiple symbols
        
        Args:
            financial_data: Dict mapping symbol to financial metrics
            query_id: Query ID for file naming
            
        Returns:
            Dict with graph info (file_path, base64_data, type) or None
        """
        if not financial_data or len(financial_data) == 0:
            return None
        
        try:
            # Prepare data for visualization
            # financial_data can be: {symbol: {metric: value}} or {metric: value}
            symbols = []
            metrics_to_plot = ['revenue', 'market_cap', 'net_profit']
            
            # Check structure - if keys look like stock symbols (uppercase, 1-5 chars), treat as symbols
            # Otherwise, treat as flat metric dict
            first_key = list(financial_data.keys())[0] if financial_data else None
            is_symbol_based = first_key and isinstance(first_key, str) and first_key.isupper() and len(first_key) <= 5
            
            if is_symbol_based:
                symbols = list(financial_data.keys())
            else:
                # Flat structure - check if we have metrics directly
                has_metrics = any(metric in financial_data for metric in metrics_to_plot)
                if not has_metrics:
                    return None
                # Create a single "General" symbol for flat data
                symbols = ["General"]
                financial_data = {"General": financial_data}
            
            # Filter symbols that have at least one metric
            valid_symbols = []
            for symbol in symbols:
                symbol_data = financial_data.get(symbol, {})
                if isinstance(symbol_data, dict):
                    if any(metric in symbol_data and symbol_data[metric] is not None 
                           for metric in metrics_to_plot):
                        valid_symbols.append(symbol)
            
            if not valid_symbols:
                log.warning(f"No valid symbols found in financial_data: {list(financial_data.keys())}")
                return None
            
            # Create figure
            fig, axes = plt.subplots(len(metrics_to_plot), 1, figsize=(10, 6 * len(metrics_to_plot)))
            if len(metrics_to_plot) == 1:
                axes = [axes]
            
            fig.suptitle('Financial Metrics Comparison', fontsize=16, fontweight='bold', y=0.995)
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(valid_symbols)))
            
            for idx, metric in enumerate(metrics_to_plot):
                ax = axes[idx]
                values = []
                labels = []
                
                for symbol in valid_symbols:
                    symbol_data = financial_data.get(symbol, {})
                    if isinstance(symbol_data, dict):
                        value = symbol_data.get(metric)
                    else:
                        value = None
                    
                    if value is not None:
                        try:
                            value = float(value)
                            # Convert to billions for readability
                            if metric in ['revenue', 'market_cap', 'net_profit']:
                                value_b = value / 1e9
                                values.append(value_b)
                                labels.append(f"{symbol}\n({value_b:.2f}B)")
                            else:
                                values.append(value)
                                labels.append(symbol)
                        except (ValueError, TypeError):
                            log.warning(f"Could not convert {metric} value to float for {symbol}: {value}")
                            continue
                
                if values:
                    bars = ax.bar(range(len(values)), values, color=colors[:len(values)])
                    ax.set_xticks(range(len(values)))
                    ax.set_xticklabels([label.split('\n')[0] for label in labels], rotation=45, ha='right')
                    ax.set_ylabel(f'{metric.replace("_", " ").title()} (Billions)', fontweight='bold')
                    ax.set_title(f'{metric.replace("_", " ").title()} Comparison', fontsize=12)
                    ax.grid(axis='y', alpha=0.3)
                    
                    # Add value labels on bars
                    for bar, label in zip(bars, labels):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.2f}B',
                               ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            
            # Save to file
            filename = f"{query_id}_financial_metrics.png"
            filepath = self.output_dir / filename
            fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            # Generate base64 for HTML embedding
            img_buffer = io.BytesIO()
            fig2, axes2 = plt.subplots(len(metrics_to_plot), 1, figsize=(10, 6 * len(metrics_to_plot)))
            if len(metrics_to_plot) == 1:
                axes2 = [axes2]
            fig2.suptitle('Financial Metrics Comparison', fontsize=16, fontweight='bold', y=0.995)
            
            for idx, metric in enumerate(metrics_to_plot):
                ax = axes2[idx]
                values = []
                labels = []
                
                for symbol in valid_symbols:
                    symbol_data = financial_data.get(symbol, {})
                    if isinstance(symbol_data, dict):
                        value = symbol_data.get(metric)
                    else:
                        value = None
                    
                    if value is not None:
                        try:
                            value = float(value)
                            if metric in ['revenue', 'market_cap', 'net_profit']:
                                value_b = value / 1e9
                                values.append(value_b)
                                labels.append(f"{symbol}\n({value_b:.2f}B)")
                            else:
                                values.append(value)
                                labels.append(symbol)
                        except (ValueError, TypeError):
                            continue
                
                if values:
                    bars = ax.bar(range(len(values)), values, color=colors[:len(values)])
                    ax.set_xticks(range(len(values)))
                    ax.set_xticklabels([label.split('\n')[0] for label in labels], rotation=45, ha='right')
                    ax.set_ylabel(f'{metric.replace("_", " ").title()} (Billions)', fontweight='bold')
                    ax.set_title(f'{metric.replace("_", " ").title()} Comparison', fontsize=12)
                    ax.grid(axis='y', alpha=0.3)
                    
                    for bar, label in zip(bars, labels):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.2f}B',
                               ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            fig2.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            img_buffer.seek(0)
            base64_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            plt.close(fig2)
            
            return {
                "file_path": str(filepath),
                "base64_data": base64_data,
                "type": "financial_metrics",
                "title": "Financial Metrics Comparison",
                "description": "Comparison of key financial metrics across analyzed companies"
            }
            
        except Exception as e:
            log.error(f"Error generating financial metrics chart: {e}", exc_info=True)
            return None
    
    def generate_financial_calculations_chart(
        self,
        financial_calculations: List[Dict[str, Any]],
        query_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate charts for financial calculations
        
        Args:
            financial_calculations: List of calculation dicts with metric, value, symbol
            query_id: Query ID for file naming
            
        Returns:
            Dict with graph info or None
        """
        if not financial_calculations:
            return None
        
        try:
            # Group calculations by symbol
            by_symbol = {}
            general = []
            
            for calc in financial_calculations:
                symbol = calc.get("symbol")
                metric = calc.get("metric", "")
                value = calc.get("value", 0)
                
                if symbol:
                    if symbol not in by_symbol:
                        by_symbol[symbol] = []
                    by_symbol[symbol].append({"metric": metric, "value": value})
                else:
                    general.append({"metric": metric, "value": value})
            
            if not by_symbol and not general:
                return None
            
            # Create visualization
            num_symbols = len(by_symbol)
            if num_symbols > 0:
                fig, axes = plt.subplots(1, num_symbols, figsize=(6 * num_symbols, 6))
                if num_symbols == 1:
                    axes = [axes]
                
                fig.suptitle('Financial Calculations Summary', fontsize=16, fontweight='bold')
                
                for idx, (symbol, calcs) in enumerate(by_symbol.items()):
                    ax = axes[idx]
                    metrics = [c["metric"] for c in calcs]
                    values = [abs(float(c["value"])) if c["value"] is not None else 0 for c in calcs]
                    
                    # Create horizontal bar chart
                    y_pos = np.arange(len(metrics))
                    bars = ax.barh(y_pos, values, color=plt.cm.viridis(np.linspace(0, 1, len(metrics))))
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(metrics)
                    ax.set_xlabel('Value', fontweight='bold')
                    ax.set_title(f'{symbol}', fontsize=12, fontweight='bold')
                    ax.grid(axis='x', alpha=0.3)
                    
                    # Add value labels
                    for i, (bar, val) in enumerate(zip(bars, values)):
                        ax.text(val, bar.get_y() + bar.get_height()/2.,
                               f'{val:.2f}',
                               ha='left', va='center', fontsize=9, fontweight='bold')
                
                plt.tight_layout()
                
                # Save to file
                filename = f"{query_id}_financial_calculations.png"
                filepath = self.output_dir / filename
                fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
                plt.close(fig)
                
                # Generate base64
                img_buffer = io.BytesIO()
                fig2, axes2 = plt.subplots(1, num_symbols, figsize=(6 * num_symbols, 6))
                if num_symbols == 1:
                    axes2 = [axes2]
                fig2.suptitle('Financial Calculations Summary', fontsize=16, fontweight='bold')
                
                for idx, (symbol, calcs) in enumerate(by_symbol.items()):
                    ax = axes2[idx]
                    metrics = [c["metric"] for c in calcs]
                    values = [abs(float(c["value"])) if c["value"] is not None else 0 for c in calcs]
                    
                    y_pos = np.arange(len(metrics))
                    bars = ax.barh(y_pos, values, color=plt.cm.viridis(np.linspace(0, 1, len(metrics))))
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(metrics)
                    ax.set_xlabel('Value', fontweight='bold')
                    ax.set_title(f'{symbol}', fontsize=12, fontweight='bold')
                    ax.grid(axis='x', alpha=0.3)
                    
                    for i, (bar, val) in enumerate(zip(bars, values)):
                        ax.text(val, bar.get_y() + bar.get_height()/2.,
                               f'{val:.2f}',
                               ha='left', va='center', fontsize=9, fontweight='bold')
                
                plt.tight_layout()
                fig2.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                img_buffer.seek(0)
                base64_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                plt.close(fig2)
                
                return {
                    "file_path": str(filepath),
                    "base64_data": base64_data,
                    "type": "financial_calculations",
                    "title": "Financial Calculations Summary",
                    "description": "Programmatically calculated financial metrics"
                }
            
        except Exception as e:
            log.error(f"Error generating financial calculations chart: {e}", exc_info=True)
            return None
    
    def generate_ratio_comparison_chart(
        self,
        financial_data: Dict[str, Dict[str, Any]],
        query_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a comparison chart for financial ratios (PE, PB, etc.)
        
        Args:
            financial_data: Dict mapping symbol to financial metrics
            query_id: Query ID for file naming
            
        Returns:
            Dict with graph info or None
        """
        if not financial_data:
            return None
        
        try:
            ratios = ['pe_ratio', 'pb_ratio', 'profit_margin', 'roe']
            
            # Handle both symbol-based and flat structures
            first_key = list(financial_data.keys())[0] if financial_data else None
            is_symbol_based = first_key and isinstance(first_key, str) and first_key.isupper() and len(first_key) <= 5
            
            if is_symbol_based:
                symbols = [s for s in financial_data.keys() 
                          if isinstance(financial_data.get(s), dict) and 
                          any(financial_data[s].get(r) is not None for r in ratios)]
            else:
                # Flat structure - check if we have ratios directly
                has_ratios = any(r in financial_data for r in ratios)
                if has_ratios:
                    symbols = ["General"]
                    financial_data = {"General": financial_data}
                else:
                    return None
            
            if not symbols:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x = np.arange(len(ratios))
            width = 0.8 / len(symbols)
            
            colors = plt.cm.tab10(np.linspace(0, 1, len(symbols)))
            
            for i, symbol in enumerate(symbols):
                values = []
                symbol_data = financial_data.get(symbol, {})
                if not isinstance(symbol_data, dict):
                    continue
                    
                for ratio in ratios:
                    val = symbol_data.get(ratio)
                    try:
                        values.append(float(val) if val is not None else 0)
                    except (ValueError, TypeError):
                        values.append(0)
                
                if values:
                    offset = (i - len(symbols)/2 + 0.5) * width
                    bars = ax.bar(x + offset, values, width, label=symbol, color=colors[i])
                    
                    # Add value labels
                    for bar, val in zip(bars, values):
                        if val > 0:
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{val:.2f}',
                                   ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel('Financial Ratios', fontweight='bold')
            ax.set_ylabel('Value', fontweight='bold')
            ax.set_title('Financial Ratios Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([r.replace('_', ' ').title() for r in ratios])
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            
            # Save to file
            filename = f"{query_id}_ratios.png"
            filepath = self.output_dir / filename
            fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            # Generate base64
            img_buffer = io.BytesIO()
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            
            for i, symbol in enumerate(symbols):
                values = []
                symbol_data = financial_data.get(symbol, {})
                if not isinstance(symbol_data, dict):
                    continue
                    
                for ratio in ratios:
                    val = symbol_data.get(ratio)
                    try:
                        values.append(float(val) if val is not None else 0)
                    except (ValueError, TypeError):
                        values.append(0)
                
                if values:
                    offset = (i - len(symbols)/2 + 0.5) * width
                    bars = ax2.bar(x + offset, values, width, label=symbol, color=colors[i])
                    
                    for bar, val in zip(bars, values):
                        if val > 0:
                            height = bar.get_height()
                            ax2.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{val:.2f}',
                                   ha='center', va='bottom', fontsize=8)
            
            ax2.set_xlabel('Financial Ratios', fontweight='bold')
            ax2.set_ylabel('Value', fontweight='bold')
            ax2.set_title('Financial Ratios Comparison', fontsize=14, fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels([r.replace('_', ' ').title() for r in ratios])
            ax2.legend()
            ax2.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            fig2.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            img_buffer.seek(0)
            base64_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            plt.close(fig2)
            
            return {
                "file_path": str(filepath),
                "base64_data": base64_data,
                "type": "ratios",
                "title": "Financial Ratios Comparison",
                "description": "Comparison of key financial ratios"
            }
            
        except Exception as e:
            log.error(f"Error generating ratios chart: {e}", exc_info=True)
            return None
    
    def generate_all_graphs(
        self,
        report_data: Dict[str, Any],
        query_id: str
    ) -> List[Dict[str, Any]]:
        """
        Generate all applicable graphs for a report
        
        Args:
            report_data: Full report data dictionary
            query_id: Query ID for file naming
            
        Returns:
            List of graph info dicts
        """
        graphs = []
        
        # Extract financial data from report
        report = report_data.get("report", {})
        financial_calculations = report.get("financial_calculations", [])
        
        # Try to extract financial data from metadata or findings
        # This would need to be passed from the synthesizer
        financial_data = {}
        
        # Generate financial calculations chart
        if financial_calculations:
            calc_chart = self.generate_financial_calculations_chart(financial_calculations, query_id)
            if calc_chart:
                graphs.append(calc_chart)
        
        # Generate financial metrics chart if we have financial data
        # This would be populated from findings in the actual implementation
        if financial_data:
            metrics_chart = self.generate_financial_metrics_chart(financial_data, query_id)
            if metrics_chart:
                graphs.append(metrics_chart)
            
            ratios_chart = self.generate_ratio_comparison_chart(financial_data, query_id)
            if ratios_chart:
                graphs.append(ratios_chart)
        
        return graphs
