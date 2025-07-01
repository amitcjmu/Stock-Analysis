import { useState, useMemo } from 'react';
import { AssetInventory, AssetFilters } from '../types/inventory.types';

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
      
      const matchesType = filters.selectedAssetType === 'all' || 
        asset.asset_type === filters.selectedAssetType;
      
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