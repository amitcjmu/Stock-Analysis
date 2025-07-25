/**
 * Monitoring API Types
 *
 * Types for health checks, metrics, monitoring, and system observability.
 */

import type { BaseApiRequest, BaseApiResponse } from './base-types';
import type { MultiTenantContext } from './tenant-types';
import type { TimeRange } from './query-types'
import type { FilterParameter } from './query-types'

// Health and monitoring
export interface HealthCheckRequest extends BaseApiRequest {
  deep?: boolean;
  services?: string[];
  timeout?: number;
}

export interface HealthCheckResponse extends BaseApiResponse<HealthStatus> {
  data: HealthStatus;
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: HealthCheck[];
  timestamp: string;
  uptime: number;
  version: string;
}

export interface MetricsRequest extends BaseApiRequest {
  metrics?: string[];
  timeRange?: TimeRange;
  granularity?: string;
  aggregation?: string[];
  filters?: FilterParameter[];
  context?: MultiTenantContext;
}

export interface MetricsResponse extends BaseApiResponse<MetricValue[]> {
  data: MetricValue[];
  timeRange: TimeRange;
  granularity: string;
  totalDataPoints: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime: number;
  timestamp: string;
  environment: string;
  region?: string;
  checks: HealthCheck[];
  dependencies: DependencyHealth[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message?: string;
  time: string;
  duration: number;
  details?: Record<string, string | number | boolean | null | undefined>;
}

export interface DependencyHealth {
  name: string;
  type: 'database' | 'cache' | 'queue' | 'external_api' | 'storage' | 'other';
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime?: number;
  lastChecked: string;
  error?: string;
  version?: string;
}

export interface MetricValue {
  name: string;
  value: number;
  unit?: string;
  timestamp: string;
  tags?: Record<string, string>;
  aggregation?: string;
}
