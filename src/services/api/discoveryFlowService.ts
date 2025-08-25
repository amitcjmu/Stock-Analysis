/**
 * Discovery Flow Service
 *
 * Service for operational discovery flow status and management.
 * This service queries child flow status (discovery_flows table) for operational decisions.
 *
 * As per ADR-012: Flow Status Management Separation, this service should be used for:
 * - All operational decisions (field mapping, data cleansing, agent decisions)
 * - Phase-specific state management
 * - Frontend display of current status
 * - Agent decision context
 */

import { ApiClient } from '../ApiClient';
import type { ApiResponse, ApiError } from '../../types/shared/api-types';
import type { AuditableMetadata } from '../../types/shared/metadata-types';

const apiClient = ApiClient.getInstance();

// Supporting type definitions for discovery flow data
export interface FieldMapping {
  id: string;
  source_field: string;
  target_field: string;
  confidence_score: number;
  mapping_type: 'exact' | 'fuzzy' | 'derived' | 'manual';
  transformation_rule?: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface CleanedDataRecord {
  id: string;
  source_data: Record<string, unknown>;
  cleaned_data: Record<string, unknown>;
  applied_transformations: string[];
  quality_score: number;
  validation_errors: string[];
}

export interface AssetInventoryData {
  total_assets: number;
  categorized_assets: Record<string, number>;
  discovery_methods: string[];
  coverage_percentage: number;
  last_updated: string;
}

export interface DependencyData {
  total_dependencies: number;
  dependency_types: Record<string, number>;
  critical_paths: string[];
  circular_dependencies: string[];
  coverage_percentage: number;
}

export interface TechnicalDebtData {
  total_debt_score: number;
  debt_categories: Record<string, number>;
  critical_issues: number;
  recommendations: string[];
  remediation_effort_hours: number;
}

export interface AgentInsight {
  id: string;
  agent_type: string;
  insight_category: string;
  title: string;
  description: string;
  confidence: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  actionable: boolean;
  metadata: AuditableMetadata;
  created_at: string;
}

export interface PhaseExecutionRequest {
  phase: string;
  data: Record<string, unknown>;
  client_account_id: string;
  engagement_id: string;
  validation_overrides?: Record<string, boolean>;
}

export interface PhaseExecutionResponse {
  success: boolean;
  phase: string;
  status: 'started' | 'completed' | 'failed';
  message?: string;
  data?: Record<string, unknown>;
  estimated_duration?: number;
  errors?: string[];
}

export interface ClarificationAnswers {
  [questionId: string]: {
    answer: string | number | boolean | string[];
    confidence?: number;
    notes?: string;
  };
}

export interface ClarificationSubmissionResponse {
  success: boolean;
  processed_answers: number;
  validation_errors: string[];
  next_phase?: string;
  message?: string;
}

export interface DiscoveryFlowStatusResponse {
  success: boolean;
  flow_id: string;
  status: string;
  current_phase: string;
  progress_percentage: number;
  summary: {
    data_import_completed: boolean;
    field_mapping_completed: boolean;
    data_cleansing_completed: boolean;
    asset_inventory_completed: boolean;
    dependency_analysis_completed: boolean;
    tech_debt_assessment_completed: boolean;
    total_records: number;
    records_processed: number;
    quality_score: number;
  };
  created_at: string;
  updated_at: string;
  // Additional operational fields
  field_mappings?: FieldMapping[];
  cleaned_data?: CleanedDataRecord[];
  asset_inventory?: AssetInventoryData;
  dependencies?: DependencyData;
  technical_debt?: TechnicalDebtData;
  agent_insights?: AgentInsight[];
  errors?: string[];
  warnings?: string[];
}

// Learning-related interfaces for field mapping feedback
export interface FieldMappingLearningApprovalRequest {
  confidence_score?: number;
  approval_metadata?: Record<string, unknown>;
  learning_enabled?: boolean;
}

export interface FieldMappingLearningRejectionRequest {
  rejection_reason: string;
  alternative_suggestion?: string;
  rejection_metadata?: Record<string, unknown>;
  learning_enabled?: boolean;
}

export interface BulkFieldMappingLearningAction {
  mapping_id: string;
  action_type: 'approve' | 'reject';
  approval_request?: FieldMappingLearningApprovalRequest;
  rejection_request?: FieldMappingLearningRejectionRequest;
}

export interface BulkFieldMappingLearningRequest {
  actions: BulkFieldMappingLearningAction[];
  continue_on_error?: boolean;
}

export interface FieldMappingLearningResponse {
  success: boolean;
  mapping_id: string;
  message?: string;
  error_message?: string;
  patterns_created?: number;
  patterns_updated?: number;
  learning_metadata?: Record<string, unknown>;
}

export interface BulkFieldMappingLearningResponse {
  success: boolean;
  total_actions: number;
  successful_actions: number;
  failed_actions: number;
  results: FieldMappingLearningResponse[];
  global_patterns_created: number;
  global_patterns_updated: number;
  errors?: string[];
}

export interface LearnedFieldMappingPattern {
  id: string;
  pattern_type: string;
  insight_type: string;
  source_field_pattern: string;
  target_field_suggestion: string | null;
  confidence_adjustment: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface LearnedFieldMappingPatternsResponse {
  success: boolean;
  total_patterns: number;
  patterns: LearnedFieldMappingPattern[];
  context_summary?: Record<string, unknown>;
}

export interface DiscoveryFlowService {
  /**
   * Get operational discovery flow status
   * This returns the child flow status for operational decisions
   */
  getOperationalStatus(flowId: string, clientAccountId: string, engagementId: string): Promise<DiscoveryFlowStatusResponse>;

