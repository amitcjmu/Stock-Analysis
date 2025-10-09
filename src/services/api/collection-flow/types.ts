import type {
  CollectionFlow,
  CleanupResult,
  FlowContinueResult,
} from "@/hooks/collection/useCollectionFlowManagement";
import type { BaseMetadata } from "../../../types/shared/metadata-types";
import type {
  MaintenanceWindow,
  VendorProduct,
  CompletenessMetrics,
} from "@/components/collection/types";

// Error interface for proper type handling
export interface ApiError {
  status?: number;
  response?: {
    status?: number;
    data?: {
      detail?: unknown;
    };
    detail?: unknown;
  };
}

export interface CollectionFlowConfiguration extends BaseMetadata {
  automation_tier?: "basic" | "standard" | "advanced" | "enterprise";
  platform_scope?: string[];
  collection_methods?: string[];
  validation_rules?: ValidationRuleConfig[];
  notification_settings?: NotificationConfig;
}

export interface ValidationRuleConfig {
  rule_id: string;
  rule_type: "required" | "format" | "range" | "dependency";
  field_path: string;
  validation_criteria: Record<string, unknown>;
  error_message: string;
  severity: "error" | "warning" | "info";
}

export interface NotificationConfig {
  email_notifications: boolean;
  slack_notifications: boolean;
  webhook_notifications: boolean;
  notification_levels: Array<"error" | "warning" | "info" | "success">;
}

export interface CollectionFlowCreateRequest {
  automation_tier?: string;
  collection_config?: CollectionFlowConfiguration;
  allow_multiple?: boolean; // Allow multiple concurrent flows
}

export interface CollectionFlowResponse extends CollectionFlow {
  client_account_id: string;
  engagement_id: string;
  collection_config: CollectionFlowConfiguration;
  gaps_identified?: number;
  collection_metrics?: {
    platforms_detected: number;
    data_collected: number;
    gaps_resolved: number;
  };
}

export interface CollectionGapAnalysisResponse {
  id: string;
  collection_flow_id: string;
  attribute_name: string;
  attribute_category: string;
  business_impact: string;
  priority: string;
  collection_difficulty: string;
  affects_strategies: boolean;
  blocks_decision: boolean;
  recommended_collection_method: string;
  resolution_status: string;
  created_at: string;
}

export interface GapTargetInfo {
  gap_id: string;
  attribute_name: string;
  priority: "low" | "medium" | "high" | "critical";
  collection_difficulty: "easy" | "medium" | "hard";
  business_impact: "low" | "medium" | "high" | "critical";
  resolution_method: string;
}

export interface QuestionnaireQuestion {
  field_id: string;  // Backend uses field_id, not question_id
  question_text: string;
  field_type:  // Backend uses field_type, not question_type
    | "text"
    | "number"
    | "boolean"
    | "select"
    | "multiselect"
    | "date";
  required: boolean;
  category?: string;  // Added from backend structure
  metadata?: Record<string, unknown>;  // Added from backend structure
  options?: string[];
  validation_rules?: ValidationRuleConfig[];
  conditional_logic?: ConditionalLogic;
  help_text?: string;
}

export interface ConditionalLogic {
  show_if: Array<{
    question_id: string;
    operator:
      | "equals"
      | "not_equals"
      | "contains"
      | "greater_than"
      | "less_than";
    value: string | number | boolean;
  }>;
}

export interface QuestionnaireResponse {
  question_id: string;
  response_value: string | number | boolean | string[];
  confidence_level?: number;
  notes?: string;
  validation_passed: boolean;
  validation_errors?: string[];
}

export interface FlowUpdateData extends BaseMetadata {
  status?: string;
  progress?: number;
  configuration_updates?: Partial<CollectionFlowConfiguration>;
  phase_data?: Record<string, unknown>;
  error_details?: string[];
}

export interface AdaptiveQuestionnaireResponse {
  id: string;
  collection_flow_id: string;
  title: string;
  description: string;
  target_gaps: GapTargetInfo[];
  questions: QuestionnaireQuestion[];
  validation_rules: ValidationRuleConfig[];
  completion_status: "pending" | "ready" | "fallback" | "failed";
  status_line?: string;
  responses_collected?: QuestionnaireResponse[];
  created_at: string;
  completed_at?: string;
}

export interface CollectionFlowStatusResponse {
  status: string;
  message?: string;
  flow_id?: string;
  current_phase?: string;
  automation_tier?: string;
  progress?: number;
  created_at?: string;
  updated_at?: string;
}

// Phase 3: TypeScript interface for transition response
export interface TransitionResult {
  status: string;
  assessment_flow_id: string; // snake_case
  collection_flow_id: string; // snake_case
  message: string;
  created_at: string;
}

// Two-Phase Gap Analysis Interfaces
export interface DataGap {
  asset_id: string;
  asset_name: string;
  field_name: string;
  gap_type: string;
  gap_category: string;
  priority: number;
  current_value: unknown | null;
  suggested_resolution: string;
  confidence_score: number | null;
  ai_suggestions?: string[];
}

export interface GapScanSummary {
  total_gaps: number;
  assets_analyzed: number;
  critical_gaps: number;
  execution_time_ms: number;
  gaps_persisted?: number;
}

export interface ScanGapsResponse {
  gaps: DataGap[];
  summary: GapScanSummary;
  status: string;
}

export interface AnalysisSummary {
  total_gaps: number;
  enhanced_gaps: number;
  execution_time_ms: number;
  agent_duration_ms: number;
}

export interface AnalyzeGapsResponse {
  enhanced_gaps: DataGap[];
  summary: AnalysisSummary;
  status: string;
}

export interface GapUpdate {
  gap_id: string;
  field_name: string;
  resolved_value: string;
  resolution_status: "pending" | "resolved" | "skipped";
  resolution_method: "manual_entry" | "ai_suggestion" | "hybrid";
}

export interface UpdateGapsResponse {
  updated_gaps: number;
  gaps_resolved: number;
  remaining_gaps: number;
}

// Re-export types from dependencies for convenience
export type { CollectionFlow, CleanupResult, FlowContinueResult };
export type { MaintenanceWindow, VendorProduct, CompletenessMetrics };
