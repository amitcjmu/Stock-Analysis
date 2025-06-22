import { useState, useCallback } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useInventoryLogic = () => {
  // Use the unified discovery flow
  const {
    flowState,
    isLoading,
    error,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    executeFlowPhase,
    isExecutingPhase,
    refreshFlow
  } = useUnifiedDiscoveryFlow();

  // Local UI state for filters, pagination, etc.
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [filters, setFilters] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);

  // Get asset inventory data from unified flow
  const inventoryData = getPhaseData('asset_inventory');
  const assets = (inventoryData && !Array.isArray(inventoryData) && inventoryData.assets) ? inventoryData.assets : [];
  const summary = (inventoryData && !Array.isArray(inventoryData) && inventoryData.summary) ? inventoryData.summary : { total: 0 };
  const inventoryProgress = (inventoryData && !Array.isArray(inventoryData) && inventoryData.progress) ? inventoryData.progress : {
    total_assets: 0,
    classified_assets: 0,
    classification_accuracy: 0
  };

  // Pagination
  const pagination = {
    currentPage,
    pageSize,
    total: summary.total || 0,
    totalPages: Math.ceil((summary.total || 0) / pageSize)
  };

  // Loading states
  const isFlowStateLoading = isLoading;
  const isAnalyzing = isExecutingPhase;
  const lastUpdated = new Date();

  // Error states
  const flowStateError = error;

  // Action handlers
  const handleTriggerInventoryBuildingCrew = useCallback(async () => {
    await executeFlowPhase('asset_inventory');
  }, [executeFlowPhase]);

  const fetchAssets = useCallback(async () => {
    await refreshFlow();
  }, [refreshFlow]);

  const canContinueToAppServerDependencies = useCallback(() => {
    return canProceedToPhase('dependency_analysis');
  }, [canProceedToPhase]);

  // UI action handlers
  const handleFilterChange = useCallback((newFilters: any) => {
    setFilters(newFilters);
  }, []);

  const handleSearchChange = useCallback((term: string) => {
    setSearchTerm(term);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const toggleAssetSelection = useCallback((assetId: string) => {
    setSelectedAssets(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  }, []);

  const selectAllAssets = useCallback(() => {
    const assetIds = assets.map((asset: any) => asset.id || asset.asset_id).filter(Boolean);
    setSelectedAssets(assetIds);
  }, [assets]);

  const clearSelection = useCallback(() => {
    setSelectedAssets([]);
  }, []);

  // Placeholder handlers for bulk operations
  const handleBulkUpdate = useCallback(() => {
    // TODO: Implement bulk update functionality
    console.log('Bulk update triggered for assets:', selectedAssets);
  }, [selectedAssets]);

  const handleAssetClassificationUpdate = useCallback(() => {
    // TODO: Implement asset classification update
    console.log('Asset classification update triggered');
  }, []);

  return {
    // Data
    assets,
    summary,
    pagination,
    inventoryProgress,
    flowState,
    
    // Loading states
    isLoading,
    isFlowStateLoading,
    isAnalyzing,
    lastUpdated,
    
    // Errors
    error,
    flowStateError,
    
    // Filters and search
    currentPage,
    pageSize,
    filters,
    searchTerm,
    
    // Selection
    selectedAssets,
    
    // Actions
    handleTriggerInventoryBuildingCrew,
    handleBulkUpdate,
    handleAssetClassificationUpdate,
    handleFilterChange,
    handleSearchChange,
    handlePageChange,
    toggleAssetSelection,
    selectAllAssets,
    clearSelection,
    fetchAssets,
    canContinueToAppServerDependencies,
  };
}; 