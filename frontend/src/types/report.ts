/**
 * Type definitions for reports
 */

export interface ReportMetadata {
  duration_seconds: number;
  total_steps: number;
  sources_used: string[];
  plan_type?: string;
  sections?: Record<string, boolean>;
}

export interface ReportContent {
  title: string;
  executive_summary: string;
  analysis: string;
  key_findings: string[];
  recommendations: string[];
  financial_highlights?: string[];
  citations?: any[];
  all_citations?: any[];
  financial_calculations?: any[];
}

export interface ReportResponse {
  query_id: string;
  query: string;
  sector: string;
  status: string;
  report: ReportContent;
  metadata: ReportMetadata;
  created_at: string;
  updated_at: string;
}


