import { apiClient } from './client';
import type { CollectionFlow, CleanupResult, FlowContinueResult } from '@/hooks/collection/useCollectionFlowManagement';

export interface CollectionFlowCreateRequest {
  automation_tier?: string;
  collection_config?: any;
}

export interface CollectionFlowResponse extends CollectionFlow {
  client_account_id: string;
  engagement_id: string;
  collection_config: any;
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

export interface AdaptiveQuestionnaireResponse {
  id: string;
  collection_flow_id: string;
  title: string;
  description: string;
  target_gaps: any[];
  questions: any[];
  validation_rules: any;
  completion_status: string;
  responses_collected?: any;
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

  async getFlowStatus(): Promise<CollectionFlowStatusResponse> {
    const response = await apiClient.get(`${this.baseUrl}/status`);
    return response.data;
  }

  async createFlow(data: CollectionFlowCreateRequest): Promise<CollectionFlowResponse> {
    const response = await apiClient.post(`${this.baseUrl}/flows`, data);
    return response.data;
  }

  async getFlowDetails(flowId: string): Promise<CollectionFlowResponse> {
    const response = await apiClient.get(`${this.baseUrl}/flows/${flowId}`);
    return response.data;
  }

  async updateFlow(flowId: string, data: any): Promise<CollectionFlowResponse> {
    const response = await apiClient.put(`${this.baseUrl}/flows/${flowId}`, data);
    return response.data;
  }

  async getFlowGaps(flowId: string): Promise<CollectionGapAnalysisResponse[]> {
    const response = await apiClient.get(`${this.baseUrl}/flows/${flowId}/gaps`);
    return response.data;
  }

  async getFlowQuestionnaires(flowId: string): Promise<AdaptiveQuestionnaireResponse[]> {
    const response = await apiClient.get(`${this.baseUrl}/flows/${flowId}/questionnaires`);
    return response.data;
  }

  async submitQuestionnaireResponse(
    flowId: string, 
    questionnaireId: string, 
    responses: any
  ): Promise<{ status: string; message: string; questionnaire_id: string }> {
    const response = await apiClient.post(
      `${this.baseUrl}/flows/${flowId}/questionnaires/${questionnaireId}/submit`,
      responses
    );
    return response.data;
  }

  // Flow Management Endpoints
  async getIncompleteFlows(): Promise<CollectionFlowResponse[]> {
    const response = await apiClient.get(`${this.baseUrl}/incomplete`);
    return response.data;
  }

  async continueFlow(flowId: string, resumeContext?: any): Promise<FlowContinueResult> {
    const response = await apiClient.post(`${this.baseUrl}/flows/${flowId}/continue`, {
      resume_context: resumeContext
    });
    return response.data;
  }

  async deleteFlow(flowId: string, force: boolean = false): Promise<{ status: string; message: string; flow_id: string }> {
    const response = await apiClient.delete(`${this.baseUrl}/flows/${flowId}`, {
      params: { force }
    });
    return response.data;
  }

  async batchDeleteFlows(flowIds: string[], force: boolean = false): Promise<{
    status: string;
    deleted_count: number;
    failed_count: number;
    deleted_flows: string[];
    failed_deletions: Array<{ flow_id: string; error: string }>;
  }> {
    const response = await apiClient.post(`${this.baseUrl}/flows/batch-delete`, flowIds, {
      params: { force }
    });
    return response.data;
  }

  async cleanupFlows(
    expirationHours: number = 72,
    dryRun: boolean = true,
    includeFailedFlows: boolean = true,
    includeCancelledFlows: boolean = true
  ): Promise<CleanupResult> {
    const response = await apiClient.post(`${this.baseUrl}/cleanup`, null, {
      params: {
        expiration_hours: expirationHours,
        dry_run: dryRun,
        include_failed: includeFailedFlows,
        include_cancelled: includeCancelledFlows
      }
    });
    return response.data;
  }

  // Utility methods for flow management
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

  private isFlowStale(updatedAt: string): boolean {
    const updated = new Date(updatedAt);
    const now = new Date();
    const hoursSinceUpdate = (now.getTime() - updated.getTime()) / (1000 * 60 * 60);
    return hoursSinceUpdate > 24; // Consider flows stale if not updated in 24 hours
  }

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
      const oldFlowsPreview = await this.cleanupFlows(2160, true, false, true); // 90 days
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