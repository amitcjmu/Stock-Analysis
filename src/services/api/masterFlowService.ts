/**
 * Master Flow Service - Unified API for all flow operations
 * Replaces all legacy discovery, assessment, and other flow services
 */

import apiClient from '../ApiClient';
import { AuthService } from '../../contexts/AuthContext/services/authService';

export interface MasterFlowRequest {
  clientAccountId: number;
  engagementId: string;
  flowType: 'discovery' | 'assessment' | 'planning' | 'execution' | 'modernize' | 'finops' | 'observability' | 'decommission';
  config?: Record<string, any>;
  userId?: number;
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
  clientAccountId: number,
  engagementId?: string,
  userId?: number
) => ({
  'X-Client-Account-ID': clientAccountId.toString(),
  ...(engagementId && { 'X-Engagement-ID': engagementId }),
  ...(userId && { 'X-User-ID': userId.toString() }),
  'Content-Type': 'application/json',
});

/**
 * Handle API errors consistently
 */
const handleApiError = (error: any, operation: string) => {
  console.error(`MasterFlowService.${operation} failed:`, error);
  if (error.response?.data?.message) {
    throw new Error(error.response.data.message);
  }
  throw new Error(`${operation} failed: ${error.message}`);
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
      const response = await apiClient.post(
        '/api/v1/flows/',
        request,
        {
          headers: getMultiTenantHeaders(
            request.clientAccountId,
            request.engagementId,
            request.userId
          ),
        }
      );
      return response.data;
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
    clientAccountId: number,
    engagementId?: string
  ): Promise<FlowStatusResponse> {
    try {
      const response = await apiClient.get(
        `/api/v1/flows/${flowId}/status`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error, 'getFlowStatus');
      throw error;
    }
  },

  /**
   * Get all active flows for a client
   */
  async getActiveFlows(
    clientAccountId: number,
    engagementId?: string,
    flowType?: string
  ): Promise<MasterFlowResponse[]> {
    try {
      const params = new URLSearchParams();
      if (flowType) params.append('flowType', flowType);
      
      const response = await apiClient.get(
        `/api/v1/flows/active${params.toString() ? `?${params}` : ''}`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response.data;
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
    clientAccountId: number,
    engagementId?: string
  ): Promise<void> {
    try {
      await apiClient.delete(`/api/v1/flows/${flowId}`, {
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
    clientAccountId: number,
    engagementId?: string
  ): Promise<void> {
    try {
      await apiClient.put(
        `/api/v1/flows/${flowId}/config`,
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
    clientAccountId: number,
    engagementId?: string
  ): Promise<void> {
    try {
      await apiClient.post(
        `/api/v1/flows/${flowId}/pause`,
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
    clientAccountId: number,
    engagementId?: string
  ): Promise<void> {
    try {
      await apiClient.post(
        `/api/v1/flows/${flowId}/resume`,
        {},
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
    } catch (error) {
      handleApiError(error, 'resumeFlow');
      throw error;
    }
  },

  /**
   * Get flow metrics and analytics
   */
  async getFlowMetrics(
    clientAccountId: number,
    engagementId?: string,
    flowType?: string
  ): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (flowType) params.append('flowType', flowType);
      
      const response = await apiClient.get(
        `/api/v1/flows/metrics${params.toString() ? `?${params}` : ''}`,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId),
        }
      );
      return response.data;
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
    clientAccountId: number,
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
    clientAccountId: number,
    engagementId?: string
  ): Promise<FlowStatusResponse> {
    return this.getFlowStatus(flowId, clientAccountId, engagementId);
  },

  /**
   * Get active discovery flows (legacy compatibility)
   */
  async getActiveDiscoveryFlows(
    clientAccountId: number,
    engagementId?: string
  ): Promise<MasterFlowResponse[]> {
    return this.getActiveFlows(clientAccountId, engagementId, 'discovery');
  },
};

export default masterFlowService;