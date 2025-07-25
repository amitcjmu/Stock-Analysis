/**
 * System Configuration and Integration Types
 *
 * System settings, integration management, configuration validation,
 * and environment management types.
 *
 * Generated with CC for modular admin type organization.
 */

// System and Configuration Types
export interface SystemConfiguration {
  category: ConfigurationCategory;
  settings: ConfigurationSetting[];
  environment: Environment;
  version: string;
  lastModified: string;
  modifiedBy: string;
  validation: ConfigurationValidation;
}

export interface ConfigurationSetting {
  key: string;
  value: unknown;
  type: SettingType;
  required: boolean;
  sensitive: boolean;
  description: string;
  validation: SettingValidation;
  dependencies: string[];
  scope: SettingScope;
}

export interface IntegrationConfiguration {
  integrationId: string;
  name: string;
  type: IntegrationType;
  provider: string;
  status: IntegrationStatus;
  configuration: Record<string, string | number | boolean | null>;
  credentials: IntegrationCredentials;
  endpoints: IntegrationEndpoint[];
  healthCheck: HealthCheckConfiguration;
  monitoring: IntegrationMonitoring;
}

export interface IntegrationCredentials {
  type: CredentialType;
  encrypted: boolean;
  fields: CredentialField[];
  expires_at?: string;
  last_rotated?: string;
}

export interface IntegrationEndpoint {
  name: string;
  url: string;
  method: HttpMethod;
  authentication: EndpointAuthentication;
  rate_limit?: RateLimit;
  timeout: number;
  retry_policy: RetryPolicy;
}

export interface HealthCheckConfiguration {
  enabled: boolean;
  interval: number;
  timeout: number;
  retry_count: number;
  endpoint: string;
  expected_status: number[];
  failure_threshold: number;
}

export interface IntegrationMonitoring {
  metrics: MonitoringMetric[];
  alerts: MonitoringAlert[];
  logs: LogConfiguration;
  tracing: TracingConfiguration;
}

// Configuration validation
export interface SettingValidation {
  required: boolean;
  type: SettingType;
  min?: number;
  max?: number;
  pattern?: string;
  allowed_values?: unknown[];
  custom_validator?: string;
}

export interface ConfigurationValidation {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  dependencies_satisfied: boolean;
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
  severity: ValidationSeverity;
  context?: Record<string, string | number | boolean | null>;
}

export interface ValidationWarning {
  field: string;
  code: string;
  message: string;
  recommendation?: string;
  context?: Record<string, string | number | boolean | null>;
}

// Supporting configuration interfaces
export interface CredentialField {
  name: string;
  type: CredentialFieldType;
  required: boolean;
  sensitive: boolean;
  description: string;
  validation?: FieldValidation;
}

export interface EndpointAuthentication {
  type: AuthenticationType;
  credentials: Record<string, string | number | boolean | null>;
  headers?: Record<string, string>;
  refresh_token?: RefreshTokenConfig;
}

export interface RateLimit {
  requests_per_second: number;
  burst_limit: number;
  window_size: number;
  backoff_strategy: BackoffStrategy;
}

export interface RetryPolicy {
  max_attempts: number;
  initial_delay: number;
  max_delay: number;
  backoff_multiplier: number;
  retry_conditions: RetryCondition[];
}

export interface MonitoringMetric {
  name: string;
  type: MetricType;
  unit: string;
  collection_interval: number;
  retention_period: number;
  aggregation: AggregationMethod;
}

export interface MonitoringAlert {
  name: string;
  condition: AlertCondition;
  threshold: number;
  severity: AlertSeverity;
  channels: NotificationChannel[];
  cooldown_period: number;
}

export interface LogConfiguration {
  level: LogLevel;
  format: LogFormat;
  destination: LogDestination[];
  retention_days: number;
  rotation_policy: LogRotationPolicy;
}

export interface TracingConfiguration {
  enabled: boolean;
  sampling_rate: number;
  trace_headers: string[];
  span_attributes: string[];
  exporters: TracingExporter[];
}

export interface RefreshTokenConfig {
  endpoint: string;
  method: HttpMethod;
  headers: Record<string, string>;
  body_template: string;
}

export interface FieldValidation {
  pattern?: string;
  min_length?: number;
  max_length?: number;
  allowed_values?: string[];
}

export interface RetryCondition {
  status_codes: number[];
  error_types: string[];
  timeout: boolean;
  network_error: boolean;
}

export interface AlertCondition {
  metric: string;
  operator: ComparisonOperator;
  value: number;
  duration: number;
  aggregation: AggregationMethod;
}

export interface NotificationChannel {
  type: ChannelType;
  configuration: Record<string, string | number | boolean | null>;
  enabled: boolean;
}

export interface LogDestination {
  type: LogDestinationType;
  configuration: Record<string, string | number | boolean | null>;
  enabled: boolean;
}

export interface LogRotationPolicy {
  max_size: string;
  max_files: number;
  compress: boolean;
  rotation_schedule: string;
}

export interface TracingExporter {
  type: TracingExporterType;
  endpoint: string;
  configuration: Record<string, string | number | boolean | null>;
  enabled: boolean;
}

// System configuration enums
export type ConfigurationCategory = 'security' | 'performance' | 'integration' | 'ui' | 'business' | 'compliance';
export type SettingType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'secret';
export type SettingScope = 'global' | 'tenant' | 'user' | 'session';
export type IntegrationType = 'api' | 'webhook' | 'sso' | 'data_sync' | 'notification' | 'analytics';
export type IntegrationStatus = 'active' | 'inactive' | 'error' | 'pending' | 'suspended';
export type Environment = 'production' | 'staging' | 'development' | 'testing' | 'sandbox';
export type CredentialType = 'api_key' | 'oauth' | 'basic_auth' | 'certificate' | 'token' | 'custom';
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';
export type ValidationSeverity = 'error' | 'warning' | 'info';
export type CredentialFieldType = 'text' | 'password' | 'email' | 'url' | 'number' | 'boolean' | 'file';
export type AuthenticationType = 'none' | 'basic' | 'bearer' | 'oauth2' | 'api_key' | 'custom';
export type BackoffStrategy = 'fixed' | 'exponential' | 'linear' | 'custom';
export type MetricType = 'counter' | 'gauge' | 'histogram' | 'summary';
export type AggregationMethod = 'sum' | 'average' | 'min' | 'max' | 'count' | 'percentile';
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type LogFormat = 'json' | 'text' | 'structured' | 'custom';
export type ComparisonOperator = 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'ne';
export type ChannelType = 'email' | 'slack' | 'webhook' | 'sms' | 'pagerduty' | 'teams';
export type LogDestinationType = 'file' | 'console' | 'syslog' | 'elasticsearch' | 'cloudwatch' | 'custom';
export type TracingExporterType = 'jaeger' | 'zipkin' | 'otlp' | 'console' | 'custom';
