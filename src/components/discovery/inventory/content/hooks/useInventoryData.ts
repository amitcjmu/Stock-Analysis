import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { Asset } from '../../../../../types/asset';

interface UseInventoryDataProps {
  clientId?: number;
  engagementId?: number;
  viewMode: 'all' | 'current_flow';
  flowId?: string;
  setNeedsClassification: (value: boolean) => void;
  setHasTriggeredInventory: (value: boolean) => void;
  getAssetsFromFlow: () => Asset[];
}

interface AssetApiResponse {
  data_source?: string;
  assets?: Asset[];
  data?: Asset[];
  pagination?: {
    pageSize?: number;
    page_size?: number;
    totalPages?: number;
    total_pages?: number;
  };
  needs_classification?: boolean;
  needsClassification?: boolean;
}

export const useInventoryData = ({
  clientId,
  engagementId,
  viewMode,
  flowId,
  setNeedsClassification,
  setHasTriggeredInventory,
  getAssetsFromFlow
}: UseInventoryDataProps): {
  assets: Asset[];
  assetsLoading: boolean;
  refetchAssets: () => void;
  hasBackendError: boolean;
  isFlowNotFound: boolean;
  error: Error | null;
} => {
  // Get assets data - fetch from API endpoint that returns assets based on view mode
  // Updated to support both "All Assets" and "Current Flow Only" modes
  const { data: assetsData, isLoading: assetsLoading, error: assetsError, refetch: refetchAssets } = useQuery({
    queryKey: ['discovery-assets', String(clientId ?? ''), String(engagementId ?? ''), viewMode, flowId || 'no-flow'],
    queryFn: async () => {
      try {
        // Import API call function with proper headers
        const { apiCall } = await import('../../../../../config/api');

        // Helper function to fetch a single page
        const fetchPage = async (page: number, pageSize: number = 100) => {
          const queryParams = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString()
          });

          // Only include flow_id when in current_flow mode and flowId is available
          // FIX: Don't throw error if no flowId - just fetch all assets from database
          const normalizedFlowId = flowId && flowId !== 'no-flow' ? String(flowId) : '';

          // Security: Validate flow ID to prevent injection attacks
          const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
          if (viewMode === 'current_flow' && normalizedFlowId) {
            if (uuidRegex.test(normalizedFlowId)) {
              queryParams.append('flow_id', normalizedFlowId);
              console.log(`🔍 API call will include flow_id: ${normalizedFlowId}`);
            } else {
              console.warn(`⚠️ Invalid flow ID format, skipping: ${normalizedFlowId}`);
              // Don't include invalid flow_id in request - fetch all assets instead
            }
          } else if (viewMode === 'current_flow') {
            console.log(`📊 current_flow mode but no flowId - fetching all assets from database`);
            // Don't throw error - inventory should load assets from DB regardless of flow state
          }

          const response = await apiCall(`/unified-discovery/assets?${queryParams.toString()}`);

          // Validate response status
          if (!response || (typeof response.status === 'number' && response.status >= 400)) {
            throw new Error(`Assets API error${response?.status ? ` (status ${response.status})` : ''}`);
          }

          // Validate response shape
          if (!response || typeof response !== 'object') {
            throw new Error('Invalid assets response shape');
          }

          return response;
        };

        // Helper function to handle both structured and legacy response formats
        const parseResponse = (response: AssetApiResponse | Asset[]) => {
          // Check if this is an array (legacy format)
          if (Array.isArray(response)) {
            return {
              assets: response,
              pagination: null,
              needsClassification: false,
              isError: false
            };
          }

          // Check if the response indicates an error
          if (response && 'data_source' in response && response.data_source === 'error') {
            console.warn('⚠️ Assets API returned error state. Backend may have failed to fetch assets.');
            return {
              assets: [],
              pagination: null,
              needsClassification: false,
              isError: true
            };
          }

          // Handle structured response format (with data/pagination)
          if (response.data && Array.isArray(response.data)) {
            return {
              assets: response.data,
              pagination: response.pagination || null,
              needsClassification: response.needs_classification || false,
              isError: false
            };
          }

          // Handle legacy flat array format
          if (Array.isArray(response.assets)) {
            return {
              assets: response.assets,
              pagination: response.pagination || null,
              needsClassification: response.needs_classification || false,
              isError: false
            };
          }

          // Handle direct array response (legacy)
          if (Array.isArray(response)) {
            return {
              assets: response,
              pagination: null,
              needsClassification: false,
              isError: false
            };
          }

          // No valid data found
          return {
            assets: [],
            pagination: null,
            needsClassification: false,
            isError: false
          };
        };

        // Fetch first page to understand pagination structure
        const firstPageResponse = await fetchPage(1);
        const firstPageData = parseResponse(firstPageResponse);

        console.log('📊 First page response:', firstPageResponse);
        console.log('📊 Parsed first page data:', firstPageData);

        // If error response, return early
        if (firstPageData.isError) {
          return [];
        }

        // Update classification state based on first page
        setNeedsClassification(firstPageData.needsClassification);

        // If assets are properly classified, mark as triggered to prevent auto-execution loops
        if (!firstPageData.needsClassification && firstPageData.assets && firstPageData.assets.length > 0) {
          setHasTriggeredInventory(true);
        }

        // If no pagination metadata, return first page only
        if (!firstPageData.pagination) {
          console.log(`📊 Using single page (no pagination):`, firstPageData.assets.length);
          return firstPageData.assets;
        }

        // For 'all' mode with pagination, fetch all pages iteratively
        const pagination = firstPageData.pagination;
        let allAssets = [...firstPageData.assets];

        // Respect server-imposed page size and total pages
        const serverPageSize = pagination.pageSize || pagination.page_size || 100;
        const totalPages = pagination.totalPages || pagination.total_pages || 1;
        const safetyLimit = Math.min(totalPages, 50); // Safety limit: max 50 pages

        console.log(`📊 Pagination info - Total pages: ${totalPages}, Server page size: ${serverPageSize}, Safety limit: ${safetyLimit}`);

        // Fetch remaining pages if we have more pages
        // Both 'all' and 'current_flow' modes should support pagination
        if (totalPages > 1) {
          console.log(`📊 Fetching remaining ${Math.min(totalPages - 1, safetyLimit - 1)} pages...`);

          const pagePromises: Array<Promise<AssetApiResponse | Asset[]>> = [];
          for (let page = 2; page <= safetyLimit; page++) {
            pagePromises.push(fetchPage(page, serverPageSize));
          }

          try {
            // Fetch all remaining pages in parallel
            const remainingResponses = await Promise.all(pagePromises);

            // Process each response and combine assets
            for (const response of remainingResponses) {
              const pageData = parseResponse(response);
              if (!pageData.isError && pageData.assets.length > 0) {
                allAssets = allAssets.concat(pageData.assets);
              }
            }

            console.log(`📊 Combined assets from ${safetyLimit} pages: ${allAssets.length} total`);
          } catch (error) {
            console.warn('⚠️ Failed to fetch some pages, proceeding with partial data:', error);
            // Continue with whatever assets we have
          }
        }

        console.log('📊 Assets from API (final):', allAssets.length);
        console.log('📊 Assets need classification:', firstPageData.needsClassification);

        return allAssets;

      } catch (error) {
        console.error('Error fetching assets:', error);

        // FIX #326: Normalize error shape across different API clients (fetch/axios/custom)
        // Check multiple common locations for HTTP status code
        const anyErr = error;
        const status =
          anyErr?.response?.status ?? // Axios format
          anyErr?.status ?? // Custom/fetch format
          (typeof anyErr?.code === 'string' && anyErr.code.startsWith('4')
            ? Number(anyErr.code)
            : undefined);

        if (status === 404) {
          console.error('❌ 404 Error: Flow not found or invalid flow_id');
          throw new Error('FLOW_NOT_FOUND');
        }

        // Fallback to flow assets if API fails completely
        const flowAssets = getAssetsFromFlow();
        console.log('📊 Using flow assets as fallback:', flowAssets.length);
        return flowAssets;
      }
    },
    // FIX: Enable query when we have client/engagement regardless of flowId
    // Inventory should load assets from database even without a discovery flow
    // The API will filter by flow_id only if provided in current_flow mode
    enabled: !!clientId && !!engagementId,
    // Invalidate when view mode or flowId changes
    refetchOnWindowFocus: false,
    staleTime: 30000
  });

  const assets: Asset[] = useMemo(() => {
    if (!assetsData) return [];
    if (Array.isArray(assetsData)) return assetsData;
    if (assetsData && Array.isArray((assetsData as { assets?: Asset[] }).assets)) {
      return (assetsData as { assets: Asset[] }).assets;
    }
    return [];
  }, [assetsData]);

  // Check if we have a backend error
  const hasBackendError = assetsData === null || (assetsData && (assetsData as AssetApiResponse).data_source === 'error');

  // FIX #326: Check if this is a flow not found error (404)
  const isFlowNotFound = assetsError?.message === 'FLOW_NOT_FOUND';

  return {
    assets,
    assetsLoading,
    refetchAssets,
    hasBackendError,
    isFlowNotFound,
    error: assetsError
  };
};
