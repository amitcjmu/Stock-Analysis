import React from 'react'
import { useState, useRef } from 'react'
import { useMemo, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useAuth } from '../../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../../hooks/useUnifiedDiscoveryFlow';
import type { Asset } from '../../../types/asset';

// Components
import { InventoryOverview } from './components/InventoryOverview';
import { ClassificationProgress } from './components/ClassificationProgress';
import { ClassificationCards } from './components/ClassificationCards';
import { AssetTable } from './components/AssetTable';
import { NextStepCard } from './components/NextStepCard';
import EnhancedInventoryInsights from './EnhancedInventoryInsights';
import { InventoryContentFallback } from './InventoryContentFallback';
import { ApplicationSelectionModal } from './components/ApplicationSelectionModal';

// Hooks
import { useInventoryProgress } from './hooks/useInventoryProgress';
import { useAssetFilters } from './hooks/useAssetFilters';
import { useAssetSelection } from './hooks/useAssetSelection';

// Utils
import { exportAssets } from './utils/exportHelpers';

// Types
import type { InventoryContentProps } from './types/inventory.types'
import type { AssetInventory } from './types/inventory.types'

const DEFAULT_COLUMNS = [
  'asset_name', 'asset_type', 'environment', 'operating_system',
  'location', 'status', 'business_criticality', 'risk_score',
  'migration_readiness', 'dependencies', 'last_updated'
];

const RECORDS_PER_PAGE = 10;

