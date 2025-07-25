/**
 * Extensions to masterFlowService for missing functionality
 * These methods support operations that are actively used but missing from the base service
 */

import { ApiClient } from '../ApiClient';
import { masterFlowService } from './masterFlowService';
import type { ApiResponse } from '../../types/shared/api-types';

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
    phaseData: Record<string, unknown>,
    clientAccountId: string,
    engagementId?: string
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post<ApiResponse<{ valid: boolean; errors?: string[]; warnings?: string[] }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post<ApiResponse<{ success: boolean; message?: string }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get<ApiResponse<{ status: string; errors?: string[]; warnings?: string[]; last_validated?: string }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get<ApiResponse<{ insights: Array<{ agent: string; insight: string; confidence: number; timestamp: string }> }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.post<ApiResponse<{ success: boolean; completed_at: string; message?: string }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get<ApiResponse<{ total_flows: number; completed_flows: number; active_flows: number; failed_flows: number; metrics: Record<string, unknown> }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get<ApiResponse<{ applications: Array<Record<string, unknown>>; total_count: number; categories: Record<string, number> }>>(
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
  ): Promise<ApiResponse<{ success: boolean; message?: string; data?: Record<string, unknown> }>> {
    const token = localStorage.getItem('auth_token');
    return apiClient.get<ApiResponse<{ infrastructure: Array<Record<string, unknown>>; total_count: number; types: Record<string, number> }>>(
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
