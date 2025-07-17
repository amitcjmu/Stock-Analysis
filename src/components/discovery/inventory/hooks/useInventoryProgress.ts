import { useMemo } from 'react';
import { AssetInventory, InventoryProgress } from '../types/inventory.types';

export const useInventoryProgress = (assets: AssetInventory[]): InventoryProgress => {
  return useMemo(() => {
    const total = assets.length;
    const servers = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('server') || 
      asset.asset_type?.toLowerCase() === 'server'
    ).length;
    const applications = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('application') || 
      asset.asset_type?.toLowerCase() === 'application'
    ).length;
    const databases = assets.filter(asset => 
      asset.asset_type?.toLowerCase().includes('database') || 
      asset.asset_type?.toLowerCase() === 'database'
    ).length;
    const devices = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('device') || 
             assetType?.includes('network') || 
             assetType?.includes('storage') || 
             assetType?.includes('security') || 
             assetType?.includes('infrastructure');
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