  /**
   * Execute discovery flow phase
   */
  executePhase(flowId: string, phase: string, data: Record<string, unknown>, clientAccountId: string, engagementId: string): Promise<PhaseExecutionResponse>;

  /**
   * Submit agent clarification answers
   */
  submitClarificationAnswers(flowId: string, answers: ClarificationAnswers, clientAccountId: string, engagementId: string): Promise<ClarificationSubmissionResponse>;

  /**
   * Retry a failed discovery flow
   */
  retryFlow(flowId: string, clientAccountId: string, engagementId: string): Promise<ApiResponse<{ success: boolean; message?: string }>>;

  /**
   * Field Mapping Learning Endpoints
   */

  /**
   * Approve a field mapping and learn from the approval
   */
  approveFieldMapping(mappingId: string, request: FieldMappingLearningApprovalRequest, clientAccountId: string, engagementId: string): Promise<FieldMappingLearningResponse>;

  /**
   * Reject a field mapping and learn from the rejection
   */
  rejectFieldMapping(mappingId: string, request: FieldMappingLearningRejectionRequest, clientAccountId: string, engagementId: string): Promise<FieldMappingLearningResponse>;

  /**
   * Bulk learn from multiple field mappings
   */
  bulkLearnFieldMappings(request: BulkFieldMappingLearningRequest, clientAccountId: string, engagementId: string): Promise<BulkFieldMappingLearningResponse>;

  /**
   * Get learned field mapping patterns
   */
  getLearnedFieldMappingPatterns(clientAccountId: string, engagementId: string, patternType?: string, insightType?: string, limit?: number): Promise<LearnedFieldMappingPatternsResponse>;

  /**
   * Refresh learned patterns cache
   */
  refreshLearnedPatternsCache(clientAccountId: string, engagementId: string): Promise<{ success: boolean; message: string }>;
}

class DiscoveryFlowServiceImpl implements DiscoveryFlowService {

  async getOperationalStatus(flowId: string, clientAccountId: string, engagementId: string): Promise<DiscoveryFlowStatusResponse> {
    console.log(`🔍 [DiscoveryFlowService] Getting operational status for flow: ${flowId}`);

    const response = await apiClient.get<DiscoveryFlowStatusResponse>(
      `/unified-discovery/flow/${flowId}/status`,  // Updated to unified-discovery endpoint as part of API migration
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Retrieved operational status:`, response);
    return response;
  }

  async executePhase(flowId: string, phase: string, data: Record<string, unknown>, clientAccountId: string, engagementId: string): Promise<PhaseExecutionResponse> {
    console.log(`🚀 [DiscoveryFlowService] Executing phase ${phase} for flow: ${flowId}`);

    // FIXED: Use unified-discovery flow execution endpoint that only requires client/engagement context
    // instead of the master flow endpoint that requires user authentication
    const response = await apiClient.post<PhaseExecutionResponse>(
      `/unified-discovery/flow/${flowId}/execute`,  // Updated to unified-discovery endpoint as part of API migration
      {
        phase,
        phase_input: data,
        force: false
      },
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Phase execution result:`, response);
    return response;
  }

