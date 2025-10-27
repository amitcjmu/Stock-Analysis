/**
 * Custom hook for handling navigation and routing logic in adaptive forms
 * Extracted from AdaptiveForms.tsx
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import type { AssetGroup } from "../types";
import { debugLog, debugWarn, debugError } from '@/utils/debug';

interface UseFlowNavigationProps {
  activeFlowId: string | null;
}

interface UseFlowNavigationReturn {
  handleContinueToDiscovery: () => void;
  handleViewCollectionOverview: () => void;
  handleStartNewCollection: () => void;
  handleCancelCollection: () => void;
  handleContinueFlow: (flowId: string) => void;
  handleViewFlowDetails: (flowId: string, phase: string) => void;
}

/**
 * Hook for managing all navigation actions in the adaptive forms flow
 */
export const useFlowNavigation = ({ activeFlowId }: UseFlowNavigationProps): UseFlowNavigationReturn => {
  const navigate = useNavigate();

  const handleContinueToDiscovery = () => {
    navigate(`/discovery?flowId=${activeFlowId}`);
  };

  const handleViewCollectionOverview = () => {
    navigate("/collection/overview");
  };

  const handleStartNewCollection = () => {
    navigate("/collection");
  };

  const handleCancelCollection = () => {
    navigate("/collection");
  };

  const handleContinueFlow = (flowId: string): void => {
    if (!flowId) {
      debugError("Cannot continue flow: flowId is missing");
      return;
    }
    // Navigate to adaptive forms page with flowId to resume the flow
    navigate(`/collection/adaptive-forms?flowId=${encodeURIComponent(flowId)}`);
  };

  const handleViewFlowDetails = (flowId: string, phase: string): void => {
    navigate(`/collection/progress/${flowId}`);
  };

  return {
    handleContinueToDiscovery,
    handleViewCollectionOverview,
    handleStartNewCollection,
    handleCancelCollection,
    handleContinueFlow,
    handleViewFlowDetails,
  };
};

/**
 * Hook for managing asset navigation in multi-asset questionnaires
 */
interface UseAssetNavigationProps {
  assetGroups: AssetGroup[];
  selectedAssetId: string | null;
  setSelectedAssetId: (id: string) => void;
}

interface UseAssetNavigationReturn {
  handlePreviousAsset: () => void;
  handleNextAsset: () => void;
  currentAssetIndex: number;
  canNavigatePrevious: boolean;
  canNavigateNext: boolean;
}

export const useAssetNavigation = ({
  assetGroups,
  selectedAssetId,
  setSelectedAssetId
}: UseAssetNavigationProps): UseAssetNavigationReturn => {
  const currentAssetIndex = React.useMemo(() => {
    if (!selectedAssetId) return -1;
    return assetGroups.findIndex(g => g.asset_id === selectedAssetId);
  }, [assetGroups, selectedAssetId]);

  const handlePreviousAsset = React.useCallback(() => {
    if (assetGroups.length === 0 || !selectedAssetId) return;

    const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
    if (currentIndex > 0) {
      setSelectedAssetId(assetGroups[currentIndex - 1].asset_id);
      // Scroll to top of form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [assetGroups, selectedAssetId, setSelectedAssetId]);

  const handleNextAsset = React.useCallback(() => {
    if (assetGroups.length === 0 || !selectedAssetId) return;

    const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
    if (currentIndex < assetGroups.length - 1) {
      setSelectedAssetId(assetGroups[currentIndex + 1].asset_id);
      // Scroll to top of form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [assetGroups, selectedAssetId, setSelectedAssetId]);

  const canNavigatePrevious = currentAssetIndex > 0;
  const canNavigateNext = currentAssetIndex >= 0 && currentAssetIndex < assetGroups.length - 1;

  return {
    handlePreviousAsset,
    handleNextAsset,
    currentAssetIndex,
    canNavigatePrevious,
    canNavigateNext,
  };
};
