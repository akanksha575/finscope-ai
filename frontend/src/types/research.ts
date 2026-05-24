/**
 * Type definitions for research-related data
 */

export type Sector = "IT" | "Pharma" | "Architecture" | "Energy" | "Unknown";

export type ResearchStatus = 
  | "planning" 
  | "researching" 
  | "synthesizing" 
  | "completed" 
  | "failed";

export interface ResearchRequest {
  query: string;
  sector: Sector;
  selected_questions: string[];
  use_rag?: boolean;
}

export interface ResearchResponse {
  query_id: string;
  query: string;
  sector: string;
  plan_type: string;
  status: string;
  report: Report;
  total_steps: number;
  duration_seconds: number;
  sources_used: string[];
}

export interface Report {
  title: string;
  executive_summary: string;
  analysis: string;
  key_findings: string[];
  recommendations: string[];
  financial_highlights?: string[];
  citations?: Citation[];
  all_citations?: Citation[];  // All citations for Sources panel
  financial_calculations?: FinancialCalculation[];
}

export interface Citation {
  title: string;
  url: string;
  type: "web" | "financial";
  domain: string;
  published_date?: string;
  symbol?: string;
}

export interface FinancialCalculation {
  metric: string;
  value: string;
  formula?: string;
  symbol?: string;
}

export interface ProgressUpdate {
  type: "tool_start" | "tool_complete" | "url_accessed" | "data_received" | "tool_error" | "progress" | "status" | "complete";
  tool?: string;
  url?: string;
  query?: string;
  message: string;
  progress?: number;
  timestamp?: string;
  status?: ResearchStatus;
  report?: Report;
  findings?: any[];
  queries?: string[];
  error?: string;
  query_id?: string;
}

