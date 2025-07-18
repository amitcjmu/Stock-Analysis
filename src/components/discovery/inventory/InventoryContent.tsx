import React, { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { useAuth } from '../../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../../hooks/useUnifiedDiscoveryFlow';

// Components
import { InventoryOverview } from './components/InventoryOverview';
import { ClassificationProgress } from './components/ClassificationProgress';
import { ClassificationCards } from './components/ClassificationCards';
import { AssetTable } from './components/AssetTable';
import { NextStepCard } from './components/NextStepCard';
import EnhancedInventoryInsights from './EnhancedInventoryInsights';

// Hooks
import { useInventoryProgress } from './hooks/useInventoryProgress';
import { useAssetFilters } from './hooks/useAssetFilters';
import { useAssetSelection } from './hooks/useAssetSelection';

// Utils
import { exportAssets } from './utils/exportHelpers';

// Types
import { AssetInventory, InventoryContentProps } from './types/inventory.types';

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

  // Get assets data - fetch from API endpoint that returns all assets for the client/engagement
  const { data: assetsData, isLoading: assetsLoading, refetch: refetchAssets } = useQuery({
    queryKey: ['discovery-assets', client?.id, engagement?.id, flowId],
    queryFn: async () => {
      try {
        // Import API call function with proper headers
        const { apiCall } = await import('../../../config/api');
        
        // First try to fetch from the database API with proper context headers
        // The apiCall function will handle the proxy and headers correctly
        const response = await apiCall('/assets/list/paginated?page=1&page_size=100');
        
        console.log('📊 Assets API response:', response);
        
        // Check if the response indicates an error
        if (response && response.data_source === 'error') {
          console.warn('⚠️ Assets API returned error state. Backend may have failed to fetch assets.');
        }
        
        if (response && response.assets && response.assets.length > 0) {
          console.log('📊 Assets from API:', response.assets.length);
          console.log('📊 Assets need classification:', response.needs_classification);
          
          // Update classification state
          setNeedsClassification(response.needs_classification || false);
          
          // Auto-trigger classification if needed
          if (response.needs_classification && !hasTriggeredInventory) {
            console.log('🚨 Assets need classification - triggering CrewAI processing');
            setTimeout(() => {
              setHasTriggeredInventory(true);
              executeFlowPhase('asset_inventory', {
                trigger: 'auto_classification',
                source: 'api_detected_unclassified_assets'
              }).then(() => {
                console.log('✅ Auto-classification triggered');
                setTimeout(() => {
                  refetchAssets();
                  refreshFlow();
                }, 3000);
              }).catch(error => {
                console.error('❌ Auto-classification failed:', error);
                setHasTriggeredInventory(false);
              });
            }, 1000);
          }
          
          // Transform API assets to match expected format
          return response.assets.map((asset: any) => ({
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
        // Return flow assets on error
        const flowAssets = getAssetsFromFlow();
        return flowAssets;
      }
    },
    enabled: !!client && !!engagement,
    staleTime: 30000,
    refetchOnWindowFocus: false
  });

  const assets: AssetInventory[] = useMemo(() => {
    if (!assetsData) return [];
    return Array.isArray(assetsData) ? assetsData : assetsData.assets || [];
  }, [assetsData]);

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
  const handleClassificationCardClick = (assetType: string) => {
    updateFilter('selectedAssetType', assetType);
    setCurrentPage(1);
  };

  const toggleColumn = (column: string) => {
    setSelectedColumns(prev =>
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const handleExportAssets = () => {
    exportAssets(filteredAssets, selectedColumns);
  };

  // Enhanced refresh function that triggers CrewAI classification
  const handleRefreshClassification = async () => {
    try {
      console.log('🔄 Refreshing asset classification with CrewAI...');
      
      // Re-execute the asset inventory phase to trigger CrewAI classification
      await executeFlowPhase('asset_inventory', {
        trigger: 'manual_refresh',
        source: 'inventory_classification_refresh'
      });
      
      console.log('✅ Asset inventory phase re-executed');
      
      // Refetch assets after phase execution
      setTimeout(() => {
        refetchAssets();
        refreshFlow();
      }, 3000);
      
    } catch (error) {
      console.error('❌ Failed to refresh asset classification:', error);
      // Fallback to just refetching assets
      refetchAssets();
    }
  };

  // Auto-execute asset inventory phase if conditions are met
  // Delay execution to ensure page has rendered first
  useEffect(() => {
    // Use setTimeout to delay execution until after page render
    const timeoutId = setTimeout(() => {
      // Check if we have raw data but no assets
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
        currentPhase: flow?.current_phase,
        phaseCompletion: flow?.phase_completion
      });

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
  }, [flow, isExecutingPhase, hasTriggeredInventory, assets.length, executeFlowPhase, refetchAssets, refreshFlow]);

  // No phase-based restrictions - inventory should be accessible at any time

  if (assetsLoading || isExecutingPhase) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
        {isExecutingPhase && (
          <div className="text-center text-gray-600 mt-4">
            <p className="font-medium">Processing asset inventory...</p>
            <p className="text-sm mt-2">The AI agents are analyzing and classifying your assets.</p>
            <p className="text-sm">This process may take up to 6 minutes for large inventories.</p>
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
                    {flow ? 
                      "The asset inventory will be populated once the inventory phase is executed." :
                      "No assets have been discovered yet for this client and engagement."
                    }
                  </p>
                  <p className="text-sm text-gray-500">
                    Assets are created during the discovery flow process or can be imported directly.
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

  return (
    <div className={`space-y-6 ${className}`}>
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
          />
        </TabsContent>

        <TabsContent value="insights">
          <EnhancedInventoryInsights flowId={flowId} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InventoryContent;