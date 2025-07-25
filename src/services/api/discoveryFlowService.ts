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
}

class DiscoveryFlowServiceImpl implements DiscoveryFlowService {

  async getOperationalStatus(flowId: string, clientAccountId: string, engagementId: string): Promise<DiscoveryFlowStatusResponse> {
    console.log(`🔍 [DiscoveryFlowService] Getting operational status for flow: ${flowId}`);

    const response = await apiClient.get<DiscoveryFlowStatusResponse>(
      `/discovery/flows/${flowId}/status`,
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Retrieved operational status:`, response);
    return response;
  }

  async executePhase(flowId: string, phase: string, data: Record<string, unknown>, clientAccountId: string, engagementId: string): Promise<PhaseExecutionResponse> {
    console.log(`🚀 [DiscoveryFlowService] Executing phase ${phase} for flow: ${flowId}`);

    // FIXED: Use discovery flow execution endpoint that only requires client/engagement context
    // instead of the master flow endpoint that requires user authentication
    const response = await apiClient.post<PhaseExecutionResponse>(
      `/discovery/flow/${flowId}/execute`,
      {
        phase,
        data,
        client_account_id: clientAccountId,
        engagement_id: engagementId
      },
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
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
      `/discovery/flows/${flowId}/clarifications/submit`,
      {
        answers,
        client_account_id: clientAccountId,
        engagement_id: engagementId
      },
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          'X-Engagement-ID': engagementId
        }
      }
    );

    console.log(`✅ [DiscoveryFlowService] Clarification submission result:`, response);
    return response;
  }
}

// Create singleton instance
const discoveryFlowService = new DiscoveryFlowServiceImpl();

// Export both named and default exports for compatibility
export { discoveryFlowService };
export default discoveryFlowService;
