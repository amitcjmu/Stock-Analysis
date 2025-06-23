/**
 * Discovery Flow V2 Service
 * Comprehensive service layer for V2 API integration with error handling and type safety
 */

import { toast } from 'sonner';

// Types
export interface DiscoveryFlowV2 {
  id: string;
  flow_id: string;
  client_account_id: string;
  engagement_id: string;
  user_id: string;
  import_session_id?: string;
  data_import_id?: string;
  flow_name: string;
  flow_description?: string;
  status: string;
  progress_percentage: number;
  phases: Record<string, boolean>;
  crewai_persistence_id?: string;
  learning_scope: string;
  memory_isolation_level: string;
  assessment_ready: boolean;
  is_mock: boolean;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
  migration_readiness_score: number;
  next_phase?: string;
  is_complete: boolean;
}

export interface DiscoveryAssetV2 {
  id: string;
  discovery_flow_id: string;
  client_account_id: string;
  engagement_id: string;
  asset_name: string;
  asset_type?: string;
  asset_subtype?: string;
  raw_data: Record<string, any>;
  normalized_data?: Record<string, any>;
  discovered_in_phase: string;
  discovery_method?: string;
  confidence_score?: number;
  migration_ready: boolean;
  migration_complexity?: string;
  migration_priority?: number;
  asset_status: string;
  validation_status: string;
  is_mock: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FlowCompletionValidation {
  flow_id: string;
  is_ready: boolean;
  validation_checks: Record<string, any>;
  warnings: string[];
  errors: string[];
  asset_summary: Record<string, any>;
  readiness_score: number;
}

export interface AssessmentPackage {
  package_id: string;
  generated_at: string;
  discovery_flow: Record<string, any>;
  assets: any[];
  summary: Record<string, any>;
  migration_waves: any[];
  risk_assessment: Record<string, any>;
  recommendations: Record<string, any>;
}

export interface CreateFlowRequest {
  flow_id: string;
  raw_data: any[];
  metadata?: Record<string, any>;
  import_session_id?: string;
  user_id?: string;
}

export interface UpdatePhaseRequest {
  phase: string;
  phase_data: any;
}

export interface FlowSummary {
  flow_id: string;
  total_assets: number;
  assets_by_phase: Record<string, number>;
  assets_by_status: Record<string, number>;
  completion_percentage: number;
  migration_readiness_score: number;
  phase_statistics: Record<string, any>;
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  database_connected: boolean;
  api_version: string;
}

// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const V2_API_BASE = `${API_BASE_URL}/api/v2/discovery-flows`;

// Error handling utility
class DiscoveryFlowV2Error extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'DiscoveryFlowV2Error';
  }
}

// HTTP client utility
class HttpClient {
  private async request<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        // Multi-tenant context headers (demo values)
        'X-Client-Account-Id': '11111111-1111-1111-1111-111111111111',
        'X-Engagement-Id': '22222222-2222-2222-2222-222222222222',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorData = null;
        
        try {
          errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch {
          // If JSON parsing fails, use the default error message
        }
        
        throw new DiscoveryFlowV2Error(errorMessage, response.status, errorData);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof DiscoveryFlowV2Error) {
        throw error;
      }
      
      // Network or other errors
      throw new DiscoveryFlowV2Error(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  async get<T>(url: string): Promise<T> {
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>(url, { method: 'DELETE' });
  }
}

// Service class
export class DiscoveryFlowV2Service {
  private http = new HttpClient();

