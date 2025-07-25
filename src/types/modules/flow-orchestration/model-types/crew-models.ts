/**
 * Crew Models
 *
 * Type definitions for crew configuration, execution, status, results, and metrics.
 */

import type { ExecutionError, ExecutionConstraints, RetryPolicy, TimeRange } from '../base-types'
import type { AgentConfiguration } from '../base-types'

import type { AgentStatus, AgentResult } from './agent-models'
import type { AgentInstance, AgentResourceUsage } from './agent-models'

// Crew Models
export interface CrewConfiguration {
  name: string;
  description: string;
  agents: AgentConfiguration[];
  tasks: CrewTask[];
  process: 'sequential' | 'hierarchical' | 'consensus';
  manager?: AgentConfiguration;
  maxIterations: number;
  timeout: number;
  memoryEnabled: boolean;
  planningEnabled: boolean;
  outputFormat: 'json' | 'text' | 'structured';
  callbacks: CrewCallback[];
}

export interface CrewInstance {
  id: string;
  configuration: CrewConfiguration;
  status: CrewStatus;
  agents: AgentInstance[];
  tasks: CrewTaskInstance[];
  manager?: AgentInstance;
  createdAt: string;
  deployedAt?: string;
}

export interface CrewExecutionContext {
  flowId: string;
  executionId: string;
  inputs: Record<string, string | number | boolean | null>;
  parameters: Record<string, string | number | boolean | null>;
  context: Record<string, string | number | boolean | null>;
  constraints: ExecutionConstraints;
  callbacks: CrewCallback[];
}

export interface CrewExecutionResult {
  crewId: string;
  executionId: string;
  status: 'completed' | 'failed' | 'cancelled';
  result: unknown;
  taskResults: CrewTaskResult[];
  agentResults: AgentResult[];
  metrics: CrewMetrics;
  error?: ExecutionError;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface CrewStatus {
  crewId: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  currentTask?: string;
  completedTasks: number;
  totalTasks: number;
  progress: number;
  agents: AgentStatus[];
  error?: ExecutionError;
  startTime?: string;
  estimatedCompletion?: string;
}

export interface CrewResults {
  crewId: string;
  executionId: string;
  finalResult: unknown;
  taskResults: CrewTaskResult[];
  agentContributions: AgentContribution[];
  consensusReached: boolean;
  qualityScore: number;
  confidence: number;
  recommendations: string[];
  metadata: Record<string, string | number | boolean | null>;
}

export interface CrewMetrics {
  crewId: string;
  executionCount: number;
  successRate: number;
  averageExecutionTime: number;
  resourceUtilization: ResourceUtilization;
  qualityMetrics: QualityMetrics;
  collaborationMetrics: CollaborationMetrics;
  timeRange: TimeRange;
}

export interface CrewState {
  crewId: string;
  status: string;
  currentTask?: string;
  completedTasks: number;
  totalTasks: number;
  agents: string[];
  sharedMemory: Record<string, string | number | boolean | null>;
  lastUpdate: string;
}

export interface CrewTask {
  id: string;
  name: string;
  description: string;
  agentId: string;
  dependencies: string[];
  inputs: Record<string, string | number | boolean | null>;
  outputs: Record<string, string | number | boolean | null>;
  timeout: number;
  retryPolicy: RetryPolicy;
  priority: number;
}

export interface CrewTaskInstance {
  id: string;
  task: CrewTask;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  agentId: string;
  startTime?: string;
  endTime?: string;
  duration?: number;
  result?: unknown;
  error?: ExecutionError;
  retryCount: number;
}

export interface CrewCallback {
  event: string;
  handler: string;
  parameters: Record<string, string | number | boolean | null>;
}

export interface CrewTaskResult {
  taskId: string;
  result: unknown;
  status: 'success' | 'failure' | 'partial';
  agentId: string;
  error?: ExecutionError;
  metrics: TaskMetrics;
  startTime: string;
  endTime: string;
  duration: number;
}

export interface CrewResourceUsage {
  crewId: string;
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  agents: AgentResourceUsage[];
  efficiency: number;
}

export interface ResourceUtilization {
  cpu: number;
  memory: number;
  network: number;
  disk: number;
  efficiency: number;
}

export interface QualityMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  consistency: number;
  completeness: number;
}

export interface CollaborationMetrics {
  communicationFrequency: number;
  consensusTime: number;
  conflictRate: number;
  collaborationEfficiency: number;
  teamCohesion: number;
}

export interface TaskMetrics {
  taskId: string;
  executionTime: number;
  cpuUsage: number;
  memoryUsage: number;
  networkIO: number;
  diskIO: number;
  qualityScore: number;
  errorCount: number;
  retryCount: number;
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
