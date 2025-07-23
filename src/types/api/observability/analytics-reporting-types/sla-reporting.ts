/**
 * SLA Reporting Types
 * 
 * Type definitions for SLA monitoring, breach analysis, compliance tracking,
 * and generating SLA reports and forecasts.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../../shared';
import type { ImpactMeasure, TrendData } from './shared-types'
import type { SeasonalPattern, PredictionFactor } from './shared-types'

// SLA Reporting Requests and Responses
export interface GetSLAReportRequest extends BaseApiRequest {
  flowId: string;
  slaIds?: string[];
  timeRange: {
    start: string;
    end: string;
  };
  includeBreaches?: boolean;
  includeForecasts?: boolean;
  aggregation?: 'hour' | 'day' | 'week' | 'month';
  context: MultiTenantContext;
}

export interface GetSLAReportResponse extends BaseApiResponse<SLAReport> {
  data: SLAReport;
  slaStatus: SLAStatus[];
  breaches: SLABreach[];
  compliance: SLACompliance;
  forecasts: SLAForecast[];
  trends: SLATrend[];
}

// Core SLA Types
export interface SLAReport {
  id: string;
  reportId: string;
  flowId: string;
  timeRange: {
    start: string;
    end: string;
  };
  slas: SLADefinition[];
  overallCompliance: number;
  summary: SLAReportSummary;
  breachAnalysis: BreachAnalysis;
  trendAnalysis: SLATrendAnalysis;
  recommendations: SLARecommendation[];
  generatedAt: string;
}

export interface SLAStatus {
  slaId: string;
  name: string;
  target: number;
  actual: number;
  compliance: number;
  status: 'met' | 'at_risk' | 'breached' | 'unknown';
  timeToTarget: number;
  trend: 'improving' | 'degrading' | 'stable';
  lastEvaluation: string;
}

export interface SLABreach {
  id: string;
  slaId: string;
  slaName: string;
  startTime: string;
  endTime?: string;
  duration: number;
  severity: 'minor' | 'major' | 'critical';
  impact: BreachImpact;
  rootCause: string;
  resolution: string;
  preventionMeasures: PreventionMeasure[];
}

export interface SLACompliance {
  overall: number;
  byPeriod: ComplianceByPeriod[];
  bySLA: ComplianceBySLA[];
  trends: ComplianceTrend[];
  riskFactors: RiskFactor[];
}

export interface SLAForecast {
  slaId: string;
  period: string;
  predictedCompliance: number;
  confidence: number;
  riskLevel: 'low' | 'medium' | 'high';
  assumptions: ForecastAssumption[];
  scenarios: ForecastScenario[];
}

export interface SLATrend {
  slaId: string;
  metric: string;
  direction: 'improving' | 'degrading' | 'stable';
  rate: number;
  timeframe: string;
  significance: 'low' | 'medium' | 'high';
}

// SLA Definition and Supporting Types
export interface SLADefinition {
  id: string;
  name: string;
  description: string;
  metric: string;
  target: number;
  unit: string;
  operator: 'gte' | 'lte' | 'eq';
  measurementWindow: string;
  evaluationFrequency: string;
}

export interface SLAReportSummary {
  totalSLAs: number;
  metSLAs: number;
  breachedSLAs: number;
  atRiskSLAs: number;
  overallCompliance: number;
  previousCompliance: number;
  trend: 'improving' | 'degrading' | 'stable';
}

export interface BreachAnalysis {
  totalBreaches: number;
  averageBreachDuration: number;
  mttr: number;
  topCauses: BreachCause[];
  impactAssessment: BreachImpactAssessment;
  patterns: BreachPattern[];
}

export interface SLATrendAnalysis {
  complianceTrend: TrendData[];
  seasonalPatterns: SeasonalPattern[];
  correlations: SLACorrelation[];
  predictions: SLAPrediction[];
}

export interface SLARecommendation {
  id: string;
  type: 'target_adjustment' | 'monitoring_improvement' | 'process_optimization' | 'resource_allocation';
  slaId: string;
  title: string;
  description: string;
  rationale: string;
  impact: SLARecommendationImpact;
  effort: 'low' | 'medium' | 'high';
  priority: number;
}

// Breach and Impact Types
export interface BreachImpact {
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedUsers: number;
  businessImpact: string;
  financialImpact: number;
  reputationImpact: 'minimal' | 'moderate' | 'significant' | 'severe';
}

export interface PreventionMeasure {
  id: string;
  type: 'monitoring' | 'automation' | 'process' | 'documentation' | 'training';
  description: string;
  priority: 'low' | 'medium' | 'high';
  estimatedEffort: string;
  responsible: string;
  dueDate?: string;
}

export interface ComplianceByPeriod {
  period: string;
  compliance: number;
  target: number;
  status: 'met' | 'at_risk' | 'breached';
}

export interface ComplianceBySLA {
  slaId: string;
  slaName: string;
  compliance: number;
  target: number;
  trend: 'improving' | 'degrading' | 'stable';
}

export interface ComplianceTrend {
  metric: string;
  direction: 'improving' | 'degrading' | 'stable';
  rate: number;
  significance: 'low' | 'medium' | 'high';
}

export interface RiskFactor {
  type: string;
  description: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  probability: number;
  mitigation: string[];
}

export interface ForecastAssumption {
  id: string;
  description: string;
  type: 'business' | 'technical' | 'external';
  confidence: number;
  impact: 'low' | 'medium' | 'high';
}

export interface ForecastScenario {
  name: string;
  probability: number;
  compliance: number;
  description: string;
  assumptions: string[];
}

export interface BreachCause {
  cause: string;
  frequency: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
  preventable: boolean;
  cost: number;
}

export interface BreachImpactAssessment {
  totalCost: number;
  userImpact: number;
  reputationImpact: 'minimal' | 'moderate' | 'significant' | 'severe';
  complianceImpact: boolean;
  operationalImpact: string;
}

export interface BreachPattern {
  pattern: string;
  frequency: string;
  timeOfDay: string[];
  dayOfWeek: string[];
  seasonality: boolean;
  triggers: string[];
}

export interface SLACorrelation {
  slaIds: string[];
  coefficient: number;
  significance: boolean;
  description: string;
}

export interface SLAPrediction {
  slaId: string;
  period: string;
  predictedValue: number;
  confidence: number;
  factors: PredictionFactor[];
}

export interface SLARecommendationImpact {
  compliance: ImpactMeasure;
  cost: ImpactMeasure;
  effort: 'low' | 'medium' | 'high';
  risk: 'low' | 'medium' | 'high';
}