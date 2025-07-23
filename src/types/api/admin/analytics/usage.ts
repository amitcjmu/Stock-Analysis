/**
 * Usage Analytics Types
 * 
 * Detailed usage analytics for users, accounts, features, and resources.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { TrendDirection } from '../common';

// Main usage analytics container
export interface UsageAnalytics {
  users: UserUsageAnalytics;
  accounts: AccountUsageAnalytics;
  engagements: EngagementUsageAnalytics;
  features: FeatureUsageAnalytics;
  api: ApiUsageAnalytics;
  storage: StorageUsageAnalytics;
  compute: ComputeUsageAnalytics;
  integrations: IntegrationUsageAnalytics;
}

// User usage analytics
export interface UserUsageAnalytics {
  total_users: UserMetrics;
  active_users: UserMetrics;
  new_users: UserMetrics;
  returning_users: UserMetrics;
  user_sessions: SessionMetrics;
  user_engagement: EngagementMetrics;
  user_retention: RetentionMetrics;
  user_cohorts: CohortAnalysis[];
}

// Account usage analytics
export interface AccountUsageAnalytics {
  total_accounts: AccountMetrics;
  active_accounts: AccountMetrics;
  new_accounts: AccountMetrics;
  account_growth: GrowthMetrics;
  account_health: HealthMetrics;
  subscription_metrics: SubscriptionMetrics;
  revenue_metrics: RevenueMetrics;
}

// Engagement usage analytics
export interface EngagementUsageAnalytics {
  total_engagements: EngagementMetrics;
  active_engagements: EngagementMetrics;
  completed_engagements: EngagementMetrics;
  engagement_duration: DurationMetrics;
  engagement_success: SuccessMetrics;
  engagement_types: TypeDistribution[];
  engagement_outcomes: OutcomeAnalysis[];
}

// Feature usage analytics
export interface FeatureUsageAnalytics {
  feature_adoption: FeatureAdoptionMetrics[];
  feature_engagement: FeatureEngagementMetrics[];
  feature_performance: FeaturePerformanceMetrics[];
  feature_feedback: FeatureFeedbackMetrics[];
  feature_abandonment: FeatureAbandonmentMetrics[];
  feature_correlation: FeatureCorrelation[];
}

// API usage analytics
export interface ApiUsageAnalytics {
  total_calls: ApiMetrics;
  unique_clients: ApiMetrics;
  endpoint_usage: EndpointUsage[];
  response_times: ResponseTimeDistribution;
  error_rates: ErrorRateAnalysis;
  rate_limiting: RateLimitingMetrics;
  api_versions: VersionUsageMetrics[];
}

// Storage usage analytics
export interface StorageUsageAnalytics {
  total_storage: StorageMetrics;
  storage_growth: GrowthMetrics;
  storage_by_type: TypeDistribution[];
  storage_efficiency: EfficiencyMetrics;
  backup_metrics: BackupMetrics;
  retention_compliance: ComplianceMetrics;
}

// Compute usage analytics
export interface ComputeUsageAnalytics {
  cpu_utilization: UtilizationMetrics;
  memory_utilization: UtilizationMetrics;
  network_utilization: UtilizationMetrics;
  scaling_events: ScalingMetrics;
  cost_optimization: CostOptimizationMetrics;
  resource_efficiency: ResourceEfficiencyMetrics;
}

// Integration usage analytics
export interface IntegrationUsageAnalytics {
  active_integrations: IntegrationMetrics;
  integration_health: IntegrationHealthMetrics[];
  data_flow: DataFlowMetrics;
  sync_performance: SyncPerformanceMetrics;
  error_rates: IntegrationErrorMetrics;
  usage_patterns: IntegrationPatternMetrics[];
}

// Supporting metric interfaces
export interface UserMetrics {
  total: number;
  change: number;
  change_percentage: number;
  trend: TrendDirection;
}

export interface SessionMetrics {
  total_sessions: number;
  average_duration: number;
  bounce_rate: number;
  pages_per_session: number;
}

export interface EngagementMetrics {
  score: number;
  duration: number;
  frequency: number;
  depth: number;
}

export interface RetentionMetrics {
  rate: number;
  day_1: number;
  day_7: number;
  day_30: number;
  cohort_curves: number[];
}

export interface CohortAnalysis {
  cohortId: string;
  cohort_date: string;
  size: number;
  retention: number[];
  engagement: number[];
  revenue: number[];
}

export interface AccountMetrics {
  total: number;
  active: number;
  new: number;
  churned: number;
}

export interface GrowthMetrics {
  rate: number;
  absolute_growth: number;
  percentage_growth: number;
  compound_annual: number;
}

export interface HealthMetrics {
  score: number;
  status: HealthStatus;
  risk_factors: string[];
  alerts: number;
}

export interface SubscriptionMetrics {
  total: number;
  active: number;
  new: number;
  upgrades: number;
  downgrades: number;
  churn: number;
  mrr: number;
  arr: number;
}

export interface RevenueMetrics {
  total: number;
  recurring: number;
  non_recurring: number;
  growth: number;
  per_user: number;
  per_account: number;
}

export interface DurationMetrics {
  average: number;
  median: number;
  p95: number;
  p99: number;
  distribution: Record<string, number>;
}

export interface SuccessMetrics {
  rate: number;
  criteria: string[];
  score: number;
  trend: TrendDirection;
}

export interface TypeDistribution {
  type: string;
  count: number;
  percentage: number;
  trend: TrendDirection;
}

export interface OutcomeAnalysis {
  outcome: string;
  count: number;
  percentage: number;
  success_rate: number;
  average_value: number;
}

export interface FeatureAdoptionMetrics {
  featureId: string;
  feature_name: string;
  adoption_rate: number;
  unique_users: number;
  usage_frequency: number;
  time_to_adopt: number;
}

export interface FeatureEngagementMetrics {
  featureId: string;
  engagement_score: number;
  session_percentage: number;
  retention_impact: number;
  satisfaction_score: number;
}

export interface FeaturePerformanceMetrics {
  featureId: string;
  response_time: number;
  error_rate: number;
  success_rate: number;
  resource_usage: number;
}

export interface FeatureFeedbackMetrics {
  featureId: string;
  satisfaction_score: number;
  nps_score: number;
  feedback_count: number;
  improvement_suggestions: number;
}

export interface FeatureAbandonmentMetrics {
  featureId: string;
  abandonment_rate: number;
  drop_off_points: string[];
  time_to_abandon: number;
  return_rate: number;
}

export interface FeatureCorrelation {
  feature1: string;
  feature2: string;
  correlation_coefficient: number;
  usage_pattern: string;
  impact_score: number;
}

export interface ApiMetrics {
  calls: number;
  unique_callers: number;
  success_rate: number;
  average_latency: number;
}

export interface EndpointUsage {
  endpoint: string;
  method: string;
  calls: number;
  unique_callers: number;
  average_latency: number;
  error_rate: number;
}

export interface ResponseTimeDistribution {
  p50: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
  average: number;
  histogram: Record<string, number>;
}

export interface ErrorRateAnalysis {
  overall_rate: number;
  by_status_code: Record<string, number>;
  by_endpoint: Record<string, number>;
  by_time: Record<string, number>;
  trends: TrendDirection;
}

export interface RateLimitingMetrics {
  requests_limited: number;
  unique_clients_limited: number;
  limit_violations: number;
  throttling_effectiveness: number;
}

export interface VersionUsageMetrics {
  version: string;
  usage_percentage: number;
  unique_clients: number;
  deprecation_status: string;
  migration_rate: number;
}

export interface StorageMetrics {
  total_bytes: number;
  used_bytes: number;
  available_bytes: number;
  utilization_percentage: number;
}

export interface EfficiencyMetrics {
  compression_ratio: number;
  deduplication_ratio: number;
  optimization_score: number;
  waste_percentage: number;
}

export interface BackupMetrics {
  backup_frequency: number;
  total_backups: number;
  backup_size: number;
  restore_tests: number;
  success_rate: number;
}

export interface ComplianceMetrics {
  compliance_score: number;
  violations: number;
  frameworks: string[];
  audit_readiness: number;
}

export interface UtilizationMetrics {
  current: number;
  average: number;
  peak: number;
  trend: TrendDirection;
  forecast: number;
}

export interface ScalingMetrics {
  scale_up_events: number;
  scale_down_events: number;
  auto_scaling_efficiency: number;
  manual_interventions: number;
  cost_impact: number;
}

export interface CostOptimizationMetrics {
  current_cost: number;
  optimized_cost: number;
  savings_potential: number;
  recommendations: string[];
  implementation_effort: number;
}

export interface ResourceEfficiencyMetrics {
  cpu_efficiency: number;
  memory_efficiency: number;
  storage_efficiency: number;
  network_efficiency: number;
  overall_score: number;
}

export interface IntegrationMetrics {
  total: number;
  active: number;
  healthy: number;
  failing: number;
  deprecated: number;
}

export interface IntegrationHealthMetrics {
  integrationId: string;
  integration_name: string;
  health_score: number;
  uptime_percentage: number;
  last_sync: string;
  error_rate: number;
}

export interface DataFlowMetrics {
  inbound_volume: number;
  outbound_volume: number;
  processing_rate: number;
  latency: number;
  throughput: number;
}

export interface SyncPerformanceMetrics {
  sync_frequency: number;
  average_duration: number;
  success_rate: number;
  records_processed: number;
  conflict_rate: number;
}

export interface IntegrationErrorMetrics {
  total_errors: number;
  error_rate: number;
  by_type: Record<string, number>;
  by_integration: Record<string, number>;
  resolution_time: number;
}

export interface IntegrationPatternMetrics {
  pattern: string;
  usage_count: number;
  integrations_using: number;
  performance_score: number;
  reliability_score: number;
}

// Enums
export type HealthStatus = 'healthy' | 'at_risk' | 'unhealthy' | 'critical';