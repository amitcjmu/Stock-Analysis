/**
 * Monitoring Configuration Types
 * 
 * Type definitions for setting up monitoring configurations, deployments,
 * and managing monitoring infrastructure across different environments.
 */

import {
  BaseApiRequest,
  CreateRequest,
  CreateResponse,
  GetRequest,
  GetResponse,
  MultiTenantContext
} from '../shared';
import { CostBreakdown, MetricThreshold, RetryPolicy, DeploymentStatus } from './core-types';

// Monitoring Configuration
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

// Monitoring Deployment
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

// Supporting Types
export interface MonitoringConfigurationData {
  name: string;
  description?: string;
  version: string;
  environment: string;
  tags: Record<string, string>;
  settings: MonitoringSettings;
}

export interface MonitoringTarget {
  id: string;
  type: 'host' | 'service' | 'application' | 'database' | 'network' | 'container';
  name: string;
  address: string;
  port?: number;
  protocol: 'http' | 'https' | 'tcp' | 'udp' | 'grpc';
  credentials?: TargetCredentials;
  tags: Record<string, string>;
  enabled: boolean;
}

export interface MetricConfiguration {
  id: string;
  name: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary' | 'distribution';
  source: string;
  query?: string;
  interval: string;
  timeout: string;
  labels: Record<string, string>;
  thresholds: MetricThreshold[];
  enabled: boolean;
}

export interface DataCollectionConfig {
  interval: string;
  timeout: string;
  retries: number;
  bufferSize: number;
  compression: boolean;
  encryption: boolean;
  batchSize: number;
  flushInterval: string;
}

export interface RetentionPolicy {
  shortTerm: string;
  mediumTerm: string;
  longTerm: string;
  archival: string;
  deletion: string;
  compression: RetentionCompression;
}

export interface AlertingConfiguration {
  enabled: boolean;
  defaultSeverity: 'info' | 'warning' | 'minor' | 'major' | 'critical' | 'blocker';
  escalationPolicy: EscalationPolicy;
  notifications: NotificationConfig[];
  suppressionRules: SuppressionRule[];
  customFields: Record<string, any>;
}

export interface MonitoringConfiguration {
  id: string;
  configurationId: string;
  name: string;
  description?: string;
  type: 'infrastructure' | 'application' | 'business' | 'security' | 'user_experience';
  version: string;
  environment: string;
  status: 'draft' | 'validated' | 'deployed' | 'active' | 'inactive' | 'deprecated';
  targets: MonitoringTarget[];
  metrics: MetricConfiguration[];
  collection: DataCollectionConfig;
  retention: RetentionPolicy;
  alerting: AlertingConfiguration;
  createdAt: string;
  updatedAt: string;
  deployedAt?: string;
}

export interface MonitoringDeploymentPlan {
  phases: DeploymentPhase[];
  estimatedDuration: string;
  dependencies: string[];
  validations: ValidationStep[];
  rollbackPlan: RollbackPlan;
}

export interface ConfigurationValidation {
  rule: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  details?: any;
}

export interface MonitoringCost {
  setup: number;
  monthly: number;
  storage: number;
  compute: number;
  network: number;
  currency: string;
  breakdown: CostBreakdown[];
}

export interface MonitoringTargetStatus {
  targetId: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown' | 'disabled';
  lastCheck: string;
  responseTime: number;
  availability: number;
  errors: string[];
}

export interface MetricStatus {
  metricId: string;
  status: 'collecting' | 'failed' | 'disabled';
  lastCollection: string;
  dataPoints: number;
  errors: string[];
}

export interface AlertingStatus {
  enabled: boolean;
  activeRules: number;
  activeAlerts: number;
  lastEvaluation: string;
  errors: string[];
}

export interface MonitoringHealth {
  overall: 'healthy' | 'warning' | 'critical' | 'unknown';
  targets: number;
  targetsHealthy: number;
  metrics: number;
  metricsCollecting: number;
  lastUpdate: string;
}

export interface MonitoringDeployment {
  deploymentId: string;
  configurationId: string;
  strategy: 'immediate' | 'phased' | 'canary' | 'blue_green';
  environments: string[];
  progress: number;
  currentPhase: string;
  startedAt: string;
  estimatedCompletion: string;
}

// DeploymentStatus imported from core-types

export interface DeploymentPlan {
  phases: DeploymentPhase[];
  totalDuration: string;
  rollbackPlan: RollbackPlan;
}

// Additional supporting interfaces
export interface MonitoringSettings {
  sampling: SamplingConfig;
  buffering: BufferingConfig;
  security: SecurityConfig;
  performance: PerformanceConfig;
}

export interface TargetCredentials {
  type: 'basic' | 'token' | 'certificate' | 'oauth';
  username?: string;
  password?: string;
  token?: string;
  certificate?: string;
  privateKey?: string;
}

// MetricThreshold imported from core-types

export interface RetentionCompression {
  enabled: boolean;
  algorithm: 'gzip' | 'lz4' | 'snappy' | 'zstd';
  level: number;
}

export interface EscalationPolicy {
  levels: EscalationLevel[];
  maxEscalations: number;
  escalationInterval: string;
}

export interface NotificationConfig {
  type: 'email' | 'sms' | 'webhook' | 'slack' | 'teams' | 'pagerduty';
  target: string;
  conditions: NotificationCondition[];
  template?: string;
  enabled: boolean;
}

export interface SuppressionRule {
  id: string;
  name: string;
  conditions: SuppressionCondition[];
  duration: string;
  enabled: boolean;
}

export interface DeploymentPhase {
  name: string;
  description: string;
  duration: string;
  dependencies: string[];
  tasks: DeploymentTask[];
  rollbackTasks: DeploymentTask[];
}

export interface ValidationStep {
  name: string;
  type: 'connectivity' | 'permissions' | 'configuration' | 'performance';
  timeout: string;
  required: boolean;
}

export interface RollbackPlan {
  enabled: boolean;
  trigger: 'manual' | 'automatic';
  conditions: RollbackCondition[];
  steps: RollbackStep[];
}

// CostBreakdown imported from core-types

export interface SamplingConfig {
  rate: number;
  strategy: 'random' | 'deterministic' | 'adaptive';
  maxSamples: number;
}

export interface BufferingConfig {
  size: number;
  timeout: string;
  strategy: 'memory' | 'disk' | 'hybrid';
}

export interface SecurityConfig {
  encryption: boolean;
  authentication: boolean;
  authorization: boolean;
  audit: boolean;
}

export interface PerformanceConfig {
  maxConcurrency: number;
  timeout: string;
  retryPolicy: RetryPolicy;
}

export interface EscalationLevel {
  level: number;
  delay: string;
  targets: string[];
  methods: string[];
}

export interface NotificationCondition {
  field: string;
  operator: string;
  value: any;
}

export interface SuppressionCondition {
  field: string;
  operator: string;
  value: any;
}

export interface DeploymentTask {
  name: string;
  type: string;
  timeout: string;
  dependencies: string[];
  parameters: Record<string, any>;
}

export interface RollbackCondition {
  metric: string;
  threshold: number;
  duration: string;
}

export interface RollbackStep {
  name: string;
  action: string;
  timeout: string;
  parameters: Record<string, any>;
}

// RetryPolicy imported from core-types