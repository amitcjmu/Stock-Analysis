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

// Import custom hooks
import { useAdaptiveFormFlow } from "@/hooks/collection/useAdaptiveFormFlow";
import {
  useIncompleteCollectionFlows,
  useCollectionFlowManagement,
} from "@/hooks/collection/useCollectionFlowManagement";
import { useCollectionWorkflowWebSocket } from "@/hooks/collection/useCollectionWorkflowWebSocket";
import { useQuery } from "@tanstack/react-query";
import { apiCall } from "@/config/api";

// Import types
import type { ProgressMilestone } from "@/components/collection/types";

// Import UI components
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/constants/routes";

/**
 * Adaptive Forms collection page
 * Refactored to use modular components and custom hooks for better maintainability
 */
const AdaptiveForms: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  // Get application ID and flow ID from URL params
  const applicationId = searchParams.get("applicationId");
  const flowId = searchParams.get("flowId");

  // State to track flows being deleted
  const [deletingFlows, setDeletingFlows] = useState<Set<string>>(new Set());
  const [hasJustDeleted, setHasJustDeleted] = useState(false);

  // State to show app selection prompt when no applications are selected
  const [showAppSelectionPrompt, setShowAppSelectionPrompt] = useState(false);

  // Function to detect if applications are selected in the collection flow
  const hasApplicationsSelected = (collectionFlow: any): boolean => {
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

  // Check for incomplete flows that would block new collection processes
  const {
    data: incompleteFlows = [],
    isLoading: checkingFlows,
    refetch: refetchFlows,
  } = useIncompleteCollectionFlows();

  // Filter out the current flow and flows being deleted from the blocking check
  const blockingFlows = incompleteFlows.filter((flow) => {
    const id = flow.flow_id || flow.id;
    return id !== flowId && !deletingFlows.has(id);
  });

  const hasBlockingFlows = blockingFlows.length > 0;

  // Use collection flow management hook for flow operations
  const { deleteFlow, isDeleting } = useCollectionFlowManagement();

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
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow,
  } = useAdaptiveFormFlow({
    applicationId,
    flowId,
    autoInitialize: !checkingFlows && (!hasBlockingFlows || hasJustDeleted),
  });

  // Use WebSocket for real-time updates during workflow initialization
  const { isWebSocketActive, requestStatusUpdate } =
    useCollectionWorkflowWebSocket({
      flowId: activeFlowId,
      enabled: !!activeFlowId && isLoading,
      onQuestionnaireReady: (event) => {
        console.log(
          "🎉 WebSocket: Questionnaire ready, triggering re-initialization",
        );
        // Trigger a re-fetch when questionnaire is ready
        if (!formData) {
          initializeFlow();
        }
      },
      onWorkflowUpdate: (event) => {
        console.log("📊 WebSocket: Workflow status update:", event.data);
        // Request status update for more details
        if (
          event.data.status === "completed" ||
          event.data.phase === "questionnaire_generation"
        ) {
          requestStatusUpdate();
        }
      },
      onError: (error) => {
        console.error("❌ WebSocket: Collection workflow error:", error);
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
    // Set cache time to 30 seconds to reduce stale data issues
    staleTime: 30 * 1000,
    // Refetch on window focus to catch updates from application selection
    refetchOnWindowFocus: true,
  });

  // Detect if we need to redirect to application selection
  useEffect(() => {
    if (isLoadingFlow || !currentCollectionFlow || !activeFlowId) return;

    const hasApps = hasApplicationsSelected(currentCollectionFlow);

    // Only redirect for NEW flows (not existing ones being continued)
    // Check if this is a continuation of an existing flow by looking for flowId in URL
    const isExistingFlowContinuation = flowId !== null && flowId !== undefined;

    // Also check if the flow has already progressed beyond initial state
    const hasProgressed =
      currentCollectionFlow.progress > 0 ||
      currentCollectionFlow.current_phase !== "initialization";

    if (!hasApps && !isExistingFlowContinuation && !hasProgressed) {
      // For NEW flows without apps, redirect to application selection
      console.log(
        "🔄 New collection flow has no applications selected, redirecting to application selection",
        {
          flowId: activeFlowId,
        },
      );

      navigate(`/collection/select-applications?flowId=${activeFlowId}`);
      return;
    } else if (!hasApps && (isExistingFlowContinuation || hasProgressed)) {
      // For existing flows without apps, show a warning but don't redirect
      console.log(
        "⚠️ Existing collection flow has no applications selected, but not redirecting to avoid loop",
        {
          flowId: activeFlowId,
          isExistingFlowContinuation,
          hasProgressed,
        },
      );

      // Show app selection prompt to give users a path forward
      setShowAppSelectionPrompt(true);

      // Show a warning toast
      toast({
        title: "No Applications Selected",
        description:
          "This collection flow does not have any applications selected. You may need to restart the flow.",
        variant: "destructive",
        duration: 7000,
      });
    }
  }, [
    currentCollectionFlow,
    isLoadingFlow,
    activeFlowId,
    flowId,
    navigate,
    toast,
  ]);

  // Flow management handlers for incomplete flows
  const handleContinueFlow = async (flowId: string): void => {
    try {
      // Navigate to appropriate collection phase
      navigate(`/collection/progress/${flowId}`);
    } catch (error) {
      console.error("Failed to continue collection flow:", error);
    }
  };

  const handleDeleteFlow = async (flowId: string): void => {
    // Mark this flow as being deleted to hide it from UI immediately
    setDeletingFlows((prev) => new Set(prev).add(flowId));

    try {
      // Force delete the flow since it's stuck
      await deleteFlow(flowId, true);

      // Wait a bit for backend to process
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Manually invalidate and refetch the specific query
      await queryClient.invalidateQueries({
        queryKey: ["collection-flows", "incomplete"],
        exact: true,
      });

      // Also refetch to ensure UI updates
      await refetchFlows();

      // Mark that we just deleted a flow to trigger re-initialization
      setHasJustDeleted(true);
    } catch (error: unknown) {
      console.error("Failed to delete collection flow:", error);

      // If deletion failed, remove from deleting set to show it again
      setDeletingFlows((prev) => {
        const newSet = new Set(prev);
        newSet.delete(flowId);
        return newSet;
      });

      // Show error toast if it's not a 404 (which means it was already deleted)
      if (error?.status !== 404) {
        toast({
          title: "Delete Failed",
          description: error?.message || "Failed to delete collection flow",
          variant: "destructive",
        });
      }
    }
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

  // Show app selection prompt if no applications are selected for the current flow
  if (showAppSelectionPrompt && activeFlowId) {
    const handleGoToAppSelection = () => {
      navigate(
        `${ROUTES.COLLECTION.SELECT_APPLICATIONS}?flowId=${activeFlowId}`,
      );
    };

    const handleRestartFlow = () => {
      // Clear the current flow and start fresh
      navigate("/collection");
      setShowAppSelectionPrompt(false);
    };

    return (
      <CollectionPageLayout
        title="Application Selection Required"
        description="This collection flow needs applications to proceed"
      >
        <div className="max-w-2xl mx-auto mt-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">
              No Applications Selected
            </h3>
            <p className="text-yellow-700 mb-4">
              This collection flow does not have any applications selected. You
              need to select applications before proceeding with data
              collection.
            </p>

            <div className="space-y-3">
              <Button
                onClick={handleGoToAppSelection}
                variant="default"
                className="w-full"
              >
                Select Applications for This Flow
              </Button>

              <Button
                onClick={handleRestartFlow}
                variant="outline"
                className="w-full"
              >
                Start New Collection Flow
              </Button>

              <Button
                onClick={() => navigate("/collection/overview")}
                variant="outline"
                className="w-full"
              >
                View All Collection Flows
              </Button>
            </div>
          </div>
        </div>
      </CollectionPageLayout>
    );
  }

  // Show blocker if there are other incomplete flows (not including current one)
  if (hasBlockingFlows) {
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

  // Show loading state while form data is being generated
  if (!formData && !hasBlockingFlows) {
    // Check if there's an error
    if (error) {
      return (
        <CollectionPageLayout
          title="Adaptive Data Collection"
          description="Error initializing collection form"
        >
          <CollectionWorkflowError
            error={error}
            flowId={activeFlowId}
            isWebSocketActive={isWebSocketActive}
            onRetry={() => initializeFlow()}
            onRefresh={() => window.location.reload()}
          />
        </CollectionPageLayout>
      );
    }

    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Generating personalized collection form"
        isLoading={isLoading}
        loadingMessage={
          isLoading
            ? "CrewAI agents are analyzing your requirements..."
            : "Preparing collection form..."
        }
        loadingSubMessage={
          isLoading
            ? `Generating adaptive questionnaire based on your specific needs${isWebSocketActive ? " (Real-time updates active)" : " (Polling for updates)"}`
            : "Initializing workflow"
        }
      >
        {!isLoading && (
          <div className="flex justify-center mt-8">
            <Button onClick={() => initializeFlow()} size="lg">
              Start Collection Flow
            </Button>
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

  // Main component render
  return (
    <CollectionPageLayout
      title="Adaptive Data Collection"
      description={
        applicationId
          ? `Collecting data for application ${applicationId}`
          : "New application data collection"
      }
    >
      <AdaptiveFormContainer
        formData={formData}
        formValues={formValues}
        validation={validation}
        milestones={progressMilestones}
        isSaving={isSaving}
        isSubmitting={isLoading}
        onFieldChange={handleFieldChange}
        onValidationChange={handleValidationChange}
        onSave={handleSave}
        onSubmit={handleSubmit}
        onCancel={() => navigate("/collection")}
      />
    </CollectionPageLayout>
  );
};

export default AdaptiveForms;
