/**
 * Metrics and Monitoring Models
 * 
 * Type definitions for system metrics, performance monitoring, resource usage, health status, and alerts.
 */

import type { TimeRange } from '../base-types';
import type { AgentResourceUsage, CrewResourceUsage } from './crew-models';

// Metrics and Monitoring Models
export interface FlowMetrics {
  flowId: string;
  executionTime: number;
  cpuUsage: number;
  memoryUsage: number;
  networkIO: number;
  diskIO: number;
  taskCount: number;
  completedTasks: number;
  failedTasks: number;
  retryCount: number;
  errorRate: number;
  throughput: number;
  latency: number;
  resourceEfficiency: number;
  qualityScore: number;
  userSatisfaction: number;
}

export interface SystemMetrics {
  totalFlows: number;
  activeFlows: number;
  completedFlows: number;
  failedFlows: number;
  totalAgents: number;
  activeAgents: number;
  totalCrews: number;
  activeCrews: number;
  systemLoad: number;
  memoryUsage: number;
  diskUsage: number;
  networkTraffic: number;
  errorRate: number;
  averageResponseTime: number;
  uptime: number;
}

export interface PerformanceMetrics {
  flowId: string;
  benchmarks: PerformanceBenchmark[];
  bottlenecks: PerformanceBottleneck[];
  optimizations: PerformanceOptimization[];
  trends: PerformanceTrend[];
  alerts: PerformanceAlert[];
  recommendations: string[];
}

export interface ResourceUsage {
  flowId: string;
  cpu: ResourceMetric;
  memory: ResourceMetric;
  network: ResourceMetric;
  disk: ResourceMetric;
  agents: AgentResourceUsage[];
  crews: CrewResourceUsage[];
  predictions: ResourcePrediction[];
  limits: ResourceLimits;
  alerts: ResourceAlert[];
}

export interface HealthStatus {
  overall: 'healthy' | 'warning' | 'critical' | 'down';
  components: ComponentHealth[];
  checks: HealthCheck[];
  lastChecked: string;
  uptime: number;
  version: string;
  environment: string;
}

export interface Alert {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  description: string;
  flowId?: string;
  agentId?: string;
  crewId?: string;
  status: 'active' | 'acknowledged' | 'resolved';
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  acknowledgedBy?: string;
  resolvedBy?: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface PerformanceBenchmark {
  name: string;
  value: number;
  unit: string;
  benchmark: number;
  status: 'good' | 'warning' | 'poor';
  trend: 'improving' | 'stable' | 'degrading';
}

export interface PerformanceBottleneck {
  location: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  recommendation: string;
  estimatedImprovement: number;
}

export interface PerformanceOptimization {
  type: string;
  description: string;
  impact: number;
  effort: 'low' | 'medium' | 'high';
  status: 'suggested' | 'implemented' | 'rejected';
}

export interface PerformanceTrend {
  metric: string;
  direction: 'up' | 'down' | 'stable';
  rate: number;
  confidence: number;
  prediction: number;
}

export interface PerformanceAlert {
  metric: string;
  threshold: number;
  currentValue: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
}

export interface ResourceMetric {
  current: number;
  peak: number;
  average: number;
  unit: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface ResourcePrediction {
  metric: string;
  predictedValue: number;
  confidence: number;
  timeHorizon: number;
  unit: string;
  trend: string;
}

export interface ResourceLimits {
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  agents: number;
  crews: number;
}

export interface ResourceAlert {
  resource: string;
  currentUsage: number;
  threshold: number;
  severity: 'warning' | 'critical';
  message: string;
  recommendation: string;
}

export interface ComponentHealth {
  component: string;
  status: 'healthy' | 'warning' | 'critical' | 'down';
  message: string;
  lastChecked: string;
  metrics: Record<string, number>;
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message: string;
  duration: number;
  lastRun: string;
  details: Record<string, string | number | boolean | null>;
}

export interface AlertConfiguration {
  name: string;
  description: string;
  conditions: AlertCondition[];
  actions: AlertAction[];
  enabled: boolean;
  severity: 'info' | 'warning' | 'error' | 'critical';
  cooldown: number;
  escalation: AlertEscalation;
}

export interface AlertCondition {
  metric: string;
  operator: 'gt' | 'lt' | 'eq' | 'ne' | 'gte' | 'lte';
  threshold: number;
  duration: number;
  aggregation: 'avg' | 'max' | 'min' | 'sum' | 'count';
}

export interface AlertAction {
  type: 'email' | 'slack' | 'webhook' | 'sms' | 'ticket';
  target: string;
  parameters: Record<string, string | number | boolean | null>;
  enabled: boolean;
}

export interface AlertEscalation {
  enabled: boolean;
  levels: EscalationLevel[];
  timeout: number;
}

export interface EscalationLevel {
  level: number;
  recipients: string[];
  channels: string[];
  delay: number;
}