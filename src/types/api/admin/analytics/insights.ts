/**
 * Analytics Insights Types
 * 
 * Types for analytics insights, alerts, and predictive analytics.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { BaseMetadata } from '../../../shared/metadata-types';
import type { ConfigurationValue } from '../../../shared/config-types';
import type { ConfidenceLevel, ImpactLevel, EffortLevel, ThresholdDefinition } from '../common'
import type { Priority } from '../common'
import type {
  InsightType, 
  AlertType, 
  AlertSeverity, 
  DataVisualizationType 
} from './enums';

// Analytics insight
export interface AnalyticsInsight {
  id: string;
  type: InsightType;
  priority: InsightPriority;
  title: string;
  description: string;
  metrics_affected: string[];
  confidence: ConfidenceLevel;
  impact_score: number;
  recommendations: InsightRecommendation[];
  supporting_data: InsightData[];
}

// Analytics alert
export interface AnalyticsAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  metric: string;
  threshold: ThresholdDefinition;
  current_value: number;
  triggered_at: string;
  message: string;
  actions: AlertAction[];
  acknowledged: boolean;
}

// Insight recommendation
export interface InsightRecommendation {
  action: string;
  priority: RecommendationPriority;
  impact_estimate: ImpactEstimate;
  implementation_guide: string[];
  dependencies: string[];
}

// Supporting data for insights
export interface InsightData {
  type: DataVisualizationType;
  data: Record<string, ConfigurationValue>;
  metadata: BaseMetadata;
}

// Alert action
export interface AlertAction {
  action: string;
  automated: boolean;
  executed_at?: string;
  result?: string;
}

// Impact estimate
export interface ImpactEstimate {
  metric: string;
  estimated_change: number;
  confidence: ConfidenceLevel;
  timeframe: string;
}

// Contributing factor for trends
export interface ContributingFactor {
  factor: string;
  impact_score: number;
  confidence: ConfidenceLevel;
  correlation: number;
}

// Trend prediction
export interface TrendPrediction {
  period: string;
  value: number;
  confidence_interval: ConfidenceInterval;
  probability: number;
}

// Confidence interval
export interface ConfidenceInterval {
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
}

// Forecast types
export type ForecastType = 'linear' | 'exponential' | 'seasonal' | 'arima' | 'neural_network';

// Type aliases
export type InsightPriority = Priority;
export type RecommendationPriority = Priority;