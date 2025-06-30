/**
 * Discovery Flow Client for API v3
 * Handles all discovery flow operations
 */

import type { ApiClient } from './client';
import type {
  FlowCreate,
  FlowUpdate,
  FlowResponse,
  FlowListResponse,
  FlowStatusResponse,
  FlowExecutionResponse,
  FlowDeletionResponse,
  FlowHealthResponse,
  AssetPromotionResponse,
  PhaseExecution,
  FlowResumeRequest,
  FlowPauseRequest,
  FlowListParams,
  FlowSubscriptionConfig,
  FlowStatusUpdate,
  FlowPhase
} from './types/discovery';
import type { StreamResponse, RequestConfig } from './types/common';

/**
 * Discovery Flow API Client
 */
export class DiscoveryFlowClient {
  constructor(private apiClient: ApiClient) {}

  /**
   * Create a new discovery flow
   */
  async createFlow(
    data: FlowCreate,
    config: RequestConfig = {}
  ): Promise<FlowResponse> {
    return this.apiClient.post<FlowResponse>('/discovery-flow/flows', data, config);
  }

  /**
   * Get flow details with all sub-resources
   */
  async getFlow(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<FlowResponse> {
    return this.apiClient.get<FlowResponse>(`/discovery-flow/flows/${flowId}`, undefined, config);
  }

  /**
   * Update flow details
   */
  async updateFlow(
    flowId: string,
    data: FlowUpdate,
    config: RequestConfig = {}
  ): Promise<FlowResponse> {
    return this.apiClient.put<FlowResponse>(`/discovery-flow/flows/${flowId}`, data, config);
  }

  /**
   * Get real-time flow execution status
   */
  async getFlowStatus(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<FlowStatusResponse> {
    return this.apiClient.get<FlowStatusResponse>(
      `/discovery-flow/flows/${flowId}/status`,
      undefined,
      config
    );
  }

  /**
   * Execute a specific flow phase
   */
  async executePhase(
    flowId: string,
    phase: FlowPhase,
    execution?: Partial<PhaseExecution>,
    config: RequestConfig = {}
  ): Promise<FlowExecutionResponse> {
    const phaseData: PhaseExecution = {
      phase,
      ...execution
    };

    return this.apiClient.post<FlowExecutionResponse>(
      `/discovery-flow/flows/${flowId}/execute/${phase}`,
      phaseData,
      config
    );
  }

  /**
   * List all flows with filtering and pagination
   */
  async listFlows(
    params: FlowListParams = {},
    config: RequestConfig = {}
  ): Promise<FlowListResponse> {
    return this.apiClient.get<FlowListResponse>('/discovery-flow/flows', params, config);
  }

  /**
   * Delete a flow (soft delete)
   */
  async deleteFlow(
    flowId: string,
    forceDelete: boolean = false,
    config: RequestConfig = {}
  ): Promise<FlowDeletionResponse> {
    const params = forceDelete ? { force_delete: true } : undefined;
    
    return this.apiClient.delete<FlowDeletionResponse>(
      `/discovery-flow/flows/${flowId}`,
      { ...config }
    );
  }

  /**
   * Pause a running discovery flow
   */
  async pauseFlow(
    flowId: string,
    pauseRequest: FlowPauseRequest = {},
    config: RequestConfig = {}
  ): Promise<FlowExecutionResponse> {
    return this.apiClient.post<FlowExecutionResponse>(
      `/discovery-flow/flows/${flowId}/pause`,
      pauseRequest,
      config
    );
  }

  /**
   * Resume a paused discovery flow
   */
  async resumeFlow(
    flowId: string,
    resumeRequest: FlowResumeRequest = {},
    config: RequestConfig = {}
  ): Promise<FlowExecutionResponse> {
    return this.apiClient.post<FlowExecutionResponse>(
      `/discovery-flow/flows/${flowId}/resume`,
      resumeRequest,
      config
    );
  }

  /**
   * Promote discovery assets to main assets table
   */
  async promoteAssets(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<AssetPromotionResponse> {
    return this.apiClient.post<AssetPromotionResponse>(
      `/discovery-flow/flows/${flowId}/promote-assets`,
      undefined,
      config
    );
  }

  /**
   * Get discovery flow health status
   */
  async getHealth(
    config: RequestConfig = {}
  ): Promise<FlowHealthResponse> {
    return this.apiClient.get<FlowHealthResponse>('/discovery-flow/health', undefined, config);
  }

  /**
   * Subscribe to flow status updates via Server-Sent Events
   */
  subscribeToFlowUpdates(
    flowId: string,
    onUpdate: (status: FlowStatusUpdate) => void,
    subscriptionConfig: FlowSubscriptionConfig = {}
  ): StreamResponse {
    const params: Record<string, any> = {};
    
    if (subscriptionConfig.includePhaseUpdates) {
      params.include_phase_updates = true;
    }
    if (subscriptionConfig.includeAgentInsights) {
      params.include_agent_insights = true;
    }
    if (subscriptionConfig.includeErrors) {
      params.include_errors = true;
    }
    if (subscriptionConfig.heartbeatInterval) {
      params.heartbeat_interval = subscriptionConfig.heartbeatInterval;
    }

    const streamResponse = this.apiClient.createEventSource(
      `/discovery-flow/flows/${flowId}/subscribe`,
      params
    );

    // Set up message handler
    streamResponse.onMessage((data) => {
      if (data.type === 'flow_status_update') {
        onUpdate(data.payload as FlowStatusUpdate);
      }
    });

    return streamResponse;
  }

  /**
   * Subscribe to all flow updates
   */
  subscribeToAllFlowUpdates(
    onUpdate: (update: FlowStatusUpdate) => void,
    subscriptionConfig: FlowSubscriptionConfig = {}
  ): StreamResponse {
    const params: Record<string, any> = {};
    
    if (subscriptionConfig.includePhaseUpdates) {
      params.include_phase_updates = true;
    }
    if (subscriptionConfig.includeAgentInsights) {
      params.include_agent_insights = true;
    }
    if (subscriptionConfig.includeErrors) {
      params.include_errors = true;
    }

    const streamResponse = this.apiClient.createEventSource(
      '/discovery-flow/flows/subscribe',
      params
    );

    streamResponse.onMessage((data) => {
      if (data.type === 'flow_status_update') {
        onUpdate(data.payload as FlowStatusUpdate);
      }
    });

    return streamResponse;
  }

  /**
   * Get flow execution history
   */
  async getExecutionHistory(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<FlowExecutionResponse[]> {
    return this.apiClient.get<FlowExecutionResponse[]>(
      `/discovery-flow/flows/${flowId}/history`,
      undefined,
      config
    );
  }

  /**
   * Cancel a running flow
   */
  async cancelFlow(
    flowId: string,
    reason: string = 'User requested cancellation',
    config: RequestConfig = {}
  ): Promise<FlowExecutionResponse> {
    return this.apiClient.post<FlowExecutionResponse>(
      `/discovery-flow/flows/${flowId}/cancel`,
      { reason },
      config
    );
  }

  /**
   * Retry a failed flow
   */
  async retryFlow(
    flowId: string,
    fromPhase?: FlowPhase,
    config: RequestConfig = {}
  ): Promise<FlowExecutionResponse> {
    const body = fromPhase ? { from_phase: fromPhase } : undefined;
    
    return this.apiClient.post<FlowExecutionResponse>(
      `/discovery-flow/flows/${flowId}/retry`,
      body,
      config
    );
  }

  /**
   * Get flow metrics and statistics
   */
  async getFlowMetrics(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<{
    execution_time: number;
    phases_completed: number;
    total_phases: number;
    success_rate: number;
    error_count: number;
    warning_count: number;
  }> {
    return this.apiClient.get(
      `/discovery-flow/flows/${flowId}/metrics`,
      undefined,
      config
    );
  }

  /**
   * Export flow data
   */
  async exportFlow(
    flowId: string,
    format: 'json' | 'csv' | 'excel' = 'json',
    config: RequestConfig = {}
  ): Promise<Blob> {
    const response = await this.apiClient.get<Response>(
      `/discovery-flow/flows/${flowId}/export`,
      { format },
      { ...config, cache: false }
    );

    return response as unknown as Blob;
  }

  /**
   * Get recommended next actions for a flow
   */
  async getRecommendations(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<{
    recommendations: Array<{
      action: string;
      description: string;
      priority: 'low' | 'medium' | 'high';
      reason: string;
    }>;
  }> {
    return this.apiClient.get(
      `/discovery-flow/flows/${flowId}/recommendations`,
      undefined,
      config
    );
  }

  /**
   * Validate flow configuration before creation
   */
  async validateFlowConfig(
    config: FlowCreate,
    requestConfig: RequestConfig = {}
  ): Promise<{
    is_valid: boolean;
    issues: Array<{
      field: string;
      message: string;
      severity: 'error' | 'warning';
    }>;
    recommendations: string[];
  }> {
    return this.apiClient.post(
      '/discovery-flow/flows/validate',
      config,
      requestConfig
    );
  }

  /**
   * Duplicate an existing flow
   */
  async duplicateFlow(
    flowId: string,
    newName: string,
    config: RequestConfig = {}
  ): Promise<FlowResponse> {
    return this.apiClient.post<FlowResponse>(
      `/discovery-flow/flows/${flowId}/duplicate`,
      { name: newName },
      config
    );
  }
}