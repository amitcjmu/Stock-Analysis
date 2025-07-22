/**
 * Monitoring Settings Configuration Types
 * 
 * System monitoring configuration including metrics collection,
 * logging, tracing, alerting, and dashboard settings.
 * 
 * Generated with CC for modular admin type organization.
 */

// Monitoring Settings Configuration
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
  thresholds: Record<string, string | number | boolean | null>;
}

export interface DashboardConfig {
  id: string;
  name: string;
  widgets: Record<string, string | number | boolean | null>;
}

export interface HealthCheckConfig {
  enabled: boolean;
  interval: number;
  timeout: number;
}

export interface PerformanceMonitoringConfig {
  enabled: boolean;
  metrics: string[];
  thresholds: Record<string, string | number | boolean | null>;
}

export interface SecurityMonitoringConfig {
  enabled: boolean;
  events: string[];
  alerting: boolean;
}