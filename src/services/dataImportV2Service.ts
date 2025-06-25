import { apiCall } from '../config/api';
import { getAuthHeaders } from '../utils/contextUtils';
import { 
  unifiedDiscoveryService,
  UnifiedDiscoveryFlowRequest,
  UnifiedDiscoveryFlowResponse
} from './discoveryUnifiedService';

/**
 * Data Import Service v2 - MIGRATED TO UNIFIED DISCOVERY API
 * Now uses consolidated /api/v1/discovery endpoints
 * 
 * @deprecated Use unifiedDiscoveryService directly for new code
 */

export interface CreateDiscoveryFlowRequest {
  flow_id: string;
  raw_data: Array<Record<string, any>>;
  metadata?: Record<string, any>;
  import_session_id?: string;
  user_id?: string;
}

export interface DiscoveryFlowResponse {
  id: string;
  flow_id: string;
  current_phase: string;
  progress_percentage: number;
  status: string;
  raw_data: Array<Record<string, any>>;
  field_mappings?: Record<string, any>;
  cleaned_data?: Array<Record<string, any>>;
  asset_inventory?: Record<string, any>;
  dependencies?: Record<string, any>;
  tech_debt?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PhaseUpdateRequest {
  phase_data: Record<string, any>;
  completion_percentage?: number;
}

export interface ValidationResult {
  success: boolean;
  message: string;
  errors?: string[];
  warnings?: string[];
}

/**
 * Create a new discovery flow with imported data
 * @deprecated Use unifiedDiscoveryService.initializeFlow() instead
 */
export const createDiscoveryFlow = async (
  flowId: string,
  rawData: Array<Record<string, any>>,
  metadata: Record<string, any> = {},
  importSessionId?: string
): Promise<DiscoveryFlowResponse> => {
  try {
    console.log('🔄 DEPRECATED: Redirecting createDiscoveryFlow to unified service');
    
    // Convert to unified format
    const unifiedRequest: UnifiedDiscoveryFlowRequest = {
      raw_data: rawData,
      metadata: {
        source: 'data_import',
        import_timestamp: new Date().toISOString(),
        ...metadata
      },
      import_session_id: importSessionId,
      execution_mode: 'hybrid'
    };

    const result = await unifiedDiscoveryService.initializeFlow(unifiedRequest);
    
    // Convert unified response to legacy format
    return {
      id: result.flow_id,
      flow_id: result.flow_id,
      current_phase: result.current_phase,
      progress_percentage: result.progress_percentage,
      status: result.status,
      raw_data: rawData,
      field_mappings: {},
      cleaned_data: [],
      asset_inventory: {},
      dependencies: {},
      tech_debt: {},
      created_at: result.created_at,
      updated_at: result.updated_at
    };
  } catch (error) {
    console.error('Error creating discovery flow:', error);
    throw error;
  }
};

/**
 * Get discovery flow by CrewAI Flow ID
 * @deprecated Use unifiedDiscoveryService.getFlowStatus() instead
 */
export const getDiscoveryFlow = async (flowId: string): Promise<DiscoveryFlowResponse> => {
  try {
    console.log('🔄 DEPRECATED: Redirecting getDiscoveryFlow to unified service');
    
    const result = await unifiedDiscoveryService.getFlowStatus(flowId);
    
    // Convert unified response to legacy format
    return {
      id: result.flow_id,
      flow_id: result.flow_id,
      current_phase: result.current_phase,
      progress_percentage: result.progress_percentage,
      status: result.status,
      raw_data: [], // Not available in unified response
      field_mappings: {},
      cleaned_data: [],
      asset_inventory: {},
      dependencies: {},
      tech_debt: {},
      created_at: result.created_at,
      updated_at: result.updated_at
    };
  } catch (error) {
    console.error('Error getting discovery flow:', error);
    throw error;
  }
};

/**
 * Update phase completion in discovery flow
 */
export const updatePhaseCompletion = async (
  flowId: string,
  phase: string,
  phaseData: Record<string, any>,
  completionPercentage?: number
): Promise<DiscoveryFlowResponse> => {
  try {
    const requestData: PhaseUpdateRequest = {
      phase_data: phaseData,
      completion_percentage: completionPercentage
    };

    const response = await apiCall(`/api/v1/discovery-flows/flows/${flowId}/phase?phase=${phase}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to update phase: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating phase:', error);
    throw error;
  }
};

/**
 * Execute discovery flow phase
 */
export const executeDiscoveryFlowPhase = async (flowId: string, phase: string): Promise<{
  success: boolean;
  current_phase: string;
  progress_percentage: number;
  message: string;
}> => {
  try {
    // Use unified discovery service
    const response = await unifiedDiscoveryService.executePhase(flowId, phase);
    return {
      success: true,
      current_phase: response.current_phase,
      progress_percentage: response.progress_percentage,
      message: `Phase ${phase} executed successfully`
    };
  } catch (error) {
    console.error('Error executing discovery flow phase:', error);
    throw error;
  }
};

/**
 * Complete discovery flow
 */
export const completeDiscoveryFlow = async (flowId: string): Promise<{
  success: boolean;
  assessment_package: Record<string, any>;
  message: string;
}> => {
  try {
    // Use unified discovery service
    const response = await unifiedDiscoveryService.completeFlow(flowId);
    return {
      success: true,
      assessment_package: response.assessment_package || {},
      message: 'Discovery flow completed successfully'
    };
  } catch (error) {
    console.error('Error completing discovery flow:', error);
    throw error;
  }
};

/**
 * Get discovery flow summary with statistics
 */
export const getDiscoveryFlowSummary = async (flowId: string): Promise<{
  flow: DiscoveryFlowResponse;
  statistics: Record<string, any>;
  assets_by_type: Record<string, number>;
  phase_progress: Record<string, boolean>;
}> => {
  try {
    // Use unified discovery service
    const response = await unifiedDiscoveryService.getFlowStatus(flowId);
    return {
      flow: response as DiscoveryFlowResponse,
      statistics: response.statistics || {},
      assets_by_type: response.assets_by_type || {},
      phase_progress: response.phases || {}
    };
  } catch (error) {
    console.error('Error getting flow summary:', error);
    throw error;
  }
};

/**
 * Get assets from discovery flow
 */
export const getDiscoveryFlowAssets = async (flowId: string): Promise<Array<{
  id: string;
  asset_name: string;
  asset_type: string;
  asset_data: Record<string, any>;
  discovered_in_phase: string;
  quality_score?: number;
  validation_status: string;
}>> => {
  try {
    // Use unified discovery service
    const response = await unifiedDiscoveryService.getFlowAssets(flowId);
    return response.assets || [];
  } catch (error) {
    console.error('Error getting flow assets:', error);
    throw error;
  }
};

/**
 * Validate asset data
 */
export const validateAsset = async (
  assetId: string,
  validationData: Record<string, any>
): Promise<ValidationResult> => {
  try {
    const response = await apiCall(`/api/v1/discovery-flows/assets/${assetId}/validate`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(validationData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to validate asset: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error validating asset:', error);
    throw error;
  }
};

/**
 * Check v2 API health
 */
export const checkV2ApiHealth = async (): Promise<{
  status: string;
  service: string;
  endpoints_available: number;
  database_connected: boolean;
  version: string;
}> => {
  try {
    // Use unified discovery service health check
    const response = await unifiedDiscoveryService.checkHealth();
    return {
      status: response.status,
      service: response.service,
      endpoints_available: 1,
      database_connected: true,
      version: response.version || '1.0.0'
    };
  } catch (error) {
    console.error('Error checking API health:', error);
    throw error;
  }
};

/**
 * List discovery flows with filtering
 */
export const listDiscoveryFlows = async (
  status?: string,
  limit: number = 10,
  offset: number = 0
): Promise<{
  flows: DiscoveryFlowResponse[];
  total: number;
  limit: number;
  offset: number;
}> => {
  try {
    // Use unified discovery service
    const response = await unifiedDiscoveryService.getActiveFlows();
    
    // Filter by status if provided
    let flows = response.flow_details || [];
    if (status) {
      flows = flows.filter(flow => flow.status === status);
    }
    
    // Apply pagination
    const total = flows.length;
    const paginatedFlows = flows.slice(offset, offset + limit);
    
    return {
      flows: paginatedFlows,
      total,
      limit,
      offset
    };
  } catch (error) {
    console.error('Error listing discovery flows:', error);
    throw error;
  }
}; 