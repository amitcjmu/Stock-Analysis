/**
 * Master Flow Service - Unified API for all flow operations
 * Replaces all legacy discovery, assessment, and other flow services
 */

import { ApiClient } from '../ApiClient';

const apiClient = ApiClient.getInstance();
import { AuthService } from '../../contexts/AuthContext/services/authService';

export interface MasterFlowRequest {
  clientAccountId: string;
  engagementId: string;
  flowType: 'discovery' | 'assessment' | 'planning' | 'execution' | 'modernize' | 'finops' | 'observability' | 'decommission';
  config?: Record<string, any>;
  userId?: string;
}

export interface MasterFlowResponse {
  flowId: string;
  status: 'initializing' | 'running' | 'completed' | 'failed' | 'paused';
  flowType: string;
  progress: number;
  currentPhase: string;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface FlowStatusResponse {
  flowId: string;
  status: string;
  progress: number;
  currentPhase: string;
  phaseDetails: Record<string, any>;
  errors: string[];
  metadata: Record<string, any>;
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
const handleApiError = (error: any, operation: string) => {
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
      const response = await apiClient.post<MasterFlowResponse>(
        '/flows/',
        request,
        {
          headers: getMultiTenantHeaders(
            request.clientAccountId,
            request.engagementId,
            request.userId
          ),
        }
      );
      return response;
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
      
      const response = await apiClient.get<MasterFlowResponse[]>(
        `/master-flows/active${params.toString() ? `?${params}` : ''}`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response;
    } catch (error) {
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
      await apiClient.delete(`/master-flows/${flowId}`, undefined, {
        headers: getMultiTenantHeaders(clientAccountId, engagementId),
      });
    } catch (error) {
      handleApiError(error, 'deleteFlow');
      throw error;
    }
  },

  /**
   * Update flow configuration
   */
  async updateFlowConfig(
    flowId: string,
    config: Record<string, any>,
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
  ): Promise<any> {
    try {
      const response = await apiClient.post(
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
  ): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (flowType) params.append('flowType', flowType);
      
      const response = await apiClient.get<any>(
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
    config?: Record<string, any>
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