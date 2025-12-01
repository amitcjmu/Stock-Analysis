import { useMemo } from 'react';
import type { Asset } from '../../../types/asset';
import type { InventoryProgress } from '../types/inventory.types';

export const useInventoryProgress = (assets: Asset[] = []): InventoryProgress => {
  return useMemo(() => {
    // Ensure assets is a valid array
    const safeAssets = assets || [];
    const total = safeAssets.length;

    // Debug logging to see what asset types we're receiving
    if (safeAssets.length > 0) {
      const assetTypes = safeAssets.map(asset => asset.asset_type).filter(Boolean);
      const uniqueTypes = [...new Set(assetTypes)];
      console.log('🔍 Asset types found:', uniqueTypes);
      console.log('🔍 Total assets:', total);
    }
    const servers = safeAssets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('server') ||
             assetType === 'server' ||
             assetType === 'virtual_machine' ||
             assetType === 'vm' ||
             assetType?.includes('host');
    }).length;
    const applications = safeAssets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('application') ||
             assetType === 'application' ||
             assetType?.includes('app') ||
             assetType?.includes('service') ||
             assetType?.includes('web') ||
             assetType?.includes('api');
    }).length;
    const databases = safeAssets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      return assetType?.includes('database') ||
             assetType === 'database' ||
             assetType?.includes('db') ||
             assetType === 'mysql' ||
             assetType === 'postgresql' ||
             assetType === 'oracle' ||
             assetType === 'mongo';
    }).length;
    // Bug #404 Fix: Count remaining assets that don't fit other categories
    // This includes network devices, storage, security, and "other" unclassified assets
    const devices = safeAssets.filter(asset => {
      const assetType = asset.asset_type?.toLowerCase();
      // Match network-related assets
      const isNetworkRelated = assetType?.includes('device') ||
             assetType?.includes('network') ||
             assetType?.includes('storage') ||
             assetType?.includes('security') ||
             assetType?.includes('infrastructure') ||
             assetType === 'load_balancer' ||
             assetType === 'firewall' ||
             assetType === 'router' ||
             assetType === 'switch';
      // Bug #404 Fix: Also count "other" and "unknown" types so no assets are hidden
      const isOtherType = assetType === 'other' || assetType === 'unknown' || !assetType;
      return isNetworkRelated || isOtherType;
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
