import React from 'react';

interface InventoryActionsProps {
  executeFlowPhase: (phase: string, params: unknown) => Promise<void>;
  refetchAssets: () => void;
  refreshFlow: () => void;
  setHasTriggeredInventory: (value: boolean) => void;
  setExecutionError: (value: string | null) => void;
  setShowCleansingRequiredBanner: (value: boolean) => void;
}

/**
 * Enhanced refresh function that triggers CrewAI classification with error handling
 */
export const useInventoryActions = ({
  executeFlowPhase,
  refetchAssets,
  refreshFlow,
  setHasTriggeredInventory,
  setExecutionError,
  setShowCleansingRequiredBanner
}: InventoryActionsProps) => {
  const handleRefreshClassification = async (): Promise<void> => {
    try {
      console.log('🔄 Refreshing asset classification with CrewAI...');

      // Clear any previous errors
      setExecutionError(null);
      setShowCleansingRequiredBanner(false);

      // Reset the trigger state to allow fresh execution
      setHasTriggeredInventory(false);

      // Re-execute the asset inventory phase to trigger CrewAI classification
      await executeFlowPhase('asset_inventory', {
        trigger: 'manual_refresh',
        source: 'inventory_classification_refresh'
      });

      console.log('✅ Asset inventory phase re-executed');

      // Set the trigger state to true after execution
      setHasTriggeredInventory(true);

      // Refetch assets after phase execution (no fixed delay for agentic activities)
      setTimeout(() => {
        refetchAssets();
        refreshFlow();
      }, 1000);

    } catch (error) {
      console.error('❌ Failed to refresh asset classification:', error);

      // Handle 422 CLEANSING_REQUIRED error
      let errorCode = null;
      try {
        if ((error as { response?: { data?: { error_code?: string } } })?.response?.data?.error_code) {
          errorCode = (error as { response: { data: { error_code: string } } }).response.data.error_code;
        } else if ((error as { message?: string })?.message && (error as { message: string }).message.includes('422')) {
          errorCode = 'CLEANSING_REQUIRED';
        }
      } catch (parseError) {
        console.warn('Could not parse error response:', parseError);
      }

      if (errorCode === 'CLEANSING_REQUIRED') {
        setExecutionError('Data cleansing must be completed before refreshing asset classification.');
        setShowCleansingRequiredBanner(true);
        // Keep hasTriggeredInventory as true to prevent auto-retry
      } else {
        // For other errors, reset to allow retry
        setHasTriggeredInventory(false);
        setExecutionError(`Refresh failed: ${(error as Error).message}`);
        // Fallback to just refetching assets
        refetchAssets();
      }
    }
  };

  const handleReclassifySelected = async (selectedAssets: string[], clearSelection: () => void): Promise<void> => {
    if (selectedAssets.length === 0) {
      console.warn('No assets selected for reclassification');
      return;
    }

    try {
      console.log(`🔄 Reclassifying ${selectedAssets.length} selected assets...`);

      // Import API call function
      const { apiCall } = await import('../../../../config/api');

      const response = await apiCall('/assets/auto-classify', {
        method: 'POST',
        body: JSON.stringify({
          asset_ids: selectedAssets,
          use_learned_patterns: true,
          confidence_threshold: 0.8,
          classification_context: "user_initiated_reclassification"
        })
      });

      console.log('✅ Reclassification completed:', response);

      // Refresh assets after reclassification
      setTimeout(() => {
        refetchAssets();
        refreshFlow();
        clearSelection(); // Clear selection after successful reclassification
      }, 1000);

    } catch (error) {
      console.error('❌ Failed to reclassify selected assets:', error);
      throw error;
    }
  };

  return {
    handleRefreshClassification,
    handleReclassifySelected
  };
};
