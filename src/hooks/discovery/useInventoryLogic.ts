import { useState, useCallback } from 'react';
import { useDiscoveryFlowV2 } from './useDiscoveryFlowV2';

export const useInventoryLogic = (flowId?: string) => {
  // Use the V2 discovery flow
  const {
    flow,
    assets,
    isLoading,
    error,
    updatePhase,
    refresh
  } = useDiscoveryFlowV2(flowId);

  // Local UI state for filters, pagination, etc.
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [filters, setFilters] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);

  // Get asset inventory data from V2 flow
  const flowAssets = assets || [];
  const summary = { total: flowAssets.length };
  const inventoryProgress = {
    total_assets: flowAssets.length,
    classified_assets: flowAssets.filter((asset: any) => asset.asset_type).length,
    classification_accuracy: flowAssets.length > 0 ? (flowAssets.filter((asset: any) => asset.asset_type).length / flowAssets.length) * 100 : 0
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
  const isAnalyzing = isLoading;
  const lastUpdated = new Date();

  // Error states
  const flowStateError = error;

  // Action handlers
  const handleTriggerInventoryBuildingCrew = useCallback(async () => {
    if (flow?.flow_id) {
      await updatePhase('asset_inventory', { trigger_crew: true });
    }
  }, [flow, updatePhase]);

  const handleCompleteInventoryAndTriggerParallelAnalysis = useCallback(async () => {
    if (flow?.flow_id) {
      // Complete inventory and automatically trigger parallel dependencies + tech debt analysis
      await updatePhase('inventory_completed', { 
        trigger_parallel_analysis: true,
        execute_dependencies_and_tech_debt: true 
      });
    }
  }, [flow, updatePhase]);

  const fetchAssets = useCallback(async () => {
    refresh();
  }, [refresh]);

  const canContinueToAppServerDependencies = useCallback(() => {
    return flow?.phases?.asset_inventory === true;
  }, [flow]);

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
    assets: flowAssets,
    summary,
    pagination,
    inventoryProgress,
    flowState: flow,
    
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
    handleCompleteInventoryAndTriggerParallelAnalysis,
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