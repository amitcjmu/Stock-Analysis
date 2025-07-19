/**
 * Distributed Tracing Types
 * 
 * Type definitions for configuring distributed tracing, managing traces and spans,
 * and performing trace analysis for service dependency mapping and performance monitoring.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  CreateRequest,
  CreateResponse,
  GetRequest,
  GetResponse,
  MultiTenantContext
} from '../shared';

// Tracing Configuration
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

// Trace Retrieval
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

// Trace Search
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

// Service Map
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

// Supporting Types
export interface TracingConfigurationData {
  name: string;
  description?: string;
  environment: string;
  version: string;
  settings: TracingSettings;
  tags: Record<string, string>;
  metadata: Record<string, any>;
}

export interface InstrumentationConfig {
  automatic: AutoInstrumentationConfig;
  manual: ManualInstrumentationConfig;
  libraries: InstrumentationLibrary[];
  frameworks: FrameworkConfig[];
  customInstrumentation: CustomInstrumentation[];
}

export interface SamplingConfig {
  strategy: 'head' | 'tail' | 'probabilistic' | 'rate_limiting' | 'adaptive';
  rate: number;
  maxTracesPerSecond?: number;
  rules: SamplingRule[];
  configuration: SamplingConfiguration;
}

export interface TraceCollectionConfig {
  receivers: TraceReceiver[];
  processors: TraceProcessor[];
  exporters: TraceExporter[];
  pipelines: TracePipeline[];
  reliability: TraceReliabilityConfig;
}

export interface TraceStorageConfig {
  backend: 'jaeger' | 'zipkin' | 'tempo' | 'elasticsearch' | 'clickhouse' | 'bigquery';
  configuration: TraceStorageConfiguration;
  retention: TraceRetentionPolicy;
  indexing: TraceIndexingConfig;
  compression: TraceCompressionConfig;
}

export interface TraceAnalysisConfig {
  enabled: boolean;
  realtime: boolean;
  batchProcessing: BatchProcessingConfig;
  anomalyDetection: AnomalyDetectionConfig;
  performance: PerformanceAnalysisConfig;
  dependencies: DependencyAnalysisConfig;
}

export interface TracingConfiguration {
  id: string;
  configurationId: string;
  name: string;
  description?: string;
  type: 'distributed' | 'application' | 'infrastructure' | 'business';
  environment: string;
  version: string;
  instrumentation: InstrumentationConfig;
  sampling: SamplingConfig;
  collection: TraceCollectionConfig;
  storage: TraceStorageConfig;
  analysis: TraceAnalysisConfig;
  status: 'draft' | 'validated' | 'deployed' | 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
  deployedAt?: string;
}

export interface InstrumentationPlan {
  phases: InstrumentationPhase[];
  dependencies: string[];
  rollout: RolloutStrategy;
  validation: ValidationStrategy;
  monitoring: InstrumentationMonitoring;
}

export interface PerformanceOverhead {
  cpu: number;
  memory: number;
  network: number;
  latency: number;
  throughputImpact: number;
  storageOverhead: number;
}

export interface TraceVolumeEstimate {
  tracesPerSecond: number;
  spansPerTrace: number;
  averageTraceSize: number;
  dailyVolume: number;
  monthlyVolume: number;
  storageRequirements: TraceStorageRequirements;
}

export interface Trace {
  traceId: string;
  spanCount: number;
  duration: number;
  startTime: string;
  endTime: string;
  rootService: string;
  rootOperation: string;
  services: string[];
  tags: Record<string, any>;
  processes: Record<string, TraceProcess>;
  warnings: string[];
  errors: TraceError[];
}

export interface Span {
  spanId: string;
  traceId: string;
  parentSpanId?: string;
  operationName: string;
  service: string;
  startTime: string;
  duration: number;
  tags: Record<string, any>;
  logs: SpanLog[];
  references: SpanReference[];
  status: SpanStatus;
  kind: SpanKind;
  attributes: Record<string, any>;
  events: SpanEvent[];
  links: SpanLink[];
}

export interface TraceMetrics {
  duration: number;
  spanCount: number;
  errorRate: number;
  serviceCount: number;
  criticalPath: CriticalPathMetrics;
  bottlenecks: BottleneckMetrics[];
  performance: TracePerformanceMetrics;
}

export interface TraceLog {
  timestamp: string;
  level: 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  message: string;
  spanId: string;
  service: string;
  fields: Record<string, any>;
}

export interface TraceAnalysis {
  summary: TraceAnalysisSummary;
  criticalPath: CriticalPath;
  performance: PerformanceAnalysis;
  errors: ErrorAnalysis;
  dependencies: DependencyAnalysis;
  recommendations: TraceRecommendation[];
}

export interface TraceSearchResult {
  query?: string;
  totalTraces: number;
  took: number;
  maxScore: number;
}

export interface TraceSummary {
  traceId: string;
  duration: number;
  spanCount: number;
  startTime: string;
  rootService: string;
  rootOperation: string;
  errorCount: number;
  services: string[];
  tags: Record<string, any>;
  score?: number;
}

export interface TraceStatistics {
  totalTraces: number;
  averageDuration: number;
  errorRate: number;
  serviceBreakdown: ServiceBreakdown[];
  operationBreakdown: OperationBreakdown[];
  durationDistribution: DurationDistribution[];
}

export interface ServiceMap {
  services: ServiceNode[];
  dependencies: ServiceDependency[];
  metadata: ServiceMapMetadata;
}

export interface ServiceNode {
  id: string;
  name: string;
  type: 'service' | 'database' | 'cache' | 'queue' | 'external';
  version?: string;
  environment: string;
  namespace?: string;
  cluster?: string;
  tags: Record<string, string>;
  metadata: ServiceNodeMetadata;
}

export interface ServiceDependency {
  from: string;
  to: string;
  type: 'http' | 'grpc' | 'database' | 'message_queue' | 'cache' | 'file_system';
  protocol?: string;
  weight: number;
  metrics: DependencyMetrics;
  health: DependencyHealth;
}

export interface ServiceMetrics {
  serviceId: string;
  requestRate: number;
  errorRate: number;
  averageDuration: number;
  p50Duration: number;
  p95Duration: number;
  p99Duration: number;
  throughput: number;
  availability: number;
}

export interface ServiceHealth {
  serviceId: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  score: number;
  issues: HealthIssue[];
  lastCheck: string;
  uptime: number;
}

// Additional supporting interfaces
export interface TracingSettings {
  enableProfiling: boolean;
  enableMetrics: boolean;
  enableLogging: boolean;
  resourceDetection: boolean;
  propagators: string[];
  maxAttributeLength: number;
  maxEventCount: number;
  maxLinkCount: number;
}

export interface AutoInstrumentationConfig {
  enabled: boolean;
  languages: string[];
  frameworks: string[];
  libraries: string[];
  configuration: Record<string, any>;
}

export interface ManualInstrumentationConfig {
  enabled: boolean;
  sdks: SDKConfig[];
  customSpans: CustomSpanConfig[];
  propagation: PropagationConfig;
}

export interface InstrumentationLibrary {
  name: string;
  version: string;
  language: string;
  framework?: string;
  configuration: Record<string, any>;
  enabled: boolean;
}

export interface FrameworkConfig {
  name: string;
  version: string;
  instrumentation: Record<string, any>;
  filters: InstrumentationFilter[];
  customization: FrameworkCustomization;
}

export interface CustomInstrumentation {
  id: string;
  name: string;
  type: 'span' | 'metric' | 'log' | 'event';
  trigger: InstrumentationTrigger;
  configuration: Record<string, any>;
  enabled: boolean;
}

export interface SamplingRule {
  id: string;
  name: string;
  priority: number;
  conditions: SamplingCondition[];
  action: SamplingAction;
  enabled: boolean;
}

export interface SamplingConfiguration {
  parentBased: boolean;
  traceIdRatioBasedRate?: number;
  maxTracesPerSecond?: number;
  adaptiveConfig?: AdaptiveSamplingConfig;
}

export interface TraceReceiver {
  type: 'jaeger' | 'zipkin' | 'otlp' | 'opencensus' | 'custom';
  protocol: string;
  endpoint: string;
  configuration: ReceiverConfiguration;
  authentication?: ReceiverAuthentication;
}

export interface TraceProcessor {
  type: 'batch' | 'memory_limiter' | 'resource' | 'span' | 'probabilistic_sampler';
  configuration: ProcessorConfiguration;
  order: number;
}

export interface TraceExporter {
  type: 'jaeger' | 'zipkin' | 'otlp' | 'logging' | 'file' | 'prometheus';
  configuration: ExporterConfiguration;
  authentication?: ExporterAuthentication;
  batching?: ExporterBatching;
}

export interface TracePipeline {
  name: string;
  receivers: string[];
  processors: string[];
  exporters: string[];
  configuration: PipelineConfiguration;
}

export interface TraceReliabilityConfig {
  retries: number;
  timeout: string;
  backoff: BackoffConfiguration;
  circuitBreaker: CircuitBreakerConfig;
  deadLetterQueue: boolean;
}

export interface TraceStorageConfiguration {
  hosts: string[];
  authentication?: StorageAuthentication;
  connection: StorageConnectionConfig;
  performance: StoragePerformanceConfig;
  backup: StorageBackupConfig;
}

export interface TraceRetentionPolicy {
  hotStorage: string;
  warmStorage: string;
  coldStorage: string;
  deletion: string;
  archival?: TraceArchivalConfig;
}

export interface TraceIndexingConfig {
  strategy: 'service' | 'operation' | 'tag' | 'time' | 'composite';
  fields: IndexedField[];
  optimization: IndexOptimization;
  maintenance: IndexMaintenance;
}

export interface TraceCompressionConfig {
  enabled: boolean;
  algorithm: 'gzip' | 'lz4' | 'snappy' | 'zstd';
  level: number;
  threshold: number;
}

export interface BatchProcessingConfig {
  enabled: boolean;
  batchSize: number;
  interval: string;
  parallelism: number;
  timeout: string;
}

export interface AnomalyDetectionConfig {
  enabled: boolean;
  algorithms: string[];
  sensitivity: 'low' | 'medium' | 'high';
  baseline: BaselineConfig;
  alerting: AnomalyAlertingConfig;
}

export interface PerformanceAnalysisConfig {
  enabled: boolean;
  metrics: string[];
  thresholds: PerformanceThreshold[];
  trending: TrendingConfig;
  benchmarking: BenchmarkingConfig;
}

export interface DependencyAnalysisConfig {
  enabled: boolean;
  mapping: DependencyMappingConfig;
  health: DependencyHealthConfig;
  impact: ImpactAnalysisConfig;
}

export interface TraceProcess {
  serviceName: string;
  tags: Record<string, any>;
}

export interface TraceError {
  spanId: string;
  message: string;
  type: string;
  stack?: string;
  tags: Record<string, any>;
}

export type SpanStatus = 'ok' | 'error' | 'timeout' | 'cancelled';
export type SpanKind = 'internal' | 'server' | 'client' | 'producer' | 'consumer';

export interface SpanLog {
  timestamp: string;
  fields: Record<string, any>;
}

export interface SpanReference {
  type: 'child_of' | 'follows_from';
  traceId: string;
  spanId: string;
}

export interface SpanEvent {
  name: string;
  timestamp: string;
  attributes: Record<string, any>;
}

export interface SpanLink {
  traceId: string;
  spanId: string;
  traceState?: string;
  attributes: Record<string, any>;
}

export interface CriticalPathMetrics {
  duration: number;
  spans: string[];
  bottlenecks: string[];
  parallelization: number;
}

export interface BottleneckMetrics {
  spanId: string;
  service: string;
  operation: string;
  duration: number;
  percentage: number;
  type: 'cpu' | 'io' | 'network' | 'database' | 'external';
}

export interface TracePerformanceMetrics {
  totalDuration: number;
  networkTime: number;
  processingTime: number;
  waitTime: number;
  concurrency: number;
  efficiency: number;
}

export interface TraceAnalysisSummary {
  traceId: string;
  overallHealth: 'healthy' | 'warning' | 'critical';
  performanceScore: number;
  errorCount: number;
  bottleneckCount: number;
  anomalies: number;
}

export interface CriticalPath {
  spans: CriticalPathSpan[];
  totalDuration: number;
  bottlenecks: CriticalPathBottleneck[];
  optimizationOpportunities: OptimizationOpportunity[];
}

export interface ErrorAnalysis {
  totalErrors: number;
  errorRate: number;
  errorsByService: Record<string, number>;
  errorsByType: Record<string, number>;
  topErrors: TopTraceError[];
}

export interface DependencyAnalysis {
  serviceMap: ServiceDependencyMap;
  criticalPaths: DependencyCriticalPath[];
  failures: DependencyFailure[];
  recommendations: DependencyRecommendation[];
}

export interface TraceRecommendation {
  id: string;
  type: 'performance' | 'reliability' | 'cost' | 'observability';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  priority: number;
}

export interface ServiceBreakdown {
  service: string;
  count: number;
  percentage: number;
  averageDuration: number;
  errorRate: number;
}

export interface OperationBreakdown {
  operation: string;
  service: string;
  count: number;
  percentage: number;
  averageDuration: number;
  errorRate: number;
}

export interface DurationDistribution {
  bucket: string;
  count: number;
  percentage: number;
}

export interface ServiceMapMetadata {
  totalServices: number;
  totalDependencies: number;
  lastUpdated: string;
  coverage: number;
  healthScore: number;
}

export interface ServiceNodeMetadata {
  instances: number;
  version: string;
  deployment: string;
  lastSeen: string;
  metrics: ServiceNodeMetrics;
}

export interface DependencyMetrics {
  requestRate: number;
  errorRate: number;
  averageLatency: number;
  p99Latency: number;
  availability: number;
}

export interface DependencyHealth {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  score: number;
  issues: DependencyIssue[];
  lastCheck: string;
}

export interface HealthIssue {
  type: 'latency' | 'errors' | 'availability' | 'throughput';
  severity: 'low' | 'medium' | 'high';
  description: string;
  threshold: number;
  actual: number;
}

// Additional complex supporting types would continue here...
// This represents a comprehensive but focused subset for brevity

export interface TraceStorageRequirements {
  dailyStorage: number;
  monthlyStorage: number;
  retentionStorage: number;
  indexStorage: number;
  totalStorage: number;
  unit: string;
}

export interface CriticalPathSpan {
  spanId: string;
  service: string;
  operation: string;
  duration: number;
  startTime: string;
  critical: boolean;
}

export interface CriticalPathBottleneck {
  spanId: string;
  service: string;
  operation: string;
  bottleneckType: string;
  impact: number;
  recommendation: string;
}

export interface OptimizationOpportunity {
  type: 'parallelization' | 'caching' | 'optimization' | 'elimination';
  description: string;
  estimatedGain: number;
  effort: 'low' | 'medium' | 'high';
}

export interface TopTraceError {
  message: string;
  count: number;
  services: string[];
  operations: string[];
  lastOccurrence: string;
}

export interface ServiceDependencyMap {
  nodes: ServiceMapNode[];
  edges: ServiceMapEdge[];
  clusters: ServiceCluster[];
}

export interface DependencyCriticalPath {
  path: string[];
  duration: number;
  bottlenecks: string[];
  risk: 'low' | 'medium' | 'high';
}

export interface DependencyFailure {
  from: string;
  to: string;
  type: string;
  frequency: number;
  impact: 'low' | 'medium' | 'high';
  lastOccurrence: string;
}

export interface DependencyRecommendation {
  type: 'redundancy' | 'circuit_breaker' | 'retry' | 'timeout' | 'fallback';
  description: string;
  services: string[];
  priority: number;
}

export interface ServiceNodeMetrics {
  requestRate: number;
  errorRate: number;
  responseTime: number;
  throughput: number;
  cpuUsage: number;
  memoryUsage: number;
}

export interface DependencyIssue {
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  firstDetected: string;
  lastDetected: string;
}

export interface ServiceMapNode {
  id: string;
  name: string;
  type: string;
  metadata: Record<string, any>;
}

export interface ServiceMapEdge {
  from: string;
  to: string;
  weight: number;
  metadata: Record<string, any>;
}

export interface ServiceCluster {
  id: string;
  name: string;
  services: string[];
  type: string;
}