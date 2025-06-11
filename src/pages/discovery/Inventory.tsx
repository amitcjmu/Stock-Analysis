import React, { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, Download, AlertCircle, Database } from 'lucide-react';

// Components
import { FilterBar } from './inventory/components/Filters/FilterBar';
import { InventorySummary } from './inventory/components/SummaryCards/InventorySummary';
import { AssetTable } from './inventory/components/AssetTable/AssetTable';
import { BulkEditDialog } from './inventory/components/BulkActions/BulkEditDialog';

// Hooks
import { useInventoryData, useBulkUpdateAssets } from './inventory/hooks/useInventory';

// Types
import { InventoryFilters } from './inventory/types';

const NewInventory: React.FC = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();
  
  // Filter state
  const [filters, setFilters] = useState<InventoryFilters>({
    page: 1,
    page_size: 50,
    filter: 'all',
    department: 'all',
    environment: 'all',
    criticality: 'all',
    search: ''
  });

  // UI state
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [showBulkEditDialog, setShowBulkEditDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data fetching
  const {
    data: inventoryData,
    isLoading,
    error,
    refetch
  } = useInventoryData(filters);
  
  // Mutations
  const { mutate: bulkUpdate } = useBulkUpdateAssets();

  // Handlers
  const handleFilterChange = useCallback((updates: Partial<InventoryFilters>) => {
    setFilters(prev => ({ ...prev, ...updates }));
  }, []);

  const handleSelectAsset = useCallback((assetId: string) => {
    setSelectedAssets(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  }, []);

  const handleSelectAll = useCallback((checked: boolean) => {
    if (!inventoryData?.assets) return;
    setSelectedAssets(checked ? inventoryData.assets.map(asset => asset.id) : []);
  }, [inventoryData?.assets]);

  const handleBulkUpdate = useCallback((updateData: any) => {
    bulkUpdate(
      { assetIds: selectedAssets, updateData },
      {
        onSuccess: () => {
          setSelectedAssets([]);
          setShowBulkEditDialog(false);
        }
      }
    );
  }, [bulkUpdate, selectedAssets]);

  const handleExport = useCallback(() => {
    // Export logic here
  }, []);

  // Render loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading inventory data...</span>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center text-red-800">
          <AlertCircle className="h-5 w-5 mr-2" />
          <h3 className="font-medium">Error loading inventory data</h3>
        </div>
        <p className="mt-2 text-sm text-red-700">
          {error.message || 'Failed to load inventory data. Please try again.'}
        </p>
        <Button 
          variant="outline" 
          className="mt-4" 
          onClick={() => refetch()}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  // Render no data state
  if (!inventoryData?.assets?.length) {
    return (
      <div className="text-center py-12">
        <Database className="h-12 w-12 mx-auto text-gray-400" />
        <h3 className="mt-2 text-lg font-medium text-gray-900">No inventory data available</h3>
        <p className="mt-1 text-sm text-gray-500">
          The inventory data has not been generated yet or no assets match your filters.
        </p>
        <Button className="mt-4" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Asset Inventory</h1>
          <p className="text-sm text-gray-500">
            Manage and analyze your IT assets
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="assets">Assets</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <InventorySummary summary={inventoryData.summary} />
          {/* Add more overview components here */}
        </TabsContent>

        {/* Assets Tab */}
        <TabsContent value="assets" className="space-y-6">
          <FilterBar 
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={() => setFilters({
              page: 1,
              page_size: 50,
              filter: 'all',
              department: 'all',
              environment: 'all',
              criticality: 'all',
              search: ''
            })}
            availableDepartments={inventoryData.available_departments || []}
            availableEnvironments={inventoryData.available_environments || []}
            availableCriticalities={inventoryData.available_criticalities || []}
          />
          
          <AssetTable 
            assets={inventoryData.assets}
            selectedAssets={selectedAssets}
            onSelectAsset={handleSelectAsset}
            onSelectAll={handleSelectAll}
            onSort={(key) => {
              // Sort logic here
            }}
            sortConfig={null}
            isLoading={isLoading}
            error={error}
            columnVisibility={{
              id: true,
              name: true,
              type: true,
              status: true,
              environment: true,
              department: true,
              criticality: true,
              lastSeen: true
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Bulk Edit Dialog */}
      <BulkEditDialog
        isOpen={showBulkEditDialog}
        onClose={() => setShowBulkEditDialog(false)}
        onSave={handleBulkUpdate}
        selectedCount={selectedAssets.length}
      />
    </div>
  );
};

const Inventory = NewInventory;
export default Inventory;
