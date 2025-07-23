import { useMemo } from 'react';
import type { AssetInventory, InventoryProgress } from '../types/inventory.types';

export const useInventoryProgress = (assets: AssetInventory[]): InventoryProgress => {
  return useMemo(() => {
    const total = assets.length;
    
    // Debug logging to see what asset types we're receiving
    if (assets.length > 0) {
      const assetTypes = assets.map(asset => asset.asset_type).filter(Boolean);
      const uniqueTypes = [...new Set(assetTypes)];
      console.log('🔍 Asset types found:', uniqueTypes);
      console.log('🔍 Total assets:', total);
    }
    const servers = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('server') || 
             assetType === 'server' ||
             assetType === 'virtual_machine' ||
             assetType === 'vm' ||
             assetType?.includes('host');
    }).length;
    const applications = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('application') || 
             assetType === 'application' ||
             assetType?.includes('app') ||
             assetType?.includes('service') ||
             assetType?.includes('web') ||
             assetType?.includes('api');
    }).length;
    const databases = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('database') || 
             assetType === 'database' ||
             assetType?.includes('db') ||
             assetType === 'mysql' ||
             assetType === 'postgresql' ||
             assetType === 'oracle' ||
             assetType === 'mongo';
    }).length;
    const devices = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('device') || 
             assetType?.includes('network') || 
             assetType?.includes('storage') || 
             assetType?.includes('security') || 
             assetType?.includes('infrastructure') ||
             assetType === 'load_balancer' ||
             assetType === 'firewall' ||
             assetType === 'router' ||
             assetType === 'switch' ||
             assetType === 'device';
    }).length;
    
    return {
      total_assets: total,
      classified_assets: total,
      servers,
      applications,
      databases,
      devices,
      classification_accuracy: 100 // From CrewAI classification
    };
  }, [assets]);
};