const InventoryContent: React.FC<InventoryContentProps> = ({
  className = "",
  flowId
}) => {
  const { client, engagement } = useAuth();
  const { flowState: flow, getPhaseData, executeFlowPhase, isExecutingPhase, refreshFlow } = useUnifiedDiscoveryFlow(flowId);

  // Debug logging
  console.log('🔍 InventoryContent flow state:', {
    flowId,
    currentPhase: flow?.current_phase,
    hasAssetInventory: !!flow?.asset_inventory,
    assetCount: flow?.asset_inventory?.assets?.length || 0,
    rawDataCount: flow?.raw_data?.length || 0,
    phaseCompletion: flow?.phase_completion
  });

  // Get assets from flow if available, but this should not be the only source
  const getAssetsFromFlow = () => flow?.asset_inventory?.assets || [];
  const getFlow = () => flow;

  // State
  const [selectedColumns, setSelectedColumns] = useState(DEFAULT_COLUMNS);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasTriggeredInventory, setHasTriggeredInventory] = useState(false);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [showCleansingRequiredBanner, setShowCleansingRequiredBanner] = useState(false);
  const attemptCountRef = useRef(0);
  const maxRetryAttempts = 3;
  const [needsClassification, setNeedsClassification] = useState(false);
  const [isReclassifying, setIsReclassifying] = useState(false);
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [viewMode, setViewMode] = useState<'all' | 'current_flow'>(!flowId ? 'all' : 'current_flow');
  const [hasFlowId, setHasFlowId] = useState<boolean>(Boolean(flowId));

  // Update hasFlowId state to prevent SSR hydration mismatch
  React.useEffect(() => {
    setHasFlowId(Boolean(flowId));
  }, [flowId]);

  // Safety: auto-revert to 'all' if flowId disappears while in 'current_flow'
  React.useEffect(() => {
    let mounted = true;
    if (!flowId && mounted) {
      setViewMode((prev) => (prev === 'current_flow' ? 'all' : prev));
    }
    return () => {
      mounted = false;
    };
  }, [flowId]);

  // Check for collectionFlowId parameter to auto-show application selection modal
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const collectionFlowId = urlParams.get('collectionFlowId');

    if (collectionFlowId) {
      console.log('🔗 Collection flow requires application selection:', collectionFlowId);
      setShowApplicationModal(true);
    }
  }, []);

  // Get assets data - fetch from API endpoint that returns assets based on view mode
  // Updated to support both "All Assets" and "Current Flow Only" modes
  const { data: assetsData, isLoading: assetsLoading, refetch: refetchAssets } = useQuery({
    queryKey: ['discovery-assets', String(client?.id ?? ''), String(engagement?.id ?? ''), viewMode, flowId || 'no-flow'],
    queryFn: async () => {
      try {
        // Import API call function with proper headers
        const { apiCall } = await import('../../../config/api');

        // Helper function to fetch a single page
        const fetchPage = async (page: number, pageSize: number = 100) => {
          const queryParams = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString()
          });

          // Only include flow_id when in current_flow mode and flowId is available
          const normalizedFlowId = flowId && flowId !== 'no-flow' ? String(flowId) : '';
          if (viewMode === 'current_flow' && normalizedFlowId) {
            queryParams.append('flow_id', normalizedFlowId);
            console.log(`🔍 API call will include flow_id: ${normalizedFlowId}`);
          } else if (viewMode === 'current_flow') {
            console.warn(`⚠️ current_flow mode but no valid flowId available: ${flowId}`);
            throw new Error('Flow ID is required for current_flow mode but is not available');
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

        // Define response type for better type safety
        interface AssetApiResponse {
          data_source?: string;
          assets?: Asset[];
          pagination?: unknown;
          needsClassification?: boolean;
        }

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

        // If no pagination metadata or in 'current_flow' mode, return first page only
        if (!firstPageData.pagination || viewMode === 'current_flow') {
          console.log(`📊 Using single page (${viewMode === 'current_flow' ? 'current_flow mode' : 'no pagination'}):`, firstPageData.assets.length);

          // Transform and return first page assets
          return firstPageData.assets.map((asset: Asset) => ({
            id: asset.id,
            asset_name: asset.name,
            asset_type: asset.asset_type,
            environment: asset.environment,
            criticality: asset.business_criticality,
            status: 'discovered',
            six_r_strategy: asset.six_r_strategy,
            migration_wave: asset.migration_wave,
            application_name: asset.name,
            hostname: asset.hostname,
            operating_system: asset.operating_system,
            cpu_cores: asset.cpu_cores,
            memory_gb: asset.memory_gb,
            storage_gb: asset.storage_gb,
            business_criticality: asset.business_criticality,
            risk_score: 0,
            migration_readiness: asset.sixr_ready ? 'ready' : 'pending',
            dependencies: 0,
            last_updated: asset.updated_at || asset.created_at
          }));
        }

        // For 'all' mode with pagination, fetch all pages iteratively
        const pagination = firstPageData.pagination;
        let allAssets = [...firstPageData.assets];

        // Respect server-imposed page size and total pages
        const serverPageSize = pagination.pageSize || pagination.page_size || 100;
        const totalPages = pagination.totalPages || pagination.total_pages || 1;
        const safetyLimit = Math.min(totalPages, 50); // Safety limit: max 50 pages

        console.log(`📊 Pagination info - Total pages: ${totalPages}, Server page size: ${serverPageSize}, Safety limit: ${safetyLimit}`);

        // Fetch remaining pages if we're in 'all' mode and have more pages
        if (viewMode === 'all' && totalPages > 1) {
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

        // Transform all assets to match expected format
        return allAssets.map((asset: Asset) => ({
          id: asset.id,
          asset_name: asset.name,
          asset_type: asset.asset_type,
          environment: asset.environment,
          criticality: asset.business_criticality,
          status: 'discovered',
          six_r_strategy: asset.six_r_strategy,
          migration_wave: asset.migration_wave,
          application_name: asset.name,
          hostname: asset.hostname,
          operating_system: asset.operating_system,
          cpu_cores: asset.cpu_cores,
          memory_gb: asset.memory_gb,
          storage_gb: asset.storage_gb,
          business_criticality: asset.business_criticality,
          risk_score: 0,
          migration_readiness: asset.sixr_ready ? 'ready' : 'pending',
          dependencies: 0,
          last_updated: asset.updated_at || asset.created_at
        }));

      } catch (error) {
        console.error('Error fetching assets:', error);

        // Fallback to flow assets if API fails completely
        const flowAssets = getAssetsFromFlow();
        console.log('📊 Using flow assets as fallback:', flowAssets.length);
        return flowAssets;
      }
    },
    // Enable query when we have client/engagement, and either in 'all' mode or have flowId for 'current_flow'
    // For current_flow mode, we must have a valid flowId before making the API call
    enabled: !!client && !!engagement && (viewMode === 'all' || (viewMode === 'current_flow' && !!flowId && flowId !== 'no-flow')),
    // Invalidate when view mode or flowId changes
    refetchOnWindowFocus: false,
    staleTime: 30000
  });

  const assets: AssetInventory[] = useMemo(() => {
    if (!assetsData) return [];
    if (Array.isArray(assetsData)) return assetsData;
    if (assetsData && Array.isArray(assetsData.assets)) return assetsData.assets;
    return [];
  }, [assetsData]);

  // Check if we have a backend error
  const hasBackendError = assetsData === null || (assetsData && assetsData.data_source === 'error');

  // Get all available columns
  const allColumns = useMemo(() => {
    if (assets.length === 0) return [];
    const columns = new Set<string>();
    assets.forEach(asset => {
      Object.keys(asset).forEach(key => {
        if (key !== 'id') columns.add(key);
      });
    });
    return Array.from(columns).sort();
  }, [assets]);

  // Hooks
  const inventoryProgress = useInventoryProgress(assets);
  const {
    filters,
    updateFilter,
    resetFilters,
    filteredAssets,
    uniqueEnvironments,
    uniqueAssetTypes
  } = useAssetFilters(assets);
  const {
    selectedAssets,
    handleSelectAsset,
    handleSelectAll,
    clearSelection
  } = useAssetSelection();

  // Handlers
  const handleClassificationCardClick = (assetType: string): void => {
    updateFilter('selectedAssetType', assetType);
    setCurrentPage(1);
  };

  const toggleColumn = (column: string): unknown => {
    setSelectedColumns(prev =>
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const handleExportAssets = (): void => {
    exportAssets(filteredAssets, selectedColumns);
  };

  // Enhanced refresh function that triggers CrewAI classification with error handling
  const handleRefreshClassification = async (): void => {
    try {
      console.log('🔄 Refreshing asset classification with CrewAI...');

      // Clear any previous errors
      setExecutionError(null);
      setShowCleansingRequiredBanner(false);

      // Reset the trigger state to allow fresh execution
      setHasTriggeredInventory(false);
      attemptCountRef.current = 0; // Reset retry counter

      // Re-execute the asset inventory phase to trigger CrewAI classification
      await executeFlowPhase('asset_inventory', {
        trigger: 'manual_refresh',
        source: 'inventory_classification_refresh'
      });

      console.log('✅ Asset inventory phase re-executed');

      // Set the trigger state to true after execution
      setHasTriggeredInventory(true);

      // Refetch assets after phase execution (no fixed delay for agentic activities)
      setTimeout(() => {
        refetchAssets();
        refreshFlow();
      }, 1000);

    } catch (error) {
      console.error('❌ Failed to refresh asset classification:', error);

      // Handle 422 CLEANSING_REQUIRED error
      let errorCode = null;
      try {
        if (error?.response?.data?.error_code) {
          errorCode = error.response.data.error_code;
        } else if (error?.message && error.message.includes('422')) {
          errorCode = 'CLEANSING_REQUIRED';
        }
      } catch (parseError) {
        console.warn('Could not parse error response:', parseError);
      }

      if (errorCode === 'CLEANSING_REQUIRED') {
        setExecutionError('Data cleansing must be completed before refreshing asset classification.');
        setShowCleansingRequiredBanner(true);
        // Keep hasTriggeredInventory as true to prevent auto-retry
      } else {
        // For other errors, reset to allow retry
        setHasTriggeredInventory(false);
        setExecutionError(`Refresh failed: ${error.message}`);
        // Fallback to just refetching assets
        refetchAssets();
      }
    }
  };

  // Process selected applications for assessment
  const handleProcessForAssessment = (): void => {
    setShowApplicationModal(true);
  };

  // Get selected application IDs
  const selectedApplicationIds = useMemo(() => {
    return filteredAssets
      .filter(asset => selectedAssets.includes(asset.id) && asset.asset_type === 'Application')
      .map(asset => asset.id);
  }, [selectedAssets, filteredAssets]);

  // Check if any selected assets are applications
  const isApplicationsSelected = selectedApplicationIds.length > 0;

  // Reclassify selected assets function
  const handleReclassifySelected = async (): void => {
    if (selectedAssets.length === 0) {
      console.warn('No assets selected for reclassification');
      return;
    }

    setIsReclassifying(true);

    try {
      console.log(`🔄 Reclassifying ${selectedAssets.length} selected assets...`);

      // Import API call function
      const { apiCall } = await import('../../../config/api');

      const response = await apiCall('/assets/auto-classify', {
        method: 'POST',
        body: JSON.stringify({
          asset_ids: selectedAssets,
          use_learned_patterns: true,
          confidence_threshold: 0.8,
          classification_context: "user_initiated_reclassification"
        })
      });

      console.log('✅ Reclassification completed:', response);

      // Refresh assets after reclassification
      setTimeout(() => {
        refetchAssets();
        refreshFlow();
        clearSelection(); // Clear selection after successful reclassification
      }, 1000);

    } catch (error) {
      console.error('❌ Failed to reclassify selected assets:', error);
    } finally {
      setIsReclassifying(false);
    }
  };

  // Auto-execute asset inventory phase if conditions are met with proper gating and error handling
  useEffect(() => {
    // Use setTimeout to delay execution until after page render
    const timeoutId = setTimeout(() => {
      // CRITICAL CONDITIONS: All must be true for auto-execution
      const hasRawData = flow && flow.raw_data && flow.raw_data.length > 0;
      const hasNoAssets = assets.length === 0;
      // FIX #447: Backend returns phases_completed as array, not phase_completion object
      // Support both data formats for backward compatibility
      const dataCleansingCompleted =
        flow?.phases_completed?.includes('data_cleansing') ||
        flow?.phase_completion?.data_cleansing === true;
      // FIX #447 Priority 3: Filter out deleted flows
      const flowNotDeleted = flow?.status !== 'deleted';
      const notExecuting = !isExecutingPhase;
      const notTriggered = !hasTriggeredInventory;
      const withinRetryLimit = attemptCountRef.current < maxRetryAttempts;

      // Clear any previous execution errors when conditions change
      if (hasRawData && hasNoAssets && dataCleansingCompleted && !executionError) {
        setExecutionError(null);
        setShowCleansingRequiredBanner(false);
      }

      // Log the conditions for debugging
      console.log('🔍 Auto-execute conditions (gated):', {
        hasRawData,
        rawDataCount: flow?.raw_data?.length || 0,
        hasNoAssets,
        dataCleansingCompleted,
        flowNotDeleted,
        flowStatus: flow?.status,
        notExecuting,
        notTriggered,
        withinRetryLimit,
        attemptCount: attemptCountRef.current,
        currentPhase: flow?.current_phase,
        phaseCompletion: flow?.phase_completion,
        phasesCompleted: flow?.phases_completed
      });

      // GATED AUTO-EXECUTION: Only execute when ALL conditions are met
      const shouldAutoExecute = hasRawData &&
                               hasNoAssets &&
                               dataCleansingCompleted &&
                               flowNotDeleted &&
                               notExecuting &&
                               notTriggered &&
                               withinRetryLimit;

      if (shouldAutoExecute) {
        console.log('🚀 Auto-executing asset inventory phase (gated execution)...');
        setHasTriggeredInventory(true);
        attemptCountRef.current += 1;

        executeFlowPhase('asset_inventory', {
          trigger: 'auto',
          source: 'inventory_page_gated_auto_execution'
        }).then(() => {
          console.log('✅ Asset inventory phase execution initiated');
          // Reset attempt counter on success
          attemptCountRef.current = 0;
          // Refetch after a delay
          setTimeout(() => {
            refetchAssets();
            refreshFlow();
          }, 3000);
        }).catch(error => {
          console.error('❌ Failed to auto-execute asset inventory phase:', error);

          // Parse error response for specific handling
          let errorCode = null;
          let shouldRetry = false;

          try {
            if (error?.response?.data?.error_code) {
              errorCode = error.response.data.error_code;
            } else if (error?.message && error.message.includes('422')) {
              errorCode = 'CLEANSING_REQUIRED';
            }
          } catch (parseError) {
            console.warn('Could not parse error response:', parseError);
          }

          if (errorCode === 'CLEANSING_REQUIRED') {
            // 422 CLEANSING_REQUIRED: Do NOT reset hasTriggeredInventory, show banner
            console.log('🚨 Data cleansing required - stopping auto-execution');
            setExecutionError('Data cleansing must be completed before generating asset inventory.');
            setShowCleansingRequiredBanner(true);
            // Do NOT reset hasTriggeredInventory to prevent retry loop
          } else {
            // Handle HTTP status codes for retry logic
            const httpStatus = error?.response?.status || 0;

            if (httpStatus === 429 || (httpStatus >= 500 && httpStatus < 600)) {
              // Transient errors: 429 (rate limit) or 5xx (server errors)
              if (attemptCountRef.current < maxRetryAttempts) {
                shouldRetry = true;
                const backoffDelay = Math.min(1000 * Math.pow(2, attemptCountRef.current - 1), 30000);
                console.log(`🔄 Transient error (${httpStatus}), will retry in ${backoffDelay}ms (attempt ${attemptCountRef.current}/${maxRetryAttempts})`);

                setTimeout(() => {
                  setHasTriggeredInventory(false); // Allow retry
                }, backoffDelay);
              } else {
                console.log(`❌ Max retry attempts (${maxRetryAttempts}) reached for transient error`);
                setExecutionError(`Server temporarily unavailable. Please try again later. (Status: ${httpStatus})`);
              }
            } else if (httpStatus === 401 || httpStatus === 403) {
              // Authentication/Authorization errors: Do not retry
              console.log(`❌ Authentication error (${httpStatus}) - no retry`);
              setExecutionError(`Authentication error. Please refresh the page and try again.`);
              // Do NOT reset hasTriggeredInventory
            } else {
              // Other errors: Do not retry but reset for manual retry
              console.log(`❌ Non-retryable error: ${error.message}`);
              setExecutionError(`Execution failed: ${error.message}`);
              setHasTriggeredInventory(false); // Allow manual retry
            }
          }
        });
      }
    }, 1500); // 1.5 second delay to ensure page is fully rendered

    // Cleanup timeout on unmount
    return () => clearTimeout(timeoutId);
  }, [flow, isExecutingPhase, hasTriggeredInventory, assets.length, executeFlowPhase, refetchAssets, refreshFlow, executionError]);

  // Separate useEffect to handle classification needs without causing loops
  useEffect(() => {
    // Only show console message when classification is needed
    if (needsClassification && assets.length > 0) {
      console.log('🚨 Assets need classification - use the refresh button to trigger CrewAI processing');
    }
  }, [needsClassification, assets.length]);

  // Error Banner Component for cleansing required
  const CleansingRequiredBanner = () => (
    showCleansingRequiredBanner && (
      <Card className="mb-6 border-amber-200 bg-amber-50">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-5 h-5 text-amber-500">
                ⚠️
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-amber-800">Data Cleansing Required</h3>
              <p className="mt-1 text-sm text-amber-700">
                Asset inventory cannot be generated until data cleansing is completed.
                Please complete the data cleansing phase before proceeding.
              </p>
              <div className="mt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowCleansingRequiredBanner(false);
                    setExecutionError(null);
                  }}
                  className="border-amber-300 text-amber-800 hover:bg-amber-100"
                >
                  Dismiss
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  );

  // View Mode Toggle Component - defined here for consistent access across all states
  const ViewModeToggle = () => (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Label htmlFor="view-mode-toggle" className="text-sm font-medium">
              View Mode:
            </Label>
            <div className="flex items-center space-x-2">
              <Label
                htmlFor="view-mode-toggle"
                className={`text-sm cursor-pointer ${
                  viewMode === 'all' ? 'text-blue-600 font-medium' : 'text-gray-600'
                }`}
              >
                All Assets
              </Label>
              <Switch
                id="view-mode-toggle"
                checked={viewMode === 'current_flow'}
                onCheckedChange={(checked) => {
                  if (assetsLoading) return; // Prevent toggling during loading
                  if (!hasFlowId && checked) return; // Guard against switching to current_flow without flowId
                  setViewMode(checked ? 'current_flow' : 'all');
                  setCurrentPage(1); // Reset pagination when switching modes
                }}
                disabled={!hasFlowId || assetsLoading} // Disable toggle if no flow is available or loading
                aria-disabled={!hasFlowId || assetsLoading}
                aria-busy={assetsLoading}
              />
              <Label
                htmlFor="view-mode-toggle"
                className={`text-sm cursor-pointer ${
                  viewMode === 'current_flow' ? 'text-blue-600 font-medium' : 'text-gray-600'
                }`}
              >
                Current Flow Only
              </Label>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            {viewMode === 'all'
              ? 'Showing all assets for this client and engagement'
              : hasFlowId
                ? `Showing assets for flow: ${String(flowId).substring(0, 8)}...`
                : 'No flow selected'
            }
          </div>
        </div>
        {!hasFlowId && (
          <div className="mt-2 text-xs text-amber-600">
            ⚠️ No flow selected - only "All Assets" view is available
          </div>
        )}
      </CardContent>
    </Card>
  );

  // Render ViewModeToggle and error banners at top level, always visible regardless of state
  return (
    <div className={`space-y-6 ${className}`}>
      <ViewModeToggle />
      <CleansingRequiredBanner />
      {executionError && !showCleansingRequiredBanner && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-5 h-5 text-red-500">
                  ❌
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800">Execution Error</h3>
                <p className="mt-1 text-sm text-red-700">{executionError}</p>
                <div className="mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setExecutionError(null);
                      attemptCountRef.current = 0;
                    }}
                    className="border-red-300 text-red-800 hover:bg-red-100"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {(assetsLoading || isExecutingPhase) && (
        <>
          <div className="animate-pulse">
            <div className="h-32 bg-gray-200 rounded mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
          {isExecutingPhase && (
            <div className="text-center text-gray-600 mt-4">
              <p className="font-medium">Processing asset inventory...</p>
              <p className="text-sm mt-2">The AI agents are analyzing and classifying your assets.</p>
              <p className="text-sm">This process may take up to 6 minutes for large inventories.</p>
              <p className="text-sm mt-1 text-blue-600">
                View Mode: {viewMode === 'all' ? 'All Assets' : 'Current Flow Only'}
              </p>
              <div className="mt-4">
                <div className="inline-flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                  <span className="text-sm text-gray-500">Processing in background...</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Error State */}
      {hasBackendError && !assetsLoading && (
        <InventoryContentFallback
          error={`Backend service is temporarily unavailable. Please try again in a few moments. (View Mode: ${viewMode === 'all' ? 'All Assets' : 'Current Flow Only'})`}
          onRetry={() => refetchAssets()}
        />
      )}

      {/* Empty State */}
      {assets.length === 0 && !assetsLoading && !hasBackendError && (() => {
        // Check if we need to execute the asset inventory phase
        // FIX #447: Support both phases_completed array and phase_completion object
        const dataCleansingDone =
          flow?.phases_completed?.includes('data_cleansing') ||
          flow?.phase_completion?.data_cleansing === true;
        const inventoryNotDone =
          !(flow?.phases_completed?.includes('asset_inventory') ||
            flow?.phase_completion?.inventory === true);

        const shouldExecuteInventoryPhase = flow &&
          dataCleansingDone &&
          inventoryNotDone &&
          flow.current_phase !== 'asset_inventory' &&
          !isExecutingPhase;

        // Check if inventory processing might be starting soon
        const mightStartProcessing = flow && flow.raw_data && flow.raw_data.length > 0 && !hasTriggeredInventory;

        return (
          <Card>
            <CardContent className="p-8">
              <div className="text-center">
                {mightStartProcessing ? (
                  <>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Preparing Asset Inventory</h3>
                    <p className="text-gray-600 mb-4">
                      The system is preparing to process your asset inventory.
                    </p>
                    <p className="text-sm text-gray-500 mb-4">
                      Processing will begin automatically in a moment...
                    </p>
                    <div className="inline-flex items-center mb-4">
                      <div className="animate-pulse rounded-full h-3 w-3 bg-blue-600 mr-2"></div>
                      <span className="text-sm text-gray-500">Initializing...</span>
                    </div>
                    {/* FIX #447: Manual bypass button when auto-execution is blocked */}
                    {!dataCleansingCompleted && (
                      <div className="mt-4">
                        <p className="text-sm text-amber-600 mb-3">
                          Auto-execution is waiting for data cleansing to complete. You can manually start the process:
                        </p>
                        <Button
                          onClick={async () => {
                            try {
                              console.log('📦 Manual execution of asset inventory phase...');
                              setHasTriggeredInventory(true);
                              await executeFlowPhase('asset_inventory', {
                                trigger: 'manual_bypass',
                                source: 'inventory_page_manual_bypass'
                              });
                              setTimeout(() => {
                                refetchAssets();
                                refreshFlow();
                              }, 2000);
                            } catch (error) {
                              console.error('Failed to manually execute asset inventory:', error);
                              setHasTriggeredInventory(false);
                            }
                          }}
                          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          disabled={isExecutingPhase}
                        >
                          Run Asset Inventory Manually
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Assets Found</h3>
                    <p className="text-gray-600 mb-4">
                      {viewMode === 'current_flow' && flow ?
                        "The asset inventory will be populated once the inventory phase is executed for this flow." :
                        viewMode === 'current_flow' && !flow ?
                        "No flow is selected or the flow has no assets yet." :
                        "No assets have been discovered yet for this client and engagement."
                      }
                    </p>
                    <p className="text-sm text-gray-500">
                      {viewMode === 'all'
                        ? "Assets are created during discovery flows or can be imported directly. Try switching to 'All Assets' mode to see assets from other flows."
                        : "Assets are created during the discovery flow process or can be imported directly. Try switching to 'All Assets' mode to see all available assets."
                      }
                    </p>
                    {shouldExecuteInventoryPhase && (
                      <div className="mt-6">
                        <p className="text-sm text-gray-600 mb-4">
                          Data cleansing is complete. Click below to create the asset inventory.
                        </p>
                        <button
                          onClick={async () => {
                            try {
                              console.log('📦 Executing asset inventory phase...');
                              await executeFlowPhase('asset_inventory', {
                                trigger: 'user_initiated',
                                source: 'inventory_page'
                              });
                              // Refetch assets after execution
                              setTimeout(() => {
                                refetchAssets();
                                refreshFlow();
                              }, 2000);
                            } catch (error) {
                              console.error('Failed to execute asset inventory phase:', error);
                            }
                          }}
                          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          disabled={isExecutingPhase}
                        >
                          Create Asset Inventory
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })()}

      {/* Main Content State - Only render when we have assets */}
      {assets.length > 0 && !assetsLoading && !hasBackendError && (
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid grid-cols-3 w-full max-w-md mx-auto mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="inventory">Inventory</TabsTrigger>
            <TabsTrigger value="insights">AI Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <InventoryOverview inventoryProgress={inventoryProgress} />
            <ClassificationProgress
              inventoryProgress={inventoryProgress}
              onRefresh={handleRefreshClassification}
              needsClassification={needsClassification}
            />
            <ClassificationCards
              inventoryProgress={inventoryProgress}
              selectedAssetType={filters.selectedAssetType}
              onAssetTypeSelect={handleClassificationCardClick}
              flowId={flowId}
            />
            <NextStepCard inventoryProgress={inventoryProgress} />

            {/* Show filtered asset details below Next Step when a type is selected */}
            {filters.selectedAssetType !== 'all' && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">
                  {filters.selectedAssetType.charAt(0).toUpperCase() + filters.selectedAssetType.slice(1)} Assets
                </h3>
                <AssetTable
                  assets={assets}
                  filteredAssets={filteredAssets}
                  selectedAssets={selectedAssets}
                  onSelectAsset={handleSelectAsset}
                  onSelectAll={handleSelectAll}
                  searchTerm={filters.searchTerm}
                  onSearchChange={(value) => updateFilter('searchTerm', value)}
                  selectedEnvironment={filters.selectedEnvironment}
                  onEnvironmentChange={(value) => updateFilter('selectedEnvironment', value)}
                  uniqueEnvironments={uniqueEnvironments}
                  showAdvancedFilters={filters.showAdvancedFilters}
                  onToggleAdvancedFilters={() => updateFilter('showAdvancedFilters', !filters.showAdvancedFilters)}
                  onExport={handleExportAssets}
                  currentPage={currentPage}
                  recordsPerPage={RECORDS_PER_PAGE}
                  onPageChange={setCurrentPage}
                  selectedColumns={selectedColumns}
                  allColumns={allColumns}
                  onToggleColumn={toggleColumn}
                  onReclassifySelected={handleReclassifySelected}
                  isReclassifying={isReclassifying}
                  onProcessForAssessment={handleProcessForAssessment}
                  isApplicationsSelected={isApplicationsSelected}
                />
              </div>
            )}
          </TabsContent>

          <TabsContent value="inventory">
            <AssetTable
              assets={assets}
              filteredAssets={filteredAssets}
              selectedAssets={selectedAssets}
              onSelectAsset={handleSelectAsset}
              onSelectAll={handleSelectAll}
              searchTerm={filters.searchTerm}
              onSearchChange={(value) => updateFilter('searchTerm', value)}
              selectedEnvironment={filters.selectedEnvironment}
              onEnvironmentChange={(value) => updateFilter('selectedEnvironment', value)}
              uniqueEnvironments={uniqueEnvironments}
              showAdvancedFilters={filters.showAdvancedFilters}
              onToggleAdvancedFilters={() => updateFilter('showAdvancedFilters', !filters.showAdvancedFilters)}
              onExport={handleExportAssets}
              currentPage={currentPage}
              recordsPerPage={RECORDS_PER_PAGE}
              onPageChange={setCurrentPage}
              selectedColumns={selectedColumns}
              allColumns={allColumns}
              onToggleColumn={toggleColumn}
              onReclassifySelected={handleReclassifySelected}
              isReclassifying={isReclassifying}
              onProcessForAssessment={handleProcessForAssessment}
              isApplicationsSelected={isApplicationsSelected}
            />
          </TabsContent>

          <TabsContent value="insights">
            <EnhancedInventoryInsights flowId={flowId} />
          </TabsContent>
        </Tabs>
      )}

      {/* Application Selection Modal */}
      {showApplicationModal && (
        <ApplicationSelectionModal
          isOpen={showApplicationModal}
          onClose={() => setShowApplicationModal(false)}
          flowId={flowId}
          preSelectedApplicationIds={selectedApplicationIds}
          existingCollectionFlowId={new URLSearchParams(window.location.search).get('collectionFlowId') || undefined}
        />
      )}
    </div>
  );
};

export default InventoryContent;
