/**
 * Observability Analytics Types
 * 
 * Type definitions for core observability analytics, metrics analysis,
 * KPI tracking, and overall system health assessment.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../../shared';

// Observability Analytics Requests and Responses
export interface GetObservabilityAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  includeAnomalies?: boolean;
  context: MultiTenantContext;
}

export interface GetObservabilityAnalyticsResponse extends BaseApiResponse<ObservabilityAnalytics> {
  data: ObservabilityAnalytics;
  insights: ObservabilityInsight[];
  trends: ObservabilityTrend[];
  anomalies: ObservabilityAnomaly[];
  health: OverallHealth;
}

// Core Observability Analytics Types
export interface ObservabilityAnalytics {
  id: string;
  timeRange: {
    start: string;
    end: string;
  };
  summary: AnalyticsSummary;
  metrics: AnalyticsMetric[];
  kpis: KPIAnalysis[];
  correlations: MetricCorrelation[];
  patterns: AnalyticsPattern[];
  generatedAt: string;
}

export interface ObservabilityInsight {
  id: string;
  type: 'optimization' | 'anomaly' | 'trend' | 'correlation' | 'prediction';
  category: 'performance' | 'availability' | 'cost' | 'security' | 'reliability';
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  confidence: number;
  impact: InsightImpact;
  actionable: boolean;
  recommendations: InsightRecommendation[];
  evidence: InsightEvidence[];
}

export interface ObservabilityTrend {
  metric: string;
  direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  magnitude: number;
  confidence: number;
  timeframe: string;
  seasonality: boolean;
  forecast: ObservabilityForecast;
  significance: 'low' | 'medium' | 'high';
}

export interface ObservabilityAnomaly {
  id: string;
  type: 'point' | 'contextual' | 'collective' | 'drift';
  metric: string;
  timestamp: string;
  actualValue: number;
  expectedValue: number;
  deviation: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  context: AnomalyContext;
  impact: AnomalyImpact;
}

export interface OverallHealth {
  score: number;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  components: ComponentHealthScore[];
  trends: HealthTrend[];
  alerts: HealthAlert[];
  lastAssessment: string;
}

// Supporting Analytics Types
export interface AnalyticsSummary {
  totalMetrics: number;
  healthScore: number;
  anomaliesDetected: number;
  trendsIdentified: number;
  correlationsFound: number;
  lastAnalysis: string;
}

export interface AnalyticsMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'increasing' | 'decreasing' | 'stable';
  change: number;
  significance: 'low' | 'medium' | 'high';
}

export interface KPIAnalysis {
  kpi: string;
  current: number;
  target: number;
  status: 'on_track' | 'at_risk' | 'off_track';
  trend: 'improving' | 'degrading' | 'stable';
  forecast: number;
}

export interface MetricCorrelation {
  metrics: string[];
  coefficient: number;
  pValue: number;
  strength: 'weak' | 'moderate' | 'strong';
  causal: boolean;
}

export interface AnalyticsPattern {
  id: string;
  type: 'periodic' | 'seasonal' | 'trending' | 'anomalous';
  description: string;
  confidence: number;
  metrics: string[];
  timeframe: string;
}

export interface InsightImpact {
  scope: 'local' | 'service' | 'system' | 'business';
  severity: 'low' | 'medium' | 'high' | 'critical';
  urgency: 'low' | 'medium' | 'high' | 'immediate';
  effort: 'low' | 'medium' | 'high';
}

export interface InsightRecommendation {
  action: string;
  priority: number;
  effort: 'low' | 'medium' | 'high';
  benefit: 'low' | 'medium' | 'high';
  timeline: string;
}

export interface InsightEvidence {
  type: 'metric' | 'trend' | 'anomaly' | 'pattern' | 'correlation';
  source: string;
  value: unknown;
  confidence: number;
  timestamp: string;
}

export interface ObservabilityForecast {
  value: number;
  confidence: number;
  upperBound: number;
  lowerBound: number;
  timeframe: string;
}

export interface AnomalyContext {
  related: string[];
  contributing: string[];
  environmental: Record<string, string | number | boolean | undefined>;
  temporal: string;
}

export interface AnomalyImpact {
  severity: 'low' | 'medium' | 'high' | 'critical';
  scope: string[];
  duration: string;
  userImpact: number;
  businessImpact: string;
}

export interface ComponentHealthScore {
  component: string;
  score: number;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  issues: string[];
  lastCheck: string;
}

export interface HealthTrend {
  component: string;
  direction: 'improving' | 'degrading' | 'stable';
  rate: number;
  timeframe: string;
  forecast: number;
}

export interface HealthAlert {
  component: string;
  type: 'degradation' | 'failure' | 'risk';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
}