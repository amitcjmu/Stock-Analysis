/**
 * Discovery Flow State Management API Types
 *
 * Type definitions for flow state operations including state transitions,
 * checkpoints, agent states, and state history management.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  GetRequest,
  GetResponse,
  UpdateRequest,
  UpdateResponse,
  ValidationResult,
  MultiTenantContext
} from '../shared';

// Flow State Management APIs
export interface GetFlowStateRequest extends GetRequest {
  flow_id: string;
  include_history?: boolean;
  include_agent_states?: boolean;
  include_checkpoints?: boolean;
}

export interface GetFlowStateResponse extends GetResponse<FlowStateDetail> {
  data: FlowStateDetail;
  state_history?: FlowStateHistory[];
  available_transitions?: FlowTransition[];
}

export interface UpdateFlowStateRequest extends UpdateRequest<Partial<FlowState>> {
  flow_id: string;
  data: Partial<FlowState>;
  validate_transition?: boolean;
  create_checkpoint?: boolean;
  notify_agents?: boolean;
}

export interface UpdateFlowStateResponse extends UpdateResponse<FlowState> {
  data: FlowState;
  transition_result?: StateTransitionResult;
  checkpoint_id?: string;
  notifications?: StateChangeNotification[];
}

export interface TransitionFlowPhaseRequest extends BaseApiRequest {
  flow_id: string;
  context: MultiTenantContext;
  target_phase: string;
  skip_validation?: boolean;
  force?: boolean;
  reason?: string;
}

export interface TransitionFlowPhaseResponse extends BaseApiResponse<PhaseTransitionResult> {
  data: PhaseTransitionResult;
  new_state: FlowState;
  validation_results?: ValidationResult[];
  warnings?: string[];
}

// Flow State Models
export interface FlowState {
  flow_id: string;
  current_phase: string;
  next_phase?: string;
  previous_phase?: string;
  // FIX #447: Support both data formats for backward compatibility
  // Backend returns phases_completed as array, but some legacy code uses phase_completion object
  phase_completion?: Record<string, boolean>; // Legacy format (object)
  phases_completed?: string[]; // New format (array) - backend standard
  phase_data: Record<string, string | number | boolean | null>;
  agent_states: Record<string, AgentState>;
  shared_data: Record<string, string | number | boolean | null>;
  checkpoints: StateCheckpoint[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface FlowStateDetail extends FlowState {
  state_history: FlowStateHistory[];
  agent_states: Record<string, AgentStateDetail>;
  validation_results: ValidationResult[];
  performance_metrics: StatePerformanceMetrics;
}

export interface FlowStateHistory {
  timestamp: string;
  phase: string;
  action: string;
  actor: string;
  changes: Record<string, string | number | boolean | null>;
  reason?: string;
}

export interface AgentState {
  agent_id: string;
  status: AgentStatus;
  current_task?: string;
  task_queue: string[];
  configuration: AgentConfiguration;
  last_activity: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface AgentStateDetail extends AgentState {
  performance: AgentPerformance;
  history: AgentStateHistory[];
  insights: AgentInsight[];
  clarifications: AgentClarification[];
}

export interface AgentConfiguration {
  capabilities: string[];
  preferences: Record<string, string | number | boolean | null>;
  constraints: Record<string, string | number | boolean | null>;
  learning_enabled: boolean;
}

export interface AgentPerformance {
  tasks_completed: number;
  average_task_time: number;
  success_rate: number;
  quality_score: number;
  learning_progress: number;
  user_rating?: number;
}

export interface AgentStateHistory {
  timestamp: string;
  status: string;
  task?: string;
  changes: Record<string, string | number | boolean | null>;
  performance?: AgentPerformance;
}

export interface AgentInsight {
  id: string;
  agent_id: string;
  type: InsightType;
  category: string;
  confidence: number;
  description: string;
  recommendations?: string[];
  evidence?: Record<string, string | number | boolean | null>;
  created_at: string;
}

export interface AgentClarification {
  id: string;
  agent_id: string;
  question: string;
  context: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'answered' | 'dismissed';
  created_at: string;
  answered_at?: string;
  answer?: string;
}

export interface StateCheckpoint {
  id: string;
  timestamp: string;
  phase: string;
  data: Record<string, string | number | boolean | null>;
  description?: string;
  created_by: string;
  restore_available: boolean;
}

export interface StatePerformanceMetrics {
  transition_time: number;
  validation_time: number;
  persistence_time: number;
  agent_response_time: number;
  overall_efficiency: number;
}

export interface FlowTransition {
  from_phase: string;
  to_phase: string;
  conditions: TransitionCondition[];
  validations: ValidationRule[];
  automated: boolean;
  estimated_duration?: number;
}

export interface TransitionCondition {
  type: 'completion' | 'approval' | 'validation' | 'manual' | 'time';
  description: string;
  required: boolean;
  current_status: 'met' | 'not_met' | 'pending';
  details?: Record<string, string | number | boolean | null>;
}

export interface StateTransitionResult {
  success: boolean;
  from_phase: string;
  to_phase: string;
  transition_time: number;
  validation_results: ValidationResult[];
  warnings: string[];
  rollback_available: boolean;
}

export interface PhaseTransitionResult extends StateTransitionResult {
  agent_notifications: AgentNotification[];
  next_steps: string[];
  automatic_actions: AutomaticAction[];
}

export interface AgentNotification {
  agent_id: string;
  type: 'phase_change' | 'task_assignment' | 'clarification_request' | 'alert';
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  action_required: boolean;
  deadline?: string;
}

export interface AutomaticAction {
  type: string;
  description: string;
  scheduled: boolean;
  scheduled_time?: string;
  dependencies?: string[];
}

export interface StateChangeNotification {
  type: 'user' | 'agent' | 'system' | 'webhook';
  target: string;
  message: string;
  channels: string[];
  sent: boolean;
  error?: string;
}

export interface ValidationRule {
  id: string;
  type: string;
  parameters: Record<string, string | number | boolean | null>;
  errorMessage: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// Enums and Types
export type AgentStatus = 'idle' | 'active' | 'busy' | 'error' | 'offline' | 'maintenance';
export type InsightType = 'optimization' | 'warning' | 'recommendation' | 'observation' | 'prediction';
