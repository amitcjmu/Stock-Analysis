/**
 * Observability API Types
 * 
 * Type definitions for Observability flow API endpoints, requests, and responses.
 * Covers monitoring, alerting, metrics, logging, tracing, and performance analysis.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse
} from './shared';

// Observability Flow Management APIs
export interface InitializeObservabilityFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  observabilityScope: ObservabilityScope;
  monitoringStrategy: MonitoringStrategy;
  objectives: ObservabilityObjective[];
  requirements: ObservabilityRequirement[];
  parentFlowId?: string;
  configuration?: ObservabilityFlowConfiguration;
  metadata?: Record<string, any>;
}

export interface InitializeObservabilityFlowResponse extends BaseApiResponse<ObservabilityFlowData> {
  data: ObservabilityFlowData;
  flowId: string;
  initialState: ObservabilityState;
  monitoringPlan: MonitoringPlan;
  recommendations: ObservabilityRecommendation[];
  baselineMetrics: BaselineMetrics;
}

export interface GetObservabilityFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeMetrics?: boolean;
  includeAlerts?: boolean;
  includeDashboards?: boolean;
  includeHealth?: boolean;
  includePerformance?: boolean;
}

export interface GetObservabilityFlowStatusResponse extends BaseApiResponse<ObservabilityStatusDetail> {
  data: ObservabilityStatusDetail;
  metrics: ObservabilityMetrics;
  alerts: Alert[];
  dashboards: Dashboard[];
  healthStatus: HealthStatus;
  performance: PerformanceMetrics;
}

export interface ListObservabilityFlowsRequest extends ListRequest {
  observabilityTypes?: string[];
  status?: ObservabilityStatus[];
  monitoringLevels?: string[];
  healthStates?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'last_monitored' | 'last_alert';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListObservabilityFlowsResponse extends ListResponse<ObservabilityFlowSummary> {
  data: ObservabilityFlowSummary[];
  aggregations?: ObservabilityAggregation[];
  trends?: ObservabilityTrend[];
  healthOverview?: HealthOverview;
}

// Monitoring Setup APIs
export interface CreateMonitoringConfigurationRequest extends CreateRequest<MonitoringConfigurationData> {
  flowId: string;
  data: MonitoringConfigurationData;
  monitoringType: 'infrastructure' | 'application' | 'business' | 'security' | 'user_experience';
  targets: MonitoringTarget[];
  metrics: MetricConfiguration[];
  collection: DataCollectionConfig;
  retention: RetentionPolicy;
  alerting: AlertingConfiguration;
}

export interface CreateMonitoringConfigurationResponse extends CreateResponse<MonitoringConfiguration> {
  data: MonitoringConfiguration;
  configurationId: string;
  deploymentPlan: MonitoringDeploymentPlan;
  validationResults: ConfigurationValidation[];
  estimatedCost: MonitoringCost;
}

export interface GetMonitoringConfigurationRequest extends GetRequest {
  configurationId: string;
  includeTargets?: boolean;
  includeMetrics?: boolean;
  includeAlerting?: boolean;
  includeStatus?: boolean;
  includeHealth?: boolean;
}

export interface GetMonitoringConfigurationResponse extends GetResponse<MonitoringConfiguration> {
  data: MonitoringConfiguration;
  targets: MonitoringTargetStatus[];
  metrics: MetricStatus[];
  alerting: AlertingStatus;
  health: MonitoringHealth;
}

export interface DeployMonitoringRequest extends BaseApiRequest {
  configurationId: string;
  deploymentStrategy: 'immediate' | 'phased' | 'canary' | 'blue_green';
  environments: string[];
  rollbackOnFailure?: boolean;
  validationEnabled?: boolean;
  context: MultiTenantContext;
}

export interface DeployMonitoringResponse extends BaseApiResponse<MonitoringDeployment> {
  data: MonitoringDeployment;
  deploymentId: string;
  status: DeploymentStatus;
  deploymentPlan: DeploymentPlan;
  monitoringEnabled: boolean;
}

// Metrics Management APIs
export interface CreateMetricDefinitionRequest extends CreateRequest<MetricDefinitionData> {
  flowId: string;
  data: MetricDefinitionData;
  metricType: 'counter' | 'gauge' | 'histogram' | 'summary' | 'distribution';
  source: MetricSource;
  aggregation: AggregationConfig;
  dimensions: MetricDimension[];
  thresholds: MetricThreshold[];
  alerting: MetricAlerting;
}

export interface CreateMetricDefinitionResponse extends CreateResponse<MetricDefinition> {
  data: MetricDefinition;
  metricId: string;
  validationResults: MetricValidation[];
  estimatedCardinality: number;
  storageRequirements: StorageRequirements;
}

export interface GetMetricDataRequest extends BaseApiRequest {
  metricId?: string;
  metricName?: string;
  timeRange: {
    start: string;
    end: string;
  };
  granularity: 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month';
  aggregation?: 'avg' | 'sum' | 'min' | 'max' | 'count' | 'p50' | 'p95' | 'p99';
  dimensions?: Record<string, string>;
  filters?: MetricFilter[];
  context: MultiTenantContext;
}

export interface GetMetricDataResponse extends BaseApiResponse<MetricData[]> {
  data: MetricData[];
  metadata: MetricMetadata;
  aggregatedValue?: number;
  trends: MetricTrend[];
  anomalies: MetricAnomaly[];
}

export interface QueryMetricsRequest extends BaseApiRequest {
  query: string;
  timeRange: {
    start: string;
    end: string;
  };
  step?: string;
  timeout?: number;
  maxSamples?: number;
  context: MultiTenantContext;
}

export interface QueryMetricsResponse extends BaseApiResponse<MetricQueryResult> {
  data: MetricQueryResult;
  queryId: string;
  executionTime: number;
  resultType: 'matrix' | 'vector' | 'scalar' | 'string';
  warnings?: string[];
}

// Alerting APIs
export interface CreateAlertRuleRequest extends CreateRequest<AlertRuleData> {
  flowId: string;
  data: AlertRuleData;
  ruleType: 'threshold' | 'anomaly' | 'pattern' | 'composite' | 'forecast';
  conditions: AlertCondition[];
  severity: AlertSeverity;
  notifications: NotificationChannel[];
  actions: AlertAction[];
  suppression: AlertSuppression;
}

export interface CreateAlertRuleResponse extends CreateResponse<AlertRule> {
  data: AlertRule;
  ruleId: string;
  validationResults: AlertRuleValidation[];
  testResults: AlertTestResult[];
  estimatedFrequency: number;
}

export interface GetAlertsRequest extends ListRequest {
  flowId?: string;
  ruleIds?: string[];
  severities?: AlertSeverity[];
  statuses?: AlertStatus[];
  timeRange?: {
    start: string;
    end: string;
  };
  acknowledged?: boolean;
  resolved?: boolean;
}

export interface GetAlertsResponse extends ListResponse<Alert> {
  data: Alert[];
  statistics: AlertStatistics;
  trends: AlertTrend[];
  topAlerts: TopAlert[];
}

export interface AcknowledgeAlertRequest extends BaseApiRequest {
  alertId: string;
  acknowledgedBy: string;
  notes?: string;
  escalate?: boolean;
  context: MultiTenantContext;
}

export interface AcknowledgeAlertResponse extends BaseApiResponse<AlertAcknowledgment> {
  data: AlertAcknowledgment;
  acknowledgedAt: string;
  escalated: boolean;
  notifications: AlertNotification[];
}

export interface ResolveAlertRequest extends BaseApiRequest {
  alertId: string;
  resolvedBy: string;
  resolution: AlertResolution;
  preventRecurrence?: boolean;
  context: MultiTenantContext;
}

export interface ResolveAlertResponse extends BaseApiResponse<AlertResolution> {
  data: AlertResolution;
  resolvedAt: string;
  preventionMeasures: PreventionMeasure[];
  learnings: AlertLearning[];
}

// Dashboard Management APIs
export interface CreateDashboardRequest extends CreateRequest<DashboardData> {
  flowId: string;
  data: DashboardData;
  dashboardType: 'operational' | 'executive' | 'technical' | 'business' | 'custom';
  widgets: WidgetConfiguration[];
  layout: DashboardLayout;
  sharing: SharingConfiguration;
  refresh: RefreshConfiguration;
}

export interface CreateDashboardResponse extends CreateResponse<Dashboard> {
  data: Dashboard;
  dashboardId: string;
  validationResults: DashboardValidation[];
  previewUrl: string;
  estimatedLoadTime: number;
}

export interface GetDashboardRequest extends GetRequest {
  dashboardId: string;
  includeData?: boolean;
  includeMetadata?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
  refresh?: boolean;
}

export interface GetDashboardResponse extends GetResponse<Dashboard> {
  data: Dashboard;
  widgetData: WidgetData[];
  metadata: DashboardMetadata;
  lastRefreshed: string;
}

export interface UpdateDashboardRequest extends UpdateRequest<Partial<DashboardData>> {
  dashboardId: string;
  data: Partial<DashboardData>;
  updateType: 'layout' | 'widgets' | 'settings' | 'sharing';
  validateChanges?: boolean;
}

export interface UpdateDashboardResponse extends UpdateResponse<Dashboard> {
  data: Dashboard;
  validationResults: DashboardValidation[];
  changeImpact: DashboardChangeImpact;
}

// Logging APIs
export interface ConfigureLoggingRequest extends CreateRequest<LoggingConfigurationData> {
  flowId: string;
  data: LoggingConfigurationData;
  logSources: LogSource[];
  collection: LogCollectionConfig;
  processing: LogProcessingConfig;
  storage: LogStorageConfig;
  retention: LogRetentionPolicy;
  forwarding: LogForwardingConfig;
}

export interface ConfigureLoggingResponse extends CreateResponse<LoggingConfiguration> {
  data: LoggingConfiguration;
  configurationId: string;
  deploymentPlan: LoggingDeploymentPlan;
  estimatedVolume: LogVolumeEstimate;
  estimatedCost: LoggingCost;
}

export interface SearchLogsRequest extends BaseApiRequest {
  flowId?: string;
  query: string;
  timeRange: {
    start: string;
    end: string;
  };
  logLevel?: LogLevel[];
  sources?: string[];
  limit?: number;
  offset?: number;
  highlight?: boolean;
  context: MultiTenantContext;
}

export interface SearchLogsResponse extends BaseApiResponse<LogSearchResult> {
  data: LogSearchResult;
  searchId: string;
  totalHits: number;
  logs: LogEntry[];
  aggregations: LogAggregation[];
  highlights: LogHighlight[];
}

export interface GetLogAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  timeRange: {
    start: string;
    end: string;
  };
  analysisType: 'patterns' | 'anomalies' | 'trends' | 'errors' | 'performance';
  logLevel?: LogLevel[];
  sources?: string[];
  groupBy?: string[];
  context: MultiTenantContext;
}

export interface GetLogAnalyticsResponse extends BaseApiResponse<LogAnalytics> {
  data: LogAnalytics;
  patterns: LogPattern[];
  anomalies: LogAnomaly[];
  trends: LogTrend[];
  insights: LogInsight[];
}

// Tracing APIs
export interface ConfigureTracingRequest extends CreateRequest<TracingConfigurationData> {
  flowId: string;
  data: TracingConfigurationData;
  tracingType: 'distributed' | 'application' | 'infrastructure' | 'business';
  instrumentation: InstrumentationConfig;
  sampling: SamplingConfig;
  collection: TraceCollectionConfig;
  storage: TraceStorageConfig;
  analysis: TraceAnalysisConfig;
}

export interface ConfigureTracingResponse extends CreateResponse<TracingConfiguration> {
  data: TracingConfiguration;
  configurationId: string;
  instrumentationPlan: InstrumentationPlan;
  estimatedOverhead: PerformanceOverhead;
  estimatedVolume: TraceVolumeEstimate;
}

export interface GetTraceRequest extends GetRequest {
  traceId: string;
  includeSpans?: boolean;
  includeMetrics?: boolean;
  includeLogs?: boolean;
  includeAnalysis?: boolean;
}

export interface GetTraceResponse extends GetResponse<Trace> {
  data: Trace;
  spans: Span[];
  metrics: TraceMetrics;
  logs: TraceLog[];
  analysis: TraceAnalysis;
}

export interface SearchTracesRequest extends BaseApiRequest {
  flowId?: string;
  query?: string;
  timeRange: {
    start: string;
    end: string;
  };
  services?: string[];
  operations?: string[];
  minDuration?: number;
  maxDuration?: number;
  tags?: Record<string, string>;
  limit?: number;
  context: MultiTenantContext;
}

export interface SearchTracesResponse extends BaseApiResponse<TraceSearchResult> {
  data: TraceSearchResult;
  searchId: string;
  totalTraces: number;
  traces: TraceSummary[];
  statistics: TraceStatistics;
}

export interface GetServiceMapRequest extends BaseApiRequest {
  flowId?: string;
  timeRange: {
    start: string;
    end: string;
  };
  services?: string[];
  includeMetrics?: boolean;
  includeHealth?: boolean;
  includeDependencies?: boolean;
  context: MultiTenantContext;
}

export interface GetServiceMapResponse extends BaseApiResponse<ServiceMap> {
  data: ServiceMap;
  services: ServiceNode[];
  dependencies: ServiceDependency[];
  metrics: ServiceMetrics[];
  healthStatus: ServiceHealth[];
}

// Performance Analysis APIs
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

// Observability Analytics and Reporting APIs
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

// Supporting Data Types
export interface ObservabilityFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  observabilityType: string;
  status: ObservabilityStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  scope: ObservabilityScope;
  strategy: MonitoringStrategy;
  objectives: ObservabilityObjective[];
  requirements: ObservabilityRequirement[];
  progress: number;
  phases: ObservabilityPhases;
  currentPhase: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  metadata: Record<string, any>;
}

export interface ObservabilityScope {
  applications: string[];
  services: string[];
  infrastructure: string[];
  environments: string[];
  regions: string[];
  namespaces: string[];
  userJourneys: string[];
  businessProcesses: string[];
  technologies: string[];
  dataflows: string[];
}

export interface MonitoringStrategy {
  approach: 'reactive' | 'proactive' | 'predictive' | 'intelligent';
  coverage: 'basic' | 'standard' | 'comprehensive' | 'full_stack';
  automation: 'manual' | 'semi_automated' | 'fully_automated';
  sampling: 'none' | 'statistical' | 'intelligent' | 'adaptive';
  retention: 'short_term' | 'medium_term' | 'long_term' | 'archive';
  integration: 'standalone' | 'federated' | 'unified' | 'centralized';
}

export type ObservabilityStatus = 
  | 'planning' | 'configuration' | 'deployment' | 'calibration'
  | 'monitoring' | 'optimization' | 'maintenance' | 'scaling'
  | 'completed' | 'paused' | 'failed' | 'deprecated';

export type AlertSeverity = 'info' | 'warning' | 'minor' | 'major' | 'critical' | 'blocker';
export type AlertStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'closed';
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type DeploymentStatus = 'pending' | 'deploying' | 'validating' | 'active' | 'failed' | 'rolled_back';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)