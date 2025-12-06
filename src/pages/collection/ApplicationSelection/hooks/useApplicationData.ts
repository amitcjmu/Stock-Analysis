/**
 * useApplicationData Hook
 * Handles data fetching for applications with infinite scroll support
 *
 * CRITICAL: Preserves multi-tenant scoping (client_account_id + engagement_id)
 */

import { useCallback, useMemo } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { apiCall } from "@/config/api";
import type { Asset } from "@/types/asset";
import type { AssetPageData, AssetsByType, FilterOptions } from "../types";
import { ASSET_TYPE_NORMALIZATION } from "../types";
import type { CollectionFlowResponse } from "@/services/api/collection-flow";

interface UseApplicationDataProps {
  flowId: string | null;
  client: { id: number } | null;
  engagement: { id: number } | null;
  searchTerm: string;
  environmentFilter: string;
  criticalityFilter: string;
}

interface UseApplicationDataReturn {
  // Data
  allAssets: Asset[];
  assetsByType: AssetsByType;
  filterOptions: FilterOptions;
  summary: {
    applications: number;
    servers: number;
    databases: number;
    components: number;
    network: number;
    storage: number;
    security: number;
    virtualization: number;
    unknown: number;
  } | null;

  // Loading states
  applicationsLoading: boolean;
  flowLoading: boolean;
  isFetchingNextPage: boolean;

  // Pagination
  hasNextPage: boolean;
  fetchNextPage: () => void;

  // Error handling
  applicationsError: Error | null;

  // Actions
  refetchApplications: () => void;

  // Collection flow data
  collectionFlow: CollectionFlowResponse | null;
}

/**
 * Hook for managing application data fetching with infinite scroll
 */
export const useApplicationData = ({
  flowId,
  client,
  engagement,
  searchTerm,
  environmentFilter,
  criticalityFilter,
}: UseApplicationDataProps): UseApplicationDataReturn => {

  // Build query parameters for API calls including filters
  const buildQueryParams = useCallback(
    (page: number) => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "50", // Optimal page size for smooth scrolling
      });

      // CRITICAL FIX: Add client_account_id and engagement_id for multi-tenant scoping
      // Without these, the query returns 0 assets even if inventory exists
      // Per Qodo review: Enforce presence with explicit error instead of conditional append
      if (!client?.id || !engagement?.id) {
        throw new Error(
          "Missing required tenant context: client_account_id and engagement_id are required for asset queries"
        );
      }
      params.append("client_account_id", client.id.toString());
      params.append("engagement_id", engagement.id.toString());

      // Add client-side filters to server request for proper pagination
      if (searchTerm.trim()) {
        params.append("search", searchTerm.trim());
      }
      if (environmentFilter) {
        params.append("environment", environmentFilter);
      }
      if (criticalityFilter) {
        params.append("business_criticality", criticalityFilter);
      }

      return params.toString();
    },
    [searchTerm, environmentFilter, criticalityFilter, client, engagement],
  );

  // Fetch applications with infinite scroll support
  const {
    data: applicationsData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: applicationsLoading,
    error: applicationsError,
    refetch: refetchApplications,
  } = useInfiniteQuery({
    queryKey: [
      "applications-for-collection",
      client?.id,
      engagement?.id,
      searchTerm,
      environmentFilter,
      criticalityFilter,
    ],
    queryFn: async ({ pageParam = 1 }) => {
      try {
        const queryParams = buildQueryParams(pageParam);
        const response = await apiCall(
          `/asset-inventory/list/paginated?${queryParams}`,
        );

        if (!response || !response.assets) {
          throw new Error("Invalid API response structure");
        }

        console.log(
          `📋 Fetched page ${pageParam}: ${response.assets.length} applications (total: ${response.pagination?.total_count || "unknown"})`,
        );

        return {
          assets: response.assets,
          pagination: response.pagination,
          currentPage: pageParam,
          summary: response.summary,
        } as AssetPageData;
      } catch (error) {
        console.error("❌ Failed to fetch applications:", error);
        throw error;
      }
    },
    getNextPageParam: (lastPage) => {
      const { pagination } = lastPage;
      return pagination?.has_next ? pagination.current_page + 1 : undefined;
    },
    enabled: !!client && !!engagement && !!flowId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Flatten all pages into a single array of assets
  const allAssets = useMemo(
    () => applicationsData?.pages?.flatMap((page) => page.assets) || [],
    [applicationsData]
  );

  // Bug #971 Fix: Group assets by type with counts using normalization map
  const assetsByType = useMemo((): AssetsByType => {
    const grouped: AssetsByType = {
      ALL: allAssets,
      APPLICATION: [],
      SERVER: [],
      DATABASE: [],
      NETWORK: [],  // Bug #971 Fix: Consolidated network types
      STORAGE_DEVICE: [],
      SECURITY_DEVICE: [],
      VIRTUALIZATION: [],
      UNKNOWN: [],
    };

    allAssets.forEach((asset) => {
      const rawType = asset.asset_type?.toUpperCase() || "UNKNOWN";
      // Bug #971 Fix: Normalize asset type using the mapping, fallback to raw type
      const normalizedType = ASSET_TYPE_NORMALIZATION[rawType] || rawType;

      if (normalizedType in grouped && normalizedType !== "ALL") {
        const assetArray = grouped[normalizedType as keyof AssetsByType];
        assetArray.push(asset);
      } else if (normalizedType !== "ALL") {
        grouped.UNKNOWN.push(asset);
      }
    });

    return grouped;
  }, [allAssets]);

  // Get unique filter options from all loaded assets
  const filterOptions = useMemo((): FilterOptions => {
    const environmentOptions = [
      ...new Set(allAssets.map((app) => app.environment).filter(Boolean)),
    ] as string[];

    const criticalityOptions = [
      ...new Set(
        allAssets.map((app) => app.business_criticality).filter(Boolean),
      ),
    ] as string[];

    return {
      environmentOptions,
      criticalityOptions,
    };
  }, [allAssets]);

  // Extract summary from first page (contains counts for ALL assets)
  const summary = useMemo(() => {
    const firstPageSummary = applicationsData?.pages?.[0]?.summary;
    if (!firstPageSummary) return null;
    return {
      applications: firstPageSummary.applications || 0,
      servers: firstPageSummary.servers || 0,
      databases: firstPageSummary.databases || 0,
      components: firstPageSummary.components || 0,
      network: firstPageSummary.network || 0,
      storage: firstPageSummary.storage || 0,
      security: firstPageSummary.security || 0,
      virtualization: firstPageSummary.virtualization || 0,
      unknown: firstPageSummary.unknown || 0,
    };
  }, [applicationsData]);

  // Fetch current collection flow details to check existing selections
  const { data: collectionFlow, isLoading: flowLoading } = useQuery({
    queryKey: ["collection-flow", flowId],
    queryFn: async () => {
      if (!flowId) return null;
      try {
        return await apiCall(`/collection/flows/${flowId}`);
      } catch (error) {
        console.error("Failed to fetch collection flow:", error);
        return null;
      }
    },
    enabled: !!flowId,
  });

    return {
      allAssets,
      assetsByType,
      filterOptions,
      summary,
      applicationsLoading,
    flowLoading,
    isFetchingNextPage,
    hasNextPage: hasNextPage || false,
    fetchNextPage,
    applicationsError: applicationsError instanceof Error ? applicationsError : null,
    refetchApplications,
    collectionFlow: collectionFlow ?? null,
  };
};
