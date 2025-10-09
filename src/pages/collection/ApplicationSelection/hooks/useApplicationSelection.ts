/**
 * useApplicationSelection Hook
 * Manages application selection state and logic
 */

import { useState, useEffect, useCallback } from "react";
import type { Asset } from "@/types/asset";
import type { CollectionFlowResponse } from "@/services/api/collection-flow";

interface UseApplicationSelectionProps {
  collectionFlow: CollectionFlowResponse | null;
}

interface UseApplicationSelectionReturn {
  selectedApplications: Set<string>;
  handleToggleApplication: (appId: string) => void;
  handleSelectAll: (filteredApplications: Asset[], checked?: boolean) => void;
  setSelectedApplications: React.Dispatch<React.SetStateAction<Set<string>>>;
}

/**
 * Hook for managing application selection state
 */
export const useApplicationSelection = ({
  collectionFlow,
}: UseApplicationSelectionProps): UseApplicationSelectionReturn => {
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(
    new Set(),
  );

  // Pre-populate selections if flow already has applications
  useEffect(() => {
    if (collectionFlow?.collection_config?.selected_application_ids) {
      const existingSelections =
        collectionFlow.collection_config.selected_application_ids;
      setSelectedApplications(new Set(existingSelections));
      console.log(
        `🔄 Pre-populated ${existingSelections.length} existing application selections`,
      );
    }
  }, [collectionFlow]);

  // Handle application selection toggle
  const handleToggleApplication = useCallback((appId: string) => {
    setSelectedApplications((prev) => {
      const newSelection = new Set(prev);
      if (newSelection.has(appId)) {
        newSelection.delete(appId);
      } else {
        newSelection.add(appId);
      }
      return newSelection;
    });
  }, []);

  // Handle select all applications (filtered)
  const handleSelectAll = useCallback(
    (filteredApplications: Asset[], checked?: boolean) => {
      if (!filteredApplications) return;
      const shouldSelectAll =
        typeof checked === "boolean"
          ? checked
          : selectedApplications.size !== filteredApplications.length;
      setSelectedApplications(
        shouldSelectAll
          ? new Set(filteredApplications.map((app: Asset) => app.id.toString()))
          : new Set(),
      );
    },
    [selectedApplications.size],
  );

  return {
    selectedApplications,
    handleToggleApplication,
    handleSelectAll,
    setSelectedApplications,
  };
};
