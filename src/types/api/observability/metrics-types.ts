/**
 * Metrics Management Types
 * 
 * Type definitions for creating, managing, and querying metrics.
 * Handles metric definitions, data retrieval, and metric analytics.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  CreateRequest,
  CreateResponse,
  MultiTenantContext
} from '../shared';

// Metric Definition Management
export interface CreateMetricDefinitionRequest extends CreateRequest<MetricDefinitionData> {
  flowId: string;
  data: MetricDefinitionData;
  metricType: 'counter' | 'gauge' | 'histogram' | 'summary' | 'distribution';
  source: MetricSource;
  aggregation: AggregationConfig;
  dimensions: MetricDimension[];
  thresholds: DetailedMetricThreshold[];
  alerting: MetricAlerting;
}

export interface CreateMetricDefinitionResponse extends CreateResponse<MetricDefinition> {
  data: MetricDefinition;
  metricId: string;
  validationResults: MetricValidation[];
  estimatedCardinality: number;
  storageRequirements: StorageRequirements;
}

// Metric Data Retrieval
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

// Metric Querying
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

// Supporting Types
export interface MetricDefinitionData {
  name: string;
  description?: string;
  unit: string;
  namespace: string;
  help: string;
  labels: Record<string, string>;
  metadata: Record<string, string | number | boolean | null>;
}

export interface MetricSource {
  type: 'prometheus' | 'influxdb' | 'cloudwatch' | 'datadog' | 'custom';
  endpoint: string;
  credentials?: SourceCredentials;
  configuration: SourceConfiguration;
  healthCheck: HealthCheckConfig;
}

export interface AggregationConfig {
  functions: AggregationFunction[];
  groupBy: string[];
  having?: HavingCondition[];
  window: WindowConfig;
  fillPolicy: FillPolicy;
}

export interface MetricDimension {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'timestamp';
  cardinality: 'low' | 'medium' | 'high';
  indexed: boolean;
  required: boolean;
  validation?: DimensionValidation;
}

export interface DetailedMetricThreshold {
  id: string;
  name: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'between' | 'outside';
  value: number | number[];
  severity: 'info' | 'warning' | 'minor' | 'major' | 'critical' | 'blocker';
  duration: string;
  hysteresis?: number;
  enabled: boolean;
}

export interface MetricAlerting {
  enabled: boolean;
  rules: AlertRule[];
  notifications: AlertNotification[];
  suppression: AlertSuppressionConfig;
  escalation: AlertEscalationConfig;
}

export interface MetricDefinition {
  id: string;
  metricId: string;
  name: string;
  description?: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary' | 'distribution';
  unit: string;
  namespace: string;
  source: MetricSource;
  aggregation: AggregationConfig;
  dimensions: MetricDimension[];
  thresholds: DetailedMetricThreshold[];
  alerting: MetricAlerting;
  status: 'active' | 'inactive' | 'deprecated';
  createdAt: string;
  updatedAt: string;
  lastCollected?: string;
}

export interface MetricValidation {
  rule: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  suggestion?: string;
}

export interface StorageRequirements {
  estimatedSize: number;
  unit: 'bytes' | 'kb' | 'mb' | 'gb' | 'tb';
  retention: string;
  compression: number;
  indexSize: number;
}

export interface MetricData {
  timestamp: string;
  value: number;
  dimensions: Record<string, string>;
  quality: DataQuality;
}

export interface MetricMetadata {
  metricId: string;
  name: string;
  unit: string;
  type: string;
  sampleCount: number;
  timeRange: {
    start: string;
    end: string;
  };
  resolution: string;
  completeness: number;
}

export interface MetricTrend {
  metric: string;
  direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  slope: number;
  confidence: number;
  timeframe: string;
  significance: 'low' | 'medium' | 'high';
}

export interface MetricAnomaly {
  id: string;
  metricId: string;
  timestamp: string;
  actualValue: number;
  expectedValue: number;
  deviation: number;
  severity: 'low' | 'medium' | 'high';
  type: 'spike' | 'dip' | 'drift' | 'outlier';
  confidence: number;
  context: AnomalyContext;
}

export interface MetricFilter {
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'regex' | 'exists';
  value: unknown;
  caseSensitive?: boolean;
}

export interface MetricQueryResult {
  resultType: 'matrix' | 'vector' | 'scalar' | 'string';
  result: QueryResultData;
  stats: QueryStats;
  explanation?: QueryExplanation;
}

// Additional supporting interfaces
export interface SourceCredentials {
  type: 'basic' | 'bearer' | 'apikey' | 'oauth' | 'certificate';
  username?: string;
  password?: string;
  token?: string;
  apiKey?: string;
  certificate?: string;
  privateKey?: string;
}

export interface SourceConfiguration {
  timeout: string;
  retries: number;
  rateLimit: RateLimit;
  batchSize: number;
  compression: boolean;
  ssl: SSLConfig;
}

export interface HealthCheckConfig {
  enabled: boolean;
  interval: string;
  timeout: string;
  retries: number;
  endpoint?: string;
}

export interface AggregationFunction {
  name: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'stddev' | 'percentile' | 'rate' | 'increase';
  parameters?: Record<string, string | number | boolean | null>;
  alias?: string;
}

export interface HavingCondition {
  function: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq';
  value: number;
}

export interface WindowConfig {
  size: string;
  step?: string;
  offset?: string;
  type: 'tumbling' | 'sliding' | 'session';
}

export interface FillPolicy {
  strategy: 'null' | 'zero' | 'previous' | 'interpolate' | 'default';
  value?: number;
}

export interface DimensionValidation {
  pattern?: string;
  minLength?: number;
  maxLength?: number;
  allowedValues?: string[];
  required: boolean;
}

export interface AlertRule {
  id: string;
  name: string;
  expression: string;
  duration: string;
  annotations: Record<string, string>;
  labels: Record<string, string>;
  enabled: boolean;
}

export interface AlertNotification {
  id: string;
  channel: 'email' | 'sms' | 'webhook' | 'slack' | 'teams';
  target: string;
  template: string;
  conditions: NotificationCondition[];
  enabled: boolean;
}

export interface AlertSuppressionConfig {
  enabled: boolean;
  rules: SuppressionRule[];
  maxDuration: string;
}

export interface AlertEscalationConfig {
  enabled: boolean;
  levels: EscalationLevel[];
  timeout: string;
}

export interface DataQuality {
  score: number;
  issues: QualityIssue[];
  completeness: number;
  accuracy: number;
  timeliness: number;
}

export interface AnomalyContext {
  relatedMetrics: string[];
  correlations: Correlation[];
  seasonality: SeasonalityInfo;
  events: ContextEvent[];
}

export interface QueryResultData {
  matrix?: MatrixResult[];
  vector?: VectorResult[];
  scalar?: ScalarResult;
  string?: string;
}

export interface QueryStats {
  samplesProcessed: number;
  executionTime: number;
  peakMemoryUsage: number;
  seriesReturned: number;
}

export interface QueryExplanation {
  steps: ExplanationStep[];
  optimizations: string[];
  performance: PerformanceHints;
}

export interface RateLimit {
  requests: number;
  period: string;
  burst?: number;
}

export interface SSLConfig {
  enabled: boolean;
  verify: boolean;
  caFile?: string;
  certFile?: string;
  keyFile?: string;
}

export interface NotificationCondition {
  field: string;
  operator: string;
  value: unknown;
}

export interface SuppressionRule {
  id: string;
  pattern: string;
  duration: string;
  reason: string;
}

export interface EscalationLevel {
  level: number;
  delay: string;
  targets: string[];
}

export interface QualityIssue {
  type: 'missing' | 'invalid' | 'stale' | 'duplicate';
  description: string;
  count: number;
  percentage: number;
}

export interface Correlation {
  metric: string;
  coefficient: number;
  pValue: number;
  significance: 'low' | 'medium' | 'high';
}

export interface SeasonalityInfo {
  detected: boolean;
  period: string;
  strength: number;
  confidence: number;
}

export interface ContextEvent {
  timestamp: string;
  type: 'deployment' | 'incident' | 'maintenance' | 'traffic_spike';
  description: string;
  impact: 'low' | 'medium' | 'high';
}

export interface MatrixResult {
  metric: Record<string, string>;
  values: Array<[number, string]>;
}

export interface VectorResult {
  metric: Record<string, string>;
  value: [number, string];
}

export interface ScalarResult {
  value: [number, string];
}

export interface ExplanationStep {
  operation: string;
  description: string;
  timeMs: number;
  samples: number;
}

export interface PerformanceHints {
  suggestions: string[];
  bottlenecks: string[];
  optimizations: string[];
}