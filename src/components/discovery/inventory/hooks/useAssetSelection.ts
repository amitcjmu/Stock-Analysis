import { useState } from 'react'
import { useCallback } from 'react'

export const useAssetSelection = () => {
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);

  const handleSelectAsset = useCallback((assetId: string) => {
    setSelectedAssets(prev =>
      prev.includes(assetId)
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  }, []);

  const handleSelectAll = useCallback((assetIds: string[]) => {
    setSelectedAssets(prev => {
      const allSelected = assetIds.every(id => prev.includes(id));
      if (allSelected) {
        return prev.filter(id => !assetIds.includes(id));
      } else {
        return [...new Set([...prev, ...assetIds])];
      }
    });
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedAssets([]);
  }, []);

  const isSelected = useCallback((assetId: string) => {
    return selectedAssets.includes(assetId);
  }, [selectedAssets]);

  const isAllSelected = useCallback((assetIds: string[]) => {
    return assetIds.length > 0 && assetIds.every(id => selectedAssets.includes(id));
  }, [selectedAssets]);

  return {
    selectedAssets,
    handleSelectAsset,
    handleSelectAll,
    clearSelection,
    isSelected,
    isAllSelected
  };
};
