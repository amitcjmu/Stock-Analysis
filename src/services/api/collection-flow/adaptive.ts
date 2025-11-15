/**
 * Adaptive Questionnaire API
 * Handles bulk answer operations, dynamic questions, and bulk import workflows
 */

import { CollectionFlowClient } from "./client";
import { apiCall } from "@/lib/api/apiClient";

// ========================================
// Request/Response Types
// ========================================

export interface QuestionDetail {
  question_id: string;
  question_text: string;
  question_type: "dropdown" | "multi_select" | "text";
  answer_options?: string[];
  section?: string;
  weight: number;
  is_required: boolean;
  display_order?: number;
}

export interface DynamicQuestionsRequest {
  child_flow_id: string;
  asset_id: string;
  asset_type: string;
  include_answered?: boolean;
  refresh_agent_analysis?: boolean;
}

export interface DynamicQuestionsResponse {
  questions: QuestionDetail[];
  agent_status: "not_requested" | "completed" | "fallback";
  fallback_used: boolean;
  total_questions: number;
}

export interface DependencyChangeRequest {
  child_flow_id: string;
  asset_id: string;
  changed_field: string;
  new_value: unknown;
  old_value?: unknown;
}

export interface DependencyChangeResponse {
  reopened_question_ids: string[];
  reason: string;
  affected_assets: string[];
}

export interface AnswerInput {
  question_id: string;
  answer_value: string;
}

export interface BulkAnswerPreviewRequest {
  child_flow_id: string;
  asset_ids: string[];
  question_ids: string[];
}

export interface ConflictDetail {
  question_id: string;
  existing_answers: Record<string, string[]>;
  conflict_count: number;
}

export interface BulkAnswerPreviewResponse {
  total_assets: number;
  total_questions: number;
  potential_conflicts: number;
  conflicts: ConflictDetail[];
}

export interface BulkAnswerSubmitRequest {
  child_flow_id: string;
  asset_ids: string[];
  answers: AnswerInput[];
  conflict_resolution_strategy?: "overwrite" | "skip" | "merge";
}

export interface ChunkError {
  chunk_index: number;
  asset_ids: string[];
  error: string;
  error_code: string;
}

export interface BulkAnswerSubmitResponse {
  success: boolean;
  assets_updated: number;
  questions_answered: number;
  updated_questionnaire_ids: string[];
  failed_chunks?: ChunkError[];
}

export interface FieldMappingSuggestion {
  csv_column: string;
  suggested_field?: string;
  confidence: number;
  suggestions: Array<{ field: string; confidence: number; reason: string }>;
}

export interface ImportAnalysisResponse {
  file_name: string;
  total_rows: number;
  detected_columns: string[];
  suggested_mappings: FieldMappingSuggestion[];
  unmapped_columns: string[];
  validation_warnings: string[];
  import_batch_id: string;
}

export interface ImportExecutionRequest {
  child_flow_id: string;
  import_batch_id: string;
  confirmed_mappings: Record<string, string>;
  import_type: "application" | "server" | "database";
  overwrite_existing?: boolean;
  gap_recalculation_mode?: "fast" | "thorough";
}

export interface ImportTaskResponse {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress_percent: number;
  current_stage: string;
}

export interface ImportTaskDetailResponse extends ImportTaskResponse {
  rows_processed: number;
  total_rows?: number;
  error_message?: string;
  result_data?: Record<string, unknown>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

/**
 * API class for adaptive questionnaire operations
 */
export class AdaptiveApi extends CollectionFlowClient {
  // ========================================
  // Dynamic Questions
  // ========================================

  /**
   * Get questions filtered by asset type with optional agent pruning
   */
  async getFilteredQuestions(
    request: DynamicQuestionsRequest
  ): Promise<DynamicQuestionsResponse> {
    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall("/api/v1/collection/questions/filtered", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return response;
  }

  /**
   * Handle dependency change and determine which questions should reopen
   */
  async handleDependencyChange(
    request: DependencyChangeRequest
  ): Promise<DependencyChangeResponse> {
    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall("/api/v1/collection/dependency-change", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return response;
  }

  // ========================================
  // Bulk Answer Operations
  // ========================================

  /**
   * Preview bulk answer operation to detect conflicts
   */
  async previewBulkAnswers(
    request: BulkAnswerPreviewRequest
  ): Promise<BulkAnswerPreviewResponse> {
    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall("/api/v1/collection/bulk-answer-preview", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return response;
  }

  /**
   * Submit bulk answers with conflict resolution strategy
   */
  async submitBulkAnswers(
    request: BulkAnswerSubmitRequest
  ): Promise<BulkAnswerSubmitResponse> {
    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall("/api/v1/collection/bulk-answer", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return response;
  }

  // ========================================
  // Bulk Import Operations
  // ========================================

  /**
   * Analyze import file and get field mapping suggestions
   */
  async analyzeImportFile(
    file: File,
    import_type: "application" | "server" | "database"
  ): Promise<ImportAnalysisResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("import_type", import_type);

    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall("/api/v1/collection/bulk-import/analyze", {
      method: "POST",
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
      headers: {},
    });
    return response;
  }

  /**
   * Execute import with confirmed field mappings
   */
  async executeImport(
    request: ImportExecutionRequest
  ): Promise<ImportTaskResponse> {
    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall("/api/v1/collection/bulk-import/execute", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return response;
  }

  /**
   * Get import task status for polling
   */
  async getImportTaskStatus(task_id: string): Promise<ImportTaskDetailResponse> {
    // apiCall() returns already-parsed JSON, no need to call .json() again
    const response = await apiCall(
      `/api/v1/collection/bulk-import/status/${task_id}`,
      {
        method: "GET",
      }
    );
    return response;
  }
}
