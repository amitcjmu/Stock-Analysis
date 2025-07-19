/**
 * Flow Models
 * 
 * Type definitions for flow configuration, execution, status, and state management.
 */

import {
  FlowExecutionContext,
  TimeRange,
  ExecutionError,
  ExecutionWarning,
  ValidationResult,
  RetryPolicy,
  ExecutionConstraints
} from '../base-types';

// Flow Configuration and Execution Models
export interface FlowInitializationConfig {
  flowType: string;
  flowName: string;
  flowDescription?: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  configuration: FlowConfiguration;
  parentFlowId?: string;
  dependencies?: string[];
  priority?: 'low' | 'medium' | 'high' | 'critical';
  scheduledStart?: string;
  timeout?: number;
}

export interface FlowExecutionResult {
  flowId: string;
  executionId: string;
  status: 'started' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  result?: any;
  error?: ExecutionError;
  metrics: ExecutionMetrics;
  startTime: string;
  endTime?: string;
  duration?: number;
}

export interface FlowStatusDetail {
  flowId: string;
  flowType: string;
  status: FlowStatus;
  currentPhase: string;
  nextPhase?: string;
  progress: number;
  phases: PhaseStatus[];
  agents: AgentStatus[];
  crews: CrewStatus[];
  childFlows: ChildFlowStatus[];
  parentFlowId?: string;
  metrics: FlowMetrics;
  events: RecentEvent[];
  errors: ExecutionError[];
  warnings: ExecutionWarning[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface FlowHistoryEntry {
  id: string;
  flowId: string;
  timestamp: string;
  eventType: string;
  eventData: Record<string, any>;
  userId?: string;
  agentId?: string;
  phaseId?: string;
  description: string;
  metadata: Record<string, any>;
}

export interface ActiveFlowSummary {
  flowId: string;
  flowType: string;
  flowName: string;
  status: FlowStatus;
  progress: number;
  currentPhase: string;
  assignedAgents: number;
  activeCrews: number;
  childFlows: number;
  priority: string;
  startTime: string;
  estimatedCompletion?: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
}

export interface FlowStateData {
  flowId: string;
  flowType: string;
  currentPhase: string;
  nextPhase?: string;
  previousPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseData: Record<string, any>;
  agentStates: Record<string, AgentState>;
  crewStates: Record<string, CrewState>;
  sharedData: Record<string, any>;
  checkpoints: StateCheckpoint[];
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface FlowConfiguration {
  maxDuration: number;
  retryPolicy: RetryPolicy;
  checkpointInterval: number;
  parallelism: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  resources: ResourceRequirements;
  notifications: NotificationConfig;
}

export interface ExecutionMetrics {
  executionId: string;
  startTime: string;
  endTime?: string;
  duration: number;
  cpuTime: number;
  memoryPeak: number;
  networkIO: number;
  diskIO: number;
  taskCount: number;
  errorCount: number;
  warningCount: number;
  qualityScore: number;
}

export interface PhaseStatus {
  phaseId: string;
  phaseName: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  startTime?: string;
  endTime?: string;
  duration?: number;
  agents: string[];
  crews: string[];
  dependencies: string[];
  outputs: Record<string, any>;
}

export interface ChildFlowStatus {
  flowId: string;
  flowType: string;
  status: FlowStatus;
  progress: number;
  currentPhase: string;
  relationship: 'child' | 'sibling' | 'dependency';
  createdAt: string;
}

export interface RecentEvent {
  id: string;
  eventType: string;
  description: string;
  timestamp: string;
  severity: string;
  source: string;
}

export interface AgentState {
  agentId: string;
  status: string;
  currentTask?: string;
  memory: Record<string, any>;
  context: Record<string, any>;
  performance: AgentPerformance;
  lastUpdate: string;
}

export interface CrewState {
  crewId: string;
  status: string;
  currentTask?: string;
  completedTasks: number;
  totalTasks: number;
  agents: string[];
  sharedMemory: Record<string, any>;
  lastUpdate: string;
}

export interface StateCheckpoint {
  id: string;
  timestamp: string;
  phase: string;
  data: Record<string, any>;
  hash: string;
  size: number;
  createdBy: string;
}

export interface ResourceRequirements {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  agents: number;
  crews: number;
}

export interface NotificationConfig {
  enabled: boolean;
  channels: string[];
  events: string[];
  threshold: string;
  recipients: string[];
}

export type FlowStatus = 'initializing' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'timeout';

// Forward declarations for referenced types from other modules
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

export interface HealthIssue {
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  resolved: boolean;
}