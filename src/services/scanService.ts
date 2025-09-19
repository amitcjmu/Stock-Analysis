import { apiCall, API_CONFIG } from '../config/api';
import { getAuthHeaders } from '../lib/api/apiClient';

export interface ScanProgress {
  scanProgress: number;
  scannedApps: number;
  totalApps: number;
  scannedServers: number;
  totalServers: number;
  scannedDatabases: number;
  totalDatabases: number;
  startTime: string;
  estimatedCompletionTime: string;
  status: 'idle' | 'scanning' | 'paused' | 'completed' | 'error';
  lastUpdated: string;
}

export interface ScanLog {
  id: string;
  message: string;
  status: 'success' | 'error' | 'warning' | 'info' | 'progress';
  timestamp: string;
  details?: string;
  component?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

/**
 * Fetches the current scan progress
 */
export const fetchScanProgress = async (): Promise<ScanProgress> => {
  try {
    const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.SCAN_PROGRESS, {
      headers: getAuthHeaders()
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to fetch scan progress');
    }

    return response.data;
  } catch (error) {
    console.error('Error fetching scan progress:', error);
    throw error;
  }
};

/**
 * Fetches the scan logs
 */
export const fetchScanLogs = async (): Promise<ScanLog[]> => {
  try {
    const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.SCAN_LOGS, {
      headers: getAuthHeaders()
    });

    if (!Array.isArray(response?.data)) {
      throw new Error('Invalid scan logs response');
    }

    return response.data;
  } catch (error) {
    console.error('Error fetching scan logs:', error);
    throw error;
  }
};

/**
 * Starts a new scan
 */
export const startScan = async (scanConfig: {
  scanType: 'full' | 'incremental' | 'targeted';
  targets?: string[];
  scanDepth?: number;
}): Promise<{ success: boolean; message: string; scanId?: string }> => {
  try {
    const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.START_SCAN, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(scanConfig)
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to start scan');
    }

    return {
      success: true,
      message: response.message || 'Scan started successfully',
      scanId: response.scanId
    };
  } catch (error) {
    console.error('Error starting scan:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to start scan'
    };
  }
};

/**
 * Pauses the current scan
 */
export const pauseScan = async (scanId: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.SCAN_CONTROL}/${scanId}/pause`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to pause scan');
    }

    return {
      success: true,
      message: response.message || 'Scan paused successfully'
    };
  } catch (error) {
    console.error('Error pausing scan:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to pause scan'
    };
  }
};

/**
 * Resumes a paused scan
 */
export const resumeScan = async (scanId: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.SCAN_CONTROL}/${scanId}/resume`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to resume scan');
    }

    return {
      success: true,
      message: response.message || 'Scan resumed successfully'
    };
  } catch (error) {
    console.error('Error resuming scan:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to resume scan'
    };
  }
};

/**
 * Stops the current scan
 */
export const stopScan = async (scanId: string): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.SCAN_CONTROL}/${scanId}/stop`, {
      method: 'POST',
      headers: getAuthHeaders()
    });

    if (!response?.success) {
      throw new Error(response?.message || 'Failed to stop scan');
    }

    return {
      success: true,
      message: response.message || 'Scan stopped successfully'
    };
  } catch (error) {
    console.error('Error stopping scan:', error);
    return {
      success: false,
      message: error instanceof Error ? error.message : 'Failed to stop scan'
    };
  }
};

export default {
  fetchScanProgress,
  fetchScanLogs,
  startScan,
  pauseScan,
  resumeScan,
  stopScan
};
