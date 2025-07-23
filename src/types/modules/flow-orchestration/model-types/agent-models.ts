/**
 * Agent Models
 * 
 * Type definitions for agent instances, status, metrics, coordination, and communication.
 */

import type { AgentConfiguration, TimeRange, ExecutionError, RetryPolicy } from '../base-types'
import type { MetricSample } from '../base-types'

// Agent Models
export interface AgentInstance {
  id: string;
  configuration: AgentConfiguration;
  status: AgentStatus;
  deployedFlows: string[];
  metrics: AgentMetrics;
  createdAt: string;
  lastActiveAt: string;
}

export interface AgentStatus {
  agentId: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  currentTask?: string;
  currentFlowId?: string;
  performance: AgentPerformance;
  health: AgentHealth;
  lastHeartbeat: string;
  errorCount: number;
  warningCount: number;
}

export interface AgentMetrics {
  agentId: string;
  tasksCompleted: number;
  tasksInProgress: number;
  tasksFailed: number;
  averageTaskDuration: number;
  successRate: number;
  errorRate: number;
  memoryUsage: number;
  cpuUsage: number;
  networkIO: number;
  timeRange: TimeRange;
  samples: MetricSample[];
}

export interface AgentCoordination {
  coordinationType: 'sequential' | 'parallel' | 'conditional' | 'pipeline';
  agents: string[];
  dependencies: AgentDependency[];
  timeout: number;
  retryPolicy: RetryPolicy;
  failureStrategy: 'abort' | 'continue' | 'fallback';
  communicationProtocol: 'event' | 'message' | 'shared_state';
}

export interface CoordinationResult {
  coordinationId: string;
  status: 'success' | 'partial' | 'failed';
  results: AgentResult[];
  errors: CoordinationError[];
  metrics: CoordinationMetrics;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface AgentMessage {
  id: string;
  fromAgentId: string;
  toAgentId?: string; // null for broadcast
  messageType: string;
  content: unknown;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: string;
  deliveryStatus: 'sent' | 'delivered' | 'acknowledged' | 'failed';
  metadata: Record<string, string | number | boolean | null>;
}

export interface AgentCommunication {
  id: string;
  flowId: string;
  participants: string[];
  messageCount: number;
  communicationType: 'coordination' | 'data_sharing' | 'status_update' | 'error_report';
  startTime: string;
  endTime?: string;
  status: 'active' | 'completed' | 'failed';
  summary: string;
}

export interface AgentState {
  agentId: string;
  status: string;
  currentTask?: string;
  memory: Record<string, string | number | boolean | null>;
  context: Record<string, string | number | boolean | null>;
  performance: AgentPerformance;
  lastUpdate: string;
}

export interface AgentPerformance {
  tasksPerMinute: number;
  averageTaskDuration: number;
  successRate: number;
  errorRate: number;
  qualityScore: number;
  efficiency: number;
}

export interface AgentHealth {
  status: 'healthy' | 'warning' | 'critical' | 'down';
  lastCheck: string;
  issues: HealthIssue[];
  recommendations: string[];
}

export interface AgentDependency {
  agentId: string;
  dependsOn: string[];
  dependencyType: 'data' | 'completion' | 'resource';
  timeout: number;
}

export interface AgentResult {
  agentId: string;
  result: unknown;
  status: 'success' | 'failure' | 'partial';
  error?: ExecutionError;
  metrics: AgentMetrics;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface CoordinationError {
  agentId: string;
  error: ExecutionError;
  impact: 'critical' | 'high' | 'medium' | 'low';
  mitigation: string;
}

export interface CoordinationMetrics {
  coordinationId: string;
  totalAgents: number;
  successfulAgents: number;
  failedAgents: number;
  averageResponseTime: number;
  coordinationOverhead: number;
  synchronizationTime: number;
  communicationLatency: number;
}

export interface AgentContribution {
  agentId: string;
  contribution: unknown;
  weight: number;
  confidence: number;
  quality: number;
  relevance: number;
  metadata: Record<string, string | number | boolean | null>;
}

export interface AgentResourceUsage {
  agentId: string;
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  efficiency: number;
}

export interface HealthIssue {
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  resolved: boolean;
}