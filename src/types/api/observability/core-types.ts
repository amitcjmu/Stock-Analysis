/**
 * Observability Core Types
 * 
 * Core type definitions and supporting data structures used across
 * all observability modules including enums, base interfaces, and shared types.
 */

// Core Observability Data Types
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

// Core Status and Priority Types
export type ObservabilityStatus = 
  | 'planning' | 'configuration' | 'deployment' | 'calibration'
  | 'monitoring' | 'optimization' | 'maintenance' | 'scaling'
  | 'completed' | 'paused' | 'failed' | 'deprecated';

export type AlertSeverity = 'info' | 'warning' | 'minor' | 'major' | 'critical' | 'blocker';
export type AlertStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'closed';
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type DeploymentStatus = 'pending' | 'deploying' | 'validating' | 'active' | 'failed' | 'rolled_back';

// Core Observability Supporting Types
export interface ObservabilityObjective {
  id: string;
  type: 'availability' | 'performance' | 'reliability' | 'security' | 'cost';
  target: number;
  threshold: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  measurement: ObjectiveMeasurement;
  validation: ObjectiveValidation;
}

export interface ObservabilityRequirement {
  id: string;
  category: 'monitoring' | 'alerting' | 'reporting' | 'compliance';
  description: string;
  mandatory: boolean;
  dependencies: string[];
  verification: RequirementVerification;
}

export interface ObservabilityPhases {
  current: string;
  completed: string[];
  remaining: string[];
  phases: PhaseDefinition[];
}

// Common Data Structures
export interface TimeRange {
  start: string;
  end: string;
  timezone?: string;
}

export interface MetricThreshold {
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'between' | 'outside';
  value: number | number[];
  severity: AlertSeverity;
  duration: string;
  hysteresis?: number;
}

export interface TaggedResource {
  id: string;
  name: string;
  type: string;
  tags: Record<string, string>;
  metadata: Record<string, any>;
}

export interface HealthCheck {
  enabled: boolean;
  interval: string;
  timeout: string;
  retries: number;
  endpoint?: string;
  expectedStatus?: number;
  expectedContent?: string;
}

export interface RetryPolicy {
  enabled: boolean;
  maxAttempts: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed' | 'custom';
  baseDelay: string;
  maxDelay: string;
  jitter: boolean;
}

export interface RateLimiting {
  enabled: boolean;
  requestsPerSecond: number;
  burstSize: number;
  timeWindow: string;
  strategy: 'token_bucket' | 'sliding_window' | 'fixed_window';
}

export interface SecurityConfig {
  encryption: EncryptionConfig;
  authentication: AuthenticationConfig;
  authorization: AuthorizationConfig;
  audit: AuditConfig;
}

// Alert and Notification Types
export interface AlertCondition {
  id: string;
  metric: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'between' | 'outside' | 'regex' | 'exists';
  threshold: number | string | number[];
  duration: string;
  aggregation?: 'avg' | 'sum' | 'min' | 'max' | 'count' | 'p50' | 'p95' | 'p99';
  dimensions?: Record<string, string>;
  hysteresis?: number;
}

export interface NotificationChannel {
  id: string;
  type: 'email' | 'sms' | 'webhook' | 'slack' | 'teams' | 'pagerduty' | 'opsgenie';
  name: string;
  target: string;
  configuration: NotificationConfiguration;
  template?: NotificationTemplate;
  filters: NotificationFilter[];
  rateLimiting: NotificationRateLimit;
  enabled: boolean;
}

export interface AlertAction {
  id: string;
  type: 'webhook' | 'script' | 'api_call' | 'ticket' | 'runbook' | 'auto_remediation';
  name: string;
  configuration: ActionConfiguration;
  conditions: ActionCondition[];
  timeout: string;
  retries: number;
  enabled: boolean;
}

// Performance and Capacity Types
export interface PerformanceMetrics {
  responseTime: ResponseTimeMetrics;
  throughput: ThroughputMetrics;
  errorRate: number;
  availability: number;
  resourceUtilization: ResourceUtilization;
}

