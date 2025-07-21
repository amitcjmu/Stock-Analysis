/**
 * Performance Analytics Types
 * 
 * Performance metrics and monitoring data structures.
 * 
 * Generated with CC for modular admin type organization.
 */

// Main performance analytics container
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

// Response time analytics
export interface ResponseTimeAnalytics {
  average_ms: number;
  median_ms: number;
  p95_ms: number;
  p99_ms: number;
  min_ms: number;
  max_ms: number;
  distribution: ResponseTimeDistribution;
  by_endpoint: Record<string, EndpointResponseTime>;
  by_operation: Record<string, OperationResponseTime>;
  trends: ResponseTimeTrend[];
}

// Throughput analytics
export interface ThroughputAnalytics {
  requests_per_second: number;
  requests_per_minute: number;
  requests_per_hour: number;
  peak_throughput: number;
  average_throughput: number;
  by_endpoint: Record<string, number>;
  by_method: Record<string, number>;
  capacity_utilization: number;
}

// Availability analytics
export interface AvailabilityAnalytics {
  uptime_percentage: number;
  downtime_minutes: number;
  incidents: AvailabilityIncident[];
  mtbf: number; // Mean Time Between Failures
  mttr: number; // Mean Time To Recovery
  sla_compliance: number;
  by_service: Record<string, ServiceAvailability>;
  by_region: Record<string, RegionAvailability>;
}

// Error analytics
export interface ErrorAnalytics {
  total_errors: number;
  error_rate: number;
  by_type: Record<string, ErrorTypeMetrics>;
  by_status_code: Record<string, number>;
  by_endpoint: Record<string, EndpointErrorMetrics>;
  error_trends: ErrorTrend[];
  top_errors: TopError[];
  resolution_metrics: ResolutionMetrics;
}

// Capacity analytics
export interface CapacityAnalytics {
  current_utilization: number;
  peak_utilization: number;
  available_capacity: number;
  scaling_headroom: number;
  resource_allocation: ResourceAllocation;
  bottlenecks: Bottleneck[];
  capacity_forecast: CapacityForecast;
  optimization_opportunities: OptimizationOpportunity[];
}

// Quality analytics
export interface QualityAnalytics {
  overall_score: number;
  defect_rate: number;
  test_coverage: number;
  code_quality_score: number;
  user_satisfaction_score: number;
  performance_score: number;
  reliability_score: number;
  maintainability_score: number;
  security_score: number;
}

// Efficiency analytics
export interface EfficiencyAnalytics {
  resource_utilization: number;
  cost_per_request: number;
  processing_efficiency: number;
  cache_hit_rate: number;
  query_optimization_score: number;
  waste_percentage: number;
  automation_percentage: number;
  productivity_metrics: ProductivityMetrics;
}

// Optimization analytics
export interface OptimizationAnalytics {
  optimization_score: number;
  implemented_optimizations: Optimization[];
  pending_optimizations: Optimization[];
  estimated_improvements: EstimatedImprovement[];
  cost_savings_potential: number;
  performance_gain_potential: number;
  recommendations: OptimizationRecommendation[];
}

// Adoption analytics
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

// Supporting interfaces
export interface ResponseTimeDistribution {
  buckets: TimeBucket[];
  percentiles: Record<string, number>;
  outliers: number;
}

export interface TimeBucket {
  range: string;
  count: number;
  percentage: number;
}

export interface EndpointResponseTime {
  average: number;
  p95: number;
  p99: number;
  request_count: number;
}

export interface OperationResponseTime {
  operation: string;
  average: number;
  median: number;
  max: number;
  count: number;
}

export interface ResponseTimeTrend {
  timestamp: string;
  average: number;
  p95: number;
  p99: number;
}

export interface AvailabilityIncident {
  start_time: string;
  end_time: string;
  duration_minutes: number;
  impact: ImpactLevel;
  affected_services: string[];
  root_cause: string;
  resolution: string;
}

export interface ServiceAvailability {
  uptime_percentage: number;
  incidents: number;
  total_downtime: number;
  sla_met: boolean;
}

export interface RegionAvailability {
  region: string;
  uptime_percentage: number;
  latency: number;
  health_score: number;
}

export interface ErrorTypeMetrics {
  count: number;
  rate: number;
  trend: TrendDirection;
  impact: ImpactLevel;
  resolution_time: number;
}

export interface EndpointErrorMetrics {
  total_errors: number;
  error_rate: number;
  by_status: Record<string, number>;
  common_errors: string[];
}

export interface ErrorTrend {
  timestamp: string;
  error_count: number;
  error_rate: number;
  by_type: Record<string, number>;
}

export interface TopError {
  error_type: string;
  count: number;
  impact: ImpactLevel;
  affected_users: number;
  first_seen: string;
  last_seen: string;
}

export interface ResolutionMetrics {
  average_time: number;
  median_time: number;
  by_severity: Record<string, number>;
  automation_rate: number;
}

export interface ResourceAllocation {
  cpu: ResourceMetrics;
  memory: ResourceMetrics;
  storage: ResourceMetrics;
  network: ResourceMetrics;
}

export interface ResourceMetrics {
  allocated: number;
  used: number;
  available: number;
  utilization_percentage: number;
}

export interface Bottleneck {
  resource: string;
  severity: SeverityLevel;
  impact: ImpactLevel;
  location: string;
  recommendations: string[];
}

export interface CapacityForecast {
  timeframe: string;
  predicted_usage: number;
  confidence: number;
  scaling_required: boolean;
  recommendations: string[];
}

export interface OptimizationOpportunity {
  area: string;
  potential_improvement: number;
  effort: EffortLevel;
  priority: Priority;
  description: string;
}

