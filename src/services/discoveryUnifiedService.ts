/**
 * Unified Discovery Service
 * Single source of truth for all discovery operations.
 * Wraps the new consolidated /api/v1/discovery endpoints.
 */

import { apiCall } from '../config/api';
import { getAuthHeaders } from '../utils/contextUtils';

// Configuration - API base URL no longer needed as apiCall handles the full URL construction

// Types for unified discovery API
export interface UnifiedDiscoveryFlowRequest {
  raw_data: Array<Record<string, any>>;
  metadata?: Record<string, any>;
  import_session_id?: string;
  execution_mode?: 'crewai' | 'database' | 'hybrid';
}

export interface UnifiedDiscoveryFlowResponse {
  flow_id: string;
  session_id?: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  status: string;
  current_phase: string;
  progress_percentage: number;
  phases: Record<string, boolean>;
  crewai_status?: string;
  database_status?: string;
  agent_insights: Array<Record<string, any>>;
  created_at: string;
  updated_at: string;
}

export interface FlowExecutionRequest {
  phase?: string;
  data?: Record<string, any>;
  execution_mode?: 'crewai' | 'database' | 'hybrid';
}

// Error handling utility
class UnifiedDiscoveryError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'UnifiedDiscoveryError';
  }
}

// HTTP client with error handling
const httpClient = {
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    try {
      const response = await apiCall(`/discovery${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new UnifiedDiscoveryError(
          errorData.detail || `Request failed: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return response.json();
    } catch (error) {
      if (error instanceof UnifiedDiscoveryError) {
        throw error;
      }
      throw new UnifiedDiscoveryError(
        error instanceof Error ? error.message : 'Unknown error occurred'
      );
    }
  },

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  },

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  },
};

/**
 * Unified Discovery Service Class
 */
export class UnifiedDiscoveryService {
  
  // === Flow Management ===
  
  /**
   * Initialize a new discovery flow
   */
  async initializeFlow(data: UnifiedDiscoveryFlowRequest): Promise<UnifiedDiscoveryFlowResponse> {
    try {
      console.log('🚀 Initializing unified discovery flow:', data);
      const result = await httpClient.post<UnifiedDiscoveryFlowResponse>('/flow/initialize', data);
      console.log('✅ Discovery flow initialized:', result.flow_id);
      return result;
    } catch (error) {
      console.error('❌ Failed to initialize discovery flow:', error);
      throw error;
    }
  }

  /**
   * Get discovery flow status
   */
  async getFlowStatus(flowId: string): Promise<UnifiedDiscoveryFlowResponse> {
    try {
      console.log('🔍 Getting flow status:', flowId);
      const result = await httpClient.get<UnifiedDiscoveryFlowResponse>(`/flow/status/${flowId}`);
      console.log('✅ Flow status retrieved:', result.status);
      return result;
    } catch (error) {
      console.error('❌ Failed to get flow status:', error);
      throw error;
    }
  }

  /**
   * Execute discovery flow phase
   */
  async executeFlow(request: FlowExecutionRequest): Promise<Record<string, any>> {
    try {
      console.log('🔄 Executing discovery flow phase:', request.phase);
      const result = await httpClient.post<Record<string, any>>('/flow/execute', request);
      console.log('✅ Flow execution completed:', result.status);
      return result;
    } catch (error) {
      console.error('❌ Failed to execute flow:', error);
      throw error;
    }
  }

  /**
   * Get active discovery flows
   */
  async getActiveFlows(): Promise<Record<string, any>> {
    try {
      console.log('🔍 Getting active discovery flows');
      const result = await httpClient.get<Record<string, any>>('/flows/active');
      console.log('✅ Active flows retrieved:', result.total_flows);
      return result;
    } catch (error) {
      console.error('❌ Failed to get active flows:', error);
      throw error;
    }
  }

  // === Asset Management ===

  /**
   * Get assets for a discovery flow
   */
  async getFlowAssets(flowId: string): Promise<{ assets: Array<Record<string, any>> }> {
    try {
      console.log('📦 Getting flow assets:', flowId);
      const result = await httpClient.get<{ assets: Array<Record<string, any>> }>(`/assets/${flowId}`);
      console.log('✅ Flow assets retrieved:', result.assets?.length || 0);
      return result;
    } catch (error) {
      console.error('❌ Failed to get flow assets:', error);
      throw error;
    }
  }

