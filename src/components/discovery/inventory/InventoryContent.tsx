import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '../../../contexts/AuthContext';
import { useDiscoveryFlowV2 } from '../../../hooks/discovery/useDiscoveryFlowV2';

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
  const { getAssets, getFlow } = useDiscoveryFlowV2(flowId);

  // State
  const [selectedColumns, setSelectedColumns] = useState(DEFAULT_COLUMNS);
  const [currentPage, setCurrentPage] = useState(1);

  // Get assets data
  const { data: assetsData, isLoading: assetsLoading, refetch: refetchAssets } = useQuery({
    queryKey: ['discovery-assets', flowId, client?.id, engagement?.id],
    queryFn: () => getAssets(),
    enabled: !!client && !!engagement && !!flowId,
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

  if (assetsLoading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
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
            onRefresh={refetchAssets}
          />
          <ClassificationCards
            inventoryProgress={inventoryProgress}
            selectedAssetType={filters.selectedAssetType}
            onAssetTypeSelect={handleClassificationCardClick}
          />
          <NextStepCard inventoryProgress={inventoryProgress} />
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