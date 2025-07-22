/**
 * Master Flow Service - Unified API for all flow operations
 * Replaces all legacy discovery, assessment, and other flow services
 */

import { ApiClient } from '../ApiClient';
import { ApiResponse, ApiError } from '../../types/shared/api-types';
import type { EnhancedApiError } from '../../config/api';
import { BaseMetadata, AuditableMetadata } from '../../types/shared/metadata-types';

const apiClient = ApiClient.getInstance();
import { AuthService } from '../../contexts/AuthContext/services/authService';

export interface FlowConfiguration extends BaseMetadata {
  flow_name?: string;
  auto_retry?: boolean;
  max_retries?: number;
  timeout_minutes?: number;
  notification_channels?: string[];
  agent_collaboration?: boolean;
}

export interface FlowMetrics {
  total_flows: number;
  active_flows: number;
  completed_flows: number;
  failed_flows: number;
  average_duration_minutes: number;
  success_rate: number;
  phase_metrics: Record<string, {
    total_executions: number;
    average_duration: number;
    success_rate: number;
  }>;
}

export interface MasterFlowRequest {
  clientAccountId: string;
  engagementId: string;
  flowType: 'discovery' | 'assessment' | 'planning' | 'execution' | 'modernize' | 'finops' | 'observability' | 'decommission';
  config?: FlowConfiguration;
  userId?: string;
}

export interface MasterFlowResponse {
  flowId: string;
  status: 'initializing' | 'running' | 'completed' | 'failed' | 'paused';
  flowType: string;
  progress: number;
  currentPhase: string;
  metadata: AuditableMetadata;
  createdAt: string;
  updatedAt: string;
}

export interface FlowStatusResponse {
  flowId: string;
  flow_id?: string; // Some endpoints return flow_id instead of flowId
  status: string;
  progress?: number;
  progress_percentage?: number; // Backend uses this
  currentPhase?: string;
  current_phase?: string; // Some endpoints use snake_case
  phase?: string; // Another variant
  phaseDetails?: Record<string, unknown>;
  phase_completion?: Record<string, boolean>; // For phase completion tracking
  errors?: string[];
  metadata?: Record<string, unknown>;
  awaitingUserApproval?: boolean;
  awaiting_user_approval?: boolean; // Snake case variant
  lastUpdated?: string;
  field_mappings?: Array<{
    id: string;
    source_field: string;
    target_field: string;
    status: string;
    confidence_score: number;
    match_type: string;
    suggested_by?: string;
    approved_by?: string;
    approved_at?: string;
    transformation_rules?: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
  }>;
  agent_insights?: Array<{
    id: string;
    agent_id: string;
    agent_name: string;
    insight_type: string;
    title: string;
    description: string;
    confidence: string | number;
    supporting_data: Record<string, unknown>;
    actionable: boolean;
    page: string;
    created_at: string;
    flow_id?: string;
    category?: string;
    message?: string;
    recommendation?: string;
    severity?: string;
  }>;
  raw_data?: Array<Record<string, unknown>>;
  import_metadata?: AuditableMetadata;
}

/**
 * Get multi-tenant headers for API requests
 */
