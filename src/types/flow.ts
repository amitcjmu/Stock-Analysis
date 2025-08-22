/**
 * Flow Type Definitions for Master Flow Orchestrator
 * MFO-080: Update TypeScript type definitions
 *
 * Unified type definitions for all flow types and operations
 */

// Common value types
export type FlowValue = string | number | boolean | Date | null | undefined;
export type FlowData = Record<string, FlowValue | FlowValue[] | FlowData | FlowData[]>;
export type FlowMetadata = Record<string, string | number | boolean>;
export type FlowState = Record<string, FlowValue | FlowValue[] | FlowData>;

// Core Flow Types
export type FlowType =
  | 'discovery'
  | 'collection'
  | 'assessment'
  | 'planning'
  | 'execution'
  | 'modernize'
  | 'finops'
  | 'observability'
  | 'decommission';

export type FlowStatusType =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'deleted';

export type PhaseStatusType =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped';

// Flow Configuration
export interface FlowConfiguration {
  [key: string]: unknown;
  // Common configuration options
  auto_retry?: boolean;
  max_retries?: number;
  timeout_minutes?: number;
  notification_channels?: string[];
  agent_collaboration?: boolean;

  // Flow-specific configurations
  discovery?: DiscoveryFlowConfig;
  collection?: CollectionFlowConfig;
  assessment?: AssessmentFlowConfig;
  planning?: PlanningFlowConfig;
  execution?: ExecutionFlowConfig;
  modernize?: ModernizeFlowConfig;
  finops?: FinOpsFlowConfig;
  observability?: ObservabilityFlowConfig;
  decommission?: DecommissionFlowConfig;
}

// Flow-specific configurations
export interface DiscoveryFlowConfig {
  enable_real_time_validation?: boolean;
  data_sources?: string[];
  mapping_templates?: string[];
  asset_templates?: string[];
}

export interface CollectionFlowConfig {
  automation_tier?: 'manual' | 'semi_automated' | 'fully_automated';
  enable_questionnaire_generation?: boolean;
  enable_adaptive_questionnaires?: boolean;
  platform_detection_scope?: 'basic' | 'comprehensive' | 'targeted';
  data_quality_threshold?: number;
  sixr_alignment_mode?: 'strict' | 'balanced' | 'flexible';
  questionnaire_delivery_method?: 'email' | 'portal' | 'api';
  synthesis_quality_threshold?: number;
}

export interface AssessmentFlowConfig {
  assessment_depth?: 'basic' | 'standard' | 'comprehensive';
  include_business_impact?: boolean;
  risk_tolerance?: 'low' | 'medium' | 'high';
  complexity_thresholds?: Record<string, number>;
}

export interface PlanningFlowConfig {
  optimization_enabled?: boolean;
  dependency_tracking?: boolean;
  resource_constraints?: boolean;
  timeline_optimization?: boolean;
}

export interface ExecutionFlowConfig {
  rollback_enabled?: boolean;
  real_time_monitoring?: boolean;
  automated_validation?: boolean;
  parallel_execution?: boolean;
}

export interface ModernizeFlowConfig {
  cloud_native_patterns?: boolean;
  microservices_assessment?: boolean;
  containerization_analysis?: boolean;
  architecture_patterns?: string[];
}

export interface FinOpsFlowConfig {
  real_time_cost_tracking?: boolean;
  automated_optimization?: boolean;
  budget_alerts?: boolean;
  cost_allocation_tags?: string[];
}

export interface ObservabilityFlowConfig {
  real_time_monitoring?: boolean;
  distributed_tracing?: boolean;
  automated_alerting?: boolean;
  log_retention_days?: number;
}

export interface DecommissionFlowConfig {
  data_backup_required?: boolean;
  approval_workflow?: boolean;
  audit_trail?: boolean;
  retention_period_days?: number;
}

// Phase Information
export interface PhaseInfo {
  name: string;
  display_name: string;
  description: string;
  order: number;
  status: PhaseStatusType;
  required: boolean;
  can_skip: boolean;
  can_pause: boolean;
  can_rollback: boolean;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  progress_percentage?: number;
  inputs?: FlowData;
  outputs?: FlowData;
  errors?: string[];
  warnings?: string[];
}

