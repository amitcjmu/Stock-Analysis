/**
 * useAssetNavigation Hook
 * Handles multi-asset questionnaire navigation and asset selection
 * Extracted from AdaptiveForms.tsx - Asset navigation logic
 */

import { useState, useCallback, useMemo, useEffect } from 'react';
import type { groupQuestionsByAsset } from '@/utils/questionnaireUtils';
import type { UseAdaptiveFormFlowReturn } from '@/hooks/collection/useAdaptiveFormFlow';

interface UseAssetNavigationProps {
  assetGroups: ReturnType<typeof groupQuestionsByAsset>;
  formData: UseAdaptiveFormFlowReturn['formData'];
  formValues: UseAdaptiveFormFlowReturn['formValues'];
}

interface UseAssetNavigationReturn {
  selectedAssetId: string | null;
  setSelectedAssetId: (id: string | null) => void;
  currentAssetIndex: number;
  canNavigatePrevious: boolean;
  canNavigateNext: boolean;
  handlePreviousAsset: () => void;
  handleNextAsset: () => void;
  filteredFormData: UseAdaptiveFormFlowReturn['formData'];
}

/**
 * Hook for managing asset navigation in multi-asset questionnaires
 */
export const useAssetNavigation = ({
  assetGroups,
  formData,
  formValues,
}: UseAssetNavigationProps): UseAssetNavigationReturn => {
  // Asset selector state for multi-asset questionnaires
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);

  // Auto-select first asset when groups change (only on initial load)
  useEffect(() => {
    if (assetGroups.length > 0 && !selectedAssetId) {
      setSelectedAssetId(assetGroups[0].asset_id);
    }
  }, [assetGroups, selectedAssetId]);

  // Filter form data to show only selected asset's questions
  const filteredFormData = useMemo(() => {
    if (!formData || !selectedAssetId || assetGroups.length <= 1) {
      return formData; // No filtering needed for single asset or no selection
    }

    const selectedGroup = assetGroups.find(g => g.asset_id === selectedAssetId);
    if (!selectedGroup) return formData;

    // Filter sections to only include selected asset's questions
    const filteredSections = formData.sections.map(section => ({
      ...section,
      fields: section.fields.filter(field =>
        selectedGroup.questions.some(q => q.field_id === field.id)
      )
    })).filter(section => section.fields.length > 0);

    return {
      ...formData,
      sections: filteredSections
    };
  }, [formData, selectedAssetId, assetGroups]);

  // Asset navigation handlers
  const handlePreviousAsset = useCallback(() => {
    if (assetGroups.length === 0 || !selectedAssetId) return;

    const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
    if (currentIndex > 0) {
      setSelectedAssetId(assetGroups[currentIndex - 1].asset_id);
      // Scroll to top of form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [assetGroups, selectedAssetId]);

  const handleNextAsset = useCallback(() => {
    if (assetGroups.length === 0 || !selectedAssetId) return;

    const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
    if (currentIndex < assetGroups.length - 1) {
      setSelectedAssetId(assetGroups[currentIndex + 1].asset_id);
      // Scroll to top of form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [assetGroups, selectedAssetId]);

  const currentAssetIndex = useMemo(() => {
    if (!selectedAssetId) return -1;
    return assetGroups.findIndex(g => g.asset_id === selectedAssetId);
  }, [assetGroups, selectedAssetId]);

  const canNavigatePrevious = currentAssetIndex > 0;
  const canNavigateNext = currentAssetIndex >= 0 && currentAssetIndex < assetGroups.length - 1;

  return {
    selectedAssetId,
    setSelectedAssetId,
    currentAssetIndex,
    canNavigatePrevious,
    canNavigateNext,
    handlePreviousAsset,
    handleNextAsset,
    filteredFormData,
  };
};
