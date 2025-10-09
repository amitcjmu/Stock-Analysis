/**
 * AssetNavigationButtons component
 * Handles asset navigation UI for multi-asset questionnaires
 * Extracted from AdaptiveForms.tsx for better maintainability
 */

import React from "react";
import type { AssetGroup } from "../types";

interface AssetNavigationButtonsProps {
  assetGroups: AssetGroup[];
  canNavigatePrevious: boolean;
  canNavigateNext: boolean;
  isLoading: boolean;
  isSaving: boolean;
  onPreviousAsset: () => void;
  onNextAsset: () => void;
}

export const AssetNavigationButtons: React.FC<AssetNavigationButtonsProps> = ({
  assetGroups,
  canNavigatePrevious,
  canNavigateNext,
  isLoading,
  isSaving,
  onPreviousAsset,
  onNextAsset,
}) => {
  // Only show navigation when there are multiple assets
  if (assetGroups.length <= 1) {
    return null;
  }

  const completedAssetsCount = assetGroups.filter(g => g.completion_percentage === 100).length;
  const totalAssets = assetGroups.length;

  return (
    <div className="mt-6 flex items-center justify-between p-4 border-t">
      <button
        onClick={onPreviousAsset}
        disabled={!canNavigatePrevious || isLoading || isSaving}
        className={`flex items-center px-4 py-2 rounded-md transition-colors ${
          canNavigatePrevious && !isLoading && !isSaving
            ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            : 'bg-gray-50 text-gray-400 cursor-not-allowed'
        }`}
      >
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Previous Asset
      </button>

      <div className="text-sm text-gray-600">
        <span className="font-medium">
          {completedAssetsCount} of {totalAssets} Assets Complete
        </span>
      </div>

      <button
        onClick={onNextAsset}
        disabled={!canNavigateNext || isLoading || isSaving}
        className={`flex items-center px-4 py-2 rounded-md transition-colors ${
          canNavigateNext && !isLoading && !isSaving
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-50 text-gray-400 cursor-not-allowed'
        }`}
      >
        Next Asset
        <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
};
