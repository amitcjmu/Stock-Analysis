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

import { 
  unifiedDiscoveryService,
  UnifiedDiscoveryFlowRequest,
  UnifiedDiscoveryFlowResponse
} from './discoveryUnifiedService';

// Configuration - DEPRECATED
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
// V2_API_BASE removed - now using unified discovery service

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

// HTTP client wrapper
class HttpClient {
  private async request<T>(url: string, options: RequestInit = {}): Promise<T> {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Account-Id': '11111111-1111-1111-1111-111111111111',  
          'X-Engagement-Id': '22222222-2222-2222-2222-222222222222',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new DiscoveryFlowV2Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof DiscoveryFlowV2Error) {
        throw error;
      }
      throw new DiscoveryFlowV2Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
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

  async delete(url: string): Promise<void> {
    await this.request<void>(url, { method: 'DELETE' });
  }
}

// Service class
export class DiscoveryFlowV2Service {
  private http = new HttpClient();

  async checkHealth(): Promise<HealthStatus> {
    try {
      // Use unified discovery service health check
      const response = await unifiedDiscoveryService.checkHealth();
      return {
        status: response.status,
        service: response.service,
        version: response.version || '1.0.0',
        endpoints_available: 1,
        database_connected: true
      };
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  async createFlow(data: CreateFlowRequest): Promise<DiscoveryFlowV2> {
    try {
      const response = await unifiedDiscoveryService.initializeFlow({
        raw_data: data.raw_data,
        metadata: data.metadata,
        import_session_id: data.import_session_id
      });
      
      // Convert to V2 format
      return this.convertToV2Format(response, data);
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
      const response = await unifiedDiscoveryService.getFlowStatus(flowId);
      return this.convertToV2Format(response);
    } catch (error) {
      console.error(`Failed to get flow ${flowId}:`, error);
      throw error;
    }
  }

  async getAllFlows(): Promise<DiscoveryFlowV2[]> {
    try {
      const response = await unifiedDiscoveryService.getActiveFlows();
      return (response.flow_details || []).map(flow => this.convertToV2Format(flow));
    } catch (error) {
      console.error('Failed to get all flows:', error);
      throw error;
    }
  }

  async updateFlowPhase(flowId: string, phase: string): Promise<DiscoveryFlowV2> {
    try {
      const response = await unifiedDiscoveryService.executePhase(flowId, phase);
      const result = this.convertToV2Format(response);
      toast.success(`Flow phase updated to ${phase}`);
      return result;
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to update flow phase';
      toast.error(message);
      throw error;
    }
  }

  async completeFlow(flowId: string): Promise<DiscoveryFlowV2> {
    try {
      const response = await unifiedDiscoveryService.completeFlow(flowId);
      const result = this.convertToV2Format(response);
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
      await unifiedDiscoveryService.deleteFlow(flowId);
      toast.success('Discovery flow deleted successfully');
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to delete discovery flow';
      toast.error(message);
      throw error;
    }
  }

  // Helper method to convert unified service response to V2 format
  private convertToV2Format(response: any, createData?: CreateFlowRequest): DiscoveryFlowV2 {
    return {
      id: response.flow_id || response.id,
      flow_id: response.flow_id || response.id,
      client_account_id: '11111111-1111-1111-1111-111111111111',
      engagement_id: '22222222-2222-2222-2222-222222222222',
      user_id: createData?.user_id || 'default-user',
      import_session_id: response.import_session_id || createData?.import_session_id,
      flow_name: createData?.flow_name || `Flow ${response.flow_id || response.id}`,
      flow_description: createData?.flow_description,
      status: response.status,
      progress_percentage: response.progress_percentage || 0,
      phases: response.phases || {},
      crewai_persistence_id: response.crewai_persistence_id,
      learning_scope: 'client',
      memory_isolation_level: 'engagement',
      assessment_ready: response.assessment_ready || false,
      created_at: response.created_at,
      updated_at: response.updated_at,
      completed_at: response.completed_at,
      migration_readiness_score: response.migration_readiness_score || 0,
      next_phase: response.next_phase,
      is_complete: response.status === 'completed'
    };
  }

  async getFlowSummary(flowId: string): Promise<FlowSummary> {
    try {
      const response = await unifiedDiscoveryService.getFlowStatus(flowId);
      return {
        flow: this.convertToV2Format(response),
        statistics: response.statistics || {},
        assets_by_type: response.assets_by_type || {},
        phase_progress: response.phases || {}
      };
    } catch (error) {
      console.error(`Failed to get flow summary for ${flowId}:`, error);
      throw error;
    }
  }

  async getFlowAssets(flowId: string): Promise<DiscoveryAssetV2[]> {
    try {
      const response = await unifiedDiscoveryService.getFlowAssets(flowId);
      return response.assets || [];
    } catch (error) {
      console.error(`Failed to get flow assets for ${flowId}:`, error);
      throw error;
    }
  }

  async getFlowAsset(flowId: string, assetId: string): Promise<DiscoveryAssetV2> {
    try {
      const response = await unifiedDiscoveryService.getFlowAssets(flowId);
      const asset = (response.assets || []).find(a => a.id === assetId);
      if (!asset) {
        throw new DiscoveryFlowV2Error(`Asset ${assetId} not found in flow ${flowId}`);
      }
      return asset;
    } catch (error) {
      console.error(`Failed to get asset ${assetId} from flow ${flowId}:`, error);
      throw error;
    }
  }

  async updateFlowAsset(flowId: string, assetId: string, data: Partial<DiscoveryAssetV2>): Promise<DiscoveryAssetV2> {
    try {
      // Note: Unified service doesn't have individual asset update yet
      // This would need to be implemented in the unified service
      console.warn('Asset update not yet implemented in unified service');
      throw new DiscoveryFlowV2Error('Asset update not yet implemented');
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to update flow asset';
      toast.error(message);
      throw error;
    }
  }

  async createFlowAssets(flowId: string): Promise<{ success: boolean; assets_created: number; message: string }> {
    try {
      // This would trigger asset creation in the unified service
      await unifiedDiscoveryService.executePhase(flowId, 'asset_creation');
      return {
        success: true,
        assets_created: 0, // Would need to be returned from unified service
        message: 'Assets creation initiated'
      };
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to create flow assets';
      toast.error(message);
      throw error;
    }
  }

  async validateFlowCompletion(flowId: string): Promise<FlowCompletionValidation> {
    try {
      const response = await unifiedDiscoveryService.getFlowStatus(flowId);
      return {
        is_valid: response.assessment_ready || false,
        missing_phases: [],
        asset_count: response.total_assets || 0,
        readiness_score: response.migration_readiness_score || 0,
        validation_errors: []
      };
    } catch (error) {
      console.error(`Failed to validate flow completion for ${flowId}:`, error);
      throw error;
    }
  }

  async getAssessmentReadyAssets(flowId: string, filters?: AssessmentAssetFilters): Promise<DiscoveryAssetV2[]> {
    try {
      const response = await unifiedDiscoveryService.getFlowAssets(flowId);
      let assets = response.assets || [];
      
      // Apply filters if provided
      if (filters?.asset_type) {
        assets = assets.filter(asset => asset.asset_type === filters.asset_type);
      }
      if (filters?.min_quality_score) {
        assets = assets.filter(asset => (asset.quality_score || 0) >= filters.min_quality_score!);
      }
      
      return assets;
    } catch (error) {
      console.error(`Failed to get assessment ready assets for ${flowId}:`, error);
      throw error;
    }
  }

  async generateAssessmentPackage(flowId: string, options?: AssessmentPackageOptions): Promise<AssessmentPackage> {
    try {
      const response = await unifiedDiscoveryService.completeFlow(flowId);
      return {
        flow_id: flowId,
        package_id: `pkg_${flowId}`,
        generated_at: new Date().toISOString(),
        assets: response.assets || [],
        summary: response.summary || {},
        recommendations: response.recommendations || [],
        metadata: response.metadata || {}
      };
    } catch (error) {
      const message = error instanceof DiscoveryFlowV2Error 
        ? error.message 
        : 'Failed to generate assessment package';
      toast.error(message);
      throw error;
    }
  }

  async completeFlowWithAssessment(flowId: string, options?: AssessmentPackageOptions): Promise<FlowCompletionResult> {
    try {
      const response = await unifiedDiscoveryService.completeFlow(flowId);
      return {
        success: true,
        flow: this.convertToV2Format(response),
        assessment_package: {
          flow_id: flowId,
          package_id: `pkg_${flowId}`,
          generated_at: new Date().toISOString(),
          assets: response.assets || [],
          summary: response.summary || {},
          recommendations: response.recommendations || [],
          metadata: response.metadata || {}
        },
        message: 'Flow completed with assessment package'
      };
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