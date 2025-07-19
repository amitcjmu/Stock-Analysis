/**
 * Discovery Flow Management API Types
 * 
 * Type definitions for flow lifecycle management including initialization,
 * status updates, configuration, and flow control operations.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ValidationResult
} from '../shared';

// Flow Management APIs
export interface InitializeDiscoveryFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  configuration?: DiscoveryFlowConfiguration;
  template?: string;
  parentFlowId?: string;
  metadata?: Record<string, any>;
}

export interface InitializeDiscoveryFlowResponse extends BaseApiResponse<DiscoveryFlowData> {
  data: DiscoveryFlowData;
  flowId: string;
  initialState: FlowState;
  nextSteps: string[];
  recommendations?: string[];
}

export interface UpdateDiscoveryFlowRequest extends BaseApiRequest {
  flowId: string;
  configuration?: Partial<DiscoveryFlowConfiguration>;
  status?: FlowStatus;
  metadata?: Record<string, any>;
  phase?: string;
  progress?: number;
}

export interface UpdateDiscoveryFlowResponse extends BaseApiResponse<DiscoveryFlowData> {
  data: DiscoveryFlowData;
  previousState: FlowState;
  currentState: FlowState;
  changesApplied: string[];
}

export interface GetDiscoveryFlowStatusRequest extends BaseApiRequest {
  flowId: string;
  includeDetails?: boolean;
  includeLogs?: boolean;
}

export interface GetDiscoveryFlowStatusResponse extends BaseApiResponse<FlowStatusData> {
  data: FlowStatusData;
  currentPhase: string;
  progress: number;
  estimatedCompletion?: string;
  issues?: FlowIssue[];
}

export interface ControlDiscoveryFlowRequest extends BaseApiRequest {
  flowId: string;
  action: FlowAction;
  parameters?: Record<string, any>;
  reason?: string;
}

export interface ControlDiscoveryFlowResponse extends BaseApiResponse<FlowActionResult> {
  data: FlowActionResult;
  newStatus: FlowStatus;
  actionTaken: FlowAction;
  timestamp: string;
}

// Flow Data Models
export interface DiscoveryFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  status: FlowStatus;
  currentPhase: string;
  progress: number;
  configuration: DiscoveryFlowConfiguration;
  context: MultiTenantContext;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  metadata: Record<string, any>;
  phases: FlowPhase[];
  state: FlowState;
}

export interface DiscoveryFlowConfiguration {
  enableAutoMapping?: boolean;
  mappingConfidenceThreshold?: number;
  enableQualityValidation?: boolean;
  requireManualApproval?: boolean;
  enableProgressNotifications?: boolean;
  customRules?: CustomRule[];
  agentSettings?: AgentSettings;
  timeoutSettings?: TimeoutSettings;
  retrySettings?: RetrySettings;
}

export interface FlowState {
  currentPhase: string;
  phaseData: Record<string, any>;
  globalData: Record<string, any>;
  flags: Record<string, boolean>;
  timestamps: Record<string, string>;
  metrics: Record<string, number>;
}

export interface FlowPhase {
  name: string;
  displayName: string;
  description: string;
  status: PhaseStatus;
  progress: number;
  startTime?: string;
  endTime?: string;
  estimatedDuration?: number;
  dependencies: string[];
  outputs: Record<string, any>;
  metadata: Record<string, any>;
}

export interface FlowStatusData {
  flowId: string;
  status: FlowStatus;
  currentPhase: string;
  progress: number;
  totalPhases: number;
  completedPhases: number;
  startTime: string;
  lastUpdated: string;
  estimatedCompletion?: string;
  performance: PerformanceMetrics;
  health: HealthStatus;
}

export interface FlowIssue {
  id: string;
  type: IssueType;
  severity: IssueSeverity;
  message: string;
  details?: string;
  phase?: string;
  timestamp: string;
  resolution?: IssueResolution;
}

export interface FlowActionResult {
  actionId: string;
  action: FlowAction;
  success: boolean;
  message: string;
  details?: Record<string, any>;
  sideEffects?: string[];
}

export interface CustomRule {
  id: string;
  name: string;
  description: string;
  condition: string;
  action: string;
  enabled: boolean;
  priority: number;
}

export interface AgentSettings {
  enableAgentAssistance?: boolean;
  agentModel?: string;
  maxTokens?: number;
  temperature?: number;
  customPrompts?: Record<string, string>;
}

export interface TimeoutSettings {
  phaseTimeout?: number;
  operationTimeout?: number;
  totalFlowTimeout?: number;
}

export interface RetrySettings {
  maxRetries?: number;
  retryDelay?: number;
  backoffMultiplier?: number;
}

export interface PerformanceMetrics {
  averagePhaseTime: number;
  totalExecutionTime: number;
  throughputRate: number;
  errorRate: number;
  resourceUtilization: Record<string, number>;
}

export interface HealthStatus {
  overall: HealthLevel;
  components: Record<string, HealthLevel>;
  lastCheck: string;
  issues: string[];
}

export interface IssueResolution {
  id: string;
  action: string;
  timestamp: string;
  resolvedBy: string;
  notes?: string;
}

// Enums and Types
export type FlowStatus = 'initializing' | 'active' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'archived';
export type PhaseStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'blocked';
export type FlowAction = 'start' | 'pause' | 'resume' | 'stop' | 'restart' | 'cancel' | 'archive';
export type IssueType = 'error' | 'warning' | 'validation' | 'performance' | 'configuration';
export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical';
export type HealthLevel = 'healthy' | 'warning' | 'critical' | 'unknown';