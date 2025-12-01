import { useMemo } from 'react';
import type { Asset } from '../../../types/asset';
import type { InventoryProgress } from '../types/inventory.types';
import {
  classifyAssetType,
  isDeviceAsset,
  type AssetCategory
} from '../../../../utils/assetClassification';

/**
 * Hook to calculate inventory progress statistics from asset data.
 * Bug #971 Fix: Uses shared assetClassification utility for consistent categorization.
 */
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

    // Bug #971 Fix: Use shared classification utility for consistent categorization
    const categoryCounts: Record<AssetCategory, number> = {
      SERVER: 0,
      APPLICATION: 0,
      DATABASE: 0,
      NETWORK: 0,
      STORAGE: 0,
      SECURITY: 0,
      VIRTUALIZATION: 0,
      OTHER: 0,
      UNKNOWN: 0,
    };

    // Count assets by category using shared utility
    safeAssets.forEach(asset => {
      const category = classifyAssetType(asset.asset_type);
      categoryCounts[category]++;
    });

    // Bug #404 Fix: Count devices as network + storage + security + other + unknown
    const devices = safeAssets.filter(asset => isDeviceAsset(asset.asset_type)).length;

    return {
      total_assets: total,
      classified_assets: total,
      servers: categoryCounts.SERVER,
      applications: categoryCounts.APPLICATION,
      databases: categoryCounts.DATABASE,
      devices,
      classification_accuracy: 100 // From CrewAI classification
    };
  }, [assets]);
};