export interface ResponseTimeMetrics {
  avg: number;
  min: number;
  max: number;
  p50: number;
  p95: number;
  p99: number;
  unit: string;
}

export interface ThroughputMetrics {
  requestsPerSecond: number;
  transactionsPerSecond: number;
  dataTransferRate: number;
  unit: string;
}

export interface ResourceUtilization {
  cpu: UtilizationMetric;
  memory: UtilizationMetric;
  disk: UtilizationMetric;
  network: UtilizationMetric;
}

export interface UtilizationMetric {
  current: number;
  average: number;
  peak: number;
  unit: string;
  threshold: number;
}

// Cost and Budget Types
export interface CostMetrics {
  total: number;
  breakdown: CostBreakdown[];
  currency: string;
  period: string;
  trend: CostTrend;
}

export interface CostBreakdown {
  category: string;
  amount: number;
  percentage: number;
  unit: string;
  description: string;
}

export interface CostTrend {
  direction: 'increasing' | 'decreasing' | 'stable';
  rate: number;
  period: string;
  projection: CostProjection;
}

export interface CostProjection {
  nextPeriod: number;
  confidence: number;
  factors: ProjectionFactor[];
}

// Data Quality and Validation Types
export interface DataQuality {
  score: number;
  dimensions: QualityDimension[];
  issues: QualityIssue[];
  trends: QualityTrend[];
  lastAssessment: string;
}

export interface QualityDimension {
  name: 'completeness' | 'accuracy' | 'consistency' | 'timeliness' | 'validity' | 'uniqueness';
  score: number;
  weight: number;
  issues: number;
  trends: 'improving' | 'degrading' | 'stable';
}

export interface QualityIssue {
  id: string;
  type: 'missing_data' | 'invalid_format' | 'duplicate' | 'stale_data' | 'inconsistent';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  count: number;
  percentage: number;
  firstDetected: string;
  lastDetected: string;
}

export interface QualityTrend {
  dimension: string;
  direction: 'improving' | 'degrading' | 'stable';
  rate: number;
  timeframe: string;
  significance: 'low' | 'medium' | 'high';
}

// Anomaly Detection Types
export interface AnomalyDetection {
  enabled: boolean;
  algorithms: AnomalyAlgorithm[];
  sensitivity: 'low' | 'medium' | 'high' | 'adaptive';
  baseline: AnomalyBaseline;
  configuration: AnomalyConfiguration;
}

export interface AnomalyAlgorithm {
  name: string;
  type: 'statistical' | 'machine_learning' | 'rule_based' | 'hybrid';
  parameters: Record<string, any>;
  enabled: boolean;
  weight: number;
}

export interface AnomalyBaseline {
  type: 'historical' | 'seasonal' | 'trend' | 'custom';
  period: string;
  dataPoints: number;
  confidence: number;
  autoUpdate: boolean;
}

export interface AnomalyConfiguration {
  minAnomalyDuration: string;
  maxAnomaliesPerPeriod: number;
  suppressDuplicates: boolean;
  correlationAnalysis: boolean;
  autoResolution: boolean;
}

// Supporting Interface Implementations
export interface ObjectiveMeasurement {
  metric: string;
  aggregation: string;
  timeWindow: string;
  evaluationFrequency: string;
  baseline?: number;
}

export interface ObjectiveValidation {
  method: 'automated' | 'manual' | 'hybrid';
  frequency: string;
  criteria: ValidationCriterion[];
  approvalRequired: boolean;
}

export interface RequirementVerification {
  method: 'testing' | 'audit' | 'review' | 'automated_check';
  frequency: string;
  evidence: EvidenceRequirement[];
  signoffRequired: boolean;
}

export interface PhaseDefinition {
  name: string;
  description: string;
  duration: string;
  prerequisites: string[];
  deliverables: string[];
  successCriteria: string[];
}

