/**
 * QuestionnaireDisplay component
 * Handles rendering of the adaptive form container with asset selection
 * Includes dynamic question filtering, agent pruning, and dependency tracking
 *
 * Issue #796 - Frontend UI Integration for Dynamic Questions
 */

import React, { useState, useCallback, useMemo } from "react";
import AdaptiveFormContainer from "@/components/collection/forms/AdaptiveFormContainer";
import { QuestionFilterControls } from "./QuestionFilterControls";
import { DependencyWarningBanner } from "./DependencyWarningBanner";
import { Badge } from "@/components/ui/badge";
import { useFilteredQuestions, useDependencyChange } from "@/hooks/collection/adaptive-questionnaire";
import type { AssetGroup, ProgressMilestone } from "../types";
import type { FormSection, FormField } from "@/components/collection/types";

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
  // State for question filtering and agent pruning
  const [answeredFilter, setAnsweredFilter] = useState<'all' | 'answered' | 'unanswered'>('all');
  const [sectionFilter, setSectionFilter] = useState<string>('all');
  const [agentPruningEnabled, setAgentPruningEnabled] = useState(false);
  const [triggerRefresh, setTriggerRefresh] = useState(false);
  const [reopenedQuestions, setReopenedQuestions] = useState<{
    ids: string[];
    reason: string;
    titles: string[];
  } | null>(null);

  // Get current asset type for API call
  const selectedAsset = useMemo(() =>
    assetGroups.find(g => g.asset_id === selectedAssetId),
    [assetGroups, selectedAssetId]
  );

  // Use filtered questions hook (only when agent pruning is enabled)
  // Note: We'll extract child_flow_id from formData or context
  const childFlowId = formData?.flow_id || formData?.formId || '';
  const assetType = selectedAsset?.asset_type || 'application';

  const {
    data: dynamicQuestionsData,
    isLoading: isLoadingDynamicQuestions,
    refetch: refetchQuestions
  } = useFilteredQuestions({
    child_flow_id: childFlowId,
    asset_id: selectedAssetId || '',
    asset_type: assetType,
    include_answered: answeredFilter !== 'unanswered',
    refresh_agent_analysis: agentPruningEnabled && triggerRefresh,
    enabled: agentPruningEnabled && !!selectedAssetId && !!childFlowId,
  });

  // Dependency change tracking hook
  const dependencyMutation = useDependencyChange();

  // Handle agent pruning refresh
  const handleRefreshQuestions = useCallback(() => {
    setTriggerRefresh(true);
    refetchQuestions();
    // Reset trigger after a delay to allow re-triggering
    setTimeout(() => setTriggerRefresh(false), 1000);
  }, [refetchQuestions]);

  // Track field changes for dependency detection
  const handleFieldChangeWithDependency = useCallback((fieldId: string, value: unknown) => {
    // Call original handler
    onFieldChange(fieldId, value);

    // Check if this is a critical field that might trigger dependencies
    // For now, trigger on any field change - backend will determine if dependencies exist
    if (selectedAssetId && childFlowId && formValues && formValues[fieldId] !== value) {
      dependencyMutation.mutate({
        child_flow_id: childFlowId,
        asset_id: selectedAssetId,
        changed_field: fieldId,
        new_value: value,
        old_value: formValues[fieldId]
      }, {
        onSuccess: (data) => {
          if (data.reopened_question_ids.length > 0) {
            // Find question titles for reopened questions
            const reopenedTitles: string[] = [];
            if (formData && formData.sections) {
              // Type guard: Verify sections is an array
              const sections = Array.isArray(formData.sections) ? formData.sections : [];
              sections.forEach((section: FormSection) => {
                const fields = Array.isArray(section.fields) ? section.fields : [];
                fields.forEach((field: FormField) => {
                  if (data.reopened_question_ids.includes(field.id)) {
                    reopenedTitles.push(field.label || field.id);
                  }
                });
              });
            }

            setReopenedQuestions({
              ids: data.reopened_question_ids,
              reason: data.reason,
              titles: reopenedTitles
            });
          }
        }
      });
    }
  }, [selectedAssetId, childFlowId, formValues, onFieldChange, dependencyMutation, formData]);

  // Filter form data to show only selected asset's questions
  const filteredFormData = React.useMemo(() => {
    if (!formData || !selectedAssetId || assetGroups.length <= 1) {
      return formData; // No filtering needed for single asset or no selection
    }

    const selectedGroup = assetGroups.find(g => g.asset_id === selectedAssetId);
    if (!selectedGroup) return formData;

    // Fix #795: Preserve global questions that apply to all assets
    // Filter sections to include selected asset's questions AND global questions
    const sections = Array.isArray(formData.sections) ? formData.sections : [];
    const filteredSections = sections.map((section: FormSection) => ({
      ...section,
      fields: section.fields.filter((field: FormField) => {
        // Include if field belongs to selected asset OR if it's a global field
        const belongsToSelectedAsset = selectedGroup.questions.some(q => q.field_id === field.id);

        // A field is global if it has no asset_id metadata OR has multiple asset_ids
        // Type guard for metadata which may have dynamic properties
        const fieldMetadata = field.metadata as Record<string, unknown> | undefined;
        const isGlobalField = !fieldMetadata?.asset_id ||
                             (Array.isArray(fieldMetadata?.asset_ids) && (fieldMetadata.asset_ids as unknown[]).length > 1);

        return belongsToSelectedAsset || isGlobalField;
      })
    })).filter((section: FormSection) => section.fields.length > 0);

    // Apply client-side filters (answered status, section)
    // FIX: Update applicationName to match selected asset
    let finalFormData = {
      ...formData,
      applicationName: selectedGroup.asset_name || selectedGroup.asset_id, // Update asset name when selection changes
      sections: filteredSections
    };

    // Apply answered filter
    if (answeredFilter !== 'all') {
      const currentSections = Array.isArray(finalFormData.sections) ? finalFormData.sections : [];
      finalFormData = {
        ...finalFormData,
        sections: currentSections.map((section: FormSection) => ({
          ...section,
          fields: section.fields.filter((field: FormField) => {
            const hasValue = formValues && formValues[field.id] !== undefined &&
              formValues[field.id] !== null && formValues[field.id] !== '';
            return answeredFilter === 'answered' ? hasValue : !hasValue;
          })
        })).filter((section: FormSection) => section.fields.length > 0)
      };
    }

    // Apply section filter
    if (sectionFilter !== 'all') {
      const currentSections = Array.isArray(finalFormData.sections) ? finalFormData.sections : [];
      finalFormData = {
        ...finalFormData,
        sections: currentSections.filter((section: FormSection) => section.id === sectionFilter)
      };
    }

    return finalFormData;
  }, [formData, selectedAssetId, assetGroups, answeredFilter, sectionFilter, formValues]);

  // Calculate question counts
  const questionCounts = useMemo(() => {
    const allSections = Array.isArray(formData?.sections) ? formData.sections : [];
    const filteredSections = Array.isArray(filteredFormData?.sections) ? filteredFormData.sections : [];

    const allFields = allSections.flatMap((s: FormSection) => s.fields);
    const filteredFields = filteredSections.flatMap((s: FormSection) => s.fields);

    const total = allFields.length;
    const unanswered = allFields.filter((field: FormField) => {
      const hasValue = formValues && formValues[field.id] !== undefined &&
        formValues[field.id] !== null && formValues[field.id] !== '';
      return !hasValue;
    }).length;
    const filtered = filteredFields.length;

    return { total, unanswered, filtered };
  }, [formData, filteredFormData, formValues]);

  // Get available sections for filter dropdown
  const availableSections = useMemo(() => {
    if (!formData || !formData.sections) return [];
    const sections = Array.isArray(formData.sections) ? formData.sections : [];
    return sections.map((section: FormSection) => ({
      id: section.id,
      title: section.title || section.id
    }));
  }, [formData]);

  // Determine agent status and pruned count
  const agentStatus = dynamicQuestionsData?.agent_status || null;
  const prunedCount = dynamicQuestionsData
    ? (dynamicQuestionsData.total_questions - dynamicQuestionsData.questions.length)
    : undefined;

  return (
    <>
      {/* Dependency Warning Banner */}
      {reopenedQuestions && (
        <div className="mb-6">
          <DependencyWarningBanner
            reopenedQuestionIds={reopenedQuestions.ids}
            reason={reopenedQuestions.reason}
            reopenedQuestionTitles={reopenedQuestions.titles}
            onDismiss={() => setReopenedQuestions(null)}
          />
        </div>
      )}

      {/* Question Filter Controls */}
      <div className="mb-6">
        <QuestionFilterControls
          totalQuestionsCount={questionCounts.total}
          unansweredQuestionsCount={questionCounts.unanswered}
          filteredQuestionsCount={questionCounts.filtered}
          prunedQuestionsCount={prunedCount}
          answeredFilter={answeredFilter}
          onAnsweredFilterChange={setAnsweredFilter}
          sectionFilter={sectionFilter}
          onSectionFilterChange={setSectionFilter}
          availableSections={availableSections}
          agentPruningEnabled={agentPruningEnabled}
          onAgentPruningToggle={setAgentPruningEnabled}
          onRefreshQuestions={handleRefreshQuestions}
          agentStatus={agentStatus}
          isRefreshing={isLoadingDynamicQuestions}
        />
      </div>

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
                data-testid="asset-selector"
              >
                {assetGroups.map((group) => (
                  <option
                    key={group.asset_id}
                    value={group.asset_id}
                    data-testid={`asset-row-${group.asset_id}`}
                  >
                    {group.asset_name} | ID: {group.asset_id.substring(0, 8)} | {group.completion_percentage || 0}% Complete
                  </option>
                ))}
              </select>
            </div>
            <div className="ml-4 text-sm text-gray-600 flex items-center gap-2">
              <div>Asset {assetGroups.findIndex(g => g.asset_id === selectedAssetId) + 1} of {assetGroups.length}</div>
              <div className="font-medium">{assetGroups.filter(g => g.completion_percentage === 100).length} of {assetGroups.length} Complete</div>
              {/* Asset Type Badge */}
              {selectedAsset && (
                <Badge variant="outline" className="ml-2" data-testid="asset-type-badge">
                  {selectedAsset.asset_type || 'Application'}
                </Badge>
              )}
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
        onFieldChange={handleFieldChangeWithDependency}
        onValidationChange={onValidationChange}
        onSave={onSave}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    </>
  );
};