// Flow Status
export interface FlowStatus {
  flow_id: string;
  flow_type: FlowType;
  flow_name: string;
  status: FlowStatusType;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;

  // Progress information
  current_phase?: string;
  progress_percentage: number;
  phases: PhaseInfo[];

  // Configuration and metadata
  configuration: FlowConfiguration;
  metadata: FlowMetadata;

  // Multi-tenant information
  client_account_id: number;
  engagement_id: number;
  user_id: string;

  // Performance and monitoring
  performance: FlowPerformance;
  errors: FlowError[];
  warnings: FlowWarning[];

  // Agent and crew information
  agent_collaboration_log?: AgentCollaboration[];
  crew_status?: Record<string, string | number | boolean>;

  // State information
  state_version?: number;
  checkpoint_id?: string;
  can_pause: boolean;
  can_resume: boolean;
  can_rollback: boolean;
  can_cancel: boolean;
}

// Performance metrics
export interface FlowPerformance {
  total_duration_seconds?: number;
  phase_durations: Record<string, number>;
  average_phase_duration?: number;
  cpu_usage?: number;
  memory_usage?: number;
  network_usage?: number;
  storage_usage?: number;
  agent_response_times?: Record<string, number>;
}

// Error and warning types
export interface FlowError {
  timestamp: string;
  phase: string;
  error_type: string;
  error_message: string;
  error_details?: FlowData;
  recovery_action?: string;
  is_recoverable: boolean;
}

export interface FlowWarning {
  timestamp: string;
  phase: string;
  warning_type: string;
  warning_message: string;
  warning_details?: FlowData;
  severity: 'low' | 'medium' | 'high';
}

// Agent collaboration
export interface AgentCollaboration {
  timestamp: string;
  phase: string;
  agent_type: string;
  agent_name: string;
  action: string;
  input_data?: FlowData;
  output_data?: FlowData;
  confidence_score?: number;
  processing_time_ms?: number;
}

// Request types
export interface CreateFlowRequest {
  flow_type: FlowType;
  flow_name?: string;
  configuration?: FlowConfiguration;
  initial_state?: FlowState;
  metadata?: FlowMetadata;
}

export interface ExecutePhaseRequest {
  phase_name: string;
  phase_input?: FlowData;
  validation_overrides?: Record<string, boolean>;
  agent_config?: Record<string, string | number | boolean>;
}

// Analytics and reporting
export interface FlowAnalytics {
  total_flows: number;
  flows_by_type: Record<FlowType, number>;
  flows_by_status: Record<FlowStatusType, number>;
  average_completion_time: Record<FlowType, number>;
  success_rates: Record<FlowType, number>;
  most_common_errors: FlowErrorSummary[];
  performance_trends: PerformanceTrend[];
  resource_utilization: ResourceUtilization;
  generated_at: string;
}

export interface FlowErrorSummary {
  error_type: string;
  count: number;
  flow_types: FlowType[];
  recovery_rate: number;
}

export interface PerformanceTrend {
  date: string;
  flow_type: FlowType;
  average_duration: number;
  success_rate: number;
  total_flows: number;
}

export interface ResourceUtilization {
  cpu_average: number;
  memory_average: number;
  storage_average: number;
  network_average: number;
  peak_usage: {
    cpu: number;
    memory: number;
    storage: number;
    network: number;
  };
}

// UI-specific types
export interface FlowUIState {
  selectedFlow?: FlowStatus;
  selectedPhase?: string;
  isLoading: boolean;
  error?: string;
  filters: FlowFilters;
  sortOrder: FlowSortOrder;
  pagination: FlowPagination;
}

export interface FlowFilters {
  flow_type?: FlowType;
  status?: FlowStatusType;
  client_account_id?: number;
  engagement_id?: number;
  date_range?: {
    start: string;
    end: string;
  };
  search_query?: string;
}

export interface FlowSortOrder {
  field: 'created_at' | 'updated_at' | 'flow_name' | 'status' | 'progress_percentage';
  direction: 'asc' | 'desc';
}

