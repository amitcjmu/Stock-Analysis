import { apiCall } from '@/config/api';
import type { CollectionFlow, CleanupResult, FlowContinueResult } from '@/hooks/collection/useCollectionFlowManagement';
import type { BaseMetadata } from '../../types/shared/metadata-types';

export interface CollectionFlowConfiguration extends BaseMetadata {
  automation_tier?: 'basic' | 'standard' | 'advanced' | 'enterprise';
  platform_scope?: string[];
  collection_methods?: string[];
  validation_rules?: ValidationRuleConfig[];
  notification_settings?: NotificationConfig;
}

export interface ValidationRuleConfig {
  rule_id: string;
  rule_type: 'required' | 'format' | 'range' | 'dependency';
  field_path: string;
  validation_criteria: Record<string, unknown>;
  error_message: string;
  severity: 'error' | 'warning' | 'info';
}

export interface NotificationConfig {
  email_notifications: boolean;
  slack_notifications: boolean;
  webhook_notifications: boolean;
  notification_levels: Array<'error' | 'warning' | 'info' | 'success'>;
}

export interface CollectionFlowCreateRequest {
  automation_tier?: string;
  collection_config?: CollectionFlowConfiguration;
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
  priority: 'low' | 'medium' | 'high' | 'critical';
  collection_difficulty: 'easy' | 'medium' | 'hard';
  business_impact: 'low' | 'medium' | 'high' | 'critical';
  resolution_method: string;
}

export interface QuestionnaireQuestion {
  question_id: string;
  question_text: string;
  question_type: 'text' | 'number' | 'boolean' | 'select' | 'multiselect' | 'date';
  required: boolean;
  options?: string[];
  validation_rules?: ValidationRuleConfig[];
  conditional_logic?: ConditionalLogic;
  help_text?: string;
}

export interface ConditionalLogic {
  show_if: Array<{
    question_id: string;
    operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than';
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
  completion_status: string;
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

class CollectionFlowApi {
  private readonly baseUrl = '/api/v1/collection';
  private static readonly STALE_HOURS_THRESHOLD = 24; // hours
  private static readonly OLD_FLOW_HOURS_THRESHOLD = 90 * 24; // 90 days

  async getFlowStatus(): Promise<CollectionFlowStatusResponse> {
    return await apiCall(`${this.baseUrl}/status`, { method: 'GET' });
  }

  async createFlow(data: CollectionFlowCreateRequest): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async ensureFlow(): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/ensure`, { method: 'POST' });
  }

  async getFlowDetails(flowId: string): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, { method: 'GET' });
  }

  async getFlowReadiness(flowId: string): Promise<{
    flow_id: string;
    engagement_id: string;
    apps_ready_for_assessment: number;
    quality: { collection_quality_score: number; confidence_score: number };
    phase_scores: { collection: number; discovery: number };
    issues: { total: number; critical: number; warning: number; info: number };
    updated_at?: string;
  }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/readiness`, {
      method: 'GET'
    });
  }

