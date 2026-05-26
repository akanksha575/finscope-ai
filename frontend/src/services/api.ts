/**
 * API service for communicating with FastAPI backend
 */
import axios from 'axios';
import type { 
  ClassifyRequest, 
  ClassifyResponse,
  PlanRequest,
  PlanResponse,
  ResearchRequest,
  ResearchResponse,
  ReportResponse
} from '../types';

// Use relative URL if VITE_API_URL is empty or not set (for nginx proxy in Docker)
// Otherwise use the provided URL (for development)
// Default to localhost:8000 for manual development (non-Docker)
const API_BASE_URL = import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== '' 
  ? import.meta.env.VITE_API_URL 
  : (import.meta.env.DEV ? 'http://localhost:8000' : ''); // Use localhost:8000 in dev mode, relative URL in production

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Classify a query to determine sector
 */
export const classifyQuery = async (request: ClassifyRequest & { signal?: AbortSignal }): Promise<ClassifyResponse> => {
  try {
    const { signal, ...data } = request;
    const response = await api.post<ClassifyResponse>('/api/classify', data, { signal });
    console.log('Classification response:', response.data);
    
    // Ensure sector is valid
    if (!response.data.sector || !['IT', 'Pharma', 'Unknown'].includes(response.data.sector)) {
      console.warn('Invalid sector received:', response.data.sector);
      return {
        ...response.data,
        sector: 'Unknown' as const
      };
    }
    
    return response.data;
  } catch (error: any) {
    console.error('Classification error:', error);
    // Return a safe fallback
    return {
      sector: 'Unknown',
      confidence: 0.0,
      reasoning: error.response?.data?.detail || error.message || 'Classification failed'
    };
  }
};

/**
 * Generate research plan
 */
export const generatePlan = async (request: PlanRequest): Promise<PlanResponse> => {
  const response = await api.post<PlanResponse>('/api/plan', request);
  return response.data;
};

/**
 * Start research workflow (REST endpoint - for non-WebSocket usage)
 */
export const startResearch = async (request: ResearchRequest): Promise<ResearchResponse> => {
  const response = await api.post<ResearchResponse>('/api/research/start', request);
  return response.data;
};

/**
 * Get report by query ID
 */
export const getReport = async (queryId: string): Promise<ReportResponse> => {
  const response = await api.get<ReportResponse>(`/api/report/${queryId}`);
  return response.data;
};

/**
 * List all reports
 */
export const listReports = async (): Promise<ReportResponse[]> => {
  const response = await api.get<ReportResponse[]>('/api/report');
  return response.data;
};

/**
 * Export report
 */
export const exportReport = async (queryId: string, format: 'pdf' | 'html' | 'markdown') => {
  const response = await api.post<{
    query_id: string;
    format: string;
    file_path: string;
    file_url: string;
    file_size: number;
  }>('/api/report/export', {
    query_id: queryId,
    format,
  });
  return response.data;
};

/**
 * Delete a report by query ID
 */
export const deleteReport = async (queryId: string): Promise<{ message: string; query_id: string }> => {
  const response = await api.delete<{ message: string; query_id: string }>(`/api/report/${queryId}`);
  return response.data;
};

/**
 * Delete all reports
 */
export const deleteAllReports = async (): Promise<{ message: string; count: number }> => {
  const response = await api.delete<{ message: string; count: number }>('/api/report/all');
  return response.data;
};

export default api;