export interface FlowPagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

// Component props types
export interface FlowCardProps {
  flow: FlowStatus;
  onSelect?: (flow: FlowStatus) => void;
  onExecute?: (flowId: string, phase: string) => void;
  onPause?: (flowId: string) => void;
  onResume?: (flowId: string) => void;
  onDelete?: (flowId: string) => void;
  showActions?: boolean;
  compact?: boolean;
}

export interface FlowListProps {
  flows: FlowStatus[];
  loading?: boolean;
  error?: string;
  onFlowSelect?: (flow: FlowStatus) => void;
  onFlowAction?: (action: string, flowId: string, data?: unknown) => void;
  filters?: FlowFilters;
  onFiltersChange?: (filters: FlowFilters) => void;
  pagination?: FlowPagination;
  onPageChange?: (page: number) => void;
}

export interface FlowDetailsProps {
  flowId: string;
  flow?: FlowStatus;
  onPhaseExecute?: (phase: string, input?: FlowData) => void;
  onFlowAction?: (action: string, data?: unknown) => void;
  showLogs?: boolean;
  showPerformance?: boolean;
  showAgent?: boolean;
}

export interface FlowCreationProps {
  flowType: FlowType;
  onFlowCreated?: (flow: FlowStatus) => void;
  onCancel?: () => void;
  initialConfig?: Partial<FlowConfiguration>;
  availableTemplates?: FlowTemplate[];
}

export interface FlowTemplate {
  id: string;
  name: string;
  description: string;
  flow_type: FlowType;
  configuration: FlowConfiguration;
  metadata: FlowMetadata;
  is_default?: boolean;
  tags: string[];
}

// Hook return types
export interface UseFlowReturn {
  flow: FlowStatus | null;
  isLoading: boolean;
  error: string | null;
  createFlow: (request: CreateFlowRequest) => Promise<FlowStatus>;
  executePhase: (flowId: string, request: ExecutePhaseRequest) => Promise<{ success: boolean; message?: string; data?: Record<string, unknown> }>;
  pauseFlow: (flowId: string, reason?: string) => Promise<void>;
  resumeFlow: (flowId: string) => Promise<void>;
  deleteFlow: (flowId: string, reason?: string) => Promise<void>;
  refreshFlow: (flowId: string) => Promise<void>;
  startPolling: (flowId: string) => void;
  stopPolling: () => void;
}

export interface UseFlowsReturn {
  flows: FlowStatus[];
  isLoading: boolean;
  error: string | null;
  refreshFlows: () => Promise<void>;
  filterFlows: (filters: FlowFilters) => void;
  sortFlows: (sortOrder: FlowSortOrder) => void;
  searchFlows: (query: string) => void;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  status_code: number;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Event types for real-time updates
export interface FlowEvent {
  type: 'flow_created' | 'flow_updated' | 'phase_started' | 'phase_completed' | 'flow_completed' | 'flow_failed';
  flow_id: string;
  flow_type: FlowType;
  data: FlowData;
  timestamp: string;
}

// Validation types
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  field_errors?: Record<string, string[]>;
}

export interface PhaseValidation {
  phase_name: string;
  required_inputs: string[];
  optional_inputs: string[];
  validation_rules: ValidationRule[];
}

export interface ValidationRule {
  field: string;
  rule_type: 'required' | 'type' | 'range' | 'pattern' | 'custom';
  rule_config: Record<string, FlowValue | FlowValue[]>;
  error_message: string;
}

// Export utility types
export type FlowTypeConfig = {
  [K in FlowType]: {
    display_name: string;
    description: string;
    icon: string;
    color: string;
    default_config: FlowConfiguration[K];
    phases: string[];
  };
};

export type FlowActionType =
  | 'create'
  | 'execute'
  | 'pause'
  | 'resume'
  | 'cancel'
  | 'delete'
  | 'rollback'
  | 'restart';

export type FlowPermission =
  | 'flows.create'
  | 'flows.read'
  | 'flows.update'
  | 'flows.delete'
  | 'flows.execute'
  | 'flows.admin';
