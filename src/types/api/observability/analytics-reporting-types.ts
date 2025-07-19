/**
 * Analytics and Reporting Types
 * 
 * Type definitions for performance analysis, SLA reporting, capacity planning,
 * and generating observability analytics reports and insights.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  CreateRequest,
  CreateResponse,
  MultiTenantContext
} from '../shared';
import { TimeRange } from './core-types';

// Performance Analysis
export interface AnalyzePerformanceRequest extends BaseApiRequest {
  flowId: string;
  analysisType: 'latency' | 'throughput' | 'errors' | 'capacity' | 'bottlenecks';
  timeRange: {
    start: string;
    end: string;
  };
  scope: PerformanceScope;
  metrics: PerformanceMetric[];
  thresholds: PerformanceThreshold[];
  context: MultiTenantContext;
}

export interface AnalyzePerformanceResponse extends BaseApiResponse<PerformanceAnalysis> {
  data: PerformanceAnalysis;
  analysisId: string;
  findings: PerformanceFinding[];
  recommendations: PerformanceRecommendation[];
  bottlenecks: PerformanceBottleneck[];
  trends: PerformanceTrend[];
}

// SLA Reporting
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

// Capacity Planning
export interface CreateCapacityPlanRequest extends CreateRequest<CapacityPlanData> {
  flowId: string;
  data: CapacityPlanData;
  planningHorizon: 'week' | 'month' | 'quarter' | 'year';
  growthProjections: GrowthProjection[];
  constraints: CapacityConstraint[];
  scenarios: CapacityScenario[];
  includeRecommendations?: boolean;
}

export interface CreateCapacityPlanResponse extends CreateResponse<CapacityPlan> {
  data: CapacityPlan;
  planId: string;
  projections: CapacityProjection[];
  recommendations: CapacityRecommendation[];
  riskAssessment: CapacityRisk[];
}

// Observability Analytics
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

// Report Generation
export interface GenerateObservabilityReportRequest extends BaseApiRequest {
  flowId: string;
  reportType: 'health' | 'performance' | 'availability' | 'capacity' | 'incident';
  format: 'pdf' | 'html' | 'docx' | 'json';
  timeRange?: {
    start: string;
    end: string;
  };
  sections?: string[];
  includeCharts?: boolean;
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateObservabilityReportResponse extends BaseApiResponse<ObservabilityReport> {
  data: ObservabilityReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Supporting Types
export interface PerformanceScope {
  services: string[];
  environments: string[];
  regions: string[];
  userSegments: string[];
  businessProcesses: string[];
  timeZones: string[];
}

export interface PerformanceMetric {
  name: string;
  type: 'latency' | 'throughput' | 'error_rate' | 'availability' | 'utilization';
  aggregation: 'avg' | 'p50' | 'p95' | 'p99' | 'max' | 'min' | 'sum';
  unit: string;
  target?: number;
  threshold?: number;
}

export interface PerformanceThreshold {
  metric: string;
  warning: number;
  critical: number;
  unit: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte';
}

export interface PerformanceAnalysis {
  id: string;
  analysisType: 'latency' | 'throughput' | 'errors' | 'capacity' | 'bottlenecks';
  timeRange: {
    start: string;
    end: string;
  };
  scope: PerformanceScope;
  summary: PerformanceAnalysisSummary;
  metrics: AnalyzedMetric[];
  correlations: PerformanceCorrelation[];
  patterns: PerformancePattern[];
  baseline: PerformanceBaseline;
  createdAt: string;
}

export interface PerformanceFinding {
  id: string;
  type: 'bottleneck' | 'anomaly' | 'trend' | 'threshold_breach' | 'correlation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: FindingImpact;
  evidence: FindingEvidence[];
  affectedComponents: string[];
  timeframe: string;
  confidence: number;
}

export interface PerformanceRecommendation {
  id: string;
  type: 'optimization' | 'scaling' | 'configuration' | 'architecture' | 'monitoring';
  title: string;
  description: string;
  rationale: string;
  impact: RecommendationImpact;
  effort: 'low' | 'medium' | 'high';
  priority: number;
  implementationSteps: ImplementationStep[];
  estimatedBenefit: EstimatedBenefit;
  risks: RecommendationRisk[];
}

export interface PerformanceBottleneck {
  id: string;
  component: string;
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'database' | 'application' | 'external';
  severity: 'low' | 'medium' | 'high' | 'critical';
  metric: string;
  currentValue: number;
  threshold: number;
  impact: BottleneckImpact;
  duration: string;
  frequency: 'rare' | 'occasional' | 'frequent' | 'constant';
  rootCause: RootCauseAnalysis;
}

export interface PerformanceTrend {
  metric: string;
  direction: 'improving' | 'degrading' | 'stable' | 'volatile';
  rate: number;
  confidence: number;
  timeframe: string;
  seasonality: SeasonalityInfo;
  forecast: TrendForecast;
  significance: 'low' | 'medium' | 'high';
}

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

export interface CapacityPlanData {
  name: string;
  description?: string;
  horizon: 'week' | 'month' | 'quarter' | 'year';
  baselineDate: string;
  resources: ResourceType[];
  objectives: CapacityObjective[];
  assumptions: PlanningAssumption[];
  metadata: Record<string, any>;
}

export interface GrowthProjection {
  resource: string;
  currentCapacity: number;
  projectedGrowthRate: number;
  seasonality: SeasonalityPattern[];
  businessDrivers: BusinessDriver[];
  confidence: number;
}

export interface CapacityConstraint {
  id: string;
  type: 'budget' | 'technical' | 'operational' | 'regulatory' | 'business';
  description: string;
  impact: ConstraintImpact;
  workarounds: string[];
  timeline: string;
}

export interface CapacityScenario {
  id: string;
  name: string;
  description: string;
  probability: number;
  growthMultiplier: number;
  assumptions: ScenarioAssumption[];
  impact: ScenarioImpact;
}

export interface CapacityPlan {
  id: string;
  planId: string;
  name: string;
  description?: string;
  flowId: string;
  horizon: 'week' | 'month' | 'quarter' | 'year';
  baselineDate: string;
  status: 'draft' | 'active' | 'archived' | 'superseded';
  summary: CapacityPlanSummary;
  projections: CapacityProjection[];
  recommendations: CapacityRecommendation[];
  scenarios: CapacityScenarioResult[];
  riskAssessment: CapacityRisk[];
  createdAt: string;
  updatedAt: string;
}

export interface CapacityProjection {
  resource: string;
  currentUsage: number;
  currentCapacity: number;
  projectedUsage: ProjectedUsage[];
  requiredCapacity: RequiredCapacity[];
  utilizationForecast: UtilizationForecast[];
  bottleneckPrediction: BottleneckPrediction[];
}

export interface CapacityRecommendation {
  id: string;
  type: 'scaling' | 'optimization' | 'migration' | 'procurement' | 'architectural';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  resource: string;
  timeline: string;
  cost: RecommendationCost;
  benefits: RecommendationBenefit[];
  risks: CapacityRecommendationRisk[];
  dependencies: string[];
}

export interface CapacityRisk {
  id: string;
  type: 'capacity_shortage' | 'over_provisioning' | 'budget_overrun' | 'technical_debt' | 'vendor_dependency';
  severity: 'low' | 'medium' | 'high' | 'critical';
  probability: number;
  impact: RiskImpact;
  timeframe: string;
  mitigation: RiskMitigation[];
  indicators: RiskIndicator[];
}

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

export interface ObservabilityReport {
  id: string;
  reportId: string;
  type: 'health' | 'performance' | 'availability' | 'capacity' | 'incident';
  format: 'pdf' | 'html' | 'docx' | 'json';
  title: string;
  summary: ReportSummary;
  sections: ReportSection[];
  metadata: ReportMetadata;
  generatedAt: string;
  generatedBy: string;
}

export interface ReportCustomization {
  template: string;
  theme: 'light' | 'dark' | 'corporate' | 'minimal';
  branding: BrandingConfig;
  sections: SectionCustomization[];
  charts: ChartCustomization[];
  formatting: FormattingConfig;
}

// Additional supporting interfaces
export interface PerformanceAnalysisSummary {
  overallScore: number;
  criticalIssues: number;
  optimizationOpportunities: number;
  baseline: PerformanceBaseline;
  keyFindings: string[];
}

export interface AnalyzedMetric {
  name: string;
  values: MetricValue[];
  statistics: MetricStatistics;
  thresholds: ThresholdAnalysis;
  trends: MetricTrend;
  anomalies: MetricAnomaly[];
}

export interface PerformanceCorrelation {
  metrics: string[];
  coefficient: number;
  pValue: number;
  strength: 'weak' | 'moderate' | 'strong';
  significance: boolean;
  causality: CausalityAnalysis;
}

export interface PerformancePattern {
  id: string;
  type: 'periodic' | 'trending' | 'threshold' | 'burst' | 'gradual';
  description: string;
  metrics: string[];
  frequency: string;
  confidence: number;
  firstObserved: string;
  lastObserved: string;
}

export interface PerformanceBaseline {
  period: string;
  metrics: BaselineMetric[];
  conditions: BaselineCondition[];
  confidence: number;
  validFrom: string;
  validTo: string;
}

export interface FindingImpact {
  scope: 'service' | 'system' | 'business' | 'user';
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedUsers: number;
  businessImpact: BusinessImpact;
  technicalImpact: TechnicalImpact;
}

export interface FindingEvidence {
  type: 'metric' | 'log' | 'trace' | 'event' | 'alert';
  source: string;
  value: any;
  timestamp: string;
  confidence: number;
}

export interface RecommendationImpact {
  performance: ImpactMeasure;
  availability: ImpactMeasure;
  cost: ImpactMeasure;
  complexity: ImpactMeasure;
  risk: ImpactMeasure;
}

export interface ImplementationStep {
  order: number;
  title: string;
  description: string;
  estimatedTime: string;
  resources: string[];
  dependencies: string[];
  risks: string[];
}

export interface EstimatedBenefit {
  performance: BenefitMeasure;
  availability: BenefitMeasure;
  cost: BenefitMeasure;
  timeframe: string;
  confidence: number;
}

export interface RecommendationRisk {
  type: 'implementation' | 'operational' | 'business' | 'technical';
  description: string;
  probability: number;
  impact: 'low' | 'medium' | 'high';
  mitigation: string[];
}

export interface BottleneckImpact {
  responseTime: number;
  throughput: number;
  userExperience: 'minimal' | 'moderate' | 'significant' | 'severe';
  businessImpact: 'low' | 'medium' | 'high' | 'critical';
  cascadeEffects: string[];
}

export interface RootCauseAnalysis {
  primaryCause: string;
  contributingFactors: string[];
  evidence: CauseEvidence[];
  confidence: number;
  investigationMethod: string;
}

export interface SeasonalityInfo {
  detected: boolean;
  period: string;
  strength: number;
  peaks: string[];
  valleys: string[];
}

export interface TrendForecast {
  nextPeriod: number;
  confidence: number;
  upperBound: number;
  lowerBound: number;
  assumptions: string[];
}

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

// Additional complex supporting types would continue here...
// This represents a comprehensive but focused subset for brevity

export interface ProjectedUsage {
  period: string;
  usage: number;
  confidence: number;
  factors: UsageFactor[];
}

export interface RequiredCapacity {
  period: string;
  capacity: number;
  buffer: number;
  reasoning: string;
}

export interface UtilizationForecast {
  period: string;
  utilization: number;
  status: 'healthy' | 'warning' | 'critical';
  threshold: number;
}

export interface BottleneckPrediction {
  period: string;
  probability: number;
  type: 'capacity' | 'performance' | 'throughput';
  severity: 'low' | 'medium' | 'high';
}

export interface MetricValue {
  timestamp: string;
  value: number;
  quality: 'high' | 'medium' | 'low';
}

export interface MetricStatistics {
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  p95: number;
  p99: number;
  stdDev: number;
}

export interface ObservabilityForecast {
  value: number;
  confidence: number;
  upperBound: number;
  lowerBound: number;
  timeframe: string;
}

export interface ComponentHealthScore {
  component: string;
  score: number;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  issues: string[];
  lastCheck: string;
}

// Missing supporting types
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

export interface ResourceType {
  name: string;
  type: 'compute' | 'storage' | 'network' | 'database' | 'application';
  unit: string;
  cost: number;
  scalability: 'manual' | 'automatic' | 'elastic';
}

export interface CapacityObjective {
  id: string;
  metric: string;
  target: number;
  threshold: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface PlanningAssumption {
  id: string;
  type: 'growth' | 'technology' | 'business' | 'external';
  description: string;
  confidence: number;
  impact: string;
}

export interface SeasonalityPattern {
  pattern: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  multiplier: number;
  confidence: number;
  description: string;
}

export interface BusinessDriver {
  name: string;
  type: 'user_growth' | 'feature_release' | 'marketing_campaign' | 'seasonal';
  impact: number;
  timeframe: string;
  confidence: number;
}

export interface ConstraintImpact {
  type: 'blocking' | 'limiting' | 'delaying' | 'increasing_cost';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affectedResources: string[];
}

export interface ScenarioAssumption {
  id: string;
  description: string;
  parameter: string;
  value: any;
  confidence: number;
}

export interface ScenarioImpact {
  resources: Record<string, number>;
  timeline: string;
  cost: number;
  risk: 'low' | 'medium' | 'high';
}

export interface CapacityPlanSummary {
  totalResources: number;
  projectedGrowth: number;
  recommendedActions: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  budgetImpact: number;
}

export interface CapacityScenarioResult {
  scenarioId: string;
  name: string;
  probability: number;
  projections: CapacityProjection[];
  recommendations: string[];
  risk: 'low' | 'medium' | 'high';
}

export interface RecommendationCost {
  implementation: number;
  operational: number;
  maintenance: number;
  total: number;
  currency: string;
  timeframe: string;
}

export interface RecommendationBenefit {
  type: 'cost_savings' | 'performance_improvement' | 'risk_reduction' | 'efficiency_gain';
  description: string;
  quantified: boolean;
  value: number;
  unit: string;
  timeframe: string;
}

export interface CapacityRecommendationRisk {
  type: 'implementation' | 'operational' | 'financial' | 'technical';
  description: string;
  probability: number;
  impact: 'low' | 'medium' | 'high';
  mitigation: string[];
}

export interface RiskImpact {
  operational: 'low' | 'medium' | 'high' | 'critical';
  financial: number;
  reputation: 'minimal' | 'moderate' | 'significant' | 'severe';
  compliance: boolean;
  timeframe: string;
}

export interface RiskMitigation {
  id: string;
  strategy: 'avoid' | 'reduce' | 'transfer' | 'accept';
  actions: string[];
  cost: number;
  effectiveness: number;
  timeline: string;
}

export interface RiskIndicator {
  metric: string;
  threshold: number;
  current: number;
  trend: 'improving' | 'degrading' | 'stable';
  alerting: boolean;
}

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
  value: any;
  confidence: number;
  timestamp: string;
}

export interface AnomalyContext {
  related: string[];
  contributing: string[];
  environmental: Record<string, any>;
  temporal: string;
}

export interface AnomalyImpact {
  severity: 'low' | 'medium' | 'high' | 'critical';
  scope: string[];
  duration: string;
  userImpact: number;
  businessImpact: string;
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

export interface ReportSummary {
  executiveSummary: string;
  keyFindings: string[];
  recommendations: string[];
  metrics: ReportMetric[];
  trends: string[];
}

export interface ReportSection {
  id: string;
  title: string;
  content: string;
  charts: ReportChart[];
  tables: ReportTable[];
  insights: string[];
}

export interface ReportMetadata {
  version: string;
  template: string;
  dataSource: string;
  timeRange: TimeRange;
  generationTime: number;
  accuracy: number;
  limitations: string[];
}

export interface BrandingConfig {
  logo: string;
  colors: ColorScheme;
  fonts: FontScheme;
  header: string;
  footer: string;
}

export interface SectionCustomization {
  sectionId: string;
  title?: string;
  include: boolean;
  order: number;
  customContent?: string;
}

export interface ChartCustomization {
  chartId: string;
  type: string;
  title?: string;
  colors?: string[];
  size?: ChartSize;
}

export interface FormattingConfig {
  dateFormat: string;
  numberFormat: string;
  currency: string;
  timezone: string;
  locale: string;
}

export interface ReportMetric {
  name: string;
  value: number;
  unit: string;
  change: number;
  status: 'good' | 'warning' | 'critical';
}

export interface ReportChart {
  id: string;
  type: string;
  title: string;
  data: any;
  config: ChartConfig;
}

export interface ReportTable {
  id: string;
  title: string;
  headers: string[];
  rows: any[][];
  formatting?: TableFormatting;
}

export interface ColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
}

export interface FontScheme {
  heading: string;
  body: string;
  monospace: string;
  sizes: FontSizes;
}

export interface ChartSize {
  width: number;
  height: number;
}

export interface ChartConfig {
  theme: string;
  responsive: boolean;
  legend: boolean;
  grid: boolean;
  animation: boolean;
}

export interface TableFormatting {
  striped: boolean;
  bordered: boolean;
  hover: boolean;
  compact: boolean;
  sortable: boolean;
}

export interface FontSizes {
  small: number;
  medium: number;
  large: number;
  xlarge: number;
}

// Additional types from other modules that were referenced
export interface ProjectedUsage {
  period: string;
  usage: number;
  confidence: number;
  factors: UsageFactor[];
}

export interface RequiredCapacity {
  period: string;
  capacity: number;
  buffer: number;
  reasoning: string;
}

export interface UtilizationForecast {
  period: string;
  utilization: number;
  status: 'healthy' | 'warning' | 'critical';
  threshold: number;
}

export interface BottleneckPrediction {
  period: string;
  probability: number;
  type: 'capacity' | 'performance' | 'throughput';
  severity: 'low' | 'medium' | 'high';
}

export interface UsageFactor {
  name: string;
  impact: number;
  confidence: number;
  type: 'business' | 'technical' | 'seasonal';
}

export interface BaselineMetric {
  name: string;
  value: number;
  unit: string;
  confidence: number;
  conditions: string[];
}

export interface BaselineCondition {
  parameter: string;
  value: any;
  tolerance: number;
  critical: boolean;
}

export interface BusinessImpact {
  revenue: number;
  customers: number;
  reputation: 'minimal' | 'moderate' | 'significant' | 'severe';
  compliance: boolean;
}

export interface TechnicalImpact {
  performance: number;
  availability: number;
  security: 'low' | 'medium' | 'high' | 'critical';
  scalability: 'minimal' | 'moderate' | 'significant' | 'severe';
}

export interface ImpactMeasure {
  current: number;
  projected: number;
  improvement: number;
  confidence: number;
  unit: string;
}

export interface BenefitMeasure {
  quantified: boolean;
  value: number;
  unit: string;
  description: string;
  confidence: number;
}

export interface CauseEvidence {
  type: 'metric' | 'log' | 'trace' | 'event';
  source: string;
  evidence: string;
  weight: number;
  timestamp: string;
}

export interface TrendData {
  timestamp: string;
  value: number;
  trend: 'up' | 'down' | 'stable';
}

export interface SeasonalPattern {
  pattern: 'daily' | 'weekly' | 'monthly' | 'yearly';
  amplitude: number;
  phase: number;
  confidence: number;
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

export interface PredictionFactor {
  name: string;
  weight: number;
  direction: 'positive' | 'negative' | 'neutral';
  confidence: number;
}

export interface MetricTrend {
  direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  rate: number;
  confidence: number;
  significance: 'low' | 'medium' | 'high';
}

export interface MetricAnomaly {
  timestamp: string;
  value: number;
  expected: number;
  deviation: number;
  type: 'spike' | 'dip' | 'drift';
  confidence: number;
}

export interface ThresholdAnalysis {
  breaches: number;
  nearMisses: number;
  worstBreach: number;
  averageBreach: number;
  breachDuration: string;
}

export interface MetricStatistics {
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  p95: number;
  p99: number;
  stdDev: number;
}

export interface CausalityAnalysis {
  causal: boolean;
  direction: 'x_causes_y' | 'y_causes_x' | 'bidirectional' | 'spurious';
  confidence: number;
  lagTime: string;
  strength: 'weak' | 'moderate' | 'strong';
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