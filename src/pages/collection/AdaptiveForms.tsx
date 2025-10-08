import React from "react";
import { useState, useEffect } from "react";
import { useSearchParams, useParams, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "@/components/ui/use-toast";

// Import modular components
import CollectionPageLayout from "@/components/collection/layout/CollectionPageLayout";
import AdaptiveFormContainer from "@/components/collection/forms/AdaptiveFormContainer";
import { CollectionUploadBlocker } from "@/components/collection/CollectionUploadBlocker";
import { CollectionWorkflowError } from "@/components/collection/CollectionWorkflowError";
import { ApplicationSelectionUI } from "@/components/collection/ApplicationSelectionUI";
import { QuestionnaireGenerationModal } from "@/components/collection/QuestionnaireGenerationModal";
import { QuestionnaireReloadButton } from "@/components/collection/QuestionnaireReloadButton";
import { IncompleteCollectionFlowManager } from "@/components/collection/IncompleteCollectionFlowManager";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

// Import custom hooks
import { useAdaptiveFormFlow } from "@/hooks/collection/useAdaptiveFormFlow";
import {
  useIncompleteCollectionFlows,
  useCollectionFlowManagement,
} from "@/hooks/collection/useCollectionFlowManagement";
import { useFlowDeletion } from "@/hooks/useFlowDeletion";
import { useAuth } from "@/contexts/AuthContext";
import { useCollectionStatePolling } from "@/hooks/collection/useCollectionStatePolling";
import { useQuery } from "@tanstack/react-query";
import { apiCall } from "@/config/api";

// Import types
import type { ProgressMilestone } from "@/components/collection/types";
import { groupQuestionsByAsset } from "@/utils/questionnaireUtils";

// Define types for collection flow
interface CollectionFlowConfig {
  selected_application_ids?: string[];
  applications?: string[];
  application_ids?: string[];
  has_applications?: boolean;
}

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: CollectionFlowConfig;
}

interface QuestionnaireData {
  questions: Array<{
    id: string;
    text: string;
    type: string;
    options?: string[];
  }>;
  metadata?: Record<string, unknown>;
}

