/**
 * Shared Analysis Type Definitions
 * 
 * Standardized analysis result interfaces to replace forward declarations
 * and any types in analysis systems
 */

import type { BaseMetadata } from './metadata-types';

/**
 * Base interface for all analysis results across the platform
 */
export interface AnalysisResult {
  /** Type of analysis performed */
  analysisType: string;
  /** Confidence level (0-1) in the analysis results */
  confidence: number;
  /** Generated recommendations based on analysis */
  recommendations: string[];
  /** Analysis-specific data payload */
  data: Record<string, unknown>;
  /** Analysis execution metadata */
  executionMetadata?: {
    startTime: string;
    endTime: string;
    duration: number;
    resourcesUsed?: Record<string, unknown>;
  };
}

/**
 * Financial cost analysis results
 */
export interface CostAnalysis extends AnalysisResult {
  /** Total calculated cost */
  totalCost: number;
  /** Detailed cost breakdown by category */
  breakdown: CostBreakdownItem[];
  /** Currency code (ISO 4217) */
  currency: string;
  /** Cost calculation methodology */
  methodology?: string;
  /** Time period for cost calculation */
  period?: {
    start: string;
    end: string;
    duration: string;
  };
}

/**
 * Individual cost breakdown item
 */
export interface CostBreakdownItem {
  /** Cost category name */
  category: string;
  /** Amount for this category */
  amount: number;
  /** Unit of measurement */
  unit?: string;
  /** Quantity measured */
  quantity?: number;
  /** Unit cost */
  unitCost?: number;
  /** Additional cost details */
  details?: Record<string, unknown>;
}

/**
 * Risk analysis results
 */
export interface RiskAnalysis extends AnalysisResult {
  /** Overall risk score (0-100) */
  riskScore: number;
  /** Risk level classification */
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  /** Identified risk factors */
  riskFactors: RiskFactor[];
  /** Suggested mitigation strategies */
  mitigationStrategies: string[];
}

/**
 * Individual risk factor
 */
export interface RiskFactor {
  /** Risk factor name */
  name: string;
  /** Impact level if risk materializes */
  impact: 'low' | 'medium' | 'high' | 'critical';
  /** Probability of occurrence */
  probability: number;
  /** Risk category */
  category: string;
  /** Detailed description */
  description?: string;
}

/**
 * Timeline analysis for project planning
 */
export interface TimelineAnalysis extends AnalysisResult {
  /** Critical path information */
  criticalPath: string[];
  /** Estimated completion date */
  estimatedCompletion: string;
  /** Timeline milestones */
  milestones: TimelineMilestone[];
  /** Resource allocation analysis */
  resourceAllocation: Record<string, unknown>;
}

/**
 * Timeline milestone definition
 */
export interface TimelineMilestone {
  /** Milestone identifier */
  id: string;
  /** Milestone name */
  name: string;
  /** Target completion date */
  targetDate: string;
  /** Milestone dependencies */
  dependencies: string[];
  /** Milestone metadata */
  metadata: BaseMetadata;
}