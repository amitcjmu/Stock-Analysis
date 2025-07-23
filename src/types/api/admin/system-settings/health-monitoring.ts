/**
 * System Health and Monitoring Types
 * 
 * System health checks, monitoring metrics, and component status types.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../../shared';

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

// System Health Types
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

// Capacity and Performance Metrics
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
  custom: Record<string, string | number | boolean | null>;
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

// Resource Metrics
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

// Detailed Metric Types
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

// Enums
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

export type TrendDirection = 'increasing' | 'decreasing' | 'stable' | 'volatile';