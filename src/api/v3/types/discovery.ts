/**
 * Discovery Flow Types for API v3
 * TypeScript interfaces matching the Pydantic schemas from backend
 */

import type { PaginatedResponse, FilterParams, PaginationParams } from './common';

// === Enums (matching backend) ===

export enum FlowPhase {
  INITIALIZATION = 'initialization',
  FIELD_MAPPING = 'field_mapping',
  DATA_CLEANSING = 'data_cleansing',
  INVENTORY_BUILDING = 'inventory_building',
  APP_SERVER_DEPENDENCIES = 'app_server_dependencies',
  APP_APP_DEPENDENCIES = 'app_app_dependencies',
  TECHNICAL_DEBT = 'technical_debt',
  COMPLETED = 'completed'
}

export enum FlowStatus {
  INITIALIZING = 'initializing',
  INITIALIZED = 'initialized',
  IN_PROGRESS = 'in_progress',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum ExecutionMode {
  CREWAI = 'crewai',
  DATABASE = 'database',
  HYBRID = 'hybrid'
}

export enum AssetType {
  SERVER = 'server',
  APPLICATION = 'application',
  DATABASE = 'database',
  NETWORK = 'network',
  STORAGE = 'storage',
  CONTAINER = 'container',
  VIRTUAL_MACHINE = 'virtual_machine',
  SERVICE = 'service',
  UNKNOWN = 'unknown'
}

export enum MigrationComplexity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// === Request Types ===

export interface FlowCreate {
  name: string;
  description?: string;
  client_account_id: string;
  engagement_id: string;
  raw_data: Record<string, any>[];
  metadata?: Record<string, any>;
  execution_mode?: ExecutionMode;
  data_import_id?: string;
}

export interface FlowUpdate {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
  status?: FlowStatus;
  current_phase?: FlowPhase;
}

export interface PhaseExecution {
  phase: FlowPhase;
  data?: Record<string, any>;
  execution_mode?: ExecutionMode;
  human_input?: Record<string, any>;
}

export interface FlowResumeRequest {
  resume_context?: Record<string, any>;
  target_phase?: FlowPhase;
  human_input?: Record<string, any>;
}

export interface FlowPauseRequest {
  reason?: string;
  save_state?: boolean;
}

// === Response Types ===

export interface PhaseStatus {
  phase: FlowPhase;
  status: FlowStatus;
  started_at?: string;
  completed_at?: string;
  progress_percentage: number;
  agent_insights: Record<string, any>[];
  results?: Record<string, any>;
  errors: string[];
}

export interface AssetInfo {
  asset_name: string;
  asset_type: AssetType;
  ip_address?: string;
  operating_system?: string;
  environment?: string;
  location?: string;
  business_owner?: string;
  migration_complexity?: MigrationComplexity;
  migration_priority?: number;
  confidence_score?: number;
}

export interface FlowResponse {
  flow_id: string;
  name: string;
  description?: string;
  status: FlowStatus;
  current_phase: FlowPhase;
  progress_percentage: number;
  created_at: string;
  updated_at: string;
  
  // Multi-tenant context
  client_account_id: string;
  engagement_id: string;
  user_id?: string;
  
  // Phase tracking
  phases_completed: FlowPhase[];
  phases_status: Record<string, PhaseStatus>;
  
  // Execution tracking
  execution_mode: ExecutionMode;
  crewai_status?: string;
  database_status?: string;
  
  // Data and results
  metadata: Record<string, any>;
  field_mapping?: Record<string, any>;
  data_cleansing_results?: Record<string, any>;
  agent_insights: Record<string, any>[];
  
  // Statistics
  records_processed: number;
  records_total: number;
  records_valid: number;
  records_failed: number;
  assets_discovered: number;
  dependencies_mapped: number;
  
  // Asset inventory
  assets: AssetInfo[];
}

export interface FlowStatusResponse {
  flow_id: string;
  status: FlowStatus;
  current_phase: FlowPhase;
  progress_percentage: number;
  updated_at: string;
  
  // Real-time status
  is_running: boolean;
  is_paused: boolean;
  can_resume: boolean;
  can_cancel: boolean;
  
  // Phase details
  current_phase_status?: PhaseStatus;
  next_phase?: FlowPhase;
  
  // Execution details
  execution_mode: ExecutionMode;
  crewai_status?: string;
  database_status?: string;
  
  // Latest insights
  latest_insights: Record<string, any>[];
}

export interface FlowExecutionResponse {
  success: boolean;
  flow_id: string;
  action: string;
  status: FlowStatus;
  message: string;
  timestamp: string;
  
  // Phase execution details
  phase?: FlowPhase;
  phase_status?: PhaseStatus;
  next_phase?: FlowPhase;
  
  // Execution tracking
  crewai_execution?: string;
  database_execution?: string;
  
  // Results
  results?: Record<string, any>;
  agent_insights: Record<string, any>[];
  errors: string[];
}

export interface FlowDeletionResponse {
  success: boolean;
  flow_id: string;
  action: string;
  force_delete: boolean;
  message: string;
  timestamp: string;
  
  // Cleanup details
  cleanup_summary: Record<string, any>;
  crewai_cleanup?: Record<string, any>;
  database_cleanup?: Record<string, any>;
}

export interface FlowHealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  
  // Component health
  components: Record<string, boolean>;
  architecture: string;
  
  // Performance metrics
  active_flows: number;
  total_flows: number;
  avg_response_time_ms?: number;
}

export interface AssetPromotionResponse {
  success: boolean;
  flow_id: string;
  action: string;
  message: string;
  timestamp: string;
  
  // Promotion statistics
  assets_promoted: number;
  assets_skipped: number;
  errors: number;
  statistics: Record<string, any>;
}

// === List and Filter Types ===

export interface FlowListParams extends PaginationParams {
  status?: FlowStatus;
  current_phase?: FlowPhase;
  execution_mode?: ExecutionMode;
  client_account_id?: string;
  engagement_id?: string;
  created_after?: string;
  created_before?: string;
  updated_after?: string;
  updated_before?: string;
}

export interface FlowFilterParams extends FilterParams {
  status?: FlowStatus;
  current_phase?: FlowPhase;
  execution_mode?: ExecutionMode;
}

export type FlowListResponse = PaginatedResponse<FlowResponse>;

// === Stream Types ===

export interface FlowStatusUpdate {
  flow_id: string;
  status: FlowStatus;
  current_phase: FlowPhase;
  progress_percentage: number;
  timestamp: string;
  phase_status?: PhaseStatus;
  agent_insights?: Record<string, any>[];
}

export interface FlowSubscriptionConfig {
  includePhaseUpdates?: boolean;
  includeAgentInsights?: boolean;
  includeErrors?: boolean;
  heartbeatInterval?: number;
}