  // Health check
  async getHealth(): Promise<HealthStatus> {
    try {
      return await this.http.get<HealthStatus>(`${V2_API_BASE}/health`);
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  // Flow operations
  async createFlow(data: CreateFlowRequest): Promise<DiscoveryFlowV2> {
    try {
      const result = await this.http.post<DiscoveryFlowV2>(`${V2_API_BASE}/flows`, data);
      toast.success('Discovery flow created successfully');
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to create discovery flow';
      toast.error(message);
      throw error;
    }
  }

  async getFlow(flowId: string): Promise<DiscoveryFlowV2> {
    try {
      return await this.http.get<DiscoveryFlowV2>(`${V2_API_BASE}/flows/${flowId}`);
    } catch (error) {
      console.error(`Failed to get flow ${flowId}:`, error);
      throw error;
    }
  }

  async getAllFlows(): Promise<DiscoveryFlowV2[]> {
    try {
      return await this.http.get<DiscoveryFlowV2[]>(`${V2_API_BASE}/flows`);
    } catch (error) {
      console.error('Failed to get all flows:', error);
      throw error;
    }
  }

  async updatePhase(flowId: string, phaseData: UpdatePhaseRequest): Promise<DiscoveryFlowV2> {
    try {
      const result = await this.http.put<DiscoveryFlowV2>(`${V2_API_BASE}/flows/${flowId}/phase`, phaseData);
      toast.success(`Phase ${phaseData.phase} updated successfully`);
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : `Failed to update phase ${phaseData.phase}`;
      toast.error(message);
      throw error;
    }
  }

  async completeFlow(flowId: string): Promise<DiscoveryFlowV2> {
    try {
      const result = await this.http.post<DiscoveryFlowV2>(`${V2_API_BASE}/flows/${flowId}/complete`);
      toast.success('Discovery flow completed successfully');
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to complete discovery flow';
      toast.error(message);
      throw error;
    }
  }

  async deleteFlow(flowId: string): Promise<void> {
    try {
      await this.http.delete(`${V2_API_BASE}/flows/${flowId}`);
      toast.success('Discovery flow deleted successfully');
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to delete discovery flow';
      toast.error(message);
      throw error;
    }
  }

  async getFlowSummary(flowId: string): Promise<FlowSummary> {
    try {
      return await this.http.get<FlowSummary>(`${V2_API_BASE}/flows/${flowId}/summary`);
    } catch (error) {
      console.error(`Failed to get flow summary for ${flowId}:`, error);
      throw error;
    }
  }

  // Asset operations
  async getAssets(flowId: string): Promise<DiscoveryAssetV2[]> {
    try {
      return await this.http.get<DiscoveryAssetV2[]>(`${V2_API_BASE}/flows/${flowId}/assets`);
    } catch (error) {
      console.error(`Failed to get assets for flow ${flowId}:`, error);
      throw error;
    }
  }

  async getAsset(flowId: string, assetId: string): Promise<DiscoveryAssetV2> {
    try {
      return await this.http.get<DiscoveryAssetV2>(`${V2_API_BASE}/flows/${flowId}/assets/${assetId}`);
    } catch (error) {
      console.error(`Failed to get asset ${assetId}:`, error);
      throw error;
    }
  }

  async updateAsset(flowId: string, assetId: string, data: Partial<DiscoveryAssetV2>): Promise<DiscoveryAssetV2> {
    try {
      const result = await this.http.put<DiscoveryAssetV2>(`${V2_API_BASE}/flows/${flowId}/assets/${assetId}`, data);
      toast.success('Asset updated successfully');
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to update asset';
      toast.error(message);
      throw error;
    }
  }

  async createAssetsFromDiscovery(flowId: string): Promise<any> {
    try {
      const result = await this.http.post(`${V2_API_BASE}/flows/${flowId}/create-assets`);
      toast.success('Assets created from discovery data successfully');
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to create assets from discovery';
      toast.error(message);
      throw error;
    }
  }

  // Flow completion and validation
  async validateCompletion(flowId: string): Promise<FlowCompletionValidation> {
    try {
      return await this.http.get<FlowCompletionValidation>(`${V2_API_BASE}/flows/${flowId}/validation`);
    } catch (error) {
      console.error(`Failed to validate completion for flow ${flowId}:`, error);
      throw error;
    }
  }

  async getAssessmentReadyAssets(flowId: string, filters?: Record<string, any>): Promise<any> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, String(value));
          }
        });
      }
      
      const url = `${V2_API_BASE}/flows/${flowId}/assessment-ready-assets${params.toString() ? `?${params.toString()}` : ''}`;
      return await this.http.get(url);
    } catch (error) {
      console.error(`Failed to get assessment-ready assets for flow ${flowId}:`, error);
      throw error;
    }
  }

  async generateAssessmentPackage(flowId: string, selectedAssetIds?: string[]): Promise<AssessmentPackage> {
    try {
      const result = await this.http.post<AssessmentPackage>(
        `${V2_API_BASE}/flows/${flowId}/assessment-package`,
        { selected_asset_ids: selectedAssetIds }
      );
      toast.success('Assessment package generated successfully');
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to generate assessment package';
      toast.error(message);
      throw error;
    }
  }

  async completeWithAssessment(flowId: string, selectedAssetIds?: string[]): Promise<any> {
    try {
      const result = await this.http.post(
        `${V2_API_BASE}/flows/${flowId}/complete-with-assessment`,
        { selected_asset_ids: selectedAssetIds }
      );
      toast.success('Flow completed with assessment package generated');
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to complete flow with assessment';
      toast.error(message);
      throw error;
    }
  }

  // Utility methods
  getProgressPercentage(flow: DiscoveryFlowV2): number {
    return flow.progress_percentage || 0;
  }

  getCompletedPhases(flow: DiscoveryFlowV2): string[] {
    if (!flow.phases) return [];
    return Object.entries(flow.phases)
      .filter(([_, completed]) => completed)
      .map(([phase]) => phase);
  }

  getNextPhase(flow: DiscoveryFlowV2): string | null {
    return flow.next_phase || null;
  }

  isFlowComplete(flow: DiscoveryFlowV2): boolean {
    return flow.is_complete || flow.status === 'completed';
  }

  isAssessmentReady(flow: DiscoveryFlowV2): boolean {
    return flow.assessment_ready || false;
  }

  // WebSocket connection for real-time updates
  createWebSocketConnection(flowId: string, onMessage?: (data: any) => void): WebSocket {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/discovery-flow/${flowId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`WebSocket connected for flow ${flowId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        onMessage?.(data);
      } catch (error) {
        console.error('WebSocket message parsing error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log(`WebSocket disconnected for flow ${flowId}`);
    };

    return ws;
  }
}

// Singleton instance
export const discoveryFlowV2Service = new DiscoveryFlowV2Service();

// Export types for convenience
export type {
  DiscoveryFlowV2Error,
};

// Utility functions
export const DiscoveryFlowV2Utils = {
  formatPhaseDisplayName: (phase: string): string => {
    return phase
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  },

  getPhaseIcon: (phase: string): string => {
    const icons: Record<string, string> = {
      data_import: '📥',
      attribute_mapping: '🗺️',
      data_cleansing: '🧹',
      inventory: '📋',
      dependencies: '🔗',
      tech_debt: '⚠️',
    };
    return icons[phase] || '📊';
  },

  getStatusColor: (status: string): string => {
    const colors: Record<string, string> = {
      created: 'blue',
      in_progress: 'yellow',
      completed: 'green',
      failed: 'red',
      cancelled: 'gray',
    };
    return colors[status] || 'gray';
  },

  formatMigrationComplexity: (complexity?: string): string => {
    if (!complexity) return 'Unknown';
    return complexity.charAt(0).toUpperCase() + complexity.slice(1);
  },

  calculateReadinessScore: (flow: DiscoveryFlowV2): number => {
    const completedPhases = Object.values(flow.phases || {}).filter(Boolean).length;
    const totalPhases = Object.keys(flow.phases || {}).length;
    return totalPhases > 0 ? Math.round((completedPhases / totalPhases) * 100) : 0;
  },
}; 