import { apiCall } from '../config/api';
import { getAuthHeaders } from '../utils/contextUtils';

/**
 * Data Import Service v2 - Uses new discovery flow architecture
 * Integrates with /api/v2/discovery-flows endpoints
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
 */
export const createDiscoveryFlow = async (
  flowId: string,
  rawData: Array<Record<string, any>>,
  metadata: Record<string, any> = {},
  importSessionId?: string
): Promise<DiscoveryFlowResponse> => {
  try {
    const requestData: CreateDiscoveryFlowRequest = {
      flow_id: flowId,
      raw_data: rawData,
      metadata: {
        source: 'data_import',
        import_timestamp: new Date().toISOString(),
        ...metadata
      },
      import_session_id: importSessionId
    };

    const response = await apiCall('/api/v2/discovery-flows/flows', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create discovery flow: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating discovery flow:', error);
    throw error;
  }
};

/**
 * Get discovery flow by CrewAI Flow ID
 */
export const getDiscoveryFlow = async (flowId: string): Promise<DiscoveryFlowResponse> => {
  try {
    const response = await apiCall(`/api/v2/discovery-flows/flows/${flowId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get discovery flow: ${response.statusText}`);
    }

    return await response.json();
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

    const response = await apiCall(`/api/v2/discovery-flows/flows/${flowId}/phase?phase=${phase}`, {
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
 * Complete discovery flow
 */
export const completeDiscoveryFlow = async (flowId: string): Promise<{
  success: boolean;
  assessment_package: Record<string, any>;
  message: string;
}> => {
  try {
    const response = await apiCall(`/api/v2/discovery-flows/flows/${flowId}/complete`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to complete discovery flow: ${response.statusText}`);
    }

    return await response.json();
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
    const response = await apiCall(`/api/v2/discovery-flows/flows/${flowId}/summary`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get flow summary: ${response.statusText}`);
    }

    return await response.json();
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
    const response = await apiCall(`/api/v2/discovery-flows/flows/${flowId}/assets`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get flow assets: ${response.statusText}`);
    }

    return await response.json();
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
    const response = await apiCall(`/api/v2/discovery-flows/assets/${assetId}/validate`, {
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
    const response = await apiCall('/api/v2/discovery-flows/health', {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking v2 API health:', error);
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
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (status) {
      params.append('status', status);
    }

    const response = await apiCall(`/api/v2/discovery-flows/flows?${params.toString()}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to list flows: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error listing discovery flows:', error);
    throw error;
  }
}; 