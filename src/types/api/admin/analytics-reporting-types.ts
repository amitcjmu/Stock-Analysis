/**
 * Analytics and Reporting API Types
 * 
 * Type definitions for platform analytics, business intelligence reporting,
 * data visualization, and performance metrics analysis.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../shared';

// Platform Analytics APIs
export interface GetPlatformAnalyticsRequest extends BaseApiRequest {
  timeRange?: AnalyticsTimeRange;
  metrics?: string[];
  dimensions?: string[];
  aggregation?: AggregationType;
  includeForecasts?: boolean;
  context: MultiTenantContext;
}

export interface GetPlatformAnalyticsResponse extends BaseApiResponse<PlatformAnalytics> {
  data: PlatformAnalytics;
  usage: UsageAnalytics;
  performance: PerformanceAnalytics;
  adoption: AdoptionAnalytics;
  trends: AnalyticsTrend[];
  forecasts: AnalyticsForecast[];
}

// Report Generation APIs
export interface GenerateAdminReportRequest extends BaseApiRequest {
  reportType: ReportType;
  format: ReportFormat;
  timeRange?: AnalyticsTimeRange;
  filters?: ReportFilter[];
  sections?: string[];
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateAdminReportResponse extends BaseApiResponse<AdminReport> {
  data: AdminReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Supporting Types for Analytics and Reporting
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

export interface PerformanceAnalytics {
  response_times: ResponseTimeAnalytics;
  throughput: ThroughputAnalytics;
  availability: AvailabilityAnalytics;
  errors: ErrorAnalytics;
  capacity: CapacityAnalytics;
  quality: QualityAnalytics;
  efficiency: EfficiencyAnalytics;
  optimization: OptimizationAnalytics;
}

export interface AdoptionAnalytics {
  user_adoption: UserAdoptionAnalytics;
  feature_adoption: FeatureAdoptionAnalytics;
  engagement_adoption: EngagementAdoptionAnalytics;
  onboarding: OnboardingAnalytics;
  retention: RetentionAnalytics;
  churn: ChurnAnalytics;
  growth: GrowthAnalytics;
  satisfaction: SatisfactionAnalytics;
}

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

export interface AdminReport {
  id: string;
  type: ReportType;
  title: string;
  description?: string;
  generated_at: string;
  generated_by: string;
  period: AnalyticsPeriod;
  format: ReportFormat;
  size: number;
  sections: ReportSection[];
  metadata: ReportMetadata;
  customizations: ReportCustomization;
  delivery: ReportDelivery;
}

export interface ReportFilter {
  field: string;
  operator: FilterOperator;
  value: any;
  label?: string;
}

export interface ReportCustomization {
  title?: string;
  subtitle?: string;
  logo?: string;
  branding?: BrandingOptions;
  layout?: LayoutOptions;
  styling?: StylingOptions;
  sections?: SectionCustomization[];
  charts?: ChartCustomization[];
  tables?: TableCustomization[];
}

// Enums and Supporting Types
export type ReportType = 
  | 'usage' 
  | 'performance' 
  | 'security' 
  | 'billing' 
  | 'engagement' 
  | 'user_activity' 
  | 'compliance' 
  | 'health' 
  | 'custom';

export type ReportFormat = 'pdf' | 'html' | 'docx' | 'xlsx' | 'json' | 'csv';

export type AggregationType = 'sum' | 'avg' | 'min' | 'max' | 'count' | 'distinct' | 'percentile';

export type TrendDirection = 'increasing' | 'decreasing' | 'stable' | 'volatile' | 'seasonal';

export type ConfidenceLevel = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';

export type TimePeriod = 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';

export type ForecastType = 'linear' | 'exponential' | 'seasonal' | 'arima' | 'neural_network';

export type FilterOperator = 
  | 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'greater_equal' | 'less_equal'
  | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'in' | 'not_in' | 'between';

// Complex Supporting Interfaces
export interface AnalyticsTimeRange {
  start: string;
  end: string;
  granularity?: TimePeriod;
  timezone?: string;
}

export interface AnalyticsPeriod {
  start: string;
  end: string;
  granularity: TimePeriod;
  total_periods: number;
  current_period: number;
  timezone: string;
}

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

export interface PlatformMetrics {
  business: BusinessMetrics;
  technical: TechnicalMetrics;
  operational: OperationalMetrics;
  financial: FinancialMetrics;
  quality: QualityMetrics;
  security: SecurityMetrics;
}

export interface AnalyticsSegmentation {
  by_tier: Record<string, SegmentMetrics>;
  by_industry: Record<string, SegmentMetrics>;
  by_size: Record<string, SegmentMetrics>;
  by_region: Record<string, SegmentMetrics>;
  by_age: Record<string, SegmentMetrics>;
  custom: Record<string, SegmentMetrics>;
}

export interface PeriodComparison {
  period: string;
  comparison_period: string;
  metrics: ComparisonMetrics;
  changes: MetricChange[];
  significance: StatisticalSignificance;
}

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

export interface AnalyticsMetadata {
  data_sources: DataSource[];
  calculation_method: string;
  quality_score: number;
  completeness: number;
  freshness: string;
  accuracy_estimate: number;
  limitations: string[];
  notes: string[];
}

// Usage Analytics Detailed Types
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

export interface AccountUsageAnalytics {
  total_accounts: AccountMetrics;
  active_accounts: AccountMetrics;
  new_accounts: AccountMetrics;
  account_growth: GrowthMetrics;
  account_health: HealthMetrics;
  subscription_metrics: SubscriptionMetrics;
  revenue_metrics: RevenueMetrics;
}

export interface EngagementUsageAnalytics {
  total_engagements: EngagementMetrics;
  active_engagements: EngagementMetrics;
  completed_engagements: EngagementMetrics;
  engagement_duration: DurationMetrics;
  engagement_success: SuccessMetrics;
  engagement_types: TypeDistribution[];
  engagement_outcomes: OutcomeAnalysis[];
}

export interface FeatureUsageAnalytics {
  feature_adoption: FeatureAdoptionMetrics[];
  feature_engagement: FeatureEngagementMetrics[];
  feature_performance: FeaturePerformanceMetrics[];
  feature_feedback: FeatureFeedbackMetrics[];
  feature_abandonment: FeatureAbandonmentMetrics[];
  feature_correlation: FeatureCorrelation[];
}

export interface ApiUsageAnalytics {
  total_calls: ApiMetrics;
  unique_clients: ApiMetrics;
  endpoint_usage: EndpointUsage[];
  response_times: ResponseTimeDistribution;
  error_rates: ErrorRateAnalysis;
  rate_limiting: RateLimitingMetrics;
  api_versions: VersionUsageMetrics[];
}

export interface StorageUsageAnalytics {
  total_storage: StorageMetrics;
  storage_growth: GrowthMetrics;
  storage_by_type: TypeDistribution[];
  storage_efficiency: EfficiencyMetrics;
  backup_metrics: BackupMetrics;
  retention_compliance: ComplianceMetrics;
}

export interface ComputeUsageAnalytics {
  cpu_utilization: UtilizationMetrics;
  memory_utilization: UtilizationMetrics;
  network_utilization: UtilizationMetrics;
  scaling_events: ScalingMetrics;
  cost_optimization: CostOptimizationMetrics;
  resource_efficiency: ResourceEfficiencyMetrics;
}

export interface IntegrationUsageAnalytics {
  active_integrations: IntegrationMetrics;
  integration_health: IntegrationHealthMetrics[];
  data_flow: DataFlowMetrics;
  sync_performance: SyncPerformanceMetrics;
  error_rates: IntegrationErrorMetrics;
  usage_patterns: IntegrationPatternMetrics[];
}

// Report Structure Types
export interface ReportSection {
  id: string;
  title: string;
  type: SectionType;
  content: SectionContent;
  order: number;
  visible: boolean;
  customizations?: SectionCustomization;
}

export interface ReportMetadata {
  template_id?: string;
  template_version?: string;
  data_sources: DataSource[];
  generation_time: number;
  filters_applied: ReportFilter[];
  permissions: ReportPermission[];
  tags: string[];
}

export interface ReportDelivery {
  method: DeliveryMethod;
  recipients: ReportRecipient[];
  schedule?: DeliverySchedule;
  notifications: DeliveryNotification[];
  history: DeliveryHistory[];
}

export type SectionType = 
  | 'summary' | 'chart' | 'table' | 'text' | 'metric_grid' | 'kpi_dashboard' 
  | 'trend_analysis' | 'comparison' | 'forecast' | 'insights' | 'recommendations';

export type InsightType = 
  | 'anomaly' | 'trend' | 'correlation' | 'prediction' | 'opportunity' | 'risk' | 'optimization';

export type InsightPriority = 'low' | 'medium' | 'high' | 'critical';

export type AlertType = 'threshold' | 'anomaly' | 'trend' | 'forecast' | 'quality' | 'performance';

export type AlertSeverity = 'info' | 'warning' | 'critical' | 'emergency';

export type DeliveryMethod = 'email' | 'download' | 'api' | 'webhook' | 's3' | 'ftp';

// Additional Complex Supporting Types
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

export interface ContributingFactor {
  factor: string;
  impact_score: number;
  confidence: ConfidenceLevel;
  correlation: number;
}

export interface TrendPrediction {
  period: string;
  value: number;
  confidence_interval: ConfidenceInterval;
  probability: number;
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
  hyperparameters: Record<string, any>;
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

export interface ThresholdDefinition {
  operator: ThresholdOperator;
  value: number;
  duration?: string;
  condition?: ThresholdCondition;
}

export interface AlertAction {
  action: string;
  automated: boolean;
  executed_at?: string;
  result?: string;
}

export interface DataSource {
  name: string;
  type: DataSourceType;
  last_updated: string;
  quality_score: number;
  completeness: number;
}

export interface InsightRecommendation {
  action: string;
  priority: RecommendationPriority;
  impact_estimate: ImpactEstimate;
  implementation_guide: string[];
  dependencies: string[];
}

export interface InsightData {
  type: DataVisualizationType;
  data: any;
  metadata: Record<string, any>;
}

// Additional enums and types
export type ChangeDirection = 'increase' | 'decrease' | 'no_change';
export type StatisticalSignificance = 'significant' | 'not_significant' | 'unknown';
export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical';
export type EffortLevel = 'minimal' | 'low' | 'medium' | 'high' | 'very_high';
export type ThresholdOperator = 'greater_than' | 'less_than' | 'equals' | 'not_equals' | 'between';
export type DataSourceType = 'database' | 'api' | 'file' | 'stream' | 'cache' | 'external';
export type DataVisualizationType = 'chart' | 'table' | 'map' | 'gauge' | 'metric' | 'text';

// Supporting metric interfaces would continue here...
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

export interface ThresholdCondition {
  field?: string;
  operator?: FilterOperator;
  value?: any;
}

export interface ModelPerformanceMetric {
  name: string;
  value: number;
  description: string;
}

export interface ImpactEstimate {
  metric: string;
  estimated_change: number;
  confidence: ConfidenceLevel;
  timeframe: string;
}

// Additional detailed metric interfaces - Basic definitions to resolve compilation errors
export interface ResponseTimeAnalytics { averageMs: number; p95Ms: number; p99Ms: number; }
export interface ThroughputAnalytics { requestsPerSecond: number; requestsPerMinute: number; }
export interface AvailabilityAnalytics { uptime: number; downtime: number; percentage: number; }
export interface ErrorAnalytics { errorRate: number; totalErrors: number; errorsByType: Record<string, number>; }
export interface CapacityAnalytics { current: number; maximum: number; utilized: number; }
export interface QualityAnalytics { score: number; defectRate: number; satisfactionScore: number; }
export interface EfficiencyAnalytics { productivity: number; resourceUtilization: number; costEfficiency: number; }
export interface OptimizationAnalytics { suggestions: string[]; potentialSavings: number; implementationEffort: string; }

export interface UserAdoptionAnalytics { adoptionRate: number; timeToAdoption: number; activeUsers: number; }
export interface FeatureAdoptionAnalytics { features: FeatureAdoptionMetrics[]; overallRate: number; }
export interface EngagementAdoptionAnalytics { engagementTypes: string[]; adoptionRates: Record<string, number>; }
export interface OnboardingAnalytics { completionRate: number; averageTime: number; dropoffPoints: string[]; }
export interface RetentionAnalytics { retentionRate: number; churnRate: number; cohortAnalysis: CohortAnalysis[]; }
export interface ChurnAnalytics { rate: number; reasons: string[]; predictiveScore: number; }
export interface GrowthAnalytics { growthRate: number; newUsers: number; expansion: number; }
export interface SatisfactionAnalytics { score: number; nps: number; feedback: string[]; }

export interface BusinessMetrics { revenue: RevenueMetrics; growth: GrowthMetrics; retention: RetentionMetrics; }
export interface TechnicalMetrics { performance: PerformanceMetrics; reliability: ReliabilityMetrics; }
export interface OperationalMetrics { efficiency: EfficiencyAnalytics; capacity: CapacityAnalytics; }
export interface FinancialMetrics { revenue: number; costs: number; profit: number; }
export interface QualityMetrics { score: number; defects: number; satisfaction: number; }
export interface SecurityMetrics { incidents: number; vulnerabilities: number; compliance: number; }

export interface UserMetrics { total: number; active: number; new: number; }
export interface SessionMetrics { total: number; duration: number; bounceRate: number; }
export interface EngagementMetrics { score: number; duration: number; frequency: number; }
export interface CohortAnalysis { cohortId: string; size: number; retention: number[]; }

export interface AccountMetrics { total: number; active: number; new: number; }
export interface HealthMetrics { score: number; status: string; alerts: number; }
export interface SubscriptionMetrics { total: number; active: number; churn: number; }
export interface RevenueMetrics { total: number; recurring: number; growth: number; }

export interface DurationMetrics { average: number; median: number; distribution: Record<string, number>; }
export interface SuccessMetrics { rate: number; criteria: string[]; score: number; }
export interface TypeDistribution { type: string; count: number; percentage: number; }
export interface OutcomeAnalysis { outcomes: string[]; distribution: Record<string, number>; }

export interface FeatureAdoptionMetrics { featureId: string; adoptionRate: number; usage: number; }
export interface FeatureEngagementMetrics { featureId: string; engagement: number; retention: number; }
export interface FeaturePerformanceMetrics { featureId: string; performance: number; errors: number; }
export interface FeatureFeedbackMetrics { featureId: string; satisfaction: number; feedback: string[]; }
export interface FeatureAbandonmentMetrics { featureId: string; abandonmentRate: number; reasons: string[]; }
export interface FeatureCorrelation { feature1: string; feature2: string; correlation: number; }

export interface ApiMetrics { calls: number; errors: number; latency: number; }
export interface EndpointUsage { endpoint: string; calls: number; latency: number; }
export interface ResponseTimeDistribution { percentiles: Record<string, number>; average: number; }
export interface ErrorRateAnalysis { rate: number; types: Record<string, number>; trends: string; }
export interface RateLimitingMetrics { limits: number; violations: number; throttling: number; }
export interface VersionUsageMetrics { version: string; usage: number; percentage: number; }

export interface StorageMetrics { total: number; used: number; available: number; }
export interface EfficiencyMetrics { score: number; optimization: number; waste: number; }
export interface BackupMetrics { frequency: number; size: number; success: number; }
export interface ComplianceMetrics { score: number; violations: number; frameworks: string[]; }

export interface UtilizationMetrics { current: number; average: number; peak: number; }
export interface ScalingMetrics { events: number; efficiency: number; cost: number; }
export interface CostOptimizationMetrics { savings: number; opportunities: string[]; recommendations: string[]; }
export interface ResourceEfficiencyMetrics { utilization: number; waste: number; optimization: number; }

export interface IntegrationMetrics { total: number; active: number; healthy: number; }
export interface IntegrationHealthMetrics { integrationId: string; status: string; uptime: number; }
export interface DataFlowMetrics { volume: number; latency: number; errors: number; }
export interface SyncPerformanceMetrics { frequency: number; duration: number; success: number; }
export interface IntegrationErrorMetrics { errors: number; types: Record<string, number>; resolution: number; }
export interface IntegrationPatternMetrics { pattern: string; usage: number; performance: number; }

// Additional placeholder interfaces
export interface CustomerMetrics { total: number; new: number; churn: number; }
export interface PerformanceMetrics { score: number; latency: number; throughput: number; }
export interface ReliabilityMetrics { uptime: number; mtbf: number; mttr: number; }
export interface ScalabilityMetrics { capacity: number; elasticity: number; efficiency: number; }
export interface SectionContent { type: string; data: any; configuration: Record<string, any>; }
export interface SectionCustomization { styling: Record<string, any>; layout: Record<string, any>; }
export interface BrandingOptions { logo: string; colors: Record<string, string>; fonts: Record<string, string>; }
export interface LayoutOptions { orientation: string; columns: number; spacing: number; }
export interface StylingOptions { theme: string; fonts: Record<string, any>; colors: Record<string, any>; }
export interface ChartCustomization { type: string; styling: Record<string, any>; data: Record<string, any>; }
export interface TableCustomization { columns: string[]; sorting: Record<string, any>; filters: Record<string, any>; }
export interface ReportPermission { userId: string; permissions: string[]; scope: string; }
export interface ReportRecipient { email: string; name: string; type: string; }
export interface DeliverySchedule { frequency: string; time: string; timezone: string; }
export interface DeliveryNotification { enabled: boolean; channels: string[]; recipients: string[]; }
export interface DeliveryHistory { timestamp: string; recipient: string; status: string; }