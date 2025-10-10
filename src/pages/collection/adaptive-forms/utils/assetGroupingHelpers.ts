/**
 * Asset Grouping Helper Functions
 * Utilities for asset-based form submission
 * Extracted from AdaptiveForms.tsx
 */

import type { CollectionFormData } from '@/components/collection/types';

/**
 * Inject asset_id into form values for multi-asset forms
 */
export const injectAssetId = (
  formValues: CollectionFormData,
  assetId: string | null
): CollectionFormData => {
  if (!assetId) return formValues;

  return {
    ...formValues,
    asset_id: assetId,
  };
};

/**
 * Create direct save handler that injects asset_id before saving
 */
export const createDirectSaveHandler = (
  handleSave: () => Promise<void>,
  handleFieldChange: ((field: string, value: unknown) => void) | undefined,
  assetGroupsLength: number,
  selectedAssetId: string | null
): (() => Promise<void>) => {
  return async () => {
    console.log('🟢 DIRECT SAVE HANDLER CALLED - Bypassing prop chain');

    // For multi-asset forms, temporarily add asset_id to formValues
    if (assetGroupsLength > 1 && selectedAssetId && handleFieldChange) {
      console.log(`💾 Saving progress for asset: ${selectedAssetId}`);
      // Inject asset_id into form values so backend knows which asset this is for
      handleFieldChange('asset_id', selectedAssetId);
    }

    if (typeof handleSave === 'function') {
      console.log('🟢 Calling handleSave from direct handler');
      await handleSave();
    } else {
      console.error('❌ handleSave is not available in AdaptiveForms');
    }
  };
};

/**
 * Create direct submit handler that injects asset_id before submission
 */
export const createDirectSubmitHandler = (
  handleSubmit: (values?: CollectionFormData) => Promise<void>,
  formValues: CollectionFormData,
  assetGroupsLength: number,
  selectedAssetId: string | null
): (() => Promise<void>) => {
  return async () => {
    console.log('🟢 DIRECT SUBMIT HANDLER CALLED - Injecting asset_id if needed');

    let submissionValues = formValues;
    // For multi-asset forms, create a submission payload with the correct asset_id
    if (assetGroupsLength > 1 && selectedAssetId) {
      console.log(`✅ Submitting form for asset: ${selectedAssetId}`);
      submissionValues = injectAssetId(formValues, selectedAssetId);
    } else {
      console.log('🟢 Not a multi-asset form, proceeding with regular submit');
    }

    if (typeof handleSubmit === 'function') {
      console.log('🟢 Calling handleSubmit from direct handler with submissionValues');
      await handleSubmit(submissionValues);
      console.log('🟢 handleSubmit completed');
    } else {
      console.error('❌ handleSubmit is not available in AdaptiveForms');
    }
  };
};
