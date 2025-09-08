import React from 'react'
import { useState } from 'react'
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
  const [needsClassification, setNeedsClassification] = useState(false);
  const [isReclassifying, setIsReclassifying] = useState(false);
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [viewMode, setViewMode] = useState<'all' | 'current_flow'>(!flowId ? 'all' : 'current_flow');

  // Safety: auto-revert to 'all' if flowId disappears while in 'current_flow'
  React.useEffect(() => {
    if (!flowId) {
      setViewMode((prev) => (prev === 'current_flow' ? 'all' : prev));
    }
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
    queryKey: ['discovery-assets', String(client?.id ?? ''), String(engagement?.id ?? ''), viewMode, String(flowId ?? '')],
    queryFn: async () => {
      try {
        // Import API call function with proper headers
        const { apiCall } = await import('../../../config/api');

        // Build query parameters based on view mode
        const queryParams = new URLSearchParams({
          page: '1',
          page_size: '100'
        });

        // Only include flow_id when in current_flow mode and flowId is available
        const normalizedFlowId = flowId ? String(flowId) : '';
        if (viewMode === 'current_flow' && normalizedFlowId) {
          queryParams.append('flow_id', normalizedFlowId);
        }

        // First try to fetch from the database API with proper context headers
        // The apiCall function will handle the proxy and headers correctly
        const response = await apiCall(`/unified-discovery/assets?${queryParams.toString()}`);

        // Validate response status
        if (!response || (typeof response.status === 'number' && response.status >= 400)) {
          throw new Error(`Assets API error${response?.status ? ` (status ${response.status})` : ''}`);
        }

        // Validate response shape
        if (!response || typeof response !== 'object') {
          throw new Error('Invalid assets response shape');
        }

        console.log('📊 Assets API response:', response);

        // Check if the response indicates an error
        if (response && response.data_source === 'error') {
          console.warn('⚠️ Assets API returned error state. Backend may have failed to fetch assets.');
          // Don't throw error, just return empty assets to show fallback UI
          return [];
        }

        if (response && response.assets && response.assets.length > 0) {
          console.log('📊 Assets from API:', response.assets.length);
          console.log('📊 Assets need classification:', response.needs_classification);

          // Update classification state
          setNeedsClassification(response.needs_classification || false);

          // If assets are properly classified, mark as triggered to prevent auto-execution loops
          if (!response.needs_classification && response.assets && response.assets.length > 0) {
            setHasTriggeredInventory(true);
          }

          // Transform API assets to match expected format
          return (response.assets || []).map((asset: Asset) => ({
            id: asset.id,
            asset_name: asset.name,
            asset_type: asset.asset_type,
            environment: asset.environment,
            criticality: asset.criticality,
            status: asset.status,
            six_r_strategy: asset.six_r_strategy,
            migration_wave: asset.migration_wave,
            application_name: asset.application_name,
            hostname: asset.hostname,
            operating_system: asset.operating_system,
            cpu_cores: asset.cpu_cores,
            memory_gb: asset.memory_gb,
            storage_gb: asset.storage_gb,
            business_criticality: asset.criticality,
            risk_score: 0,
            migration_readiness: 'pending',
            dependencies: 0,
            last_updated: asset.updated_at
          }));
        }

        // Fallback to flow assets if API returns no data
        const flowAssets = getAssetsFromFlow();
        console.log('📊 Using flow assets as fallback:', flowAssets.length);
        return flowAssets;
      } catch (error) {
        console.error('Error fetching assets:', error);
        // Don't throw, return empty array to show fallback UI
        return [];
      }
    },
    // Enable query when we have client/engagement, and either in 'all' mode or have flowId for 'current_flow'
    enabled: !!client && !!engagement && (viewMode === 'all' || (viewMode === 'current_flow' && !!flowId)),
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

  // Enhanced refresh function that triggers CrewAI classification
  const handleRefreshClassification = async (): void => {
    try {
      console.log('🔄 Refreshing asset classification with CrewAI...');

      // Reset the trigger state to allow fresh execution
      setHasTriggeredInventory(false);

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
      // Fallback to just refetching assets
      refetchAssets();
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

  // Auto-execute asset inventory phase if conditions are met
  // Delay execution to ensure page has rendered first
  useEffect(() => {
    // Use setTimeout to delay execution until after page render
    const timeoutId = setTimeout(() => {
      // Check if we have raw data but no assets, or if assets need classification
      const hasRawData = flow && flow.raw_data && flow.raw_data.length > 0;
      const hasNoAssets = assets.length === 0;
      const notExecuting = !isExecutingPhase;
      const notTriggered = !hasTriggeredInventory;

      // Log the conditions for debugging
      console.log('🔍 Auto-execute conditions (post-render):', {
        hasRawData,
        rawDataCount: flow?.raw_data?.length || 0,
        hasNoAssets,
        notExecuting,
        notTriggered,
        needsClassification,
        currentPhase: flow?.current_phase,
        phaseCompletion: flow?.phase_completion
      });

      // Only auto-execute if we have raw data but no assets (initial case)
      // Don't auto-execute just because assets need classification - use manual refresh for that
      const shouldAutoExecute = hasRawData && hasNoAssets && notExecuting && notTriggered;

      if (shouldAutoExecute) {
        console.log('🚀 Auto-executing asset inventory phase (post-render)...');
        setHasTriggeredInventory(true);
        executeFlowPhase('asset_inventory', {
          trigger: 'auto',
          source: 'inventory_page_load_post_render'
        }).then(() => {
          console.log('✅ Asset inventory phase execution initiated');
          // Refetch after a delay
          setTimeout(() => {
            refetchAssets();
            refreshFlow();
          }, 3000);
        }).catch(error => {
          console.error('❌ Failed to auto-execute asset inventory phase:', error);

          // Reset for retry on any error since we fixed the endpoint authentication issue
          console.warn('🔄 Phase execution failed, will allow retry');
          setHasTriggeredInventory(false);
        });
      }
    }, 1500); // 1.5 second delay to ensure page is fully rendered

    // Cleanup timeout on unmount
    return () => clearTimeout(timeoutId);
  }, [flow, isExecutingPhase, hasTriggeredInventory, assets.length, executeFlowPhase, needsClassification, refetchAssets, refreshFlow]);

  // Separate useEffect to handle classification needs without causing loops
  useEffect(() => {
    // Only show console message when classification is needed
    if (needsClassification && assets.length > 0) {
      console.log('🚨 Assets need classification - use the refresh button to trigger CrewAI processing');
    }
  }, [needsClassification, assets.length]);

  // No phase-based restrictions - inventory should be accessible at any time

  if (assetsLoading || isExecutingPhase) {
    return (
      <div className={`space-y-6 ${className}`}>
        <ViewModeToggle />
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
      </div>
    );
  }

  // Show error fallback if backend is having issues
  if (hasBackendError && !assetsLoading) {
    return (
      <div className={`${className}`}>
        <ViewModeToggle />
        <InventoryContentFallback
          error={`Backend service is temporarily unavailable. Please try again in a few moments. (View Mode: ${viewMode === 'all' ? 'All Assets' : 'Current Flow Only'})`}
          onRetry={() => refetchAssets()}
        />
      </div>
    );
  }

  // Show a helpful message when there are no assets
  if (assets.length === 0 && !assetsLoading) {
    // Check if we need to execute the asset inventory phase
    const shouldExecuteInventoryPhase = flow &&
      flow.phase_completion?.data_cleansing === true &&
      flow.phase_completion?.inventory !== true &&
      flow.current_phase !== 'asset_inventory' &&
      !isExecutingPhase;

    // Check if inventory processing might be starting soon
    const mightStartProcessing = flow && flow.raw_data && flow.raw_data.length > 0 && !hasTriggeredInventory;

    return (
      <div className={`space-y-6 ${className}`}>
        <ViewModeToggle />
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
                  <div className="inline-flex items-center">
                    <div className="animate-pulse rounded-full h-3 w-3 bg-blue-600 mr-2"></div>
                    <span className="text-sm text-gray-500">Initializing...</span>
                  </div>
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
      </div>
    );
  }

  // View Mode Toggle Component
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
                  if (!flowId && checked) return; // Guard against switching to current_flow without flowId
                  setViewMode(checked ? 'current_flow' : 'all');
                  setCurrentPage(1); // Reset pagination when switching modes
                }}
                disabled={!flowId || assetsLoading} // Disable toggle if no flow is available or loading
                aria-disabled={!flowId || assetsLoading}
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
              : flowId
                ? `Showing assets for flow: ${String(flowId).substring(0, 8)}...`
                : 'No flow selected'
            }
          </div>
        </div>
        {!flowId && (
          <div className="mt-2 text-xs text-amber-600">
            ⚠️ No flow selected - only "All Assets" view is available
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      <ViewModeToggle />
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
