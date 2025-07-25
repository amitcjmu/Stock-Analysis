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
  flowId: string;
  includeHistory?: boolean;
  includeAgentStates?: boolean;
  includeCheckpoints?: boolean;
}

export interface GetFlowStateResponse extends GetResponse<FlowStateDetail> {
  data: FlowStateDetail;
  stateHistory?: FlowStateHistory[];
  availableTransitions?: FlowTransition[];
}

export interface UpdateFlowStateRequest extends UpdateRequest<Partial<FlowState>> {
  flowId: string;
  data: Partial<FlowState>;
  validateTransition?: boolean;
  createCheckpoint?: boolean;
  notifyAgents?: boolean;
}

export interface UpdateFlowStateResponse extends UpdateResponse<FlowState> {
  data: FlowState;
  transitionResult?: StateTransitionResult;
  checkpointId?: string;
  notifications?: StateChangeNotification[];
}

export interface TransitionFlowPhaseRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  targetPhase: string;
  skipValidation?: boolean;
  force?: boolean;
  reason?: string;
}

export interface TransitionFlowPhaseResponse extends BaseApiResponse<PhaseTransitionResult> {
  data: PhaseTransitionResult;
  newState: FlowState;
  validationResults?: ValidationResult[];
  warnings?: string[];
}

// Flow State Models
export interface FlowState {
  flowId: string;
  currentPhase: string;
  nextPhase?: string;
  previousPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseData: Record<string, string | number | boolean | null>;
  agentStates: Record<string, AgentState>;
  sharedData: Record<string, string | number | boolean | null>;
  checkpoints: StateCheckpoint[];
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface FlowStateDetail extends FlowState {
  stateHistory: FlowStateHistory[];
  agentStates: Record<string, AgentStateDetail>;
  validationResults: ValidationResult[];
  performanceMetrics: StatePerformanceMetrics;
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
  agentId: string;
  status: AgentStatus;
  currentTask?: string;
  taskQueue: string[];
  configuration: AgentConfiguration;
  lastActivity: string;
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
  learningEnabled: boolean;
}

export interface AgentPerformance {
  tasksCompleted: number;
  averageTaskTime: number;
  successRate: number;
  qualityScore: number;
  learningProgress: number;
  userRating?: number;
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
  agentId: string;
  type: InsightType;
  category: string;
  confidence: number;
  description: string;
  recommendations?: string[];
  evidence?: Record<string, string | number | boolean | null>;
  createdAt: string;
}

export interface AgentClarification {
  id: string;
  agentId: string;
  question: string;
  context: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'answered' | 'dismissed';
  createdAt: string;
  answeredAt?: string;
  answer?: string;
}

export interface StateCheckpoint {
  id: string;
  timestamp: string;
  phase: string;
  data: Record<string, string | number | boolean | null>;
  description?: string;
  createdBy: string;
  restoreAvailable: boolean;
}

export interface StatePerformanceMetrics {
  transitionTime: number;
  validationTime: number;
  persistenceTime: number;
  agentResponseTime: number;
  overallEfficiency: number;
}

export interface FlowTransition {
  fromPhase: string;
  toPhase: string;
  conditions: TransitionCondition[];
  validations: ValidationRule[];
  automated: boolean;
  estimatedDuration?: number;
}

export interface TransitionCondition {
  type: 'completion' | 'approval' | 'validation' | 'manual' | 'time';
  description: string;
  required: boolean;
  currentStatus: 'met' | 'not_met' | 'pending';
  details?: Record<string, string | number | boolean | null>;
}

export interface StateTransitionResult {
  success: boolean;
  fromPhase: string;
  toPhase: string;
  transitionTime: number;
  validationResults: ValidationResult[];
  warnings: string[];
  rollbackAvailable: boolean;
}

export interface PhaseTransitionResult extends StateTransitionResult {
  agentNotifications: AgentNotification[];
  nextSteps: string[];
  automaticActions: AutomaticAction[];
}

export interface AgentNotification {
  agentId: string;
  type: 'phase_change' | 'task_assignment' | 'clarification_request' | 'alert';
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  actionRequired: boolean;
  deadline?: string;
}

export interface AutomaticAction {
  type: string;
  description: string;
  scheduled: boolean;
  scheduledTime?: string;
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
