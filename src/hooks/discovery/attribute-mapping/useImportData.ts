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

  // Validate that finalFlowId is a proper UUID format (not an import ID)
  const isValidFlowId = finalFlowId ? /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(finalFlowId) : false;

  // Get flow-specific import data if we have a valid flow ID
  const {
    data: flowImportData,
    isLoading: isFlowImportLoading,
    error: flowImportError,
    refetch: refetchFlowImportData
  } = useQuery({
    queryKey: ['flow-import-data', finalFlowId, user?.id],
    queryFn: async () => {
      if (!finalFlowId || !isValidFlowId) {
        console.log('⚠️ Invalid or missing flow ID for import data:', finalFlowId);
        return null; // No valid flow ID, will use latest import fallback
      }

      console.log('🔍 Fetching import data for flow:', finalFlowId);
      try {
        // Use the unified flow status endpoint to get import data
        const flowResponse = await apiCall(`/api/v1/flows/${finalFlowId}/status`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        });

        if (flowResponse) {
          // Extract import data from flow status response
          // Note: Backend returns data_import_id, but frontend expects import_id
          const importMetadata = flowResponse.import_metadata || {};
          if (importMetadata.data_import_id && !importMetadata.import_id) {
            importMetadata.import_id = importMetadata.data_import_id;
          }

          // FALLBACK: Extract import ID from flow name if not in metadata
          // Flow names follow pattern: "Discovery Import {import_id}"
          if (!importMetadata.import_id && flowResponse.flow_name) {
            const flowNameMatch = flowResponse.flow_name.match(/Discovery Import (.+)$/);
            if (flowNameMatch && flowNameMatch[1]) {
              const extractedImportId = flowNameMatch[1].trim();
              console.log('🔧 Extracted import ID from flow name:', {
                flow_name: flowResponse.flow_name,
                extracted_import_id: extractedImportId
              });
              importMetadata.import_id = extractedImportId;
            }
          }

          const importData = {
            import_metadata: importMetadata,
            raw_data: flowResponse.raw_data?.[0] || {},
            sample_record: flowResponse.raw_data?.[0] || {},
            record_count: flowResponse.raw_data?.length || 0,
            field_count: flowResponse.raw_data?.[0] ? Object.keys(flowResponse.raw_data[0]).length : 0,
            field_mappings: flowResponse.field_mappings || []
          };

          console.log('✅ Extracted import data from flow status:', importData);
          return importData;
        }
      } catch (error) {
        console.error('❌ Error fetching flow status for import data:', error);
        // Fall through to use latest import data from unified hook
      }

      return null; // Will fall back to latest import
    },
    enabled: !!(finalFlowId && isValidFlowId && user?.id),
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
