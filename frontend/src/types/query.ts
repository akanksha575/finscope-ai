/**
 * Type definitions for query classification
 */

export interface ClassifyRequest {
  query: string;
}

export interface ClassifyResponse {
  sector: "IT" | "Pharma" | "Unknown";
  confidence: number;
  reasoning?: string;
}


