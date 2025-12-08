/**
 * Discovery Flow Management API Types
 *
 * Type definitions for flow lifecycle management including initialization,
 * status updates, configuration, and flow control operations.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ValidationResult
} from '../shared';

// Common types for flow data
export type FlowValue = string | number | boolean | Date | null | undefined;
export type FlowDataRecord = Record<string, FlowValue | FlowValue[] | FlowDataRecord | FlowDataRecord[]>;
export type FlowMetadata = Record<string, string | number | boolean>;

// Flow Management APIs
export interface InitializeDiscoveryFlowRequest extends BaseApiRequest {
  flow_name: string;
  flow_description?: string;
  context: MultiTenantContext;
  configuration?: DiscoveryFlowConfiguration;
  template?: string;
  parent_flow_id?: string;
  metadata?: FlowMetadata;
}

export interface InitializeDiscoveryFlowResponse extends BaseApiResponse<DiscoveryFlowData> {
  data: DiscoveryFlowData;
  flow_id: string;
  initial_state: FlowState;
  next_steps: string[];
  recommendations?: string[];
}

export interface UpdateDiscoveryFlowRequest extends BaseApiRequest {
  flow_id: string;
  configuration?: Partial<DiscoveryFlowConfiguration>;
  status?: FlowStatus;
  metadata?: FlowMetadata;
  phase?: string;
  progress?: number;
}

export interface UpdateDiscoveryFlowResponse extends BaseApiResponse<DiscoveryFlowData> {
  data: DiscoveryFlowData;
  previous_state: FlowState;
  current_state: FlowState;
  changes_applied: string[];
}

export interface GetDiscoveryFlowStatusRequest extends BaseApiRequest {
  flow_id: string;
  include_details?: boolean;
  include_logs?: boolean;
}

export interface GetDiscoveryFlowStatusResponse extends BaseApiResponse<FlowStatusData> {
  data: FlowStatusData;
  current_phase: string;
  progress: number;
  estimated_completion?: string;
  issues?: FlowIssue[];
}

export interface ControlDiscoveryFlowRequest extends BaseApiRequest {
  flow_id: string;
  action: FlowAction;
  parameters?: FlowDataRecord;
  reason?: string;
}

export interface ControlDiscoveryFlowResponse extends BaseApiResponse<FlowActionResult> {
  data: FlowActionResult;
  new_status: FlowStatus;
  action_taken: FlowAction;
  timestamp: string;
}

// Flow Data Models
/**
 * DiscoveryFlowData type
 *
 * @deprecated Import from '@/types/discovery' instead.
 * This export is maintained for backward compatibility.
 * The authoritative type is defined in src/types/discovery.ts
 *
 * Note: The unified type in src/types/discovery.ts is more comprehensive
 * and includes all fields from the actual API response. For API-specific
 * types that extend DiscoveryFlowData, use the base type and add
 * API-specific fields as needed.
 */
export type { DiscoveryFlowData } from '../../discovery';

export interface DiscoveryFlowConfiguration {
  enable_auto_mapping?: boolean;
  mapping_confidence_threshold?: number;
  enable_quality_validation?: boolean;
  require_manual_approval?: boolean;
  enable_progress_notifications?: boolean;
  custom_rules?: CustomRule[];
  agent_settings?: AgentSettings;
  timeout_settings?: TimeoutSettings;
  retry_settings?: RetrySettings;
}

export interface FlowState {
  current_phase: string;
  phase_data: FlowDataRecord;
  global_data: FlowDataRecord;
  flags: Record<string, boolean>;
  timestamps: Record<string, string>;
  metrics: Record<string, number>;
}

export interface FlowPhase {
  name: string;
  display_name: string;
  description: string;
  status: PhaseStatus;
  progress: number;
  start_time?: string;
  end_time?: string;
  estimated_duration?: number;
  dependencies: string[];
  outputs: FlowDataRecord;
  metadata: FlowMetadata;
}

export interface FlowStatusData {
  flow_id: string;
  status: FlowStatus;
  current_phase: string;
  progress: number;
  total_phases: number;
  completed_phases: number;
  start_time: string;
  last_updated: string;
  estimated_completion?: string;
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
  action_id: string;
  action: FlowAction;
  success: boolean;
  message: string;
  details?: FlowDataRecord;
  side_effects?: string[];
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
  enable_agent_assistance?: boolean;
  agent_model?: string;
  max_tokens?: number;
  temperature?: number;
  custom_prompts?: Record<string, string>;
}

export interface TimeoutSettings {
  phase_timeout?: number;
  operation_timeout?: number;
  total_flow_timeout?: number;
}

export interface RetrySettings {
  max_retries?: number;
  retry_delay?: number;
  backoff_multiplier?: number;
}

export interface PerformanceMetrics {
  average_phase_time: number;
  total_execution_time: number;
  throughput_rate: number;
  error_rate: number;
  resource_utilization: Record<string, number>;
}

export interface HealthStatus {
  overall: HealthLevel;
  components: Record<string, HealthLevel>;
  last_check: string;
  issues: string[];
}

export interface IssueResolution {
  id: string;
  action: string;
  timestamp: string;
  resolved_by: string;
  notes?: string;
}

// Enums and Types
export type FlowStatus = 'initializing' | 'active' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'archived';
export type PhaseStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'blocked';
export type FlowAction = 'start' | 'pause' | 'resume' | 'stop' | 'restart' | 'cancel' | 'archive';
export type IssueType = 'error' | 'warning' | 'validation' | 'performance' | 'configuration';
export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical';
export type HealthLevel = 'healthy' | 'warning' | 'critical' | 'unknown';