  /**
   * Execute a specific phase of a discovery flow
   */
  async executePhase(flowId: string, phase: string): Promise<UnifiedDiscoveryFlowResponse> {
    try {
      console.log('🔄 Executing flow phase:', { flowId, phase });
      const result = await httpClient.post<UnifiedDiscoveryFlowResponse>('/flow/execute', {
        flow_id: flowId,
        phase,
        execution_mode: 'hybrid'
      });
      console.log('✅ Phase execution completed:', result.status);
      return result;
    } catch (error) {
      console.error('❌ Failed to execute phase:', error);
      throw error;
    }
  }

  /**
   * Complete a discovery flow
   */
  async completeFlow(flowId: string): Promise<Record<string, any>> {
    try {
      console.log('🏁 Completing discovery flow:', flowId);
      const result = await httpClient.post<Record<string, any>>('/flow/complete', {
        flow_id: flowId
      });
      console.log('✅ Flow completed successfully');
      return result;
    } catch (error) {
      console.error('❌ Failed to complete flow:', error);
      throw error;
    }
  }

  /**
   * Delete a discovery flow
   */
  async deleteFlow(flowId: string, forceDelete: boolean = false): Promise<void> {
    try {
      console.log('🗑️ Deleting discovery flow:', { flowId, forceDelete });
      await httpClient.delete(`/flow/${flowId}?force_delete=${forceDelete}`);
      console.log('✅ Flow deleted successfully');
    } catch (error) {
      console.error('❌ Failed to delete flow:', error);
      throw error;
    }
  }

  /**
   * Continue a discovery flow
   */
  async continueFlow(flowId: string): Promise<{ success: boolean; message: string }> {
    try {
      console.log('▶️ Continuing discovery flow:', flowId);
      const result = await httpClient.post<{ success: boolean; message: string }>('/flow/continue', {
        flow_id: flowId
      });
      console.log('✅ Flow continuation initiated');
      return result;
    } catch (error) {
      console.error('❌ Failed to continue flow:', error);
      throw error;
    }
  }

  /**
   * Check health of unified discovery service
   */
  async checkHealth(): Promise<{ status: string; service: string; version?: string }> {
    try {
      console.log('🏥 Checking unified discovery health');
      const result = await httpClient.get<{ status: string; service: string; version?: string }>('/health');
      console.log('✅ Health check completed:', result.status);
      return result;
    } catch (error) {
      console.error('❌ Health check failed:', error);
      throw error;
    }
  }

  // === Health Check ===

  /**
   * Get unified discovery health status
   */
  async getHealthStatus(): Promise<Record<string, any>> {
    try {
      const result = await httpClient.get<Record<string, any>>('/health');
      return result;
    } catch (error) {
      console.error('❌ Failed to get health status:', error);
      throw error;
    }
  }

  // === Legacy Compatibility ===

  /**
   * Legacy flow run endpoint (redirects to unified execution)
   */
  async runFlow(request: Record<string, any>): Promise<Record<string, any>> {
    try {
      console.log('🔄 Legacy flow run (redirecting to unified)');
      const result = await httpClient.post<Record<string, any>>('/flow/run', request);
      return result;
    } catch (error) {
      console.error('❌ Legacy flow run failed:', error);
      throw error;
    }
  }

  /**
   * Legacy status endpoint (converts session_id to flow_id)
   */
  async getFlowStatusLegacy(sessionId: string): Promise<UnifiedDiscoveryFlowResponse> {
    try {
      console.log('🔄 Legacy status lookup (converting session_id)');
      const result = await httpClient.get<UnifiedDiscoveryFlowResponse>(`/flow/status?session_id=${sessionId}`);
      return result;
    } catch (error) {
      console.error('❌ Legacy status lookup failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const unifiedDiscoveryService = new UnifiedDiscoveryService();

// Export individual functions for backward compatibility
export const initializeDiscoveryFlow = (data: UnifiedDiscoveryFlowRequest) => 
  unifiedDiscoveryService.initializeFlow(data);

export const getDiscoveryFlowStatus = (flowId: string) => 
  unifiedDiscoveryService.getFlowStatus(flowId);

export const executeDiscoveryFlow = (request: FlowExecutionRequest) => 
  unifiedDiscoveryService.executeFlow(request);

export const getActiveDiscoveryFlows = () => 
  unifiedDiscoveryService.getActiveFlows();

export const getDiscoveryFlowAssets = (flowId: string) => 
  unifiedDiscoveryService.getFlowAssets(flowId);

export const getDiscoveryHealthStatus = () => 
  unifiedDiscoveryService.getHealthStatus();

// Legacy compatibility exports
export const runDiscoveryFlow = (request: Record<string, any>) => 
  unifiedDiscoveryService.runFlow(request);

export const getFlowStatusBySessionId = (sessionId: string) => 
  unifiedDiscoveryService.getFlowStatusLegacy(sessionId);

export default unifiedDiscoveryService; 