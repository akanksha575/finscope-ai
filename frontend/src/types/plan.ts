/**
 * Type definitions for research planning
 */

import type { Sector } from './research';

export interface Plan {
  type: string;
  steps: number;
  questions: string[];
  estimated_time: string;
  description?: string;
}

export interface PlanRequest {
  query: string;
  sector: Sector;
}

export interface PlanResponse {
  query: string;
  sector: string;
  plan: Plan;
}


