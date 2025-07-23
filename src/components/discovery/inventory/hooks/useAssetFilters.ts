import type { useState } from 'react'
import { useMemo } from 'react'
import type { AssetInventory, AssetFilters } from '../types/inventory.types';

export const useAssetFilters = (assets: AssetInventory[]) => {
  const [filters, setFilters] = useState<AssetFilters>({
    searchTerm: '',
    selectedAssetType: 'all',
    selectedEnvironment: 'all',
    showAdvancedFilters: false
  });

  const uniqueEnvironments = useMemo(() => {
    const environments = new Set(assets.map(asset => asset.environment).filter(Boolean));
    return Array.from(environments);
  }, [assets]);

  const uniqueAssetTypes = useMemo(() => {
    const types = new Set(assets.map(asset => asset.asset_type).filter(Boolean));
    return Array.from(types);
  }, [assets]);

  const filteredAssets = useMemo(() => {
    return assets.filter(asset => {
      const matchesSearch = !filters.searchTerm || 
        Object.values(asset).some(value => 
          String(value).toLowerCase().includes(filters.searchTerm.toLowerCase())
        );
      
      const matchesType = filters.selectedAssetType === 'all' || (() => {
        const assetType = asset.asset_type?.toLowerCase();
        const filterType = filters.selectedAssetType.toLowerCase();
        
        if (filterType === 'server') {
          return assetType?.includes('server') || assetType === 'server';
        } else if (filterType === 'application') {
          return assetType?.includes('application') || assetType === 'application';
        } else if (filterType === 'database') {
          return assetType?.includes('database') || assetType === 'database';
        } else if (filterType === 'device') {
          return assetType?.includes('device') || 
                 assetType?.includes('network') || 
                 assetType?.includes('storage') || 
                 assetType?.includes('security') || 
                 assetType?.includes('infrastructure') ||
                 assetType === 'load_balancer' ||
                 assetType === 'firewall' ||
                 assetType === 'router' ||
                 assetType === 'switch';
        }
        return asset.asset_type === filters.selectedAssetType;
      })();
      
      const matchesEnvironment = filters.selectedEnvironment === 'all' || 
        asset.environment === filters.selectedEnvironment;
      
      return matchesSearch && matchesType && matchesEnvironment;
    });
  }, [assets, filters]);

  const updateFilter = <K extends keyof AssetFilters>(key: K, value: AssetFilters[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({
      searchTerm: '',
      selectedAssetType: 'all',
      selectedEnvironment: 'all',
      showAdvancedFilters: false
    });
  };

  return {
    filters,
    updateFilter,
    resetFilters,
    filteredAssets,
    uniqueEnvironments,
    uniqueAssetTypes
  };
};