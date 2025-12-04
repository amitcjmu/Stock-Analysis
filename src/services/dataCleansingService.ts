import { apiCall, API_CONFIG } from '../config/api';
import { getAuthHeaders } from '../lib/api/apiClient';

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
 * Data cleansing statistics structure
 */
export interface DataCleansingStats {
  total_records: number;
  clean_records: number;
  records_with_issues: number;
  issues_by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  completion_percentage: number;
}

/**
 * Data quality issue structure
 */
export interface DataQualityIssue {
  id: string;
  field_name: string;
  issue_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affected_records: number;
  recommendation: string;
  auto_fixable: boolean;
}

/**
 * Data cleansing recommendation structure
 */
export interface DataCleansingRecommendation {
  id: string;
  category: 'standardization' | 'validation' | 'enrichment' | 'deduplication';
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  impact: string;
  effort_estimate: string;
  fields_affected: string[];
  // Additional fields for frontend compatibility (Issue #875, #876)
  confidence?: number;  // 0.0 to 1.0 range
  status?: 'pending' | 'applied' | 'rejected';
  agent_source?: string;
  implementation_steps?: string[];
}

/**
 * Data cleansing analysis structure
 */
export interface DataCleansingAnalysis {
  flow_id: string;
  analysis_timestamp: string;
  total_records: number;
  total_fields: number;
  quality_score: number;
  issues_count: number;
  recommendations_count: number;
  quality_issues: DataQualityIssue[];
  recommendations: DataCleansingRecommendation[];
  field_quality_scores: Record<string, number>;
  processing_status: string;
  source?: 'agent' | 'fallback' | 'mock' | 'agent_failed' | 'service_unavailable';
  // CC: Sample data for UI display (Data Processing Samples section)
  raw_data_sample?: Array<Record<string, unknown>>;
  cleaned_data_sample?: Array<Record<string, unknown>>;
}

/**
 * Trigger data cleansing analysis request
 */
export interface TriggerDataCleansingRequest {
  force_refresh?: boolean;
  include_agent_analysis?: boolean;
}

/**
 * Fetches data cleansing statistics for a specific flow
 */
export const fetchDataCleansingStats = async (flowId: string): Promise<DataCleansingStats> => {
  try {
    const response = await apiCall(`/flows/${flowId}/data-cleansing/stats`, {
      headers: getAuthHeaders()
    });

    if (!response?.total_records && response?.total_records !== 0) {
      throw new Error('Invalid data cleansing stats response');
    }

    return response as DataCleansingStats;
  } catch (error) {
    console.error('Error fetching data cleansing stats:', error);
    throw error;
  }
};

/**
 * Fetches complete data cleansing analysis for a specific flow
 */
export const fetchDataCleansingAnalysis = async (flowId: string, includeDetails = true): Promise<DataCleansingAnalysis> => {
  try {
    const response = await apiCall(`/flows/${flowId}/data-cleansing?include_details=${includeDetails}`, {
      headers: getAuthHeaders()
    });

    if (!response?.flow_id) {
      throw new Error('Invalid data cleansing analysis response');
    }

    return response as DataCleansingAnalysis;
  } catch (error) {
    console.error('Error fetching data cleansing analysis:', error);
    throw error;
  }
};

/**
 * Triggers data cleansing analysis for a specific flow
 */
export const triggerDataCleansingAnalysis = async (flowId: string, forceRefresh = false, includeAgentAnalysis = true): Promise<DataCleansingAnalysis> => {
  try {
    const response = await apiCall(`/flows/${flowId}/data-cleansing/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        force_refresh: forceRefresh,
        include_agent_analysis: includeAgentAnalysis
      })
    });

    if (!response?.flow_id) {
      throw new Error('Invalid data cleansing trigger response');
    }

    return response as DataCleansingAnalysis;
  } catch (error) {
    console.error('Error triggering data cleansing analysis:', error);
    throw error;
  }
};

/**
 * Fetches the latest import data for data cleansing (legacy)
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

/**
 * Downloads raw data as CSV file
 */
export const downloadRawData = async (flowId: string): Promise<void> => {
  try {
    const response = await fetch(`/api/v1/flows/${flowId}/data-cleansing/download/raw`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
      : `raw_data_${flowId.substring(0, 8)}_${new Date().toISOString().slice(0, 10)}.csv`;

    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading raw data:', error);
    throw error;
  }
};

/**
 * Downloads cleaned data as CSV file
 */
export const downloadCleanedData = async (flowId: string): Promise<void> => {
  try {
    const response = await fetch(`/api/v1/flows/${flowId}/data-cleansing/download/cleaned`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
      : `cleaned_data_${flowId.substring(0, 8)}_${new Date().toISOString().slice(0, 10)}.csv`;

    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading cleaned data:', error);
    throw error;
  }
};

/**
 * Apply or reject a cleansing recommendation
 */
export const applyRecommendation = async (
  flowId: string,
  recommendationId: string,
  action: 'apply' | 'reject',
  notes?: string
): Promise<{
  success: boolean;
  message: string;
  recommendation_id: string;
  action: string;
  applied_at: string;
}> => {
  try {
    const response = await apiCall(`/flows/${flowId}/data-cleansing/recommendations/${recommendationId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        action: action,
        notes: notes
      })
    });

    if (!response?.success) {
      throw new Error((response as any)?.message || 'Failed to apply recommendation');
    }

    return response as {
      success: boolean;
      message: string;
      recommendation_id: string;
      action: string;
      applied_at: string;
    };
  } catch (error) {
    console.error('Error applying recommendation:', error);
    throw error;
  }
};

export default {
  fetchLatestImport,
  fetchAssets,
  performAgentAnalysis,
  applyFix,
  downloadRawData,
  downloadCleanedData,
  applyRecommendation
};
