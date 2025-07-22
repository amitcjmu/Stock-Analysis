/**
 * Supporting Types and Complex Interfaces
 * 
 * Complex supporting interfaces and remaining type definitions
 * that support the main data model domains.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  DayOfWeek,
  ContactMethod,
  BudgetCategory,
  CredentialType,
  HttpMethod,
  EvidenceType,
  ControlType,
  ControlFrequency,
  ControlStatus,
  AssessmentStatus,
  ConfidenceLevel,
  RiskProbability,
  MetricType,
  AggregationMethod,
  AlertSeverity,
  LogLevel,
  LogFormat,
  ComparisonOperator,
  ChannelType,
  LogDestinationType,
  TracingExporterType,
  ValidationSeverity,
  CredentialFieldType,
  AuthenticationType,
  BackoffStrategy,
  HolidayType,
  ExceptionType,
  ResourceType,
  ReportFormat,
  FindingSeverity,
  FindingStatus,
  RecommendationPriority,
  RecommendationStatus
} from './enums';

// Resource and project management interfaces
export interface ResourceRequirement {
  type: ResourceType;
  description: string;
  quantity: number;
  duration: string;
  skills_required: string[];
  cost_estimate?: number;
}

export interface MilestoneCriteria {
  criterion: string;
  measurable: boolean;
  target_value?: unknown;
  verification_method: string;
}

export interface WorkingHours {
  startTime: string;
  endTime: string;
  breaks: WorkBreak[];
}

export interface Holiday {
  date: string;
  name: string;
  type: HolidayType;
  recurring: boolean;
}

export interface CalendarException {
  date: string;
  type: ExceptionType;
  description: string;
  working_hours?: WorkingHours;
}

export interface WorkBreak {
  startTime: string;
  endTime: string;
  paid: boolean;
}

export interface ExpenseReceipt {
  id: string;
  filename: string;
  url: string;
  mime_type: string;
  size: number;
  uploaded_at: string;
}

export interface BudgetCategoryForecast {
  category: BudgetCategory;
  estimated_amount: number;
  confidence: ConfidenceLevel;
  assumptions: string[];
}

export interface ForecastRisk {
  description: string;
  impact_amount: number;
  probability: RiskProbability;
  mitigation: string;
}

export interface ReportingSchedule {
  frequency: CommunicationFrequency;
  recipients: string[];
  format: ReportFormat;
  delivery_method: ContactMethod;
}

// System configuration supporting interfaces
export interface ValidationError {
  field: string;
  code: string;
  message: string;
  severity: ValidationSeverity;
  context?: Record<string, any>;
}

export interface ValidationWarning {
  field: string;
  code: string;
  message: string;
  recommendation?: string;
  context?: Record<string, any>;
}

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
  credentials: Record<string, any>;
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
  configuration: Record<string, any>;
  enabled: boolean;
}

export interface LogDestination {
  type: LogDestinationType;
  configuration: Record<string, any>;
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
  configuration: Record<string, any>;
  enabled: boolean;
}

// Compliance assessment supporting interfaces
export interface AssessmentFinding {
  id: string;
  severity: FindingSeverity;
  category: string;
  description: string;
  evidence: string[];
  recommendations: string[];
  status: FindingStatus;
  assignedTo?: string;
  dueDate?: string;
}

export interface AssessmentRecommendation {
  id: string;
  priority: RecommendationPriority;
  category: string;
  description: string;
  implementation_guidance: string;
  estimated_effort: string;
  dependencies: string[];
  status: RecommendationStatus;
}

// Supporting interfaces that need to be centralized to avoid duplicates
// Note: These interfaces were moved here from other modules to prevent duplicate exports
export interface ResourceRequirement {
  type: ResourceType;
  description: string;
  quantity: number;
  duration: string;
  skills_required: string[];
  cost_estimate?: number;
}

export interface MilestoneCriteria {
  criterion: string;
  measurable: boolean;
  target_value?: unknown;
  verification_method: string;
}

export interface WorkingHours {
  startTime: string;
  endTime: string;
  breaks: WorkBreak[];
}

export interface Holiday {
  date: string;
  name: string;
  type: HolidayType;
  recurring: boolean;
}

export interface CalendarException {
  date: string;
  type: ExceptionType;
  description: string;
  working_hours?: WorkingHours;
}

export interface WorkBreak {
  startTime: string;
  endTime: string;
  paid: boolean;
}

export interface ExpenseReceipt {
  id: string;
  filename: string;
  url: string;
  mime_type: string;
  size: number;
  uploaded_at: string;
}

export interface BudgetCategoryForecast {
  category: BudgetCategory;
  estimated_amount: number;
  confidence: ConfidenceLevel;
  assumptions: string[];
}

export interface ForecastRisk {
  description: string;
  impact_amount: number;
  probability: RiskProbability;
  mitigation: string;
}

export interface ReportingSchedule {
  frequency: CommunicationFrequency;
  recipients: string[];
  format: ReportFormat;
  delivery_method: ContactMethod;
}

// System configuration supporting interfaces that were missing
export interface EndpointAuthentication {
  type: AuthenticationType;
  credentials: Record<string, any>;
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

// Re-export communication frequency type that's used in multiple places
export type CommunicationFrequency = 'daily' | 'weekly' | 'bi_weekly' | 'monthly' | 'quarterly' | 'as_needed';