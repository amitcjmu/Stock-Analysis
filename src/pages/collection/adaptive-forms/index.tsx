import React from "react";
import { useState, useEffect } from "react";
import { useSearchParams, useParams, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "@/components/ui/use-toast";

// Import modular components
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
import AdaptiveFormContainer from "@/components/collection/forms/AdaptiveFormContainer";
import { ApplicationSelectionUI } from "@/components/collection/ApplicationSelectionUI";
import { QuestionnaireReloadButton } from "@/components/collection/QuestionnaireReloadButton";
// Import PR#790 Adaptive Questionnaire components
import { BulkImportWizard } from "@/components/collection/BulkImportWizard";
import { MultiAssetAnswerModal } from "@/components/collection/MultiAssetAnswerModal";

// Import custom hooks
import { useAdaptiveFormFlow } from "@/hooks/collection/useAdaptiveFormFlow";
import {
  useActivelyIncompleteCollectionFlows,
  useCollectionFlowManagement,
} from "@/hooks/collection/useCollectionFlowManagement";
import { useFlowDeletion } from "@/hooks/useFlowDeletion";
import { useAuth } from "@/contexts/AuthContext";
import { useCollectionStatePolling } from "@/hooks/collection/useCollectionStatePolling";
import { useQuery } from "@tanstack/react-query";
import { apiCall } from "@/config/api";

// Import types
import { groupQuestionsByAsset } from "@/utils/questionnaireUtils";
import type { CollectionFlow, QuestionnaireData } from "./types";

// Import modularized hooks and components
import {
  useProgressCalculation,
  useFlowNavigation,
  useAssetNavigation,
  useWindowFocusRefetch,
} from "./hooks";
import {
  QuestionnaireDisplay,
  AssetNavigationButtons,
  FlowControlPanel,
  CompletionDisplay,
  FlowBlockerDisplay,
  LoadingStateDisplay,
} from "./components";

/**
 * Adaptive Forms collection page
 * Refactored to use modular components and custom hooks for better maintainability
 */
const AdaptiveForms: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const routeParams = useParams<{ flowId?: string; applicationId?: string }>();
  const queryClient = useQueryClient();
  const { client, engagement, user } = useAuth();

  // CRITICAL FIX: Ref guard to prevent duplicate initialization calls per flowId
  const initializationAttempts = React.useRef<Set<string>>(new Set());
  const isInitializingRef = React.useRef<boolean>(false);

  // Get application ID and flow ID from URL params (route params take precedence over query params)
  const applicationId = routeParams.applicationId || searchParams.get("applicationId");
  const flowId = routeParams.flowId || searchParams.get("flowId");

  // CRITICAL FIX: All hooks must be called before any conditional returns
  // State to track flows being deleted
  const [deletingFlows, setDeletingFlows] = useState<Set<string>>(new Set());
  const [hasJustDeleted, setHasJustDeleted] = useState(false);

  // State to show app selection prompt when no applications are selected
  const [showInlineAppSelection, setShowInlineAppSelection] = useState(false);

  // State for questionnaire generation modal
  const [showGenerationModal, setShowGenerationModal] = useState(false);
  const [isFallbackQuestionnaire, setIsFallbackQuestionnaire] = useState(false);

  // State for manage flows modal
  const [showManageFlowsModal, setShowManageFlowsModal] = useState(false);

  // PR#790: State for bulk operations modals
  const [showBulkImportWizard, setShowBulkImportWizard] = useState(false);
  const [showBulkAnswerModal, setShowBulkAnswerModal] = useState(false);

  // DISABLED: Questionnaire generation modal no longer needed (questionnaires generated faster from data gaps)
  const handleQuestionnaireGeneration = React.useCallback(() => {
    // No-op: Modal disabled to avoid unnecessary 30-second delay
    console.log('📝 Questionnaire generation started (modal disabled)');
  }, []);

  // Handle questionnaire ready from modal
  const handleQuestionnaireReady = React.useCallback((questionnaire: QuestionnaireData) => {
    setShowGenerationModal(false);
    setIsFallbackQuestionnaire(false);
    // Reload the form with the new questionnaire
    window.location.reload();
  }, []);

  // Handle fallback to template questionnaire
  const handleQuestionnaireFallback = React.useCallback(() => {
    setShowGenerationModal(false);
    setIsFallbackQuestionnaire(true);
  }, []);

  // Check for actively incomplete flows (INITIALIZED, RUNNING) that would block new operations
  // Per ADR-012, PAUSED flows are waiting for user input and should not block
  // Skip checking if we're continuing a specific flow (flowId provided)
  const skipIncompleteCheck = !!flowId;
  const {
    data: incompleteFlows = [],
    isLoading: checkingFlows,
    refetch: refetchFlows,
  } = useActivelyIncompleteCollectionFlows(); // Always call the hook to maintain consistent hook order

  // Use collection flow management hook for flow operations
  const { deleteFlow, isDeleting } = useCollectionFlowManagement();

  // Use the flow deletion hook with modal confirmation
  const [deletionState, deletionActions] = useFlowDeletion(
    async (result) => {
      // Refresh flows after successful deletion
      await refetchFlows();
      setHasJustDeleted(true);

      // Remove from deleting set only for successfully deleted flows
      result.results.forEach((res) => {
        const normalizedFlowId = String(res.flowId || ''); // Normalize to string
        if (res.success) {
          setDeletingFlows((prev) => {
            const newSet = new Set(prev);
            newSet.delete(normalizedFlowId);
            return newSet;
          });
        } else {
          // Failed deletion - unhide the flow
          setDeletingFlows((prev) => {
            const newSet = new Set(prev);
            newSet.delete(normalizedFlowId);
            return newSet;
          });
        }
      });
    },
    (error) => {
      console.error('Flow deletion failed:', error);

      // On error, unhide all flows that were being deleted
      deletionState.candidates.forEach((flowId) => {
        const normalizedFlowId = String(flowId || ''); // Normalize to string
        setDeletingFlows((prev) => {
          const newSet = new Set(prev);
          newSet.delete(normalizedFlowId);
          return newSet;
        });
      });

      toast({
        title: "Error",
        description: error.message || "Failed to delete flow",
        variant: "destructive",
      });
    }
  );

  // Filter out the current flow and flows being deleted from the blocking check
  // CRITICAL FIX: Allow continuation of any existing flow by matching flowId in URL
  // When skipping incomplete check, treat as no blocking flows
  const blockingFlows = skipIncompleteCheck ? [] : incompleteFlows.filter((flow) => {
    const id = String(flow.flow_id || flow.id || ''); // Normalize to string
    const normalizedFlowId = String(flowId || ''); // Normalize to string
    // If flowId is provided in URL, allow continuing that specific flow
    if (flowId && (id === normalizedFlowId)) {
      return false; // Don't block if this is the flow we want to continue
    }
    // Only block if it's a different flow and not being deleted
    return id !== normalizedFlowId && !deletingFlows.has(id);
  });

  // Don't block if we're continuing a specific flow
  const hasBlockingFlows = !skipIncompleteCheck && blockingFlows.length > 0;

  // Calculate autoInitialize value
  const shouldAutoInitialize = !checkingFlows && (!hasBlockingFlows || hasJustDeleted || !!flowId);

  // Debug logging
  console.log('🔍 AdaptiveForms initialization state:', {
    flowId,
    checkingFlows,
    hasBlockingFlows,
    hasJustDeleted,
    shouldAutoInitialize,
    blockingFlowsCount: blockingFlows.length
  });

  // Use the adaptive form flow hook for all flow management
  const {
    formData,
    formValues,
    validation,
    isLoading,
    isSaving,
    isCompleted,
    error,
    flowId: activeFlowId, // Extract flowId from hook return
    // New polling state fields
    isPolling,
    completionStatus,
    statusLine,
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow,
  } = useAdaptiveFormFlow({
    applicationId,
    flowId,
    // CRITICAL FIX: Allow auto-initialization when continuing a specific flow
    autoInitialize: shouldAutoInitialize,
    onQuestionnaireGenerationStart: handleQuestionnaireGeneration,
  });

  // Asset selector state for multi-asset questionnaires
  const [selectedAssetId, setSelectedAssetId] = React.useState<string | null>(null);

  // DISABLED: Auto-show generation modal (modal disabled to avoid unnecessary delays)
  // Questionnaires are now generated faster from data gaps, no need for 30-second modal
  // React.useEffect(() => {
  //   if (completionStatus === "pending" && activeFlowId) {
  //     setShowGenerationModal(true);
  //   } else if (completionStatus === "ready" || completionStatus === "fallback") {
  //     setShowGenerationModal(false);
  //   }
  // }, [completionStatus, activeFlowId]);

  // Group questions by asset and auto-select first asset
  // Pass formValues to calculate real-time completion percentage
  // CRITICAL: Must be defined BEFORE navigation handlers that use it
  const assetGroups = React.useMemo(() => {
    if (!formData?.sections) return [];

    // Extract all questions from sections
    const allQuestions = formData.sections.flatMap(section =>
      section.fields.map(field => ({
        field_id: field.id,
        question_text: field.label,
        field_type: field.fieldType,
        required: field.validation?.required,
        options: field.options,
        metadata: field.metadata,
        ...field
      }))
    );

    return groupQuestionsByAsset(allQuestions, undefined, formValues);
  }, [formData, formValues]);

  // Auto-select first asset when groups change (only on initial load)
  React.useEffect(() => {
    if (assetGroups.length > 0 && !selectedAssetId) {
      setSelectedAssetId(assetGroups[0].asset_id);
    }
  }, [assetGroups, selectedAssetId]);

  // MODULARIZED: Use extracted asset navigation hook
  const {
    handlePreviousAsset,
    handleNextAsset,
    currentAssetIndex,
    canNavigatePrevious,
    canNavigateNext,
  } = useAssetNavigation({
    assetGroups,
    selectedAssetId,
    setSelectedAssetId
  });

  // Use HTTP polling for real-time updates during workflow initialization
  // CRITICAL FIX: Remove re-initialization calls from polling to prevent loops
  const { isActive: isPollingActive, requestStatusUpdate, flowState } =
    useCollectionStatePolling({
      flowId: activeFlowId,
      enabled: !!activeFlowId && isLoading && !formData, // Only poll if we're loading and don't have data
      onQuestionnaireReady: (state) => {
        console.log(
          "🎉 HTTP Polling: Questionnaire ready notification",
        );
        // DO NOT trigger re-initialization here - the hook handles it internally
      },
      onStatusUpdate: (state) => {
        console.log("📊 HTTP Polling: Workflow status update:", state);
        // DO NOT trigger re-initialization here - the hook handles it internally
      },
      onError: (error) => {
        console.error("❌ HTTP Polling: Collection workflow error:", error);
        toast({
          title: "Workflow Error",
          description: `Collection workflow encountered an error: ${error}`,
          variant: "destructive",
        });
      },
    });

  // Check if the current Collection flow has application selection
  // Now that formData is available from useAdaptiveFormFlow
  const { data: currentCollectionFlow, isLoading: isLoadingFlow, refetch: refetchCollectionFlow } = useQuery({
    queryKey: ["collection-flow", activeFlowId],
    queryFn: async () => {
      if (!activeFlowId) return null;
      try {
        console.log(
          "🔍 Fetching collection flow details for application check:",
          activeFlowId,
        );
        return await apiCall(`/collection/flows/${activeFlowId}`);
      } catch (error) {
        console.error("Failed to fetch collection flow:", error);
        return null;
      }
    },
    enabled: !!activeFlowId,
    // Set cache time to 5 minutes to prevent excessive re-fetching
    staleTime: 5 * 60 * 1000,
    // Cache data for 10 minutes
    gcTime: 10 * 60 * 1000,
    // Disable automatic refetching to prevent loops
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  });

  // CC: Debugging - Log handleSave function only when it changes
  React.useEffect(() => {
    console.log('🔍 AdaptiveForms handleSave initialized:', typeof handleSave === 'function');
  }, [handleSave]); // Only log when handleSave changes

  // CC: Create a direct save handler to bypass potential prop passing issues
  // CRITICAL: Inject selected asset_id before saving for multi-asset forms
  const directSaveHandler = React.useCallback(async () => {
    console.log('🟢 DIRECT SAVE HANDLER CALLED - Bypassing prop chain');

    let valuesToSave = formValues;
    // For multi-asset forms, create a payload with the correct asset_id
    if (assetGroups.length > 1 && selectedAssetId) {
      console.log(`💾 Saving progress for asset: ${selectedAssetId}`);
      valuesToSave = {
        ...formValues,
        asset_id: selectedAssetId,
      };
    }

    if (typeof handleSave === 'function') {
      console.log('🟢 Calling handleSave from direct handler with valuesToSave');
      await handleSave(valuesToSave);
    } else {
      console.error('❌ handleSave is not available in AdaptiveForms');
    }
  }, [handleSave, assetGroups.length, selectedAssetId, formValues]);

  // CC: Wrap handleSubmit to inject asset_id for multi-asset forms
  const directSubmitHandler = React.useCallback(async () => {
    console.log('🟢 DIRECT SUBMIT HANDLER CALLED - Injecting asset_id if needed');

    let submissionValues = formValues;
    // For multi-asset forms, create a submission payload with the correct asset_id
    if (assetGroups.length > 1 && selectedAssetId) {
      console.log(`✅ Submitting form for asset: ${selectedAssetId}`);
      submissionValues = {
        ...formValues,
        asset_id: selectedAssetId,
      };
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
  }, [handleSubmit, assetGroups, selectedAssetId, formValues]);

  // CRITICAL FIX: Protected initialization function with ref guard
  const protectedInitializeFlow = React.useCallback(async () => {
    const currentFlowKey = activeFlowId || flowId || 'new-flow';

    // Prevent duplicate initializations for the same flow
    if (isInitializingRef.current) {
      console.log('⚠️ Initialization already in progress, skipping duplicate call');
      return;
    }

    if (initializationAttempts.current.has(currentFlowKey)) {
      console.log('⚠️ Already attempted initialization for flow:', currentFlowKey);
      return;
    }

    console.log('🔐 Protected initialization starting for flow:', currentFlowKey);
    isInitializingRef.current = true;
    initializationAttempts.current.add(currentFlowKey);

    try {
      await initializeFlow();
      console.log('✅ Protected initialization completed for flow:', currentFlowKey);
    } catch (error) {
      console.error('❌ Protected initialization failed for flow:', currentFlowKey, error);
      // Remove from attempts on error to allow retry
      initializationAttempts.current.delete(currentFlowKey);
      throw error;
    } finally {
      isInitializingRef.current = false;
    }
  }, [initializeFlow, activeFlowId, flowId]);

  // Reset initialization attempts when flowId changes
  React.useEffect(() => {
    const currentFlowKey = activeFlowId || flowId || 'new-flow';
    // Clear attempts for different flows, but keep current one
    const newAttempts = new Set<string>();
    if (initializationAttempts.current.has(currentFlowKey)) {
      newAttempts.add(currentFlowKey);
    }
    initializationAttempts.current = newAttempts;
  }, [activeFlowId, flowId]);

  // Asset-Agnostic: No longer require application selection
  // Collection can work with ANY asset type, not just applications
  useEffect(() => {
    if (isLoadingFlow || !currentCollectionFlow || !activeFlowId) return;

    // Log the flow state but don't redirect - asset-agnostic collection
    console.log(
      "📊 Asset-agnostic collection flow initialized",
      {
        flowId: activeFlowId,
        phase: currentCollectionFlow.current_phase,
        progress: currentCollectionFlow.progress,
      },
    );
  }, [
    currentCollectionFlow,
    isLoadingFlow,
    activeFlowId,
  ]);

  // Reset the hasJustDeleted flag after auto-initialization triggers
  React.useEffect(() => {
    if (hasJustDeleted && !hasBlockingFlows && !checkingFlows) {
      // Give a small delay to ensure state updates have propagated
      const timer = setTimeout(() => {
        setHasJustDeleted(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [hasJustDeleted, hasBlockingFlows, checkingFlows]);

  // MODULARIZED: Use window focus refetch hook
  useWindowFocusRefetch({
    activeFlowId,
    isLoadingFlow,
    refetchCollectionFlow,
    enabled: true,
  });

  // Refetch collection flow data when flowId changes or when we first get an activeFlowId
  // This handles navigation back from application selection page
  useEffect(() => {
    if (activeFlowId && activeFlowId === flowId) {
      console.log(
        "🔄 Flow ID matched - refetching collection flow data for latest application status",
        { activeFlowId, flowId },
      );
      refetchCollectionFlow();
    }
  }, [activeFlowId, flowId, refetchCollectionFlow]);

  // Debug hook state
  console.log('🎯 useAdaptiveFormFlow state:', {
    hasFormData: !!formData,
    isLoading,
    error: error?.message,
    activeFlowId,
  });

  // MODULARIZED: Use extracted flow navigation hook
  const flowNavigation = useFlowNavigation({ activeFlowId });

  // Flow management handlers for incomplete flows
  const handleContinueFlow = flowNavigation.handleContinueFlow;

  const handleDeleteFlow = async (flowId: string): void => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }

    // Find the flow data from blockingFlows to pass to deletion modal
    const flowToDelete = blockingFlows.find(f =>
      String(f.flow_id || f.id) === String(flowId)
    );

    // Request deletion with modal confirmation, passing flow data for display
    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'manual',
      user?.id,
      flowToDelete // Pass flow data to avoid "Unknown Flow" in modal
    );
  };

  const handleViewFlowDetails = flowNavigation.handleViewFlowDetails;

  const handleManageFlows = (): void => {
    setShowManageFlowsModal(true);
  };

  // MODULARIZED: Use extracted progress calculation hook
  const progressMilestones = useProgressCalculation(formData, formValues);

  // Show loading state while checking for incomplete flows
  if (checkingFlows) {
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Initializing collection workflow"
        isLoading={true}
        loadingMessage="Checking for existing collection flows..."
        loadingSubMessage="Validating workflow state"
      >
        {/* Loading content handled by layout */}
      </CollectionPageLayout>
    );
  }

  // Show blocker only if there are other incomplete flows AND we're not continuing a specific flow
  // NEVER block if we have a flowId - we're continuing an existing flow
  if (hasBlockingFlows && !flowId && !skipIncompleteCheck) {
    return (
      <FlowBlockerDisplay
        blockingFlows={blockingFlows}
        incompleteFlows={incompleteFlows}
        deletionState={deletionState}
        showManageFlowsModal={showManageFlowsModal}
        isDeleting={isDeleting}
        onContinueFlow={handleContinueFlow}
        onDeleteFlow={handleDeleteFlow}
        onBatchDelete={(flowIds: string[]) => flowIds.forEach(handleDeleteFlow)}
        onViewDetails={handleViewFlowDetails}
        onManageFlows={handleManageFlows}
        onRefresh={refetchFlows}
        onManageFlowsModalChange={setShowManageFlowsModal}
        onDeletionConfirm={async () => {
          // Hide candidates only after user confirms
          setDeletingFlows((prev) => {
            const next = new Set(prev);
            deletionState.candidates.forEach((candidate) => {
              const normalizedId = String(candidate.flowId || '');
              next.add(normalizedId);
            });
            return next;
          });
          await deletionActions.confirmDeletion();
        }}
        onDeletionCancel={() => {
          deletionActions.cancelDeletion();
        }}
      />
    );
  }

  // Show loading state while form data is being generated OR while we're still loading the form
  // IMPORTANT: We should wait until both formData AND the initial loading is complete
  // This prevents showing empty forms that get populated later
  // If we have a flowId, always show loading/initialization state (never block)
  if ((!formData || isLoading) && (!hasBlockingFlows || flowId)) {
    return (
      <LoadingStateDisplay
        completionStatus={completionStatus}
        statusLine={statusLine}
        error={error}
        isLoading={isLoading}
        isPolling={isPollingActive}
        flowId={flowId}
        onRetry={() => protectedInitializeFlow()}
        onRefresh={() => window.location.reload()}
        onInitialize={() => protectedInitializeFlow()}
      />
    );
  }

  // Show completion state when form submission is complete
  if (isCompleted) {
    return (
      <CompletionDisplay
        onContinueToDiscovery={flowNavigation.handleContinueToDiscovery}
        onViewCollectionOverview={flowNavigation.handleViewCollectionOverview}
        onStartNewCollection={flowNavigation.handleStartNewCollection}
      />
    );
  }

  // Handle inline application selection for 422 errors
  const handleAppSelectionComplete = () => {
    setShowInlineAppSelection(false);
    // Re-initialize the flow after app selection
    protectedInitializeFlow();
  };

  const handleAppSelectionCancel = () => {
    setShowInlineAppSelection(false);
  };

  // Show inline application selection UI if needed
  if (showInlineAppSelection && activeFlowId) {
    return (
      <CollectionPageLayout
        title="Application Selection Required"
        description="Select applications for data collection"
      >
        <ApplicationSelectionUI
          flowId={activeFlowId}
          onComplete={handleAppSelectionComplete}
          onCancel={handleAppSelectionCancel}
        />
      </CollectionPageLayout>
    );
  }

  // Main component render
  return (
    <CollectionPageLayout
      title="Adaptive Data Collection"
      description={
        applicationId
          ? `Collecting data for application ${applicationId}`
          : "Asset-agnostic data collection"
      }
    >
      {isFallbackQuestionnaire && activeFlowId && (
        <QuestionnaireReloadButton
          flowId={activeFlowId}
          onQuestionnaireReady={handleQuestionnaireReady}
          className="mb-6"
        />
      )}

      {/* PR#790: Bulk Operations Action Bar */}
      {activeFlowId && (
        <div className="mb-6 flex gap-3" data-testid="bulk-operations-bar">
          <button
            onClick={() => setShowBulkAnswerModal(true)}
            data-testid="bulk-answer-button"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
          >
            Bulk Answer
          </button>
          <button
            onClick={() => setShowBulkImportWizard(true)}
            data-testid="bulk-import-button"
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition"
          >
            Bulk Import
          </button>
        </div>
      )}

      {/* MODULARIZED: Use QuestionnaireDisplay component */}
      <QuestionnaireDisplay
        formData={formData}
        formValues={formValues}
        validation={validation}
        milestones={progressMilestones}
        isSaving={isSaving}
        isSubmitting={isLoading}
        completionStatus={completionStatus}
        assetGroups={assetGroups}
        selectedAssetId={selectedAssetId}
        isLoading={isLoading}
        onFieldChange={handleFieldChange}
        onValidationChange={handleValidationChange}
        onSave={directSaveHandler || handleSave}
        onSubmit={directSubmitHandler || handleSubmit}
        onCancel={flowNavigation.handleCancelCollection}
        onAssetChange={setSelectedAssetId}
      />

      {/* MODULARIZED: Use AssetNavigationButtons component */}
      <AssetNavigationButtons
        assetGroups={assetGroups}
        canNavigatePrevious={canNavigatePrevious}
        canNavigateNext={canNavigateNext}
        isLoading={isLoading}
        isSaving={isSaving}
        onPreviousAsset={handlePreviousAsset}
        onNextAsset={handleNextAsset}
      />

      {/* MODULARIZED: Use FlowControlPanel component for all modals */}
      <FlowControlPanel
        showGenerationModal={showGenerationModal}
        activeFlowId={activeFlowId}
        onQuestionnaireReady={handleQuestionnaireReady}
        onQuestionnaireFallback={handleQuestionnaireFallback}
        onGenerationRetry={() => window.location.reload()}
        deletionState={deletionState}
        onDeletionConfirm={async () => {
          setDeletingFlows((prev) => {
            const next = new Set(prev);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
            deletionState.candidates.forEach((candidate: any) => {
              const normalizedId = String(candidate.flowId || '');
              next.add(normalizedId);
            });
            return next;
          });
          await deletionActions.confirmDeletion();
        }}
        onDeletionCancel={() => {
          deletionActions.cancelDeletion();
          setDeletingFlows((prev) => {
            const next = new Set(prev);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
            deletionState.candidates.forEach((candidate: any) => {
              const normalizedId = String(candidate.flowId || '');
              next.delete(normalizedId);
            });
            return next;
          });
        }}
        showManageFlowsModal={showManageFlowsModal}
        incompleteFlows={incompleteFlows}
        isDeleting={isDeleting}
        onManageFlowsChange={setShowManageFlowsModal}
        onContinueFlow={handleContinueFlow}
        onDeleteFlow={handleDeleteFlow}
        onBatchDelete={(flowIds: string[]) => flowIds.forEach(handleDeleteFlow)}
        onViewDetails={handleViewFlowDetails}
      />

      {/* PR#790: Bulk Operations Modals */}
      {activeFlowId && client?.id && engagement?.id && formData && (
        <>
          <BulkImportWizard
            flow_id={activeFlowId}
            import_type="application"
            is_open={showBulkImportWizard}
            on_close={() => setShowBulkImportWizard(false)}
            on_success={(rows_imported) => {
              toast({
                title: "Import Successful",
                description: `Successfully imported ${rows_imported} rows`
              });
              setShowBulkImportWizard(false);
              // Refresh the form data
              queryClient.invalidateQueries({ queryKey: ['collection-flow'] });
            }}
          />

          <MultiAssetAnswerModal
            flow_id={activeFlowId}
            questions={
              formData?.sections
                ? formData.sections.flatMap(section =>
                    section.fields.map(field => ({
                      question_id: field.id,
                      question_text: field.label,
                      question_type: field.fieldType === 'select' ? 'dropdown' :
                                    field.fieldType === 'multiselect' ? 'multi_select' : 'text',
                      answer_options: field.options,
                      section: section.title,
                      weight: field.metadata?.weight || 1,
                      is_required: field.validation?.required || false,
                      display_order: field.metadata?.display_order
                    }))
                  )
                : []
            }
            is_open={showBulkAnswerModal}
            on_close={() => setShowBulkAnswerModal(false)}
            on_success={(updated_count) => {
              toast({
                title: "Bulk Answer Successful",
                description: `Successfully updated ${updated_count} assets`
              });
              setShowBulkAnswerModal(false);
              queryClient.invalidateQueries({ queryKey: ['collection-flow'] });
            }}
          />
        </>
      )}
    </CollectionPageLayout>
  );
};

export default AdaptiveForms;
