import { apiCall, API_CONFIG } from '../config/api';
import { getAuthHeaders } from '../utils/contextUtils';

/**
 * Asset data structure for external data cleansing integrations
 */
export interface AssetData {
  id?: string;
  name: string;
  type: string;
  status?: string;
  attributes?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

/**
 * Fix data structure for quality issue resolution
 */
export interface QualityFixData {
  action: 'merge' | 'update' | 'delete' | 'validate';
  targetId?: string;
  updates?: Record<string, unknown>;
  reason?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Fetches the latest import data for data cleansing
 */
export const fetchLatestImport = async (): Promise<AssetData[]> => {
  try {
    const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.LATEST_IMPORT, {
      headers: getAuthHeaders()
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to fetch latest import');
    }

    return response.data || [];
  } catch (error) {
    console.error('Error fetching latest import:', error);
    throw error;
  }
};

/**
 * Fetches assets from the backend
 */
export const fetchAssets = async (page = 1, pageSize = 1000): Promise<AssetData[]> => {
  try {
    const response = await apiCall(
      `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}?page=${page}&page_size=${pageSize}`,
      { headers: getAuthHeaders() }
    );

    if (!response?.assets) {
      throw new Error('Invalid assets response');
    }

    return response.assets;
  } catch (error) {
    console.error('Error fetching assets:', error);
    throw error;
  }
};

/**
 * Performs agent quality analysis on the provided data
 */
export const performAgentAnalysis = async (data: AssetData[]): Promise<{
  success: boolean;
  data: {
    issues: Array<{
      id: string;
      type: string;
      severity: string;
      description: string;
      affected_assets: string[];
    }>;
    summary: {
      total_issues: number;
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
}> => {
  try {
    const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.ANALYZE_QUALITY, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ assets: data })
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Analysis failed');
    }

    return response.data;
  } catch (error) {
    console.error('Error performing agent analysis:', error);
    throw error;
  }
};

/**
 * Applies a fix to a specific issue
 */
export const applyFix = async (issueId: string, fixData: QualityFixData): Promise<{
  success: boolean;
  data: {
    fixed: boolean;
    message: string;
    updated_assets: string[];
  };
}> => {
  try {
    const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.APPLY_FIX}/${issueId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(fixData)
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to apply fix');
    }

    return response.data;
  } catch (error) {
    console.error('Error applying fix:', error);
    throw error;
  }
};

export default {
  fetchLatestImport,
  fetchAssets,
  performAgentAnalysis,
  applyFix
};
