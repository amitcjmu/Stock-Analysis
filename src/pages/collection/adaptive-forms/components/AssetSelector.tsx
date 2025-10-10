/**
 * AssetSelector Component
 * Dropdown selector for multi-asset questionnaires
 * Extracted from AdaptiveForms.tsx
 */

import React from 'react';
import type { groupQuestionsByAsset } from '@/utils/questionnaireUtils';

interface AssetSelectorProps {
  assetGroups: ReturnType<typeof groupQuestionsByAsset>;
  selectedAssetId: string | null;
  onAssetChange: (assetId: string) => void;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  assetGroups,
  selectedAssetId,
  onAssetChange,
}) => {
  if (assetGroups.length <= 1) {
    return null; // Don't show selector for single asset
  }

  const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
  const completedCount = assetGroups.filter(g => g.completion_percentage === 100).length;

  return (
    <div className="mb-6 p-4 border rounded-lg bg-white">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Asset to Answer Questions For:
          </label>
          <select
            value={selectedAssetId || ''}
            onChange={(e) => onAssetChange(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            {assetGroups.map((group) => (
              <option key={group.asset_id} value={group.asset_id}>
                {group.asset_name} - {group.completion_percentage || 0}% Complete
              </option>
            ))}
          </select>
        </div>
        <div className="ml-4 text-sm text-gray-600">
          <div>Asset {currentIndex + 1} of {assetGroups.length}</div>
          <div className="font-medium">{completedCount} of {assetGroups.length} Complete</div>
        </div>
      </div>
    </div>
  );
};
