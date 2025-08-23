/**
 * Flow Models
 *
 * Type definitions for flow configuration, execution, status, and state management.
 */

import type { FlowExecutionContext, TimeRange, ExecutionError, ValidationResult, RetryPolicy, ExecutionConstraints } from '../base-types'
import type { ExecutionWarning } from '../base-types'

// Flow Configuration and Execution Models
export interface FlowInitializationConfig {
  flow_type: string;
  flow_name: string;
  flow_description?: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  configuration: FlowConfiguration;
  parent_flow_id?: string;
  dependencies?: string[];
  priority?: 'low' | 'medium' | 'high' | 'critical';
  scheduled_start?: string;
  timeout?: number;
}

export interface FlowExecutionResult {
  flow_id: string;
  execution_id: string;
  status: 'started' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  result?: unknown;
  error?: ExecutionError;
  metrics: ExecutionMetrics;
  start_time: string;
  end_time?: string;
  duration?: number;
}

export interface FlowStatusDetail {
  flow_id: string;
  flow_type: string;
  status: FlowStatus;
  current_phase: string;
  next_phase?: string;
  progress: number;
  phases: PhaseStatus[];
  agents: AgentStatus[];
  crews: CrewStatus[];
  child_flows: ChildFlowStatus[];
  parent_flow_id?: string;
  metrics: FlowMetrics;
  events: RecentEvent[];
  errors: ExecutionError[];
  warnings: ExecutionWarning[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface FlowHistoryEntry {
  id: string;
  flow_id: string;
  timestamp: string;
  event_type: string;
  event_data: Record<string, string | number | boolean | null>;
  user_id?: string;
  agent_id?: string;
  phase_id?: string;
  description: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface ActiveFlowSummary {
  flow_id: string;
  flow_type: string;
  flow_name: string;
  status: FlowStatus;
  progress: number;
  current_phase: string;
  assigned_agents: number;
  active_crews: number;
  child_flows: number;
  priority: string;
  start_time: string;
  estimated_completion?: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
}

export interface FlowStateData {
  flow_id: string;
  flow_type: string;
  current_phase: string;
  next_phase?: string;
  previous_phase?: string;
  phase_completion: Record<string, boolean>;
  phase_data: Record<string, string | number | boolean | null>;
  agent_states: Record<string, AgentState>;
  crew_states: Record<string, CrewState>;
  shared_data: Record<string, string | number | boolean | null>;
  checkpoints: StateCheckpoint[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface FlowConfiguration {
  max_duration: number;
  retry_policy: RetryPolicy;
  checkpoint_interval: number;
  parallelism: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  resources: ResourceRequirements;
  notifications: NotificationConfig;
}

export interface ExecutionMetrics {
  execution_id: string;
  start_time: string;
  end_time?: string;
  duration: number;
  cpu_time: number;
  memory_peak: number;
  network_io: number;
  disk_io: number;
  task_count: number;
  error_count: number;
  warning_count: number;
  quality_score: number;
}

export interface PhaseStatus {
  phase_id: string;
  phase_name: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  start_time?: string;
  end_time?: string;
  duration?: number;
  agents: string[];
  crews: string[];
  dependencies: string[];
  outputs: Record<string, string | number | boolean | null>;
}

export interface ChildFlowStatus {
  flow_id: string;
  flow_type: string;
  status: FlowStatus;
  progress: number;
  current_phase: string;
  relationship: 'child' | 'sibling' | 'dependency';
  created_at: string;
}

export interface RecentEvent {
  id: string;
  event_type: string;
  description: string;
  timestamp: string;
  severity: string;
  source: string;
}

export interface AgentState {
  agent_id: string;
  status: string;
  current_task?: string;
  memory: Record<string, string | number | boolean | null>;
  context: Record<string, string | number | boolean | null>;
  performance: AgentPerformance;
  last_update: string;
}

export interface CrewState {
  crew_id: string;
  status: string;
  current_task?: string;
  completed_tasks: number;
  total_tasks: number;
  agents: string[];
  shared_memory: Record<string, string | number | boolean | null>;
  last_update: string;
}

export interface StateCheckpoint {
  id: string;
  timestamp: string;
  phase: string;
  data: Record<string, string | number | boolean | null>;
  hash: string;
  size: number;
  created_by: string;
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
  agent_id: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  current_task?: string;
  current_flow_id?: string;
  performance: AgentPerformance;
  health: AgentHealth;
  last_heartbeat: string;
  error_count: number;
  warning_count: number;
}

export interface CrewStatus {
  crew_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled';
  current_task?: string;
  completed_tasks: number;
  total_tasks: number;
  progress: number;
  agents: AgentStatus[];
  error?: ExecutionError;
  start_time?: string;
  estimated_completion?: string;
}

export interface FlowMetrics {
  flow_id: string;
  execution_time: number;
  cpu_usage: number;
  memory_usage: number;
  network_io: number;
  disk_io: number;
  task_count: number;
  completed_tasks: number;
  failed_tasks: number;
  retry_count: number;
  error_rate: number;
  throughput: number;
  latency: number;
  resource_efficiency: number;
  quality_score: number;
  user_satisfaction: number;
}

export interface AgentPerformance {
  tasks_per_minute: number;
  average_task_duration: number;
  success_rate: number;
  error_rate: number;
  quality_score: number;
  efficiency: number;
}

export interface AgentHealth {
  status: 'healthy' | 'warning' | 'critical' | 'down';
  last_check: string;
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
