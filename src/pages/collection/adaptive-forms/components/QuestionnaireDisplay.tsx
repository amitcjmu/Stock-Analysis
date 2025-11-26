/**
 * QuestionnaireDisplay component
 * Handles rendering of the adaptive form container with asset selection
 * Includes dynamic question filtering, agent pruning, and dependency tracking
 *
 * Issue #796 - Frontend UI Integration for Dynamic Questions
 */

import React, { useState, useCallback, useEffect, useMemo } from "react";
import AdaptiveFormContainer from "@/components/collection/forms/AdaptiveFormContainer";
import { QuestionFilterControls } from "./QuestionFilterControls";
import { DependencyWarningBanner } from "./DependencyWarningBanner";
import { Badge } from "@/components/ui/badge";
import { useFilteredQuestions, useDependencyChange } from "@/hooks/collection/adaptive-questionnaire";
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
  // FIX: Validate UUID format to prevent 422 errors from dependency-change endpoint
  const rawChildFlowId = formData?.flow_id || formData?.formId || '';
  const isValidUUID = (str: string): boolean => {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  };
  const childFlowId = isValidUUID(rawChildFlowId) ? rawChildFlowId : '';
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
    // FIX: Validate both IDs are proper UUIDs to prevent 422 errors
    const hasValidIds = selectedAssetId && childFlowId &&
      isValidUUID(selectedAssetId) && isValidUUID(childFlowId);

    if (hasValidIds && formValues && formValues[fieldId] !== value) {
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
              formData.sections.forEach((section: any) => {
                section.fields?.forEach((field: any) => {
                  if (data.reopened_question_ids.includes(field.id)) {
                    reopenedTitles.push(field.label || field.name || field.id);
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
    if (!formData) {
      return formData;
    }

    // CRITICAL FIX: Always update applicationName from assetGroups, even for single asset
    // This ensures asset name is displayed correctly instead of UUID
    const selectedGroup = assetGroups.find(g => g.asset_id === selectedAssetId) || assetGroups[0];
    const assetName = selectedGroup?.asset_name || selectedGroup?.asset_id || formData.applicationName;

    // For single asset or no selection, just update applicationName
    if (!selectedAssetId || assetGroups.length <= 1) {
      return {
        ...formData,
        applicationName: assetName, // CRITICAL FIX: Always set asset name from assetGroups
      };
    }

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

    // Apply client-side filters (answered status, section)
    // FIX: Update applicationName to match selected asset
    let finalFormData = {
      ...formData,
      applicationName: assetName, // Use asset name from assetGroups
      sections: filteredSections
    };

    // Apply answered filter
    if (answeredFilter !== 'all') {
      finalFormData = {
        ...finalFormData,
        sections: finalFormData.sections.map((section: any) => ({
          ...section,
          fields: section.fields.filter((field: any) => {
            const hasValue = formValues && formValues[field.id] !== undefined &&
              formValues[field.id] !== null && formValues[field.id] !== '';
            return answeredFilter === 'answered' ? hasValue : !hasValue;
          })
        })).filter((section: any) => section.fields.length > 0)
      };
    }

    // Apply section filter
    if (sectionFilter !== 'all') {
      finalFormData = {
        ...finalFormData,
        sections: finalFormData.sections.filter((section: any) => section.id === sectionFilter)
      };
    }

    return finalFormData;
  }, [formData, selectedAssetId, assetGroups, answeredFilter, sectionFilter, formValues]);

  // Calculate question counts
  const questionCounts = useMemo(() => {
    const allFields = formData?.sections?.flatMap((s: any) => s.fields) || [];
    const filteredFields = filteredFormData?.sections?.flatMap((s: any) => s.fields) || [];

    const total = allFields.length;
    const unanswered = allFields.filter((field: any) => {
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
    return formData.sections.map((section: any) => ({
      id: section.id,
      title: section.title || section.name || section.id
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
