/**
 * Alerting Management Types
 *
 * Type definitions for creating and managing alert rules, handling alerts,
 * and configuring notification systems for observability monitoring.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  CreateRequest,
  CreateResponse,
  ListRequest,
  ListResponse,
  MultiTenantContext
} from '../shared';
import type { FilterValue, ThresholdValue } from '../shared/value-types'
import type { PrimitiveValue } from '../shared/value-types'
import type { GenericMetadata } from '../shared/metadata-types';

// Alert Rule Management
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

// Alert Retrieval and Management
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

// Alert Actions
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

// Supporting Types
export interface AlertRuleData {
  name: string;
  description?: string;
  expression: string;
  duration: string;
  frequency: string;
  enabled: boolean;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  metadata: Record<string, PrimitiveValue | GenericMetadata>;
}

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

export type AlertSeverity = 'info' | 'warning' | 'minor' | 'major' | 'critical' | 'blocker';
export type AlertStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'closed';

export interface NotificationChannel {
  id: string;
  type: 'email' | 'sms' | 'webhook' | 'slack' | 'teams' | 'pagerduty' | 'opsgenie';
  name: string;
  target: string;
  configuration: ChannelConfiguration;
  template?: NotificationTemplate;
  filters: NotificationFilter[];
  rateLimiting: RateLimitingConfig;
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

export interface AlertSuppression {
  enabled: boolean;
  rules: SuppressionRule[];
  globalSuppression: GlobalSuppressionConfig;
  maintenanceWindows: MaintenanceWindow[];
}

export interface AlertRule {
  id: string;
  ruleId: string;
  name: string;
  description?: string;
  type: 'threshold' | 'anomaly' | 'pattern' | 'composite' | 'forecast';
  expression: string;
  conditions: AlertCondition[];
  severity: AlertSeverity;
  duration: string;
  frequency: string;
  enabled: boolean;
  notifications: NotificationChannel[];
  actions: AlertAction[];
  suppression: AlertSuppression;
  tags: Record<string, string>;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  createdAt: string;
  updatedAt: string;
  lastFired?: string;
  fireCount: number;
}

export interface AlertRuleValidation {
  rule: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  field?: string;
  suggestion?: string;
}

export interface AlertTestResult {
  testId: string;
  status: 'passed' | 'failed';
  message: string;
  duration: number;
  fired: boolean;
  mockData?: Record<string, PrimitiveValue> | PrimitiveValue[];
}

export interface Alert {
  id: string;
  alertId: string;
  ruleId: string;
  ruleName: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  description: string;
  message: string;
  source: string;
  tags: Record<string, string>;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  firedAt: string;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  resolvedAt?: string;
  resolvedBy?: string;
  escalatedAt?: string;
  escalationLevel: number;
  fingerprint: string;
  groupKey: string;
  activeTime: string;
  value: number;
  threshold: number;
  context: AlertContext;
  relatedAlerts: string[];
  actionsTaken: AlertActionResult[];
  silenced: boolean;
}

export interface AlertStatistics {
  total: number;
  byStatus: Record<AlertStatus, number>;
  bySeverity: Record<AlertSeverity, number>;
  byRule: RuleStatistics[];
  averageResolutionTime: number;
  escalationRate: number;
  falsePositiveRate: number;
  topSources: SourceStatistics[];
}

export interface AlertTrend {
  metric: 'count' | 'resolution_time' | 'escalation_rate' | 'false_positive_rate';
  direction: 'increasing' | 'decreasing' | 'stable';
  percentage: number;
  period: string;
  significance: 'low' | 'medium' | 'high';
}

export interface TopAlert {
  ruleId: string;
  ruleName: string;
  count: number;
  avgResolutionTime: number;
  lastOccurrence: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface AlertAcknowledgment {
  alertId: string;
  acknowledgedBy: string;
  acknowledgedAt: string;
  notes?: string;
  escalated: boolean;
  automaticEscalation?: string;
}

export interface AlertNotification {
  id: string;
  channel: string;
  target: string;
  status: 'sent' | 'failed' | 'pending' | 'delivered' | 'bounced';
  sentAt: string;
  deliveredAt?: string;
  failureReason?: string;
  retryCount: number;
}

export interface AlertResolution {
  alertId: string;
  resolvedBy: string;
  resolvedAt: string;
  resolution: string;
  category: 'resolved' | 'false_positive' | 'duplicate' | 'maintenance' | 'expected';
  rootCause?: string;
  timeToResolution: number;
  preventRecurrence: boolean;
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

export interface AlertLearning {
  id: string;
  category: 'threshold_adjustment' | 'new_monitoring' | 'process_improvement' | 'automation_opportunity';
  insight: string;
  recommendation: string;
  confidence: number;
  applicability: 'specific' | 'general' | 'similar_systems';
}

// Additional supporting interfaces
export interface ChannelConfiguration {
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
}

export interface NotificationFilter {
  field: string;
  operator: 'eq' | 'neq' | 'contains' | 'regex' | 'in' | 'nin';
  value: FilterValue;
  enabled: boolean;
}

export interface RateLimitingConfig {
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
  parameters: Record<string, PrimitiveValue | string[]>;
  timeout: string;
  authentication?: ActionAuthentication;
}

export interface ActionCondition {
  field: string;
  operator: string;
  value: FilterValue;
  required: boolean;
}

export interface SuppressionRule {
  id: string;
  name: string;
  pattern: string;
  duration: string;
  reason: string;
  enabled: boolean;
  createdBy: string;
  createdAt: string;
  expiresAt?: string;
}

export interface GlobalSuppressionConfig {
  enabled: boolean;
  defaultDuration: string;
  maxDuration: string;
  allowOverride: boolean;
}

export interface MaintenanceWindow {
  id: string;
  name: string;
  start: string;
  end: string;
  recurrence?: RecurrenceConfig;
  reason: string;
  suppressAll: boolean;
  suppressRules: string[];
  createdBy: string;
}

export interface AlertContext {
  source: string;
  environment: string;
  service?: string;
  instance?: string;
  region?: string;
  namespace?: string;
  cluster?: string;
  node?: string;
  pod?: string;
  container?: string;
  customContext: Record<string, string | number | boolean | null>;
}

export interface AlertActionResult {
  actionId: string;
  actionName: string;
  status: 'success' | 'failed' | 'timeout' | 'skipped';
  executedAt: string;
  duration: number;
  result?: {
    fired?: boolean;
    timestamp?: string;
    value?: PrimitiveValue;
    message?: string;
  };
  error?: string;
}

export interface RuleStatistics {
  ruleId: string;
  ruleName: string;
  fireCount: number;
  falsePositives: number;
  averageResolutionTime: number;
  lastFired: string;
}

export interface SourceStatistics {
  source: string;
  count: number;
  percentage: number;
  severity: AlertSeverity;
}

export interface ActionAuthentication {
  type: 'basic' | 'bearer' | 'apikey' | 'oauth' | 'certificate';
  credentials: Record<string, string>;
}

export interface RecurrenceConfig {
  type: 'daily' | 'weekly' | 'monthly' | 'yearly';
  interval: number;
  daysOfWeek?: number[];
  dayOfMonth?: number;
  endDate?: string;
  maxOccurrences?: number;
}
