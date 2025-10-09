/**
 * QuestionnaireDisplay component
 * Handles rendering of the adaptive form container with asset selection
 * Extracted from AdaptiveForms.tsx for better maintainability
 */

import React from "react";
import AdaptiveFormContainer from "@/components/collection/forms/AdaptiveFormContainer";
import type { AssetGroup, ProgressMilestone } from "../types";

interface QuestionnaireDisplayProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
  formData: any;
  formValues: Record<string, unknown> | null;
  validation: Record<string, unknown>;
  milestones: ProgressMilestone[];
  isSaving: boolean;
  isSubmitting: boolean;
  completionStatus: string | null;
  assetGroups: AssetGroup[];
  selectedAssetId: string | null;
  isLoading: boolean;
  onFieldChange: (fieldId: string, value: unknown) => void;
  onValidationChange: (fieldId: string, validation: unknown) => void;
  onSave: () => Promise<void>;
  onSubmit: (values?: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
  onAssetChange: (assetId: string) => void;
}

export const QuestionnaireDisplay: React.FC<QuestionnaireDisplayProps> = ({
  formData,
  formValues,
  validation,
  milestones,
  isSaving,
  isSubmitting,
  completionStatus,
  assetGroups,
  selectedAssetId,
  isLoading,
  onFieldChange,
  onValidationChange,
  onSave,
  onSubmit,
  onCancel,
  onAssetChange,
}) => {
  // Filter form data to show only selected asset's questions
  const filteredFormData = React.useMemo(() => {
    if (!formData || !selectedAssetId || assetGroups.length <= 1) {
      return formData; // No filtering needed for single asset or no selection
    }

    const selectedGroup = assetGroups.find(g => g.asset_id === selectedAssetId);
    if (!selectedGroup) return formData;

    // Filter sections to only include selected asset's questions
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
    const filteredSections = formData.sections.map((section: any) => ({
      ...section,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
      fields: section.fields.filter((field: any) =>
        selectedGroup.questions.some(q => q.field_id === field.id)
      )
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
    })).filter((section: any) => section.fields.length > 0);

    return {
      ...formData,
      sections: filteredSections
    };
  }, [formData, selectedAssetId, assetGroups]);

  return (
    <>
      {/* Asset Selector - Show when multiple assets */}
      {assetGroups.length > 1 && (
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
              <div>Asset {assetGroups.findIndex(g => g.asset_id === selectedAssetId) + 1} of {assetGroups.length}</div>
              <div className="font-medium">{assetGroups.filter(g => g.completion_percentage === 100).length} of {assetGroups.length} Complete</div>
            </div>
          </div>
        </div>
      )}

      <AdaptiveFormContainer
        formData={filteredFormData || formData}
        formValues={formValues}
        validation={validation}
        milestones={milestones}
        isSaving={isSaving}
        isSubmitting={isSubmitting}
        completionStatus={completionStatus}
        onFieldChange={onFieldChange}
        onValidationChange={onValidationChange}
        onSave={onSave}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    </>
  );
};
