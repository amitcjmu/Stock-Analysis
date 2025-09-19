import { apiCall, API_CONFIG } from '../config/api';
import { getAuthHeaders } from '../lib/api/apiClient';

export interface DependencyCreate {
  source_id: string;
  target_id: string;
  dependency_type: string;
  is_app_to_app: boolean;
  description?: string;
}

export interface DependencyResponse {
  id: string;
  source_id: string;
  target_id: string;
  dependency_type: string;
  is_app_to_app: boolean;
  description?: string;
  confidence_score?: number;
  created_at: string;
  updated_at: string;
}

export interface DependencyAnalysisResponse {
  cross_application_mapping: {
    dependencies: Array<{
      source_app: string;
      target_app: string;
      dependency_type: string;
      confidence: number;
      status: string;
    }>;
    available_applications: Array<{
      id: string;
      name: string;
      asset_name?: string;
    }>;
  };
  app_server_mapping: {
    dependencies: Array<{
      application_name: string;
      server_name: string;
      confidence: number;
      status: string;
    }>;
    available_servers: Array<{
      id: string;
      name: string;
      asset_name?: string;
    }>;
  };
  total_dependencies: number;
  analysis_timestamp: string;
}

/**
 * Get comprehensive dependency analysis
 */
export const getDependencyAnalysis = async (flowId?: string): Promise<DependencyAnalysisResponse> => {
  try {
    const url = flowId
      ? `/unified-discovery/dependencies/analysis?flow_id=${flowId}`  // Updated to unified-discovery endpoint as part of API migration
      : '/unified-discovery/dependencies/analysis';  // Updated to unified-discovery endpoint as part of API migration

    const response = await apiCall(url, {
      headers: getAuthHeaders()
    });

    return response;
  } catch (error) {
    console.error('Error fetching dependency analysis:', error);
    throw error;
  }
};

/**
 * Create a new dependency relationship
 */
export const createDependency = async (dependency: DependencyCreate): Promise<DependencyResponse> => {
  try {
    const response = await apiCall('/unified-discovery/dependencies', {  // Updated to unified-discovery endpoint as part of API migration
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(dependency)
    });

    return response;
  } catch (error) {
    console.error('Error creating dependency:', error);
    throw error;
  }
};

/**
 * Get available applications for dependency mapping
 */
export const getAvailableApplications = async (): Promise<unknown> => {
  try {
    const response = await apiCall('/unified-discovery/dependencies/applications', {  // Updated to unified-discovery endpoint as part of API migration
      headers: getAuthHeaders()
    });

    return response;
  } catch (error) {
    console.error('Error fetching available applications:', error);
    throw error;
  }
};

/**
 * Get available servers for dependency mapping
 */
export const getAvailableServers = async (): Promise<unknown> => {
  try {
    const response = await apiCall('/unified-discovery/dependencies/servers', {  // Updated to unified-discovery endpoint as part of API migration
      headers: getAuthHeaders()
    });

    return response;
  } catch (error) {
    console.error('Error fetching available servers:', error);
    throw error;
  }
};

/**
 * Helper function to find asset ID by name from available assets
 */
export const findAssetIdByName = (
  assetName: string,
  assets: Array<{ id: string; name?: string; asset_name?: string }>
): string | null => {
  const asset = assets.find(a =>
    a.name === assetName ||
    a.asset_name === assetName
  );
  return asset?.id || null;
};

export default {
  getDependencyAnalysis,
  createDependency,
  getAvailableApplications,
  getAvailableServers,
  findAssetIdByName
};
