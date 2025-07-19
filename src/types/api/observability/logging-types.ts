/**
 * Logging Configuration and Analytics Types
 * 
 * Type definitions for configuring logging systems, searching logs,
 * and performing log analytics for observability monitoring.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  CreateRequest,
  CreateResponse,
  MultiTenantContext
} from '../shared';

// Logging Configuration
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

// Log Search
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

// Log Analytics
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

// Supporting Types
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export interface LoggingConfigurationData {
  name: string;
  description?: string;
  environment: string;
  version: string;
  settings: LoggingSettings;
  tags: Record<string, string>;
  metadata: Record<string, any>;
}

export interface LogSource {
  id: string;
  name: string;
  type: 'application' | 'system' | 'infrastructure' | 'security' | 'audit' | 'custom';
  source: string;
  format: LogFormat;
  parser: LogParser;
  filters: LogFilter[];
  enrichment: LogEnrichment;
  sampling: LogSampling;
  enabled: boolean;
}

export interface LogCollectionConfig {
  agents: CollectionAgent[];
  protocols: CollectionProtocol[];
  buffering: BufferingConfig;
  compression: CompressionConfig;
  encryption: EncryptionConfig;
  batching: BatchingConfig;
  reliability: ReliabilityConfig;
}

export interface LogProcessingConfig {
  pipelines: ProcessingPipeline[];
  parsers: ParserConfig[];
  transformations: TransformationConfig[];
  enrichment: EnrichmentConfig[];
  validation: ValidationConfig;
  errorHandling: ErrorHandlingConfig;
}

export interface LogStorageConfig {
  backend: 'elasticsearch' | 'opensearch' | 'clickhouse' | 'loki' | 'bigquery' | 's3';
  configuration: StorageConfiguration;
  indexing: IndexingConfig;
  sharding: ShardingConfig;
  replication: ReplicationConfig;
  compression: StorageCompressionConfig;
}

export interface LogRetentionPolicy {
  hotStorage: string;
  warmStorage: string;
  coldStorage: string;
  deletion: string;
  archival: ArchivalConfig;
  compliance: ComplianceConfig;
}

export interface LogForwardingConfig {
  enabled: boolean;
  destinations: ForwardingDestination[];
  filtering: ForwardingFilter[];
  batching: ForwardingBatching;
  errorHandling: ForwardingErrorHandling;
}

export interface LoggingConfiguration {
  id: string;
  configurationId: string;
  name: string;
  description?: string;
  environment: string;
  version: string;
  sources: LogSource[];
  collection: LogCollectionConfig;
  processing: LogProcessingConfig;
  storage: LogStorageConfig;
  retention: LogRetentionPolicy;
  forwarding: LogForwardingConfig;
  status: 'draft' | 'validated' | 'deployed' | 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
  deployedAt?: string;
}

export interface LoggingDeploymentPlan {
  phases: DeploymentPhase[];
  dependencies: string[];
  validations: ValidationCheck[];
  rollback: RollbackStrategy;
  monitoring: DeploymentMonitoring;
}

export interface LogVolumeEstimate {
  dailyVolume: number;
  monthlyVolume: number;
  peakVolumePerHour: number;
  averageEventSize: number;
  compressionRatio: number;
  storageRequirements: StorageRequirements;
}

export interface LoggingCost {
  ingestion: number;
  storage: number;
  processing: number;
  transfer: number;
  total: number;
  currency: string;
  breakdown: CostBreakdown[];
}

export interface LogSearchResult {
  query: string;
  totalHits: number;
  took: number;
  timedOut: boolean;
  maxScore: number;
  searchAfter?: any[];
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  fields: Record<string, any>;
  tags: Record<string, string>;
  score?: number;
  highlight?: Record<string, string[]>;
}

export interface LogAggregation {
  name: string;
  type: 'terms' | 'date_histogram' | 'range' | 'stats' | 'cardinality';
  buckets: AggregationBucket[];
  value?: number;
}

export interface LogHighlight {
  field: string;
  fragments: string[];
}

export interface LogAnalytics {
  summary: LogSummary;
  distribution: LogDistribution;
  topSources: TopSource[];
  errorAnalysis: ErrorAnalysis;
  performanceMetrics: LogPerformanceMetrics;
}

export interface LogPattern {
  id: string;
  pattern: string;
  template: string;
  frequency: number;
  examples: string[];
  fields: PatternField[];
  confidence: number;
  firstSeen: string;
  lastSeen: string;
}

export interface LogAnomaly {
  id: string;
  type: 'volume' | 'pattern' | 'field' | 'timing' | 'sequence';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  startTime: string;
  endTime?: string;
  affectedLogs: number;
  baseline: AnomalyBaseline;
  deviation: AnomalyDeviation;
  context: AnomalyContext;
}

export interface LogTrend {
  metric: string;
  period: string;
  direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  rate: number;
  significance: 'low' | 'medium' | 'high';
  forecast: TrendForecast;
}

export interface LogInsight {
  id: string;
  type: 'optimization' | 'anomaly' | 'pattern' | 'correlation' | 'recommendation';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  confidence: number;
  actionable: boolean;
  suggestions: string[];
  evidence: InsightEvidence[];
}

// Additional supporting interfaces
export interface LoggingSettings {
  structured: boolean;
  jsonFormat: boolean;
  timestampFormat: string;
  timezone: string;
  includeStackTrace: boolean;
  maskSensitiveData: boolean;
  samplingEnabled: boolean;
}

export interface LogFormat {
  type: 'json' | 'text' | 'syslog' | 'apache' | 'nginx' | 'custom';
  pattern?: string;
  multiline?: MultilineConfig;
  delimiter?: string;
  escape?: string;
  quote?: string;
}

export interface LogParser {
  type: 'grok' | 'json' | 'regex' | 'csv' | 'xml' | 'kv' | 'custom';
  configuration: ParserConfiguration;
  fieldMapping: FieldMapping[];
  typeConversion: TypeConversion[];
  errorHandling: ParserErrorHandling;
}

export interface LogFilter {
  type: 'include' | 'exclude' | 'transform' | 'route';
  condition: FilterCondition;
  action: FilterAction;
  priority: number;
  enabled: boolean;
}

export interface LogEnrichment {
  enabled: boolean;
  geoLocation: boolean;
  userAgent: boolean;
  dns: boolean;
  customFields: CustomField[];
  lookups: LookupConfig[];
}

export interface LogSampling {
  enabled: boolean;
  rate: number;
  strategy: 'random' | 'deterministic' | 'adaptive' | 'rate_limit';
  preserveErrors: boolean;
  configuration: SamplingConfiguration;
}

export interface CollectionAgent {
  type: 'filebeat' | 'fluentd' | 'logstash' | 'vector' | 'custom';
  version: string;
  configuration: AgentConfiguration;
  resources: ResourceRequirements;
  deployment: AgentDeployment;
}

export interface CollectionProtocol {
  type: 'syslog' | 'http' | 'tcp' | 'udp' | 'grpc' | 'kafka';
  port: number;
  ssl: boolean;
  authentication: ProtocolAuthentication;
  rateLimiting: ProtocolRateLimit;
}

export interface BufferingConfig {
  enabled: boolean;
  type: 'memory' | 'disk' | 'hybrid';
  size: string;
  flushInterval: string;
  maxEvents: number;
  persistOnShutdown: boolean;
}

export interface CompressionConfig {
  enabled: boolean;
  algorithm: 'gzip' | 'lz4' | 'snappy' | 'zstd';
  level: number;
}

export interface EncryptionConfig {
  enabled: boolean;
  algorithm: 'aes256' | 'chacha20';
  keyRotation: string;
  keyManagement: KeyManagementConfig;
}

export interface BatchingConfig {
  enabled: boolean;
  size: number;
  timeout: string;
  maxSize: string;
  compression: boolean;
}

export interface ReliabilityConfig {
  acknowledgments: boolean;
  retries: number;
  backoff: BackoffConfig;
  deadLetterQueue: boolean;
  monitoring: ReliabilityMonitoring;
}

export interface ProcessingPipeline {
  id: string;
  name: string;
  stages: PipelineStage[];
  errorHandling: PipelineErrorHandling;
  monitoring: PipelineMonitoring;
  parallelism: number;
}

export interface ParserConfig {
  name: string;
  type: string;
  configuration: Record<string, any>;
  fieldMappings: Record<string, string>;
  performance: ParserPerformance;
}

export interface TransformationConfig {
  type: 'add_field' | 'remove_field' | 'rename_field' | 'convert_type' | 'extract' | 'replace';
  configuration: Record<string, any>;
  conditions: TransformationCondition[];
}

export interface EnrichmentConfig {
  type: 'geo' | 'dns' | 'user_agent' | 'database' | 'api' | 'file';
  source: string;
  mapping: EnrichmentMapping;
  caching: EnrichmentCaching;
  failureHandling: EnrichmentFailureHandling;
}

export interface ValidationConfig {
  enabled: boolean;
  rules: ValidationRule[];
  onFailure: 'drop' | 'tag' | 'route';
  strictMode: boolean;
}

export interface ErrorHandlingConfig {
  strategy: 'drop' | 'retry' | 'dead_letter' | 'fallback';
  maxRetries: number;
  retryDelay: string;
  deadLetterIndex: string;
  alerting: ErrorAlertingConfig;
}

export interface StorageConfiguration {
  hosts: string[];
  authentication: StorageAuthentication;
  connection: StorageConnection;
  performance: StoragePerformance;
}

export interface IndexingConfig {
  strategy: 'time_based' | 'size_based' | 'custom';
  pattern: string;
  rollover: RolloverConfig;
  aliases: IndexAlias[];
  mappings: IndexMapping;
}

export interface ShardingConfig {
  numberOfShards: number;
  numberOfReplicas: number;
  routingField?: string;
  allocationRules: AllocationRule[];
}

export interface ReplicationConfig {
  enabled: boolean;
  factor: number;
  crossRegion: boolean;
  consistency: 'one' | 'quorum' | 'all';
}

export interface StorageCompressionConfig {
  enabled: boolean;
  codec: 'lz4' | 'best_compression' | 'default';
  level: number;
}

export interface ArchivalConfig {
  enabled: boolean;
  destination: 's3' | 'glacier' | 'azure' | 'gcs';
  configuration: ArchivalDestination;
  schedule: string;
  compression: boolean;
}

export interface ComplianceConfig {
  enabled: boolean;
  standards: string[];
  dataClassification: DataClassification;
  accessControls: AccessControl[];
  auditLogging: boolean;
}

export interface ForwardingDestination {
  id: string;
  name: string;
  type: 'syslog' | 'http' | 'kafka' | 'elasticsearch' | 's3';
  configuration: DestinationConfiguration;
  authentication: DestinationAuthentication;
  healthCheck: DestinationHealthCheck;
}

export interface ForwardingFilter {
  type: 'include' | 'exclude';
  conditions: FilterCondition[];
  destinations: string[];
}

export interface ForwardingBatching {
  enabled: boolean;
  size: number;
  timeout: string;
  compression: boolean;
}

export interface ForwardingErrorHandling {
  strategy: 'retry' | 'drop' | 'dead_letter';
  maxRetries: number;
  retryDelay: string;
  deadLetterDestination?: string;
}

export interface LogSummary {
  totalLogs: number;
  logsByLevel: Record<LogLevel, number>;
  logsBySource: Record<string, number>;
  timeRange: string;
  averageLogsPerSecond: number;
  errorRate: number;
}

export interface LogDistribution {
  temporal: TemporalDistribution[];
  levelDistribution: LevelDistribution[];
  sourceDistribution: SourceDistribution[];
}

export interface TopSource {
  source: string;
  count: number;
  percentage: number;
  errorRate: number;
  averageSize: number;
}

export interface ErrorAnalysis {
  totalErrors: number;
  errorRate: number;
  topErrors: TopError[];
  errorTrends: ErrorTrend[];
  errorPatterns: ErrorPattern[];
}

export interface LogPerformanceMetrics {
  ingestionRate: number;
  processingLatency: number;
  indexingRate: number;
  queryLatency: number;
  storageUtilization: number;
}

export interface PatternField {
  name: string;
  type: 'string' | 'number' | 'date' | 'ip' | 'email' | 'url';
  examples: string[];
  cardinality: number;
}

export interface AnomalyBaseline {
  metric: string;
  value: number;
  period: string;
  confidence: number;
}

export interface AnomalyDeviation {
  actual: number;
  expected: number;
  standardDeviations: number;
  percentage: number;
}

export interface AnomalyContext {
  relatedEvents: string[];
  systemMetrics: Record<string, number>;
  correlations: AnomalyCorrelation[];
}

export interface TrendForecast {
  nextPeriod: number;
  confidence: number;
  bounds: {
    upper: number;
    lower: number;
  };
}

export interface InsightEvidence {
  type: 'metric' | 'pattern' | 'correlation' | 'threshold';
  description: string;
  value: any;
  confidence: number;
}

// Additional complex supporting types would continue here...
// This represents a comprehensive but focused subset for brevity

export interface MultilineConfig {
  pattern: string;
  negate: boolean;
  match: 'after' | 'before';
  maxLines: number;
  timeout: string;
}

export interface FieldMapping {
  source: string;
  target: string;
  type?: string;
  default?: any;
}

export interface TypeConversion {
  field: string;
  from: string;
  to: string;
  format?: string;
}

export interface AggregationBucket {
  key: string;
  docCount: number;
  subAggregations?: Record<string, LogAggregation>;
}

export interface TemporalDistribution {
  timestamp: string;
  count: number;
  levels: Record<LogLevel, number>;
}

export interface LevelDistribution {
  level: LogLevel;
  count: number;
  percentage: number;
}

export interface SourceDistribution {
  source: string;
  count: number;
  percentage: number;
}

export interface TopError {
  message: string;
  count: number;
  sources: string[];
  firstSeen: string;
  lastSeen: string;
}

export interface ErrorTrend {
  period: string;
  count: number;
  rate: number;
  change: number;
}

export interface ErrorPattern {
  pattern: string;
  count: number;
  sources: string[];
  example: string;
}

export interface AnomalyCorrelation {
  metric: string;
  correlation: number;
  pValue: number;
}