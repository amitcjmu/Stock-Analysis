/**
 * Platform Analytics Types
 * 
 * Core platform analytics data structures and metrics.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { AnalyticsMetadata, AnalyticsPeriod, ConfidenceLevel, TrendDirection } from '../common';
import type { ForecastType } from './insights'
import { TrendPrediction, ContributingFactor } from './insights'

// Platform analytics summary
export interface PlatformAnalytics {
  id: string;
  period: AnalyticsPeriod;
  generated_at: string;
  summary: AnalyticsSummary;
  metrics: PlatformMetrics;
  segmentation: AnalyticsSegmentation;
  comparisons: PeriodComparison[];
  insights: AnalyticsInsight[];
  alerts: AnalyticsAlert[];
  metadata: AnalyticsMetadata;
}

// Analytics summary
export interface AnalyticsSummary {
  total_users: number;
  active_users: number;
  total_accounts: number;
  active_accounts: number;
  total_engagements: number;
  active_engagements: number;
  growth_rate: number;
  retention_rate: number;
  churn_rate: number;
  satisfaction_score: number;
}

// Platform metrics breakdown
export interface PlatformMetrics {
  business: BusinessMetrics;
  technical: TechnicalMetrics;
  operational: OperationalMetrics;
  financial: FinancialMetrics;
  quality: QualityMetrics;
  security: SecurityMetrics;
}

// Analytics segmentation
export interface AnalyticsSegmentation {
  by_tier: Record<string, SegmentMetrics>;
  by_industry: Record<string, SegmentMetrics>;
  by_size: Record<string, SegmentMetrics>;
  by_region: Record<string, SegmentMetrics>;
  by_age: Record<string, SegmentMetrics>;
  custom: Record<string, SegmentMetrics>;
}

// Period comparison
export interface PeriodComparison {
  period: string;
  comparison_period: string;
  metrics: ComparisonMetrics;
  changes: MetricChange[];
  significance: StatisticalSignificance;
}

// Analytics trend
export interface AnalyticsTrend {
  metric: string;
  direction: TrendDirection;
  magnitude: number;
  confidence: ConfidenceLevel;
  time_horizon: TimePeriod;
  contributing_factors: ContributingFactor[];
  predictions: TrendPrediction[];
  recommendations: TrendRecommendation[];
}

// Analytics forecast
export interface AnalyticsForecast {
  metric: string;
  forecast_type: ForecastType;
  time_horizon: TimePeriod;
  predictions: ForecastPrediction[];
  confidence_intervals: ConfidenceInterval[];
  model_info: ForecastModel;
  accuracy_metrics: AccuracyMetric[];
  scenarios: ForecastScenario[];
}

// Import from insights module
type AnalyticsInsight = import('./insights').AnalyticsInsight;
type AnalyticsAlert = import('./insights').AnalyticsAlert;

// Supporting interfaces
export interface SegmentMetrics {
  count: number;
  percentage: number;
  growth_rate: number;
  revenue: number;
  engagement_score: number;
  satisfaction_score: number;
}

export interface ComparisonMetrics {
  absolute_change: Record<string, number>;
  percentage_change: Record<string, number>;
  statistical_significance: Record<string, boolean>;
  confidence_intervals: Record<string, ConfidenceInterval>;
}

export interface MetricChange {
  metric: string;
  absolute_change: number;
  percentage_change: number;
  direction: ChangeDirection;
  significance: StatisticalSignificance;
}

export interface TrendRecommendation {
  action: string;
  priority: RecommendationPriority;
  impact_estimate: number;
  implementation_effort: EffortLevel;
}

export interface ForecastPrediction {
  period: string;
  predicted_value: number;
  confidence_interval: ConfidenceInterval;
  contributing_factors: ContributingFactor[];
}

export interface ConfidenceInterval {
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
}

export interface ForecastModel {
  algorithm: string;
  version: string;
  training_period: AnalyticsPeriod;
  features_used: string[];
  hyperparameters: Record<string, string | number | boolean | string[] | number[]>;
  performance_metrics: ModelPerformanceMetric[];
}

export interface AccuracyMetric {
  metric: string;
  value: number;
  benchmark: number;
  threshold: number;
}

export interface ForecastScenario {
  name: string;
  description: string;
  assumptions: string[];
  predictions: ForecastPrediction[];
  probability: number;
}

export interface ModelPerformanceMetric {
  name: string;
  value: number;
  description: string;
}

// Metric interfaces
export interface BusinessMetrics {
  revenue: RevenueMetrics;
  customers: CustomerMetrics;
  growth: GrowthMetrics;
  retention: RetentionMetrics;
  satisfaction: SatisfactionMetrics;
}

export interface TechnicalMetrics {
  performance: PerformanceMetrics;
  reliability: ReliabilityMetrics;
  scalability: ScalabilityMetrics;
  security: SecurityMetrics;
}

export interface OperationalMetrics {
  efficiency: EfficiencyMetrics;
  capacity: CapacityMetrics;
}

export interface FinancialMetrics {
  revenue: number;
  costs: number;
  profit: number;
  margins: MarginMetrics;
}

export interface QualityMetrics {
  score: number;
  defects: number;
  satisfaction: number;
  compliance: number;
}

export interface SecurityMetrics {
  incidents: number;
  vulnerabilities: number;
  compliance: number;
  risk_score: number;
}

// Import common types
type TimePeriod = import('../common').TimePeriod;
type EffortLevel = import('../common').EffortLevel;

// Enums and types
export type ChangeDirection = 'increase' | 'decrease' | 'no_change';
export type StatisticalSignificance = 'significant' | 'not_significant' | 'unknown';
export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical';

// Placeholder metric interfaces
export interface RevenueMetrics { total: number; recurring: number; growth: number; }
export interface CustomerMetrics { total: number; new: number; churn: number; }
export interface GrowthMetrics { rate: number; new_users: number; expansion: number; }
export interface RetentionMetrics { rate: number; cohort_analysis: unknown[]; }
export interface SatisfactionMetrics { score: number; nps: number; feedback: string[]; }
export interface PerformanceMetrics { score: number; latency: number; throughput: number; }
export interface ReliabilityMetrics { uptime: number; mtbf: number; mttr: number; }
export interface ScalabilityMetrics { capacity: number; elasticity: number; efficiency: number; }
export interface EfficiencyMetrics { score: number; optimization: number; waste: number; }
export interface CapacityMetrics { current: number; maximum: number; utilized: number; }
export interface MarginMetrics { gross: number; operating: number; net: number; }