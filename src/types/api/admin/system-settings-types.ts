/**
 * System Settings and Configuration API Types
 * 
 * Type definitions for system configuration management including settings,
 * health monitoring, system administration, and platform configuration.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  GetRequest,
  GetResponse,
  UpdateRequest,
  UpdateResponse
} from '../shared';

// System Settings APIs
export interface GetSystemSettingsRequest extends GetRequest {
  category?: SettingCategory;
  includeDefaults?: boolean;
  includeDescription?: boolean;
  includeValidation?: boolean;
}

export interface GetSystemSettingsResponse extends GetResponse<SystemSettings> {
  data: SystemSettings;
  categories: SettingCategoryDetails[];
  validation: SettingValidation[];
  dependencies: SettingDependency[];
}

export interface UpdateSystemSettingsRequest extends UpdateRequest<Partial<SystemSettingsData>> {
  data: Partial<SystemSettingsData>;
  category?: string;
  validateChanges?: boolean;
  notifyAdmins?: boolean;
  scheduleRestart?: boolean;
}

export interface UpdateSystemSettingsResponse extends UpdateResponse<SystemSettings> {
  data: SystemSettings;
  validationResults: SettingValidationResult[];
  changesApplied: SettingChange[];
  restartRequired: boolean;
}

// System Health APIs
export interface GetSystemHealthRequest extends BaseApiRequest {
  includeDetails?: boolean;
  includeMetrics?: boolean;
  includeAlerts?: boolean;
  includeDependencies?: boolean;
  context: MultiTenantContext;
}

export interface GetSystemHealthResponse extends BaseApiResponse<SystemHealth> {
  data: SystemHealth;
  components: ComponentHealth[];
  metrics: HealthMetrics;
  alerts: HealthAlert[];
  dependencies: DependencyHealth[];
}

// Supporting Types for System Settings
export interface SystemSettings {
  id: string;
  version: string;
  lastUpdated: string;
  updatedBy: string;
  security: SecuritySettings;
  integration: IntegrationSettings;
  notification: NotificationSettings;
  performance: PerformanceSettings;
  compliance: ComplianceSettings;
  features: FeatureSettings;
  maintenance: MaintenanceSettings;
  monitoring: MonitoringSettings;
}

export interface SystemSettingsData {
  security?: Partial<SecuritySettings>;
  integration?: Partial<IntegrationSettings>;
  notification?: Partial<NotificationSettings>;
  performance?: Partial<PerformanceSettings>;
  compliance?: Partial<ComplianceSettings>;
  features?: Partial<FeatureSettings>;
  maintenance?: Partial<MaintenanceSettings>;
  monitoring?: Partial<MonitoringSettings>;
}

export interface SettingCategoryDetails {
  category: SettingCategory;
  name: string;
  description: string;
  settings: Setting[];
  permissions: string[];
  validation: CategoryValidation;
}

export interface Setting {
  key: string;
  name: string;
  description: string;
  type: SettingType;
  value: any;
  defaultValue: any;
  required: boolean;
  validation: SettingValidationRule[];
  dependencies: string[];
  sensitive: boolean;
  restartRequired: boolean;
  metadata: Record<string, any>;
}

export interface SettingValidation {
  key: string;
  rules: SettingValidationRule[];
  dependencies: SettingDependency[];
  warnings: string[];
  errors: string[];
}

export interface SettingValidationRule {
  type: ValidationType;
  value?: any;
  message: string;
  severity: ValidationSeverity;
}

export interface SettingDependency {
  setting: string;
  dependsOn: string[];
  condition: DependencyCondition;
  message: string;
}

export interface SettingValidationResult {
  setting: string;
  valid: boolean;
  warnings: ValidationMessage[];
  errors: ValidationMessage[];
  suggestions: string[];
}

export interface SettingChange {
  setting: string;
  oldValue: any;
  newValue: any;
  appliedAt: string;
  appliedBy: string;
  impact: ChangeImpact;
  rollbackAvailable: boolean;
}

export interface SystemHealth {
  overall: HealthStatus;
  score: number;
  lastChecked: string;
  uptime: number;
  version: string;
  environment: string;
  region: string;
  maintenance: MaintenanceStatus;
  capacity: CapacityMetrics;
  performance: SystemPerformanceMetrics;
}

export interface ComponentHealth {
  component: SystemComponent;
  status: HealthStatus;
  lastChecked: string;
  responseTime?: number;
  errorRate?: number;
  uptime: number;
  version?: string;
  metrics: ComponentMetrics;
  dependencies: ComponentDependency[];
  alerts: ComponentAlert[];
}

export interface HealthMetrics {
  cpu: ResourceMetric;
  memory: ResourceMetric;
  disk: ResourceMetric;
  network: NetworkMetric;
  database: DatabaseMetric;
  cache: CacheMetric;
  queue: QueueMetric;
  api: ApiMetric;
}

export interface HealthAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  component?: SystemComponent;
  message: string;
  details: string;
  timestamp: string;
  acknowledged: boolean;
  resolvedAt?: string;
  actions: AlertAction[];
}

export interface DependencyHealth {
  service: string;
  status: HealthStatus;
  responseTime: number;
  lastChecked: string;
  critical: boolean;
  version?: string;
  endpoint: string;
  failureCount: number;
  circuitBreakerOpen: boolean;
}

// Configuration Category Interfaces
export interface SecuritySettings {
  authentication: AuthenticationConfig;
  authorization: AuthorizationConfig;
  encryption: EncryptionConfig;
  session: SessionConfig;
  audit: AuditConfig;
  rateLimit: RateLimitConfig;
  cors: CorsConfig;
  csrf: CsrfConfig;
  headers: SecurityHeadersConfig;
  mfa: MfaConfig;
}

export interface IntegrationSettings {
  apis: ApiIntegrationConfig;
  webhooks: WebhookConfig;
  oauth: OAuthConfig;
  sso: SsoConfig;
  external: ExternalIntegrationConfig;
  messaging: MessagingConfig;
  storage: StorageIntegrationConfig;
  monitoring: MonitoringIntegrationConfig;
}

export interface NotificationSettings {
  email: EmailConfig;
  sms: SmsConfig;
  push: PushConfig;
  inApp: InAppNotificationConfig;
  webhooks: WebhookNotificationConfig;
  channels: NotificationChannelConfig[];
  templates: NotificationTemplateConfig[];
  delivery: DeliveryConfig;
}

export interface PerformanceSettings {
  caching: CachingConfig;
  compression: CompressionConfig;
  cdn: CdnConfig;
  database: DatabasePerformanceConfig;
  api: ApiPerformanceConfig;
  background: BackgroundJobConfig;
  scaling: ScalingConfig;
  optimization: OptimizationConfig;
}

export interface ComplianceSettings {
  dataProtection: DataProtectionConfig;
  retention: DataRetentionConfig;
  audit: ComplianceAuditConfig;
  privacy: PrivacyConfig;
  governance: GovernanceConfig;
  frameworks: ComplianceFramework[];
  certifications: CertificationConfig[];
  policies: PolicyConfig[];
}

export interface FeatureSettings {
  flags: FeatureFlag[];
  experiments: ExperimentConfig[];
  rollouts: RolloutConfig[];
  toggles: ToggleConfig[];
  beta: BetaFeatureConfig[];
  deprecated: DeprecatedFeature[];
}

export interface MaintenanceSettings {
  windows: MaintenanceWindow[];
  notifications: MaintenanceNotificationConfig;
  automation: MaintenanceAutomationConfig;
  backup: BackupConfig;
  updates: UpdateConfig;
  monitoring: MaintenanceMonitoringConfig;
}

export interface MonitoringSettings {
  metrics: MetricsConfig;
  logging: LoggingConfig;
  tracing: TracingConfig;
  alerting: AlertingConfig;
  dashboards: DashboardConfig[];
  health: HealthCheckConfig;
  performance: PerformanceMonitoringConfig;
  security: SecurityMonitoringConfig;
}

// Enums and Supporting Types
export type SettingCategory = 
  | 'security' 
  | 'integration' 
  | 'notification' 
  | 'performance' 
  | 'compliance' 
  | 'features' 
  | 'maintenance' 
  | 'monitoring';

export type SettingType = 
  | 'string' 
  | 'number' 
  | 'boolean' 
  | 'array' 
  | 'object' 
  | 'enum' 
  | 'json' 
  | 'secret';

export type ValidationType = 
  | 'required' 
  | 'min' 
  | 'max' 
  | 'pattern' 
  | 'enum' 
  | 'custom' 
  | 'dependency';

export type ValidationSeverity = 'info' | 'warning' | 'error' | 'critical';

export type DependencyCondition = 
  | 'equals' 
  | 'not_equals' 
  | 'greater_than' 
  | 'less_than' 
  | 'contains' 
  | 'enabled' 
  | 'disabled';

export type ChangeImpact = 'none' | 'low' | 'medium' | 'high' | 'critical';

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'critical' | 'unknown';

export type SystemComponent = 
  | 'api' 
  | 'database' 
  | 'cache' 
  | 'queue' 
  | 'storage' 
  | 'auth' 
  | 'notifications' 
  | 'analytics' 
  | 'monitoring' 
  | 'search' 
  | 'scheduler';

export type MaintenanceStatus = 'none' | 'scheduled' | 'in_progress' | 'completed';

export type AlertType = 
  | 'performance' 
  | 'availability' 
  | 'security' 
  | 'capacity' 
  | 'error' 
  | 'custom';

export type AlertSeverity = 'info' | 'warning' | 'critical' | 'emergency';

// Supporting Complex Interfaces
export interface CategoryValidation {
  required: string[];
  optional: string[];
  dependencies: Record<string, string[]>;
  conflicts: Record<string, string[]>;
}

export interface ValidationMessage {
  message: string;
  field?: string;
  severity: ValidationSeverity;
  code?: string;
}

export interface CapacityMetrics {
  cpu: CapacityMetric;
  memory: CapacityMetric;
  disk: CapacityMetric;
  connections: CapacityMetric;
  requests: CapacityMetric;
}

export interface CapacityMetric {
  current: number;
  maximum: number;
  percentage: number;
  trend: TrendDirection;
  warning_threshold: number;
  critical_threshold: number;
}

export interface SystemPerformanceMetrics {
  responseTime: PerformanceMetric;
  throughput: PerformanceMetric;
  errorRate: PerformanceMetric;
  availability: PerformanceMetric;
}

export interface PerformanceMetric {
  current: number;
  average: number;
  percentiles: Record<string, number>;
  trend: TrendDirection;
  target?: number;
}

export interface ComponentMetrics {
  uptime: number;
  responseTime: PerformanceMetric;
  errorRate: PerformanceMetric;
  throughput: PerformanceMetric;
  resources: ResourceUsage;
  custom: Record<string, any>;
}

export interface ComponentDependency {
  service: string;
  critical: boolean;
  status: HealthStatus;
  lastChecked: string;
}

export interface ComponentAlert {
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface ResourceMetric {
  usage: number;
  available: number;
  percentage: number;
  trend: TrendDirection;
}

export interface NetworkMetric {
  inbound: BandwidthMetric;
  outbound: BandwidthMetric;
  latency: LatencyMetric;
  errors: number;
}

export interface DatabaseMetric {
  connections: ConnectionMetric;
  queries: QueryMetric;
  locks: LockMetric;
  replication: ReplicationMetric;
}

export interface CacheMetric {
  hitRate: number;
  missRate: number;
  evictions: number;
  memory: ResourceMetric;
}

export interface QueueMetric {
  size: number;
  throughput: number;
  latency: LatencyMetric;
  failures: number;
}

export interface ApiMetric {
  requests: RequestMetric;
  responses: ResponseMetric;
  errors: ErrorMetric;
  latency: LatencyMetric;
}

export interface AlertAction {
  action: string;
  description: string;
  automated: boolean;
  executedAt?: string;
  result?: string;
}

export type TrendDirection = 'increasing' | 'decreasing' | 'stable' | 'volatile';

// Additional supporting interfaces for complex config types
export interface ResourceUsage {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

export interface BandwidthMetric {
  current: number;
  peak: number;
  average: number;
}

export interface LatencyMetric {
  current: number;
  average: number;
  p95: number;
  p99: number;
}

export interface ConnectionMetric {
  active: number;
  idle: number;
  maximum: number;
}

export interface QueryMetric {
  total: number;
  slow: number;
  averageTime: number;
  longestTime: number;
}

export interface LockMetric {
  waiting: number;
  held: number;
  deadlocks: number;
}

export interface ReplicationMetric {
  lag: number;
  status: string;
  synced: boolean;
}

export interface RequestMetric {
  total: number;
  rate: number;
  concurrent: number;
}

export interface ResponseMetric {
  success: number;
  errors: number;
  timeouts: number;
}

export interface ErrorMetric {
  total: number;
  rate: number;
  by_status: Record<number, number>;
  by_endpoint: Record<string, number>;
}

// Configuration type placeholders (would be fully defined in actual implementation)
export interface AuthenticationConfig {
  methods: string[];
  sessionTimeout: number;
  maxAttempts: number;
  lockoutDuration: number;
}

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  percentage: number;
  conditions: Record<string, any>;
}

export interface MaintenanceWindow {
  id: string;
  name: string;
  startTime: string;
  endTime: string;
  recurring: boolean;
  timezone: string;
}

// Configuration type implementations to resolve compilation errors
export interface AuthenticationConfig {
  methods: string[];
  sessionTimeout: number;
  maxAttempts: number;
  lockoutDuration: number;
}

export interface AuthorizationConfig {
  rbacEnabled: boolean;
  defaultRole: string;
  hierarchicalRoles: boolean;
}

export interface EncryptionConfig {
  algorithm: string;
  keySize: number;
  rotationInterval: number;
}

export interface SessionConfig {
  timeout: number;
  sliding: boolean;
  sameSite: string;
}

export interface AuditConfig {
  enabled: boolean;
  level: string;
  retention: number;
}

export interface RateLimitConfig {
  enabled: boolean;
  requests: number;
  window: number;
}

export interface CorsConfig {
  enabled: boolean;
  origins: string[];
  methods: string[];
}

export interface CsrfConfig {
  enabled: boolean;
  sameSite: string;
  secure: boolean;
}

export interface SecurityHeadersConfig {
  hsts: boolean;
  xssProtection: boolean;
  contentTypeOptions: boolean;
}

export interface MfaConfig {
  required: boolean;
  methods: string[];
  gracePeriod: number;
}

export interface ApiIntegrationConfig {
  enabled: boolean;
  timeout: number;
  retries: number;
}

export interface WebhookConfig {
  enabled: boolean;
  maxRetries: number;
  timeout: number;
}

export interface OAuthConfig {
  providers: string[];
  redirectUri: string;
  scopes: string[];
}

export interface SsoConfig {
  enabled: boolean;
  provider: string;
  autoProvision: boolean;
}

export interface ExternalIntegrationConfig {
  enabled: boolean;
  providers: Record<string, any>;
  timeout: number;
}

export interface MessagingConfig {
  provider: string;
  queues: string[];
  dlq: boolean;
}

export interface StorageIntegrationConfig {
  provider: string;
  bucket: string;
  region: string;
}

export interface MonitoringIntegrationConfig {
  enabled: boolean;
  providers: string[];
  metrics: string[];
}

export interface EmailConfig {
  provider: string;
  fromAddress: string;
  templates: Record<string, any>;
}

export interface SmsConfig {
  provider: string;
  fromNumber: string;
  templates: Record<string, any>;
}

export interface PushConfig {
  enabled: boolean;
  providers: string[];
  certificates: Record<string, any>;
}

export interface InAppNotificationConfig {
  enabled: boolean;
  retention: number;
  maxPerUser: number;
}

export interface WebhookNotificationConfig {
  enabled: boolean;
  endpoints: string[];
  retries: number;
}

export interface NotificationChannelConfig {
  type: string;
  enabled: boolean;
  configuration: Record<string, any>;
}

export interface NotificationTemplateConfig {
  id: string;
  name: string;
  content: Record<string, any>;
}

export interface DeliveryConfig {
  maxRetries: number;
  retryDelay: number;
  timeout: number;
}

export interface CachingConfig {
  enabled: boolean;
  provider: string;
  ttl: number;
}

export interface CompressionConfig {
  enabled: boolean;
  algorithm: string;
  level: number;
}

export interface CdnConfig {
  enabled: boolean;
  provider: string;
  domains: string[];
}

export interface DatabasePerformanceConfig {
  poolSize: number;
  timeout: number;
  slowQueryThreshold: number;
}

export interface ApiPerformanceConfig {
  rateLimit: number;
  timeout: number;
  caching: boolean;
}

export interface BackgroundJobConfig {
  enabled: boolean;
  maxConcurrency: number;
  retries: number;
}

export interface ScalingConfig {
  autoScaling: boolean;
  minInstances: number;
  maxInstances: number;
}

export interface OptimizationConfig {
  enabled: boolean;
  strategies: string[];
  threshold: number;
}

export interface DataProtectionConfig {
  encryption: boolean;
  anonymization: boolean;
  pseudonymization: boolean;
}

export interface DataRetentionConfig {
  enabled: boolean;
  defaultPeriod: number;
  policies: Record<string, any>;
}

export interface ComplianceAuditConfig {
  enabled: boolean;
  frequency: string;
  scope: string[];
}

export interface PrivacyConfig {
  consentRequired: boolean;
  rightToErasure: boolean;
  dataPortability: boolean;
}

export interface GovernanceConfig {
  policies: string[];
  enforcement: boolean;
  reporting: boolean;
}

export interface CertificationConfig {
  type: string;
  issuer: string;
  expiryDate: string;
}

export interface PolicyConfig {
  id: string;
  name: string;
  rules: Record<string, any>;
}

export interface ExperimentConfig {
  id: string;
  name: string;
  variants: Record<string, any>;
}

export interface RolloutConfig {
  strategy: string;
  percentage: number;
  criteria: Record<string, any>;
}

export interface ToggleConfig {
  id: string;
  enabled: boolean;
  conditions: Record<string, any>;
}

export interface BetaFeatureConfig {
  id: string;
  enabled: boolean;
  eligibility: Record<string, any>;
}

export interface DeprecatedFeature {
  id: string;
  deprecatedAt: string;
  removalDate: string;
}

export interface MaintenanceWindow {
  id: string;
  name: string;
  startTime: string;
  endTime: string;
  recurring: boolean;
  timezone: string;
}

export interface MaintenanceNotificationConfig {
  enabled: boolean;
  channels: string[];
  advanceNotice: number;
}

export interface MaintenanceAutomationConfig {
  enabled: boolean;
  scripts: string[];
  rollback: boolean;
}

export interface BackupConfig {
  enabled: boolean;
  frequency: string;
  retention: number;
}

export interface UpdateConfig {
  autoUpdate: boolean;
  schedule: string;
  rollback: boolean;
}

export interface MaintenanceMonitoringConfig {
  enabled: boolean;
  metrics: string[];
  alerts: boolean;
}

export interface MetricsConfig {
  enabled: boolean;
  collection: string[];
  retention: number;
}

export interface LoggingConfig {
  level: string;
  outputs: string[];
  rotation: boolean;
}

export interface TracingConfig {
  enabled: boolean;
  samplingRate: number;
  exporter: string;
}

export interface AlertingConfig {
  enabled: boolean;
  channels: string[];
  thresholds: Record<string, any>;
}

export interface DashboardConfig {
  id: string;
  name: string;
  widgets: Record<string, any>;
}

export interface HealthCheckConfig {
  enabled: boolean;
  interval: number;
  timeout: number;
}

export interface PerformanceMonitoringConfig {
  enabled: boolean;
  metrics: string[];
  thresholds: Record<string, any>;
}

export interface SecurityMonitoringConfig {
  enabled: boolean;
  events: string[];
  alerting: boolean;
}