  async submitClarificationAnswers(flowId: string, answers: ClarificationAnswers, clientAccountId: string, engagementId: string): Promise<ClarificationSubmissionResponse> {
    console.log(`📝 [DiscoveryFlowService] Submitting clarification answers for flow: ${flowId}`);

    const response = await apiClient.post<ClarificationSubmissionResponse>(
      `/unified-discovery/flow/${flowId}/clarifications/submit`,  // Updated to unified-discovery endpoint as part of API migration
      {
        answers,
        client_account_id: clientAccountId,
        engagement_id: engagementId
      },
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Clarification submission result:`, response);
    return response;
  }

  async retryFlow(flowId: string, clientAccountId: string, engagementId: string): Promise<ApiResponse<{ success: boolean; message?: string }>> {
    console.log(`🔄 [DiscoveryFlowService] Retrying failed flow: ${flowId}`);

    const response = await apiClient.post<ApiResponse<{ success: boolean; message?: string }>>(
      `/unified-discovery/flow/${flowId}/retry`,  // Updated to unified-discovery endpoint as part of API migration
      {},
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Flow retry result:`, response);
    return response;
  }

  // Field Mapping Learning Methods

  async approveFieldMapping(mappingId: string, request: FieldMappingLearningApprovalRequest, clientAccountId: string, engagementId: string): Promise<FieldMappingLearningResponse> {
    console.log(`✅ [DiscoveryFlowService] Approving field mapping with learning: ${mappingId}`);

    const response = await apiClient.post<FieldMappingLearningResponse>(
      `/data-import/field-mappings/${mappingId}/approve`,  // Use corrected field mappings learning endpoint
      request,
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Field mapping approval result:`, response);
    return response;
  }

  async rejectFieldMapping(mappingId: string, request: FieldMappingLearningRejectionRequest, clientAccountId: string, engagementId: string): Promise<FieldMappingLearningResponse> {
    console.log(`❌ [DiscoveryFlowService] Rejecting field mapping with learning: ${mappingId}`);

    const response = await apiClient.post<FieldMappingLearningResponse>(
      `/data-import/field-mappings/${mappingId}/reject`,  // Use corrected field mappings learning endpoint
      request,
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Field mapping rejection result:`, response);
    return response;
  }

  async bulkLearnFieldMappings(request: BulkFieldMappingLearningRequest, clientAccountId: string, engagementId: string): Promise<BulkFieldMappingLearningResponse> {
    console.log(`📚 [DiscoveryFlowService] Bulk learning from ${request.actions.length} field mappings`);

    const response = await apiClient.post<BulkFieldMappingLearningResponse>(
      `/data-import/field-mappings/learn`,  // Use corrected bulk learning endpoint
      request,
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Bulk learning result:`, response);
    return response;
  }

  async getLearnedFieldMappingPatterns(clientAccountId: string, engagementId: string, patternType?: string, insightType?: string, limit = 100): Promise<LearnedFieldMappingPatternsResponse> {
    console.log(`🔍 [DiscoveryFlowService] Getting learned field mapping patterns`);

    const params = new URLSearchParams();
    if (patternType) params.append('pattern_type', patternType);
    if (insightType) params.append('insight_type', insightType);
    params.append('limit', limit.toString());

    const queryString = params.toString();
    const url = `/data-import/field-mappings/learned${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<LearnedFieldMappingPatternsResponse>(
      url,  // Use existing learned patterns endpoint
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Learned patterns result:`, response);
    return response;
  }

  async refreshLearnedPatternsCache(clientAccountId: string, engagementId: string): Promise<{ success: boolean; message: string }> {
    console.log(`🔄 [DiscoveryFlowService] Refreshing learned patterns cache`);

    const response = await apiClient.post<{ success: boolean; message: string }>(
      `/data-import/field-mappings/learned/refresh`,  // Use corrected cache refresh endpoint
      {},
      {
        headers: {
          'X-Client-Account-Id': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Cache refresh result:`, response);
    return response;
  }
}

// Create singleton instance
const discoveryFlowService = new DiscoveryFlowServiceImpl();

// Export both named and default exports for compatibility
export { discoveryFlowService };
export default discoveryFlowService;