const getMultiTenantHeaders = (
  clientAccountId: string,
  engagementId?: string,
  userId?: string
) => {
  const token = localStorage.getItem('auth_token');
  return {
    'X-Client-Account-ID': clientAccountId,
    ...(engagementId && { 'X-Engagement-ID': engagementId }),
    ...(userId && { 'X-User-ID': userId }),
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
};

/**
 * Handle API errors consistently
 */
const handleApiError = (error: Error | { message?: string; code?: string }, operation: string) => {
  console.error(`MasterFlowService.${operation} failed:`, error);
  if (error instanceof Error) {
    throw new Error(`${operation} failed: ${error.message}`);
  }
  throw new Error(`${operation} failed: Unknown error`);
};

/**
 * Master Flow Service - Single API pattern for all flows
 */
export const masterFlowService = {
  /**
   * Initialize any type of flow via master orchestrator
   */
  async initializeFlow(request: MasterFlowRequest): Promise<MasterFlowResponse> {
    try {
      // Transform the request to match backend expectations
      const backendRequest = {
        flow_type: request.flowType,
        flow_name: request.config?.flow_name || `${request.flowType} Flow`,
        configuration: request.config || {},
        initial_state: {}
      };
      
      const response = await apiClient.post<{
        flow_id: string;
        status: string;
        flow_type: string;
        progress_percentage: number;
        phase: string;
        metadata: AuditableMetadata;
        created_at: string;
        updated_at: string;
      }>(
        '/flows/',
        backendRequest,
        {
          headers: getMultiTenantHeaders(
            request.clientAccountId,
            request.engagementId,
            request.userId
          ),
        }
      );
      
      // Transform backend response to match frontend expectations
      return {
        flowId: response.flow_id,
        status: response.status as 'initializing' | 'running' | 'completed' | 'failed' | 'paused',
        flowType: response.flow_type,
        progress: response.progress_percentage || 0,
        currentPhase: response.phase || 'initialization',
        metadata: response.metadata || { tags: {}, labels: {}, annotations: {}, customFields: {} },
        createdAt: response.created_at,
        updatedAt: response.updated_at
      };
    } catch (error) {
      handleApiError(error, 'initializeFlow');
      throw error;
    }
  },

  /**
   * Get flow status for any flow type
   */
  async getFlowStatus(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<FlowStatusResponse> {
    try {
      const response = await apiClient.get<FlowStatusResponse>(
        `/flows/${flowId}/status`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response;
    } catch (error) {
      handleApiError(error, 'getFlowStatus');
      throw error;
    }
  },

  /**
   * Get all active flows for a client
   */
  async getActiveFlows(
    clientAccountId: string,
    engagementId?: string,
    flowType?: string
  ): Promise<MasterFlowResponse[]> {
    try {
      const params = new URLSearchParams();
      if (flowType) params.append('flowType', flowType);
      
      const endpoint = `/discovery/flows/active${params.toString() ? `?${params}` : ''}`;
      const headers = getMultiTenantHeaders(clientAccountId, engagementId);
      
      console.log('🔍 MasterFlowService.getActiveFlows - Making API call:', {
        endpoint,
        headers,
        clientAccountId,
        engagementId,
        flowType
      });
      
      const response = await apiClient.get<MasterFlowResponse[]>(
        endpoint,
        {
          headers,
        }
      );
      
      console.log('✅ MasterFlowService.getActiveFlows - Response received:', response);
      return response;
    } catch (error) {
      console.error('❌ MasterFlowService.getActiveFlows - API call failed:', error);
      handleApiError(error, 'getActiveFlows');
      throw error;
    }
  },

  /**
   * Delete a flow
   */
  async deleteFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<void> {
    try {
      // First try to delete via discovery flow endpoint
      await apiClient.delete(`/discovery/flow/${flowId}`, undefined, {
        headers: getMultiTenantHeaders(clientAccountId, engagementId),
      });
    } catch (error) {
      // If master flow delete fails with 404, try discovery flow endpoint
      const apiError = error as EnhancedApiError;
      if (apiError?.response?.status === 404 || apiError?.status === 404) {
        console.log('Master flow not found, trying discovery flow delete endpoint...');
        try {
          await apiClient.delete(`/discovery/flow/${flowId}`, undefined, {
            headers: getMultiTenantHeaders(clientAccountId, engagementId),
          });
          return; // Success via discovery endpoint
        } catch (discoveryError) {
          console.error('Discovery flow delete also failed:', discoveryError);
          // Continue to throw the original error
        }
      }
      handleApiError(error, 'deleteFlow');
      throw error;
    }
  },

  /**
   * Update flow configuration
   */
  async updateFlowConfig(
    flowId: string,
    config: FlowConfiguration,
    clientAccountId: string,
    engagementId?: string
  ): Promise<void> {
    try {
      await apiClient.put(
        `/flows/${flowId}/config`,
        config,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
    } catch (error) {
      handleApiError(error, 'updateFlowConfig');
      throw error;
    }
  },

  /**
   * Pause a flow
   */
  async pauseFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<void> {
    try {
      await apiClient.post(
        `/flows/${flowId}/pause`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
    } catch (error) {
      handleApiError(error, 'pauseFlow');
      throw error;
    }
  },

  /**
   * Resume a flow
   */
  async resumeFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<ApiResponse<{ success: boolean; message?: string }>> {
    try {
      const response = await apiClient.post<ApiResponse<{ success: boolean; message?: string }>>(
        `/flows/${flowId}/resume`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response;
    } catch (error) {
      handleApiError(error, 'resumeFlow');
      throw error;
    }
  },

  /**
   * Get flow metrics and analytics
   */
  async getFlowMetrics(
    clientAccountId: string,
    engagementId?: string,
    flowType?: string
  ): Promise<FlowMetrics> {
    try {
      const params = new URLSearchParams();
      if (flowType) params.append('flowType', flowType);
      
      const response = await apiClient.get<FlowMetrics>(
        `/flows/metrics${params.toString() ? `?${params}` : ''}`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response;
    } catch (error) {
      handleApiError(error, 'getFlowMetrics');
      throw error;
    }
  },

  // Legacy compatibility methods for discovery flows
  
  /**
   * Initialize discovery flow (legacy compatibility)
   */
  async initializeDiscoveryFlow(
    clientAccountId: string,
    engagementId: string,
    config?: FlowConfiguration
  ): Promise<MasterFlowResponse> {
    return this.initializeFlow({
      clientAccountId,
      engagementId,
      flowType: 'discovery',
      config,
    });
  },

  /**
   * Get discovery flow status (legacy compatibility)
   */
  async getDiscoveryFlowStatus(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<FlowStatusResponse> {
    return this.getFlowStatus(flowId, clientAccountId, engagementId);
  },

  /**
   * Get active discovery flows (legacy compatibility)
   */
  async getActiveDiscoveryFlows(
    clientAccountId: string,
    engagementId?: string
  ): Promise<MasterFlowResponse[]> {
    return this.getActiveFlows(clientAccountId, engagementId, 'discovery');
  },
};

export default masterFlowService;