export interface ProductivityMetrics {
  tasks_completed: number;
  average_task_time: number;
  automation_ratio: number;
  efficiency_score: number;
}

export interface Optimization {
  id: string;
  type: OptimizationType;
  description: string;
  impact: OptimizationImpact;
  status: OptimizationStatus;
  implemented_at?: string;
}

export interface EstimatedImprovement {
  metric: string;
  current_value: number;
  projected_value: number;
  improvement_percentage: number;
  confidence: number;
}

export interface OptimizationRecommendation {
  title: string;
  description: string;
  category: OptimizationCategory;
  priority: Priority;
  estimated_impact: OptimizationImpact;
  implementation_effort: EffortLevel;
  dependencies: string[];
}

export interface OptimizationImpact {
  performance_gain: number;
  cost_reduction: number;
  reliability_improvement: number;
  user_experience_improvement: number;
}

// User adoption analytics
export interface UserAdoptionAnalytics {
  adoption_rate: number;
  time_to_adoption: number;
  adoption_funnel: AdoptionFunnel;
  by_segment: Record<string, SegmentAdoption>;
  barriers: AdoptionBarrier[];
  accelerators: AdoptionAccelerator[];
}

// Feature adoption analytics
export interface FeatureAdoptionAnalytics {
  overall_adoption: number;
  features: FeatureAdoption[];
  adoption_velocity: number;
  feature_discovery: FeatureDiscovery;
  usage_patterns: UsagePattern[];
}

// Engagement adoption analytics
export interface EngagementAdoptionAnalytics {
  engagement_types: EngagementType[];
  adoption_rates: Record<string, number>;
  engagement_depth: number;
  progression: EngagementProgression;
}

// Onboarding analytics
export interface OnboardingAnalytics {
  completion_rate: number;
  average_time: number;
  drop_off_points: DropOffPoint[];
  success_factors: string[];
  improvement_areas: string[];
}

// Retention analytics
export interface RetentionAnalytics {
  overall_retention: number;
  cohort_retention: CohortRetention[];
  retention_curve: number[];
  churn_risk_segments: ChurnRiskSegment[];
  retention_drivers: string[];
}

// Churn analytics
export interface ChurnAnalytics {
  churn_rate: number;
  churn_reasons: ChurnReason[];
  predictive_score: number;
  at_risk_accounts: number;
  prevention_effectiveness: number;
}

// Growth analytics
export interface GrowthAnalytics {
  growth_rate: number;
  new_users: number;
  expansion_revenue: number;
  viral_coefficient: number;
  growth_channels: GrowthChannel[];
}

// Satisfaction analytics
export interface SatisfactionAnalytics {
  overall_score: number;
  nps_score: number;
  csat_score: number;
  feedback_volume: number;
  sentiment_analysis: SentimentAnalysis;
  improvement_trends: ImprovementTrend[];
}

// Import common types
type ImpactLevel = import('../common').ImpactLevel;
type TrendDirection = import('../common').TrendDirection;
type SeverityLevel = import('../common').Severity;
type EffortLevel = import('../common').EffortLevel;
type Priority = import('../common').Priority;

// Enums
export type OptimizationType = 'performance' | 'cost' | 'reliability' | 'scalability' | 'security';
export type OptimizationStatus = 'identified' | 'planned' | 'in_progress' | 'completed' | 'validated';
export type OptimizationCategory = 'infrastructure' | 'application' | 'database' | 'network' | 'process';

// Additional supporting interfaces
export interface AdoptionFunnel {
  stages: FunnelStage[];
  conversion_rates: number[];
  bottlenecks: string[];
}

export interface FunnelStage {
  name: string;
  users: number;
  conversion_rate: number;
  average_time: number;
}

export interface SegmentAdoption {
  adoption_rate: number;
  active_users: number;
  engagement_score: number;
}

export interface AdoptionBarrier {
  barrier: string;
  impact: ImpactLevel;
  affected_users: number;
  mitigation: string;
}

export interface AdoptionAccelerator {
  factor: string;
  impact: ImpactLevel;
  users_influenced: number;
}

export interface FeatureAdoption {
  feature_id: string;
  feature_name: string;
  adoption_rate: number;
  daily_active_users: number;
  retention_impact: number;
}

export interface FeatureDiscovery {
  discovery_rate: number;
  discovery_sources: Record<string, number>;
  time_to_discovery: number;
}

export interface UsagePattern {
  pattern: string;
  frequency: number;
  user_count: number;
  value_score: number;
}

export interface EngagementType {
  type: string;
  adoption_rate: number;
  frequency: number;
  value: number;
}

export interface EngagementProgression {
  stages: string[];
  progression_rates: number[];
  average_time_between_stages: number[];
}

export interface DropOffPoint {
  step: string;
  drop_off_rate: number;
  reasons: string[];
  improvements: string[];
}

export interface CohortRetention {
  cohort: string;
  size: number;
  retention_curve: number[];
}

export interface ChurnRiskSegment {
  segment: string;
  risk_score: number;
  user_count: number;
  indicators: string[];
}

export interface ChurnReason {
  reason: string;
  frequency: number;
  preventable: boolean;
  prevention_strategy: string;
}

export interface GrowthChannel {
  channel: string;
  contribution: number;
  cac: number; // Customer Acquisition Cost
  ltv: number; // Lifetime Value
  roi: number;
}

export interface SentimentAnalysis {
  positive: number;
  neutral: number;
  negative: number;
  trending_topics: string[];
}

export interface ImprovementTrend {
  metric: string;
  trend: TrendDirection;
  improvement_rate: number;
  factors: string[];
}