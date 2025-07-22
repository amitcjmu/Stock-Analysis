import { apiCall } from '@/config/api';
import type { CollectionFlow, CleanupResult, FlowContinueResult } from '@/hooks/collection/useCollectionFlowManagement';

export interface CollectionFlowCreateRequest {
  automation_tier?: string;
  collection_config?: unknown;
}

export interface CollectionFlowResponse extends CollectionFlow {
  client_account_id: string;
  engagement_id: string;
  collection_config: unknown;
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
  target_gaps: unknown[];
  questions: unknown[];
  validation_rules: unknown;
  completion_status: string;
  responses_collected?: unknown;
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
    return await apiCall(`${this.baseUrl}/status`, { method: 'GET' });
  }

  async createFlow(data: CollectionFlowCreateRequest): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows`, { 
      method: 'POST', 
      body: JSON.stringify(data)
    });
  }

  async getFlowDetails(flowId: string): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, { method: 'GET' });
  }

  async updateFlow(flowId: string, data: unknown): Promise<CollectionFlowResponse> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, { 
      method: 'PUT', 
      body: JSON.stringify(data)
    });
  }

  async getFlowGaps(flowId: string): Promise<CollectionGapAnalysisResponse[]> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/gaps`, { method: 'GET' });
  }

  async getFlowQuestionnaires(flowId: string): Promise<AdaptiveQuestionnaireResponse[]> {
    return await apiCall(`${this.baseUrl}/flows/${flowId}/questionnaires`, { method: 'GET' });
  }

  async submitQuestionnaireResponse(
    flowId: string, 
    questionnaireId: string, 
    responses: any
  ): Promise<{ status: string; message: string; questionnaire_id: string }> {
    return await apiCall(
      `${this.baseUrl}/flows/${flowId}/questionnaires/${questionnaireId}/submit`,
      { 
        method: 'POST', 
        body: JSON.stringify(responses)
      }
    );
  }

  // Flow Management Endpoints
  async getIncompleteFlows(): Promise<CollectionFlowResponse[]> {
    return await apiCall(`${this.baseUrl}/incomplete`, { method: 'GET' });
  }

  async continueFlow(flowId: string, resumeContext?: unknown): Promise<FlowContinueResult> {
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