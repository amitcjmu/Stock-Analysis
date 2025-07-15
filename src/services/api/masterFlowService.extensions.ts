/**
 * Extensions to masterFlowService for missing functionality
 * These methods support operations that are actively used but missing from the base service
 */

import { ApiClient } from '../ApiClient';
import { masterFlowService } from './masterFlowService';

const apiClient = ApiClient.getInstance();

// Extend the masterFlowService with additional methods
export const masterFlowServiceExtended = {
  // Include all existing methods
  ...masterFlowService,
  
  /**
   * Execute a specific phase in a flow
   */
  async executePhase(
    flowId: string,
    phase: string,
    phaseData: Record<string, any>,
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post(
      `/flows/${flowId}/execute`,
      { 
        phase_input: { 
          phase: phase, 
          ...phaseData 
        },
        force_execution: false
      },
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Validate flow data
   */
  async validateFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post(
      `/flows/${flowId}/validate`,
      {},
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Retry failed operations in a flow
   */
  async retryFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post(
      `/flows/${flowId}/retry`,
      {},
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Get validation status for a flow
   */
  async getValidationStatus(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get(
      `/flows/${flowId}/validation-status`,
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Get agent insights for a flow
   */
  async getAgentInsights(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get(
      `/flows/${flowId}/agent-insights`,
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Complete a flow
   * Required by: UploadBlocker
   */
  async completeFlow(
    flowId: string,
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post(
      `/flows/${flowId}/complete`,
      {},
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Get flow metrics (dashboard)
   * Required by: useDiscoveryDashboard
   */
  async getDiscoveryMetrics(
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get(
      `/flows/metrics?flowType=discovery`,
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Get application landscape data
   * Required by: useDiscoveryDashboard
   */
  async getApplicationLandscape(
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get(
      `/flows/analytics/application-landscape`,
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },

  /**
   * Get infrastructure landscape data
   * Required by: useDiscoveryDashboard
   */
  async getInfrastructureLandscape(
    clientAccountId: string,
    engagementId?: string
  ): Promise<any> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get(
      `/flows/analytics/infrastructure-landscape`,
      {
        headers: {
          'X-Client-Account-ID': clientAccountId,
          ...(engagementId && { 'X-Engagement-ID': engagementId }),
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      }
    );
  },
};

// Export as default to make it a drop-in replacement
export default masterFlowServiceExtended;