  async updateFlow(flowId: string, data: FlowUpdateData): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async getFlowGaps(flowId: string): Promise<CollectionGapAnalysisResponse[]> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/gaps`, { method: 'GET' });
  }

  async getFlowQuestionnaires(flowId: string): Promise<AdaptiveQuestionnaireResponse[]> {
    try {
      return await apiCall(`${this.baseUrl}/flows/${flowId}/questionnaires`, { method: 'GET' });
    } catch (err: any) {
      // Stabilize error handling - check multiple possible error shapes
      const status = err?.status ?? err?.response?.status;
      const detail = err?.response?.data?.detail ?? err?.response?.detail;
      const errorCode = typeof detail === 'object' ? detail?.error : undefined;

      if (status === 422 && errorCode === 'no_applications_selected') {
        // Redirect to application selection
        window.location.href = '/discovery/cmdb-import';
        // Return a promise that never resolves to prevent further handling after redirect
        return new Promise<AdaptiveQuestionnaireResponse[]>(() => {});
      }
      // Properly reject with the original error
      return Promise.reject(err);
    }
  }

  async submitQuestionnaireResponse(
    flowId: string,
    questionnaireId: string,
    responses: QuestionnaireResponse[]
  ): Promise<{ status: string; message: string; questionnaire_id: string }> {
    return await apiCall(
      `${this.baseUrl}/flows/${flowId}/questionnaires/${questionnaireId}/submit`,
      {
        method: 'POST',
        body: JSON.stringify(responses)
      }
    );
  }

  async executeFlowPhase(flowId: string, phaseInput?: Record<string, unknown>): Promise<{
    phase: string;
    status: string;
    next_phase?: string;
    requires_user_input?: boolean;
  }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/execute`, {
      method: 'POST',
      body: JSON.stringify(phaseInput || {})
    });
  }

  // Flow Management Endpoints
  async getIncompleteFlows(): Promise<CollectionFlowResponse[]> {
    return await apiCall(`${this.baseUrl}/incomplete`, { method: 'GET' });
  }

  async continueFlow(flowId: string, resumeContext?: Record<string, unknown>): Promise<FlowContinueResult> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/continue`, {
      method: 'POST',
      body: JSON.stringify({ resume_context: resumeContext })
    });
  }

  async deleteFlow(flowId: string, force: boolean = false): Promise<{ status: string; message: string; flow_id: string }> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}?force=${force}`, { method: 'DELETE' });
  }

  async batchDeleteFlows(flowIds: string[], force: boolean = false): Promise<{
    status: string;
    deleted_count: number;
    failed_count: number;
    deleted_flows: string[];
    failed_deletions: Array<{ flow_id: string; error: string }>;
  }> {
    return await apiCall(`${this.baseUrl}/flows/batch-delete?force=${force}`, {
      method: 'POST',
      body: JSON.stringify(flowIds)
    });
  }

  async cleanupFlows(
    expirationHours: number = 72,
    dryRun: boolean = true,
    includeFailedFlows: boolean = true,
    includeCancelledFlows: boolean = true
  ): Promise<CleanupResult> {
    const params = new URLSearchParams({
      expiration_hours: expirationHours.toString(),
      dry_run: dryRun.toString(),
      include_failed: includeFailedFlows.toString(),
      include_cancelled: includeCancelledFlows.toString()
    });
    return await apiCall(`${this.baseUrl}/cleanup?${params}`, { method: 'POST' });
  }

  // Utility methods for flow management
  /**
   * Compute a simple health summary across incomplete flows.
   * - healthy_flows: number of non-problematic flows
   * - problematic_flows: running/paused flows with low progress or failed
   * - health_score: percentage of healthy flows
   */
  async getFlowHealthStatus(): Promise<{
    healthy_flows: number;
    problematic_flows: number;
    total_flows: number;
    health_score: number;
  }> {
    try {
      const incompleteFlows = await this.getIncompleteFlows();
      const totalFlows = incompleteFlows.length;

      if (totalFlows === 0) {
        return {
          healthy_flows: 0,
          problematic_flows: 0,
          total_flows: 0,
          health_score: 100
        };
      }

      const problematicFlows = incompleteFlows.filter(flow =>
        flow.status === 'failed' ||
        (flow.progress < 10 && this.isFlowStale(flow.updated_at))
      ).length;

      const healthyFlows = totalFlows - problematicFlows;
      const healthScore = Math.round((healthyFlows / totalFlows) * 100);

      return {
        healthy_flows: healthyFlows,
        problematic_flows: problematicFlows,
        total_flows: totalFlows,
        health_score: healthScore
      };
    } catch (error) {
      console.error('Failed to get flow health status:', error);
      return {
        healthy_flows: 0,
        problematic_flows: 0,
        total_flows: 0,
        health_score: 0
      };
    }
  }

  /** Determine whether a flow is stale based on last update time. */
  private isFlowStale(updatedAt: string): boolean {
    const updated = new Date(updatedAt);
    const now = new Date();
    const hoursSinceUpdate = (now.getTime() - updated.getTime()) / (1000 * 60 * 60);
    return hoursSinceUpdate > CollectionFlowApi.STALE_HOURS_THRESHOLD;
  }

  /** Produce cleanup recommendations based on preview results from cleanupFlows. */
  async getCleanupRecommendations(): Promise<{
    total_flows: number;
    cleanup_candidates: number;
    estimated_space_recovery: string;
    recommendations: string[];
  }> {
    try {
      // Get cleanup preview
      const previewResult = await this.cleanupFlows(72, true, true, true);

      const recommendations = [];
      if (previewResult.flows_cleaned > 0) {
        recommendations.push(`${previewResult.flows_cleaned} flows can be cleaned up`);
        recommendations.push(`${previewResult.space_recovered} of space can be recovered`);
      }

      // Check for very old flows (90+ days)
      const oldFlowsPreview = await this.cleanupFlows(CollectionFlowApi.OLD_FLOW_HOURS_THRESHOLD, true, false, true);
      if (oldFlowsPreview.flows_cleaned > 0) {
        recommendations.push(`${oldFlowsPreview.flows_cleaned} very old flows should be archived`);
      }

      return {
        total_flows: previewResult.flows_details?.length || 0,
        cleanup_candidates: previewResult.flows_cleaned,
        estimated_space_recovery: previewResult.space_recovered,
        recommendations
      };
    } catch (error) {
      console.error('Failed to get cleanup recommendations:', error);
      return {
        total_flows: 0,
        cleanup_candidates: 0,
        estimated_space_recovery: '0 KB',
        recommendations: ['Unable to analyze cleanup opportunities']
      };
    }
  }
}

export const collectionFlowApi = new CollectionFlowApi();
