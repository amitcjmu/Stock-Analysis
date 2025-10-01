import React from "react";
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useNavigate } from "react-router-dom";
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
  const queryClient = useQueryClient();
  const { client, engagement, user } = useAuth();

  // CRITICAL FIX: Ref guard to prevent duplicate initialization calls per flowId
  const initializationAttempts = React.useRef<Set<string>>(new Set());
  const isInitializingRef = React.useRef<boolean>(false);

  // Get application ID and flow ID from URL params
  const applicationId = searchParams.get("applicationId");
  const flowId = searchParams.get("flowId");

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
  const directSaveHandler = React.useCallback(() => {
    console.log('🟢 DIRECT SAVE HANDLER CALLED - Bypassing prop chain');
    if (typeof handleSave === 'function') {
      console.log('🟢 Calling handleSave from direct handler');
      handleSave();
    } else {
      console.error('❌ handleSave is not available in AdaptiveForms');
    }
  }, [handleSave]);

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

    // Request deletion with modal confirmation (no pre-hiding)
    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'manual',
      user?.id
    );
  };

  const handleViewFlowDetails = (flowId: string, phase: string): void => {
    navigate(`/collection/progress/${flowId}`);
  };

  const handleManageFlows = (): void => {
    navigate("/collection/overview");
  };

  // Mock progress milestones - in a real implementation these would be dynamic
  const progressMilestones: ProgressMilestone[] = [
    {
      id: "form-start",
      title: "Form Started",
      description: "Begin adaptive data collection",
      achieved: true,
      achievedAt: new Date().toISOString(),
      weight: 0.1,
      required: true,
    },
    {
      id: "basic-complete",
      title: "Basic Information",
      description: "Complete core application details",
      achieved: false,
      weight: 0.3,
      required: true,
    },
    {
      id: "technical-complete",
      title: "Technical Details",
      description: "Complete technical architecture information",
      achieved: false,
      weight: 0.4,
      required: true,
    },
    {
      id: "validation-passed",
      title: "Validation Passed",
      description: "All validation checks completed successfully",
      achieved: false,
      weight: 0.2,
      required: true,
    },
  ];

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
      <AdaptiveFormContainer
        formData={formData}
        formValues={formValues}
        validation={validation}
        milestones={progressMilestones}
        isSaving={isSaving}
        isSubmitting={isLoading}
        onFieldChange={handleFieldChange}
        onValidationChange={handleValidationChange}
        onSave={directSaveHandler || handleSave}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/collection")}
      />

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
    </CollectionPageLayout>
  );
};

export default AdaptiveForms;