export interface EncryptionConfig {
  enabled: boolean;
  algorithm: 'aes256' | 'chacha20' | 'rsa' | 'ecc';
  keySize: number;
  keyRotation: string;
  keyManagement: KeyManagementConfig;
}

export interface AuthenticationConfig {
  enabled: boolean;
  methods: AuthMethod[];
  tokenExpiry: string;
  multiFactorRequired: boolean;
  sessionManagement: SessionConfig;
}

export interface AuthorizationConfig {
  enabled: boolean;
  model: 'rbac' | 'abac' | 'acl' | 'custom';
  policies: AuthorizationPolicy[];
  enforcement: 'strict' | 'permissive' | 'advisory';
}

export interface AuditConfig {
  enabled: boolean;
  events: AuditEvent[];
  retention: string;
  encryption: boolean;
  integrations: AuditIntegration[];
}

export interface NotificationConfiguration {
  endpoint?: string;
  token?: string;
  username?: string;
  password?: string;
  apiKey?: string;
  headers?: Record<string, string>;
  format?: string;
  timeout: string;
  retries: number;
}

export interface NotificationTemplate {
  subject: string;
  body: string;
  format: 'text' | 'html' | 'markdown' | 'json';
  variables: Record<string, string>;
  localization?: LocalizationConfig;
}

export interface NotificationFilter {
  field: string;
  operator: 'eq' | 'neq' | 'contains' | 'regex' | 'in' | 'nin';
  value: any;
  enabled: boolean;
}

export interface NotificationRateLimit {
  enabled: boolean;
  maxNotifications: number;
  period: string;
  burstAllowed: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed';
}

export interface ActionConfiguration {
  endpoint?: string;
  method?: string;
  headers?: Record<string, string>;
  body?: string;
  script?: string;
  command?: string;
  parameters: Record<string, any>;
  timeout: string;
  authentication?: ActionAuthentication;
}

export interface ActionCondition {
  field: string;
  operator: string;
  value: any;
  required: boolean;
}

export interface ProjectionFactor {
  name: string;
  impact: number;
  confidence: number;
  description: string;
}

export interface ValidationCriterion {
  name: string;
  type: 'metric' | 'threshold' | 'trend' | 'manual';
  condition: string;
  weight: number;
}

export interface EvidenceRequirement {
  type: 'document' | 'screenshot' | 'test_result' | 'metric' | 'approval';
  description: string;
  mandatory: boolean;
}

export interface KeyManagementConfig {
  provider: 'internal' | 'aws_kms' | 'azure_kv' | 'hashicorp_vault' | 'gcp_kms';
  configuration: Record<string, any>;
  backup: boolean;
  hsm: boolean;
}

export interface AuthMethod {
  type: 'password' | 'token' | 'certificate' | 'oauth' | 'saml' | 'ldap';
  configuration: Record<string, any>;
  priority: number;
  enabled: boolean;
}

export interface SessionConfig {
  timeout: string;
  maxConcurrentSessions: number;
  trackActivity: boolean;
  secureTransport: boolean;
}

export interface AuthorizationPolicy {
  id: string;
  name: string;
  subjects: string[];
  resources: string[];
  actions: string[];
  conditions: PolicyCondition[];
  effect: 'allow' | 'deny';
}

export interface AuditEvent {
  type: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  includePayload: boolean;
  includeResponse: boolean;
  retention: string;
}

export interface AuditIntegration {
  type: 'siem' | 'log_aggregator' | 'compliance_tool' | 'dashboard';
  configuration: Record<string, any>;
  realtime: boolean;
  encryption: boolean;
}

export interface LocalizationConfig {
  enabled: boolean;
  defaultLanguage: string;
  supportedLanguages: string[];
  fallbackStrategy: 'default' | 'empty' | 'key';
}

export interface ActionAuthentication {
  type: 'basic' | 'bearer' | 'apikey' | 'oauth' | 'certificate';
  credentials: Record<string, string>;
}

export interface PolicyCondition {
  field: string;
  operator: string;
  value: any;
  negate: boolean;
}