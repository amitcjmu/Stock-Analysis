import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';

export interface ImportDataResult {
  importData: any;
  isImportDataLoading: boolean;
  importDataError: any;
  refetchImportData: () => Promise<any>;
}

/**
 * Hook for import data fetching and management
 * Handles both flow-specific and latest import data with fallback mechanisms
 */
export const useImportData = (finalFlowId: string | null): ImportDataResult => {
  const { user, getAuthHeaders } = useAuth();

  // Get import data for this flow, with fallback to latest import
  const { 
    data: importData, 
    isLoading: isImportDataLoading, 
    error: importDataError,
    refetch: refetchImportData
  } = useQuery({
    queryKey: ['import-data', finalFlowId, user?.id],
    queryFn: async () => {
      try {
        // If we have a final flow ID, try flow-specific import data first
        if (finalFlowId) {
          console.log('🔍 Fetching import data for flow:', finalFlowId);
          console.log('🔗 Trying flow-specific import data endpoint...');
          const flowResponse = await apiCall(`/api/v1/data-import/flow/${finalFlowId}/import-data`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            }
          });
          
          if (flowResponse) {
            console.log('✅ Fetched flow-specific import data:', flowResponse);
            return flowResponse;
          }
          
          console.log('🔗 Flow-specific import not found, falling back to latest import...');
        } else {
          console.log('⚠️ No final flow ID, attempting to fetch latest import data as fallback');
        }
        
        // Fall back to latest import for client (works both with and without flow ID)
        console.log('🔗 Trying latest import endpoint...');
        const latestResponse = await apiCall(`/api/v1/data-import/latest-import`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        });
        
        if (latestResponse) {
          console.log('✅ Using latest import data as fallback:', latestResponse);
          return latestResponse;
        }
        
        console.log('❌ No import data found');
        return null;
        
      } catch (error) {
        console.error('❌ Error fetching import data:', error);
        // Return null instead of throwing to prevent breaking the entire component
        return null;
      }
    },
    enabled: !!user?.id, // Enable as long as user is authenticated, fallback logic handles missing flow ID
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes to reduce API calls
    cacheTime: 15 * 60 * 1000, // Keep in cache for 15 minutes
    retry: (failureCount, error) => {
      // Don't retry on 429 (Too Many Requests) or authentication errors
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as any).status;
        if (status === 429 || status === 401 || status === 403) {
          return false;
        }
      }
      return failureCount < 2; // Only retry twice max
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff, max 10s
  });

  return {
    importData,
    isImportDataLoading,
    importDataError,
    refetchImportData
  };
};