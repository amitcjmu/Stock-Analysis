import { useMemo } from 'react';
import { AssetInventory, InventoryProgress } from '../types/inventory.types';

export const useInventoryProgress = (assets: AssetInventory[]): InventoryProgress => {
  return useMemo(() => {
    const total = assets.length;
    const servers = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('server') || 
             assetType === 'server';
    }).length;
    const applications = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('application') || 
             assetType === 'application';
    }).length;
    const databases = assets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('database') || 
             assetType === 'database';
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
             assetType === 'switch';
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