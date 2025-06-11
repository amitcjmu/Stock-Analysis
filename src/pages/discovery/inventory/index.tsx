import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useQueryClient, useQueryState } from '@tanstack/react-query';
import { useAuth } from '../../../contexts/AuthContext';
import { useBulkUpdateAssets } from '../../../api/hooks/useInventory';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Plus, 
  RefreshCw, 
  Edit2, 
  Trash2, 
  Download,
  Database as DatabaseIcon,
  Server as ServerIcon,
  HardDrive as HardDriveIcon,
  Network as NetworkIcon,
  Shield as ShieldIcon,
  Cpu as CpuIcon,
  Cloud as CloudIcon,
  Zap as ZapIcon,
  Eye as EyeIcon,
  ArrowUpDown as ArrowUpDownIcon,
  CheckCircle as CheckCircleIcon,
  AlertCircle as AlertCircleIcon,
  X as XIcon
} from 'lucide-react';

// Components
import { FilterBar } from './components/Filters/FilterBar';
import { InventorySummary } from './components/SummaryCards/InventorySummary';
import { AssetTable } from './components/AssetTable/AssetTable';
import { BulkEditDialog } from './components/BulkActions/BulkEditDialog';

// Types
import { InventoryFilters, InventoryResponse } from './types';

const InventoryPage: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  
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
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [columnVisibility, setColumnVisibility] = useState({
    name: true,
    type: true,
    environment: true,
    department: true,
    criticality: true,
    last_seen: true,
  });

  // Define the query key
  const queryKey = ['inventory', filters];

  // Fetch inventory data with proper type safety
  const { 
    data: inventoryData, 
    isLoading, 
    error,
    refetch,
    isFetching
  } = useQuery<InventoryResponse>({
    queryKey,
    queryFn: async ({ signal }) => {
      const response = await fetch('/api/v1/discovery/inventory', {
        headers: getAuthHeaders(),
        signal
      });
      if (!response.ok) {
        throw new Error('Failed to fetch inventory data');
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 3,
    retryDelay: 1000,
    // @ts-ignore - keepPreviousData is a valid option in newer versions
    keepPreviousData: true,
  });

  // Bulk update mutation
  const bulkUpdateMutation = useBulkUpdateAssets();

  // Handle filter changes
  const handleFilterChange = useCallback((updates: Partial<InventoryFilters>) => {
    setFilters(prev => ({
      ...prev,
      ...updates,
      // Reset to first page when filters change
      ...(Object.keys(updates).some(key => key !== 'page' && key !== 'page_size') && { page: 1 })
    }));
  }, []);

  // Handle reset filters
  const handleResetFilters = useCallback(() => {
    setFilters({
      page: 1,
      page_size: 50,
      filter: 'all',
      department: 'all',
      environment: 'all',
      criticality: 'all',
      search: ''
    });
  }, []);

  // Handle sort
  const handleSort = useCallback((key: string) => {
    setSortConfig(prev => {
      // If same key, toggle direction, else set new key with 'asc' direction
      if (prev && prev.key === key) {
        return {
          key,
          direction: prev.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key, direction: 'asc' };
    });
  }, []);

  // Handle select asset
  const handleSelectAsset = useCallback((id: string) => {
    setSelectedAssets(prev => 
      prev.includes(id) 
        ? prev.filter(assetId => assetId !== id)
        : [...prev, id]
    );
  }, []);

  // Handle select all assets
  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      setSelectedAssets(inventoryData?.assets?.map(asset => asset.id) || []);
    } else {
      setSelectedAssets([]);
    }
  }, [inventoryData?.assets]);

  // Handle bulk update with proper error handling
  const handleBulkUpdate = useCallback(async (updateData: Record<string, string>) => {
    if (selectedAssets.length === 0) return;
    
    try {
      await bulkUpdateMutation.mutateAsync({
        assetIds: selectedAssets,
        updateData
      });
      
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      setSelectedAssets([]);
      
      // Show success notification
      // You can use a toast library here
      console.log('Bulk update successful');
      
    } catch (error) {
      console.error('Bulk update failed:', error);
      // Show error notification
    }
  }, [selectedAssets, bulkUpdateMutation, queryClient]);

  // Apply sorting to assets with proper type safety
  const sortedAssets = useMemo(() => {
    if (!inventoryData?.items) return [];
    
    const assets = [...inventoryData.items];
    
    if (!sortConfig || !sortConfig.key) return assets;
    
    return assets.sort((a, b) => {
      const aValue = a[sortConfig.key as keyof typeof a];
      const bValue = b[sortConfig.key as keyof typeof b];
      
      // Handle undefined/null values
      if (aValue == null) return sortConfig.direction === 'asc' ? -1 : 1;
      if (bValue == null) return sortConfig.direction === 'asc' ? 1 : -1;
      
      // Compare values
      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [inventoryData?.items, sortConfig]);

  // Extract unique values for filters with type safety
  const availableDepartments = useMemo(() => {
    if (!inventoryData?.items) return [];
    return Array.from(
      new Set(
        inventoryData.items
          .map(asset => asset.department)
          .filter((dept): dept is string => Boolean(dept))
      )
    );
  }, [inventoryData?.items]);

  const availableEnvironments = useMemo(() => {
    if (!inventoryData?.items) return [];
    return Array.from(
      new Set(
        inventoryData.items
          .map(asset => asset.environment)
          .filter((env): env is string => Boolean(env))
      )
    );
  }, [inventoryData?.items]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Asset Inventory</h1>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Asset
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="assets">All Assets</TabsTrigger>
          <TabsTrigger value="servers">
            <Server className="mr-2 h-4 w-4" />
            Servers
          </TabsTrigger>
          <TabsTrigger value="databases">
            <Database className="mr-2 h-4 w-4" />
            Databases
          </TabsTrigger>
          <TabsTrigger value="network">
            <Network className="mr-2 h-4 w-4" />
            Network
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {inventoryData && (
            <InventorySummary 
              summary={inventoryData.summary} 
              isLoading={isLoading}
              lastUpdated={inventoryData.last_updated}
            />
          )}
          
          {/* Add visualization components here */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border bg-card p-4">
              <h3 className="text-lg font-medium mb-4">Asset Distribution</h3>
              {/* Placeholder for chart */}
              <div className="h-64 bg-muted/50 rounded flex items-center justify-center">
                <p className="text-sm text-muted-foreground">Asset distribution chart</p>
              </div>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <h3 className="text-lg font-medium mb-4">Environment Distribution</h3>
              {/* Placeholder for chart */}
              <div className="h-64 bg-muted/50 rounded flex items-center justify-center">
                <p className="text-sm text-muted-foreground">Environment distribution chart</p>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="assets" className="space-y-4">
          <FilterBar
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={handleResetFilters}
            availableDepartments={availableDepartments}
            availableEnvironments={availableEnvironments}
          />

          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">All Assets</h2>
              <div className="flex items-center space-x-2">
                {selectedAssets.length > 0 && (
                  <>
                    <span className="text-sm text-muted-foreground">
                      {selectedAssets.length} selected
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowBulkEditDialog(true)}
                    >
                      <Edit2 className="mr-2 h-4 w-4" />
                      Edit
                    </Button>
                    <Button variant="outline" size="sm" disabled>
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                    <Button variant="outline" size="sm" disabled>
                      <Download className="mr-2 h-4 w-4" />
                      Export
                    </Button>
                  </>
                )}
              </div>
            </div>

            <AssetTable
              assets={sortedAssets}
              selectedAssets={selectedAssets}
              onSelectAsset={handleSelectAsset}
              onSelectAll={handleSelectAll}
              onSort={handleSort}
              sortConfig={sortConfig}
              isLoading={isLoading}
              error={error}
              columnVisibility={columnVisibility}
            />

            {/* Pagination */}
            {inventoryData?.pagination && (
              <div className="flex items-center justify-between px-2 py-4">
                <div className="text-sm text-muted-foreground">
                  Showing <span className="font-medium">
                    {(filters.page - 1) * filters.page_size + 1}
                  </span> to{' '}
                  <span className="font-medium">
                    {Math.min(filters.page * filters.page_size, inventoryData.pagination.total_items)}
                  </span>{' '}
                  of <span className="font-medium">
                    {inventoryData.pagination.total_items}
                  </span> assets
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange({ page: filters.page - 1 })}
                    disabled={filters.page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFilterChange({ page: filters.page + 1 })}
                    disabled={!inventoryData.pagination.has_next}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Other tabs content can be added here */}
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

export default InventoryPage;
