/**
 * LEGACY - MARKED FOR ARCHIVAL
 * 
 * Flow Service for Master Flow Orchestrator
 * MFO-079: Create FlowService API client
 * 
 * ⚠️ DEPRECATED: This service is superseded by masterFlowService.ts
 * All functionality should use masterFlowService and its extensions instead.
 * This file is marked for archival to avoid confusion.
 * 
 * Use: /services/api/masterFlowService.ts and masterFlowService.extensions.ts
 */

import { ApiClient } from './ApiClient';
import type { FlowStatus, FlowType, CreateFlowRequest, ExecutePhaseRequest } from '../types/flow'
import { FlowAnalytics } from '../types/flow'
import type { ApiError } from '../types/shared/api-types';

export interface FlowListOptions {
  flow_type?: FlowType;
  status?: string;
  limit?: number;
  offset?: number;
}

export interface PauseFlowRequest {
  reason?: string;
}

export interface DeleteFlowRequest {
  reason?: string;
  soft_delete?: boolean;
}

/**
 * Unified Flow Service for Master Flow Orchestrator
 * Provides type-safe API client for all flow operations
 */
export class FlowService {
  private static instance: FlowService;
  private apiClient: ApiClient;

  private constructor() {
    this.apiClient = ApiClient.getInstance();
  }

  public static getInstance(): FlowService {
    if (!FlowService.instance) {
      FlowService.instance = new FlowService();
    }
    return FlowService.instance;
  }

  /**
   * Create a new flow (MFO-075)
   */
  async createFlow(request: CreateFlowRequest): Promise<FlowStatus> {
    try {
      const response = await this.apiClient.post<FlowStatus>('/flows', request);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to create flow');
    }
  }

