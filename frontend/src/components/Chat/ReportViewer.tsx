/**
 * Report Viewer Component - Displays the generated research report
 */
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download, FileText, FileCode, Loader2, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import type { ReportResponse } from '../../types/report';
import { exportReport } from '../../services/api';

interface ReportViewerProps {
  report: ReportResponse;
}

export default function ReportViewer({ report }: ReportViewerProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async (format: 'pdf' | 'html' | 'markdown') => {
    setIsExporting(true);
    setExportError(null);
    
    try {
      // First, trigger the export on the backend
      const result = await exportReport(report.query_id, format);
      
      if (result.file_url) {
        // Get the full download URL
        const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const downloadUrl = `${apiBaseUrl}${result.file_url}`;
        
        // For PDF and binary files, fetch as blob and download
        if (format === 'pdf') {
          const response = await fetch(downloadUrl);
          if (!response.ok) {
            throw new Error('Failed to download file');
          }
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `${report.report.title || 'report'}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        } else {
          // For HTML and Markdown, use direct download
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = `${report.report.title || 'report'}.${format === 'markdown' ? 'md' : format}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
      }
    } catch (error: any) {
      console.error('Export failed:', error);
      setExportError(error.response?.data?.detail || error.message || 'Failed to export report');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Export Error Toast */}
      {exportError && (
        <div className="bg-red-950/40 border border-red-800 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-300">Export Failed</p>
            <p className="text-sm text-red-400 mt-1">{exportError}</p>
          </div>
          <button
            onClick={() => setExportError(null)}
            className="text-red-400 hover:text-red-300"
          >
            ×
          </button>
        </div>
      )}

      {/* Download Buttons - Outside and on top of the report */}
      <div className="flex justify-end gap-2">
        <button
          onClick={() => handleExport('pdf')}
          disabled={isExporting}
          className="px-4 py-2 text-sm bg-zinc-200 text-zinc-900 rounded-lg hover:bg-white disabled:bg-fs-elevated disabled:text-zinc-600 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {isExporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          PDF
        </button>
        <button
          onClick={() => handleExport('html')}
          disabled={isExporting}
          className="px-4 py-2 text-sm bg-zinc-200 text-zinc-900 rounded-lg hover:bg-white disabled:bg-fs-elevated disabled:text-zinc-600 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {isExporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FileText className="w-4 h-4" />
          )}
          HTML
        </button>
        <button
          onClick={() => handleExport('markdown')}
          disabled={isExporting}
          className="px-4 py-2 text-sm bg-zinc-200 text-zinc-900 rounded-lg hover:bg-white disabled:bg-fs-elevated disabled:text-zinc-600 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {isExporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FileCode className="w-4 h-4" />
          )}
          Markdown
        </button>
      </div>

      {/* Report Header */}
      <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-black mb-4">
            {report.report.title || report.query} - Deep Research Report
          </h1>
          <div className="space-y-2 text-sm text-zinc-600 mb-6">
            <div><strong>Generated by FinScope AI</strong></div>
            <div><strong>Date:</strong> {format(new Date(report.created_at), 'MMMM d, yyyy')}</div>
            <div><strong>Research Query:</strong> {report.query}</div>
            <div><strong>Sector:</strong> {report.sector}</div>
            <div><strong>Research Depth:</strong> {report.metadata.plan_type || 'Deep'}</div>
            <div><strong>Analysis Period:</strong> {format(new Date(report.created_at), 'MMM yyyy')}</div>
          </div>
        </div>

        <div className="border-t border-zinc-200 pt-6">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-black mb-4">Executive Summary</h2>
            <div className="prose prose-sm max-w-none text-zinc-800 space-y-3">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {report.report.executive_summary}
              </ReactMarkdown>
            </div>
            
            {/* Key Takeaways */}
            {report.report.key_findings && report.report.key_findings.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-black mb-3">Key Takeaways:</h3>
                <ul className="space-y-2">
                  {report.report.key_findings.slice(0, 4).map((finding, index) => (
                    <li key={index} className="flex items-start gap-2 text-zinc-800">
                      <span className="text-emerald-600 mt-1">✓</span>
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Analysis - Display as formatted markdown matching the template structure */}
      <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8">
        <div className="prose prose-lg max-w-none text-zinc-900">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.report.analysis}
          </ReactMarkdown>
        </div>
      </div>

      {/* Key Findings - Only show if not already in executive summary */}
      {report.report.key_findings && report.report.key_findings.length > 4 && (
        <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8">
          <h2 className="text-2xl font-bold text-black mb-4">Key Findings</h2>
          <ul className="space-y-3">
            {report.report.key_findings.slice(4).map((finding, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="text-zinc-600 mt-1 font-bold">•</span>
                <span className="text-zinc-800">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {report.report.recommendations && report.report.recommendations.length > 0 && (
        <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8">
          <h2 className="text-2xl font-bold text-black mb-4">Recommendations</h2>
          <ul className="space-y-3">
            {report.report.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="text-emerald-600 mt-1 font-bold">•</span>
                <span className="text-zinc-800">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Financial Highlights */}
      {report.report.financial_highlights && report.report.financial_highlights.length > 0 && (
        <div className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8">
          <h2 className="text-2xl font-bold text-black mb-4">Financial Highlights</h2>
          <ul className="space-y-3">
            {report.report.financial_highlights.map((highlight, index) => (
              <li key={index} className="text-zinc-800">{highlight}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

