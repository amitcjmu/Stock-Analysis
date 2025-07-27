import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';
import { useLatestImport } from '../../api/useLatestImport';

export interface ImportDataResult {
  importData: unknown;
  isImportDataLoading: boolean;
  importDataError: unknown;
  refetchImportData: () => Promise<unknown>;
}

/**
 * Hook for import data fetching and management
 * Handles both flow-specific and latest import data with fallback mechanisms
 * Now uses unified caching to prevent duplicate API calls
 */
export const useImportData = (finalFlowId: string | null): ImportDataResult => {
  const { user, getAuthHeaders } = useAuth();

  // Use the unified latest import hook for fallback data (prevents duplicate calls)
  const { data: latestImportData, isLoading: isLatestImportLoading } = useLatestImport(!!user?.id);

  // Get flow-specific import data if we have a flow ID
  const {
    data: flowImportData,
    isLoading: isFlowImportLoading,
    error: flowImportError,
    refetch: refetchFlowImportData
  } = useQuery({
    queryKey: ['flow-import-data', finalFlowId, user?.id],
    queryFn: async () => {
      if (!finalFlowId) {
        return null; // No flow ID, will use latest import fallback
      }

      console.log('🔍 Fetching import data for flow:', finalFlowId);
      try {
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
      } catch (error) {
        console.error('❌ Error fetching flow-specific import data:', error);
        // Fall through to use latest import data from unified hook
      }

      return null; // Will fall back to latest import
    },
    enabled: !!(finalFlowId && user?.id),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    cacheTime: 15 * 60 * 1000, // Keep in cache for 15 minutes
    retry: (failureCount, error) => {
      // Don't retry on 429 or auth errors
      const err = error as { status?: number };
      if (err?.status === 429 || err?.status === 401 || err?.status === 403) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 5000),
  });

  // Determine which data to use: flow-specific first, then latest import fallback
  const importData = flowImportData || latestImportData;
  const isImportDataLoading = isFlowImportLoading || isLatestImportLoading;
  const importDataError = flowImportError;

  // Combined refetch function
  const refetchImportData = async (): Promise<PromiseSettledResult<unknown>> => {
    const results = await Promise.allSettled([
      refetchFlowImportData(),
      // Note: Latest import refetch is handled by the useLatestImport hook automatically
    ]);
    return results[0]; // Return flow data refetch result
  };

  return {
    importData,
    isImportDataLoading,
    importDataError,
    refetchImportData
  };
};