  /**
   * Get all flows (MFO-077)
   */
  async getFlows(options: FlowListOptions = {}): Promise<FlowStatus[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (options.flow_type) queryParams.append('flow_type', options.flow_type);
      if (options.status) queryParams.append('status', options.status);
      if (options.limit) queryParams.append('limit', options.limit.toString());
      if (options.offset) queryParams.append('offset', options.offset.toString());

      const url = `/flows${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await this.apiClient.get<FlowStatus[]>(url);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to get flows');
    }
  }

  /**
   * Get flow status (MFO-077)
   */
  async getFlowStatus(flowId: string, includeDetails: boolean = true): Promise<FlowStatus> {
    try {
      const url = includeDetails 
        ? `/flows/${flowId}?include_details=true`
        : `/flows/${flowId}`;
      
      const response = await this.apiClient.get<FlowStatus>(url);
      return response;
    } catch (error) {
      throw this.handleError(error, `Failed to get flow status for ${flowId}`);
    }
  }

  /**
   * Execute flow phase (MFO-076)
   */
  async executePhase(flowId: string, request: ExecutePhaseRequest): Promise<{ success: boolean; message?: string; data?: Record<string, unknown> }> {
    try {
      const response = await this.apiClient.post(`/flows/${flowId}/execute`, request);
      return response;
    } catch (error) {
      throw this.handleError(error, `Failed to execute phase for flow ${flowId}`);
    }
  }

  /**
   * Pause flow
   */
  async pauseFlow(flowId: string, reason?: string): Promise<void> {
    try {
      const request: PauseFlowRequest = {};
      if (reason) request.reason = reason;

      await this.apiClient.post(`/flows/${flowId}/pause`, request);
    } catch (error) {
      throw this.handleError(error, `Failed to pause flow ${flowId}`);
    }
  }

  /**
   * Resume flow
   */
  async resumeFlow(flowId: string): Promise<void> {
    try {
      await this.apiClient.post(`/flows/${flowId}/resume`, {});
    } catch (error) {
      throw this.handleError(error, `Failed to resume flow ${flowId}`);
    }
  }

  /**
   * Delete flow
   */
  async deleteFlow(flowId: string, reason?: string, softDelete: boolean = true): Promise<void> {
    try {
      const request: DeleteFlowRequest = {
        soft_delete: softDelete
      };
      if (reason) request.reason = reason;

      await this.apiClient.delete(`/flows/${flowId}`, request);
    } catch (error) {
      throw this.handleError(error, `Failed to delete flow ${flowId}`);
    }
  }

  /**
   * Get flow analytics
   */
  async getFlowAnalytics(flowId?: string): Promise<FlowAnalytics> {
    try {
      const url = flowId ? `/flows/analytics?flow_id=${flowId}` : '/flows/analytics';
      const response = await this.apiClient.get<FlowAnalytics>(url);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to get flow analytics');
    }
  }

  /**
   * Get active flows by type
   */
  async getActiveFlowsByType(flowType: FlowType): Promise<FlowStatus[]> {
    try {
      const response = await this.apiClient.get<FlowStatus[]>(
        `/flows?flow_type=${flowType}&status=running,paused,pending`
      );
      return response;
    } catch (error) {
      throw this.handleError(error, `Failed to get active ${flowType} flows`);
    }
  }

  /**
   * Discovery-specific methods
   */
  async createDiscoveryFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'discovery'
    });
  }

  async getDiscoveryFlows(): Promise<FlowStatus[]> {
    return this.getActiveFlowsByType('discovery');
  }

  /**
   * Assessment-specific methods
   */
  async createAssessmentFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'assessment'
    });
  }

  async getAssessmentFlows(): Promise<FlowStatus[]> {
    return this.getActiveFlowsByType('assessment');
  }

  /**
   * Planning-specific methods
   */
  async createPlanningFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'planning'
    });
  }

  /**
   * Execution-specific methods
   */
  async createExecutionFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'execution'
    });
  }

  /**
   * Modernize-specific methods
   */
  async createModernizeFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'modernize'
    });
  }

  /**
   * FinOps-specific methods
   */
  async createFinOpsFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'finops'
    });
  }

  /**
   * Observability-specific methods
   */
  async createObservabilityFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'observability'
    });
  }

  /**
   * Decommission-specific methods
   */
  async createDecommissionFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    return this.createFlow({
      ...config,
      flow_type: 'decommission'
    });
  }

  /**
   * Utility methods
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await this.apiClient.get<{ status: string; timestamp: string }>('/health');
      return response;
    } catch (error) {
      throw this.handleError(error, 'Health check failed');
    }
  }

  async getFlowTypes(): Promise<string[]> {
    try {
      const response = await this.apiClient.get<string[]>('/flows/types');
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to get flow types');
    }
  }

  /**
   * Error handling
   */
  private handleError(error: ApiError | Error, message: string): Error {
    console.error(`FlowService Error: ${message}`, error);
    
    if (error.response) {
      // API returned an error response
      const apiError = error.response.data?.detail || error.response.statusText || 'Unknown API error';
      return new Error(`${message}: ${apiError}`);
    } else if (error.request) {
      // Network error
      return new Error(`${message}: Network error`);
    } else {
      // Other error
      return new Error(`${message}: ${error.message || 'Unknown error'}`);
    }
  }
}

/**
 * Legacy compatibility - backward compatibility wrappers (MFO-081)
 */
export class LegacyDiscoveryService {
  private flowService: FlowService;

  constructor() {
    this.flowService = FlowService.getInstance();
  }

  async createFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    console.warn('LegacyDiscoveryService.createFlow is deprecated. Use FlowService.createDiscoveryFlow instead.');
    return this.flowService.createDiscoveryFlow(config);
  }

  async getFlowStatus(flowId: string): Promise<FlowStatus> {
    console.warn('LegacyDiscoveryService.getFlowStatus is deprecated. Use FlowService.getFlowStatus instead.');
    return this.flowService.getFlowStatus(flowId);
  }

  async executePhase(flowId: string, phase: string, data: Record<string, unknown>): Promise<{ success: boolean; message?: string; data?: Record<string, unknown> }> {
    console.warn('LegacyDiscoveryService.executePhase is deprecated. Use FlowService.executePhase instead.');
    return this.flowService.executePhase(flowId, {
      phase_name: phase,
      phase_input: data
    });
  }
}

export class LegacyAssessmentService {
  private flowService: FlowService;

  constructor() {
    this.flowService = FlowService.getInstance();
  }

  async createFlow(config: Omit<CreateFlowRequest, 'flow_type'>): Promise<FlowStatus> {
    console.warn('LegacyAssessmentService.createFlow is deprecated. Use FlowService.createAssessmentFlow instead.');
    return this.flowService.createAssessmentFlow(config);
  }

  async getFlowStatus(flowId: string): Promise<FlowStatus> {
    console.warn('LegacyAssessmentService.getFlowStatus is deprecated. Use FlowService.getFlowStatus instead.');
    return this.flowService.getFlowStatus(flowId);
  }
}

// Export singleton instance
export const flowService = FlowService.getInstance();