// Import UI components
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/constants/routes";
import { FlowDeletionModal } from "@/components/flows/FlowDeletionModal";

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
  const [showAppSelectionPrompt, setShowAppSelectionPrompt] = useState(false);
  const [showInlineAppSelection, setShowInlineAppSelection] = useState(false);
  const [hasRedirectedForApps, setHasRedirectedForApps] = useState(false);

  // State for questionnaire generation modal
  const [showGenerationModal, setShowGenerationModal] = useState(false);
  const [isFallbackQuestionnaire, setIsFallbackQuestionnaire] = useState(false);

  // State for manage flows modal
  const [showManageFlowsModal, setShowManageFlowsModal] = useState(false);

  // Show questionnaire generation modal when flow starts
  const handleQuestionnaireGeneration = React.useCallback(() => {
    setShowGenerationModal(true);
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

  // Check for incomplete flows that would block new collection processes
  // Skip checking if we're continuing a specific flow (flowId provided)
  const skipIncompleteCheck = !!flowId;
  const {
    data: incompleteFlows = [],
    isLoading: checkingFlows,
    refetch: refetchFlows,
  } = useIncompleteCollectionFlows(); // Always call the hook to maintain consistent hook order

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

  // Auto-show generation modal when completionStatus is "pending"
  // This must be AFTER useAdaptiveFormFlow hook since it uses completionStatus
  React.useEffect(() => {
    if (completionStatus === "pending" && activeFlowId) {
      setShowGenerationModal(true);
    } else if (completionStatus === "ready" || completionStatus === "fallback") {
      setShowGenerationModal(false);
    }
  }, [completionStatus, activeFlowId]);

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
  }, [assetGroups]);

  // Filter form data to show only selected asset's questions
  const filteredFormData = React.useMemo(() => {
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

  // Asset navigation handlers - MUST be after assetGroups is defined
  const handlePreviousAsset = React.useCallback(() => {
    if (assetGroups.length === 0 || !selectedAssetId) return;

    const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
    if (currentIndex > 0) {
      setSelectedAssetId(assetGroups[currentIndex - 1].asset_id);
      // Scroll to top of form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [assetGroups, selectedAssetId]);

  const handleNextAsset = React.useCallback(() => {
    if (assetGroups.length === 0 || !selectedAssetId) return;

    const currentIndex = assetGroups.findIndex(g => g.asset_id === selectedAssetId);
    if (currentIndex < assetGroups.length - 1) {
      setSelectedAssetId(assetGroups[currentIndex + 1].asset_id);
      // Scroll to top of form
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [assetGroups, selectedAssetId]);

  const currentAssetIndex = React.useMemo(() => {
    if (!selectedAssetId) return -1;
    return assetGroups.findIndex(g => g.asset_id === selectedAssetId);
  }, [assetGroups, selectedAssetId]);

  const canNavigatePrevious = currentAssetIndex > 0;
  const canNavigateNext = currentAssetIndex >= 0 && currentAssetIndex < assetGroups.length - 1;

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

    // For multi-asset forms, temporarily add asset_id to formValues
    if (assetGroups.length > 1 && selectedAssetId && handleFieldChange) {
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
  }, [handleSave, assetGroups.length, selectedAssetId, handleFieldChange]);

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
        // Applications are optional, not required
        hasApplications: hasApplicationsSelected(currentCollectionFlow),
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

  // Add window focus listener to refetch collection flow data when returning from application selection
  // This ensures we have the latest application selection status when users navigate back
  useEffect(() => {
    const handleWindowFocus = async () => {
      if (activeFlowId && !isLoadingFlow) {
        console.log(
          "🔄 Window focused - refetching collection flow data to check for application updates",
        );
        await refetchCollectionFlow();
      }
    };

    window.addEventListener("focus", handleWindowFocus);
    return () => {
      window.removeEventListener("focus", handleWindowFocus);
    };
  }, [activeFlowId, isLoadingFlow, refetchCollectionFlow]);

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

  // No longer need to check for 'no_applications_selected' error
  // The backend now returns a bootstrap questionnaire instead

  // Function to detect if applications are selected in the collection flow
  const hasApplicationsSelected = (collectionFlow: CollectionFlow | null): boolean => {
    if (!collectionFlow) return false;

    // Check collection_config for selected applications
    const config = collectionFlow.collection_config || {};
    const selectedApps =
      config.selected_application_ids ||
      config.applications ||
      config.application_ids ||
      [];

    // Check if applications are selected
    const hasApps = Array.isArray(selectedApps) && selectedApps.length > 0;

    // Also check if has_applications flag is set in config
    const hasAppsFlag = config.has_applications === true;

    // Return true if applications are selected either way
    return hasApps || hasAppsFlag;
  };

  // Debug hook state
  console.log('🎯 useAdaptiveFormFlow state:', {
    hasFormData: !!formData,
    isLoading,
    error: error?.message,
    activeFlowId,
  });

  // Flow management handlers for incomplete flows
  const handleContinueFlow = async (flowId: string): void => {
    try {
      if (!flowId) {
        console.error("Cannot continue flow: flowId is missing");
        return;
      }
      // Navigate to adaptive forms page with flowId to resume the flow
      navigate(`/collection/adaptive-forms?flowId=${encodeURIComponent(flowId)}`);
    } catch (error) {
      console.error("Failed to continue collection flow:", error);
    }
  };

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

  const handleViewFlowDetails = (flowId: string, phase: string): void => {
    navigate(`/collection/progress/${flowId}`);
  };

  const handleManageFlows = (): void => {
    setShowManageFlowsModal(true);
  };

  // Generate progress milestones dynamically from actual form sections
  const progressMilestones: ProgressMilestone[] = React.useMemo(() => {
    if (!formData?.sections) return [];

    const milestones: ProgressMilestone[] = [
      {
        id: "form-start",
        title: "Form Started",
        description: "Begin adaptive data collection",
        achieved: true,
        achievedAt: new Date().toISOString(),
        weight: 0.1,
        required: true,
      },
    ];

    // Add milestone for each form section
    formData.sections.forEach((section, index) => {
      // Calculate if section is completed based on formValues
      const sectionFields = section.fields.map(f => f.id);
      const completedFields = sectionFields.filter(fieldId => {
        const value = formValues?.[fieldId];
        return value !== null && value !== undefined && value !== '';
      });
      const isCompleted = section.requiredFieldsCount > 0
        ? completedFields.length >= section.requiredFieldsCount
        : completedFields.length === sectionFields.length;

      milestones.push({
        id: section.id,
        title: section.title,
        description: section.description || `Complete ${section.title.toLowerCase()}`,
        achieved: isCompleted,
        achievedAt: isCompleted ? new Date().toISOString() : undefined,
        weight: section.completionWeight,
        required: section.requiredFieldsCount > 0,
      });
    });

    return milestones;
  }, [formData, formValues]);

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

  // Asset-Agnostic: Removed application selection prompt
  // Collection now works with ANY asset type, not requiring application selection
  // The system will automatically pull in relevant assets based on the data gaps identified

  // Show blocker only if there are other incomplete flows AND we're not continuing a specific flow
  // NEVER block if we have a flowId - we're continuing an existing flow
  if (hasBlockingFlows && !flowId && !skipIncompleteCheck) {
    return (
      <>
        <CollectionPageLayout
          title="Adaptive Data Collection"
          description="Collection workflow blocked - manage existing flows"
        >
          <CollectionUploadBlocker
            incompleteFlows={blockingFlows}
            onContinueFlow={handleContinueFlow}
            onDeleteFlow={handleDeleteFlow}
            onViewDetails={handleViewFlowDetails}
            onManageFlows={handleManageFlows}
            onRefresh={refetchFlows}
            isLoading={isDeleting}
          />
        </CollectionPageLayout>

        {/* Flow Deletion Modal - must be available even when blocking */}
        <FlowDeletionModal
          open={deletionState.isModalOpen}
          candidates={deletionState.candidates}
          deletionSource={deletionState.deletionSource}
          isDeleting={deletionState.isDeleting}
          onConfirm={async () => {
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
          onCancel={() => {
            deletionActions.cancelDeletion();
          }}
        />

        {/* Manage Flows Modal - must be available even when blocking */}
        <Dialog open={showManageFlowsModal} onOpenChange={setShowManageFlowsModal}>
          <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Manage Collection Flows</DialogTitle>
              <DialogDescription>
                Manage and resume incomplete collection flows. Complete existing flows before starting new ones.
              </DialogDescription>
            </DialogHeader>
            <IncompleteCollectionFlowManager
              flows={incompleteFlows}
              onContinueFlow={handleContinueFlow}
              onDeleteFlow={handleDeleteFlow}
              onBatchDelete={(flowIds: string[]) => {
                // Handle batch deletion
                flowIds.forEach(flowId => handleDeleteFlow(flowId));
              }}
              onViewDetails={handleViewFlowDetails}
              isLoading={isDeleting}
            />
          </DialogContent>
        </Dialog>
      </>
    );
  }

  // Show loading state while form data is being generated OR while we're still loading the form
  // IMPORTANT: We should wait until both formData AND the initial loading is complete
  // This prevents showing empty forms that get populated later
  // If we have a flowId, always show loading/initialization state (never block)
  if ((!formData || isLoading) && (!hasBlockingFlows || flowId)) {
    // Check if there's an error
    if (error && !isLoading) {
      return (
        <CollectionPageLayout
          title="Adaptive Data Collection"
          description="Error initializing collection form"
        >
          <CollectionWorkflowError
            error={error}
            flowId={activeFlowId}
            isPollingActive={isPollingActive}
            onRetry={() => protectedInitializeFlow()}
            onRefresh={() => window.location.reload()}
          />
        </CollectionPageLayout>
      );
    }

    // Handle questionnaire generation states based on completion_status
    if (completionStatus) {
      switch (completionStatus) {
        case 'pending':
          return (
            <CollectionPageLayout
              title="Adaptive Data Collection"
              description="Generating intelligent questionnaire..."
              isLoading={true}
              loadingMessage={statusLine || "Our AI agents are analyzing your environment to generate a tailored questionnaire..."}
              loadingSubMessage="This typically takes 30-60 seconds. Please wait while we create questions specific to your needs."
            >
              <div className="flex flex-col items-center space-y-4 mt-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <div className="text-center max-w-md">
                  <p className="text-sm text-gray-600">
                    AI agents are reviewing your selected assets and generating contextual questions...
                  </p>
                  {isPolling && (
                    <p className="text-xs text-blue-600 mt-2">
                      Status updates every 5 seconds
                    </p>
                  )}
                </div>
              </div>
            </CollectionPageLayout>
          );

        case 'failed':
          return (
            <CollectionPageLayout
              title="Adaptive Data Collection"
              description="Questionnaire generation failed"
            >
              <div className="flex flex-col items-center space-y-6 mt-8">
                <div className="text-center">
                  <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                    <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-2.186-.833-2.956 0L3.857 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Questionnaire Generation Failed
                  </h3>
                  <p className="text-gray-600 mb-4">
                    {statusLine || "Unable to generate the adaptive questionnaire. This may be due to a temporary issue with our AI agents."}
                  </p>
                </div>
                <div className="flex space-x-4">
                  <Button onClick={() => protectedInitializeFlow()} size="lg">
                    Retry Generation
                  </Button>
                  <Button variant="outline" onClick={() => window.location.reload()}>
                    Refresh Page
                  </Button>
                </div>
              </div>
            </CollectionPageLayout>
          );

        case 'fallback':
          // For fallback, we still want to show the form but with an info message
          // Continue to regular loading state but add a notification
          break;

        case 'ready':
          // Questionnaire is ready, continue to normal loading/form display
          break;
      }
    }

    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Loading collection form and saved data..."
        isLoading={isLoading || !formData}
        loadingMessage={
          isLoading
            ? "Loading form structure and saved responses..."
            : "Preparing collection form..."
        }
        loadingSubMessage={
          isLoading
            ? `Please wait while we load your saved data${isPollingActive ? " (Real-time updates active)" : ""}`
            : "Initializing workflow"
        }
      >
        {completionStatus === 'fallback' && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-amber-800">
                  Using Standard Questionnaire
                </h3>
                <div className="mt-2 text-sm text-amber-700">
                  <p>
                    {statusLine || "Our AI-generated questionnaire is not available. We're using a comprehensive standard questionnaire to ensure all important data is collected."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        {!isLoading && !formData && (
          <div className="flex flex-col items-center space-y-4 mt-8">
            <div className="text-center">
              <p className="text-gray-600 mb-4">
                The collection form is not loading automatically.
                Click the button below to start the flow manually.
              </p>
            </div>
            <Button onClick={() => protectedInitializeFlow()} size="lg">
              Start Collection Flow
            </Button>
            <p className="text-sm text-gray-500">
              Flow ID: {flowId || 'Not provided'}
            </p>
          </div>
        )}
      </CollectionPageLayout>
    );
  }

  // Show completion state when form submission is complete
  if (isCompleted) {
    const handleContinueToDiscovery = () => {
      navigate(`/discovery?flowId=${activeFlowId}`);
    };

    const handleViewCollectionOverview = () => {
      navigate("/collection/overview");
    };

    const handleStartNewCollection = () => {
      navigate("/collection");
    };

    return (
      <CollectionPageLayout
        title="Collection Complete"
        description="Your application data has been successfully collected"
      >
        <div className="max-w-3xl mx-auto mt-8">
          <div className="bg-green-50 border border-green-200 rounded-lg p-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <svg
                  className="h-8 w-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>

              <h3 className="text-2xl font-bold text-green-900 mb-2">
                Collection Complete!
              </h3>

              <p className="text-green-700 mb-6">
                Your application data has been successfully collected and processed by our AI agents.
                The information will be used to generate personalized migration recommendations.
              </p>

              <div className="bg-white rounded-lg p-6 mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">What happens next?</h4>
                <ul className="text-left text-gray-700 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>Our AI agents will analyze your application data</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>Discovery phase will identify migration patterns and dependencies</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>Personalized migration recommendations will be generated</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>You'll receive a detailed migration strategy report</span>
                  </li>
                </ul>
              </div>

              <div className="space-y-3">
                <Button
                  onClick={handleContinueToDiscovery}
                  size="lg"
                  className="w-full"
                >
                  Continue to Discovery Phase
                </Button>

                <div className="flex gap-3">
                  <Button
                    onClick={handleViewCollectionOverview}
                    variant="outline"
                    className="flex-1"
                  >
                    View Collection Overview
                  </Button>

                  <Button
                    onClick={handleStartNewCollection}
                    variant="outline"
                    className="flex-1"
                  >
                    Start New Collection
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CollectionPageLayout>
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
                onChange={(e) => setSelectedAssetId(e.target.value)}
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
        milestones={progressMilestones}
        isSaving={isSaving}
        isSubmitting={isLoading}
        completionStatus={completionStatus}
        onFieldChange={handleFieldChange}
        onValidationChange={handleValidationChange}
        onSave={directSaveHandler || handleSave}
        onSubmit={directSubmitHandler || handleSubmit}
        onCancel={() => navigate("/collection")}
      />

      {/* Asset Navigation Buttons - Show when multiple assets */}
      {assetGroups.length > 1 && (
        <div className="mt-6 flex items-center justify-between p-4 border-t">
          <button
            onClick={handlePreviousAsset}
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
              {assetGroups.filter(g => g.completion_percentage === 100).length} of {assetGroups.length} Assets Complete
            </span>
          </div>

          <button
            onClick={handleNextAsset}
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
      )}

      {/* Flow Deletion Modal */}
      <FlowDeletionModal
        open={deletionState.isModalOpen}
        candidates={deletionState.candidates}
        deletionSource={deletionState.deletionSource}
        isDeleting={deletionState.isDeleting}
        onConfirm={async () => {
          // Hide candidates only after user confirms
          setDeletingFlows((prev) => {
            const next = new Set(prev);
            deletionState.candidates.forEach((id) => {
              const normalizedId = String(id || ''); // Normalize to string
              next.add(normalizedId);
            });
            return next;
          });
          await deletionActions.confirmDeletion();
        }}
        onCancel={() => {
          deletionActions.cancelDeletion();
          // Ensure items reappear if user cancels
          setDeletingFlows((prev) => {
            const next = new Set(prev);
            deletionState.candidates.forEach((id) => {
              const normalizedId = String(id || ''); // Normalize to string
              next.delete(normalizedId);
            });
            return next;
          });
        }}
      />

      {/* Questionnaire Generation Modal */}
      <QuestionnaireGenerationModal
        isOpen={showGenerationModal}
        flowId={activeFlowId}
        onComplete={handleQuestionnaireReady}
        onFallback={handleQuestionnaireFallback}
        onRetry={() => {
          // Check for questionnaire again
          window.location.reload();
        }}
      />

      {/* Manage Flows Modal */}
      <Dialog open={showManageFlowsModal} onOpenChange={setShowManageFlowsModal}>
        <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Collection Flows</DialogTitle>
            <DialogDescription>
              Manage and resume incomplete collection flows. Complete existing flows before starting new ones.
            </DialogDescription>
          </DialogHeader>
          <IncompleteCollectionFlowManager
            flows={incompleteFlows}
            onContinueFlow={handleContinueFlow}
            onDeleteFlow={handleDeleteFlow}
            onBatchDelete={(flowIds: string[]) => {
              // Handle batch deletion
              flowIds.forEach(flowId => handleDeleteFlow(flowId));
            }}
            onViewDetails={handleViewFlowDetails}
            isLoading={isDeleting}
          />
        </DialogContent>
      </Dialog>
    </CollectionPageLayout>
  );
};

export default AdaptiveForms;
