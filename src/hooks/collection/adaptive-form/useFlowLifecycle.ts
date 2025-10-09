/**
 * Flow lifecycle management for adaptive form flow
 * Handles initialization, flow creation, and questionnaire loading
 *
 * PRESERVED FROM ORIGINAL: Lines 429-1110 of useAdaptiveFormFlow.ts (initializeFlow function)
 * This is the largest and most complex part of the original hook
 */

import { useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import { collectionFlowApi } from "@/services/api/collection-flow";
import {
  convertQuestionnairesToFormData,
  validateFormDataStructure,
  createFallbackFormData,
} from "@/utils/collection/formDataTransformation";
import type { AdaptiveFormFlowState, CollectionQuestionnaire } from "./types";
import type { CollectionFormData } from "@/components/collection/types";
import { extractExistingResponses } from "./types";
import { canCreateCollectionFlow } from "@/utils/rbac";
import type { User } from "@/contexts/AuthContext";
import type { UsePollingReturn } from "./usePolling";
import type { CollectionFlowResponse, CollectionFlowStatusResponse } from "@/services/api/collection-flow";

export interface BlockingFlow {
  id: string;
  status: string;
  created_at?: string;
  engagement_id?: string;
  client_account_id?: string;
}

export interface CurrentFlow {
  id: string;
  name: string;
  type: string;
  status: string;
  engagement_id: string;
}

export interface UseFlowLifecycleProps {
  state: AdaptiveFormFlowState;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
  urlFlowId: string | null;
  applicationId?: string | null;
  skipIncompleteCheck: boolean;
  checkingFlows: boolean;
  hasBlockingFlows: boolean;
  blockingFlows: BlockingFlow[];
  user: User | null;
  setCurrentFlow: (flow: CurrentFlow) => void;
  updateFlowId: (flowId: string | null) => void;
  onQuestionnaireGenerationStart?: () => void;
  polling: UsePollingReturn;
}

export interface UseFlowLifecycleReturn {
  initializeFlow: () => Promise<void>;
}

/**
 * Flow lifecycle hook - manages complex initialization logic
 * CRITICAL: This is the heart of the adaptive form flow - handles all initialization scenarios
 */
export function useFlowLifecycle({
  state,
  setState,
  urlFlowId,
  applicationId,
  skipIncompleteCheck,
  checkingFlows,
  hasBlockingFlows,
  blockingFlows,
  user,
  setCurrentFlow,
  updateFlowId,
  onQuestionnaireGenerationStart,
  polling,
}: UseFlowLifecycleProps): UseFlowLifecycleReturn {
  const { toast } = useToast();

  /**
   * Initialize the adaptive collection flow
   * PRESERVED FROM ORIGINAL: Lines 429-1110
   *
   * CRITICAL PATTERNS PRESERVED:
   * 1. Multi-tenant scoping (client_account_id, engagement_id)
   * 2. Existing flow detection and continuation
   * 3. HTTP polling for questionnaire generation
   * 4. Fallback form data on timeout
   * 5. Assessment-ready flow transition
   */
  const initializeFlow = useCallback(async (): Promise<void> => {
    // Don't initialize if there are blocking flows or still checking (but allow if continuing a specific flow)
    if (!skipIncompleteCheck && (checkingFlows || hasBlockingFlows)) {
      console.log(
        "🛑 Blocking flow initialization due to other incomplete flows or still checking",
        {
          checkingFlows,
          hasBlockingFlows,
          blockingFlowsCount: blockingFlows.length,
          skipIncompleteCheck,
        },
      );
      return;
    }

    // Prevent multiple simultaneous initializations
    if (state.isLoading) {
      console.log("⚠️ Flow initialization already in progress, skipping...");
      return;
    }

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    // Declare hasExistingData at the function scope
    let hasExistingData = false;

    try {
      let flowResponse: CollectionFlowResponse;

      // Check if we have a flow ID from the URL (created from overview page)
      if (urlFlowId) {
        console.log(`📋 Using existing collection flow: ${urlFlowId}`);
        flowResponse = await collectionFlowApi.getFlowDetails(urlFlowId);

        // CRITICAL FIX: Use centralized flow ID update
        updateFlowId(flowResponse.id);

        // Check if flow is already completed
        if (flowResponse.status === "completed") {
          console.log(
            "✅ Flow is already completed, redirecting to progress page",
          );
          setState((prev) => ({
            ...prev,
            isCompleted: true,
            isLoading: false,
          }));

          toast({
            title: "Flow Already Completed",
            description:
              "This collection flow has been completed. Redirecting to progress view...",
            variant: "default",
          });

          // Redirect to collection progress page
          setTimeout(() => {
            window.location.href = `/collection/progress/${flowResponse.id}`;
          }, 1500);
          return;
        }

        // Update the auth context with the existing collection flow
        setCurrentFlow({
          id: flowResponse.id,
          name: "Collection Flow",
          type: "collection",
          status: flowResponse.status || "active",
          engagement_id: flowResponse.engagement_id,
        });

        // Check if this flow already has questionnaires
        try {
          const existingQuestionnaires =
            await collectionFlowApi.getFlowQuestionnaires(flowResponse.id);
          if (existingQuestionnaires.length > 0) {
            console.log(
              `✅ Found ${existingQuestionnaires.length} existing questionnaires for flow`,
            );

            // Convert existing questionnaires to form data
            try {
              const adaptiveFormData = convertQuestionnairesToFormData(
                existingQuestionnaires[0],
                applicationId,
              );

              if (validateFormDataStructure(adaptiveFormData)) {
                // Fetch saved responses from the backend
                let existingResponses: CollectionFormData = {};

                const questionnaireId =
                  existingQuestionnaires[0]?.id || "default-questionnaire";
                try {
                  const savedResponsesData =
                    await collectionFlowApi.getQuestionnaireResponses(
                      flowResponse.id,
                      questionnaireId,
                    );

                  if (
                    savedResponsesData?.responses &&
                    Object.keys(savedResponsesData.responses).length > 0
                  ) {
                    existingResponses = savedResponsesData.responses;
                    console.log(
                      `📝 Loaded ${Object.keys(existingResponses).length} saved responses from backend:`,
                      existingResponses,
                    );
                  } else {
                    // Fallback to extracting from questionnaire if backend doesn't have responses
                    existingResponses = extractExistingResponses(
                      existingQuestionnaires[0],
                    );
                  }
                } catch (err) {
                  console.warn(
                    "Failed to fetch saved responses, using fallback:",
                    err,
                  );
                  // Fallback to extracting from questionnaire
                  existingResponses = extractExistingResponses(
                    existingQuestionnaires[0],
                  );
                }

                setState((prev) => ({
                  ...prev,
                  formData: adaptiveFormData,
                  formValues: existingResponses, // Load existing responses into form values
                  questionnaires: existingQuestionnaires,
                  isLoading: false,
                }));

                toast({
                  title: "Form Loaded",
                  description:
                    "Loaded existing questionnaire with saved responses",
                });

                return; // Skip waiting for agents
              } else {
                console.warn(
                  "⚠️ Existing questionnaire data structure is invalid, will regenerate",
                );
              }
            } catch (conversionError) {
              console.error(
                "❌ Failed to convert existing questionnaire:",
                conversionError,
              );
              // Continue to regenerate questionnaire instead of failing
            }
          }
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          console.log(
            "🔍 No existing questionnaires found or error fetching:",
            errorMessage,
          );
          hasExistingData = false;
        }
      } else {
        // First check if there's already an active flow
        try {
          const existingStatus = await collectionFlowApi.getFlowStatus();
          if (existingStatus.flow_id) {
            console.log(
              "✅ Found existing active flow:",
              existingStatus.flow_id,
            );
            flowResponse = await collectionFlowApi.getFlowDetails(
              existingStatus.flow_id,
            );
            // CRITICAL FIX: Use centralized flow ID update
            updateFlowId(flowResponse.id);
          } else {
            throw new Error("No active flow found, will create new one");
          }
        } catch (checkError: unknown) {
          // Only create new flow if no active flow exists
          const error = checkError as { status?: number; message?: string };
          if (
            error?.status === 404 ||
            error?.message?.includes("No active flow")
          ) {
            // Check if user has permission to create collection flows
            if (!canCreateCollectionFlow(user)) {
              throw new Error(
                "You do not have permission to create collection flows. Only analysts and above can create flows.",
              );
            }

            // Create a new collection flow - this triggers CrewAI agents
            const flowData = {
              automation_tier: "tier_2",
              collection_config: {
                form_type: "adaptive_data_collection",
                // Align with backend expectation: selected_application_ids array
                selected_application_ids: applicationId ? [applicationId] : [],
                collection_method: "manual_adaptive_form",
              },
            };

            console.log(
              "🤖 Creating CrewAI collection flow for adaptive forms...",
            );
            flowResponse = await collectionFlowApi.createFlow(flowData);
            // CRITICAL FIX: Use centralized flow ID update
            updateFlowId(flowResponse.id);
          } else if (error?.status === 500) {
            // Multiple flows exist - this shouldn't happen but handle gracefully
            console.error("❌ Multiple active flows detected, cannot proceed");
            throw new Error(
              "Multiple active collection flows detected. Please contact support.",
            );
          } else {
            throw error;
          }
        }
      }

      console.log(`🎯 Collection flow ${flowResponse.id} ready`);

      // Update the auth context with the collection flow
      setCurrentFlow({
        id: flowResponse.id,
        name: "Collection Flow",
        type: "collection",
        status: flowResponse.status || "active",
        engagement_id: flowResponse.engagement_id,
      });

      // CRITICAL CHECK: If collection is assessment-ready, transition instead of generating new questionnaires
      if (flowResponse.assessment_ready) {
        console.log(
          `✅ Collection flow ${flowResponse.id} is assessment-ready! Triggering transition...`,
        );

        try {
          const transitionResult = await collectionFlowApi.transitionToAssessment(flowResponse.id);
          console.log("✅ Transition to assessment successful:", transitionResult);

          setState((prev) => ({ ...prev, isCompleted: true }));

          toast({
            title: "Collection Complete - Assessment Ready",
            description: `Your data has been collected successfully. Redirecting to assessment flow...`,
          });

          // Redirect to assessment flow 6R review page (default entry point)
          setTimeout(() => {
            window.location.href = `/assessment/${transitionResult.assessment_flow_id}/sixr-review`;
          }, 2000);

          return; // Exit early - no need to generate questionnaires
        } catch (transitionError) {
          console.error("❌ Failed to transition to assessment:", transitionError);
          toast({
            title: "Transition Error",
            description: "Could not transition to assessment. Redirecting to progress page.",
            variant: "destructive",
          });
          // CRITICAL FIX: Do not fall through to questionnaire generation when assessment is ready
          // Redirect to progress page where user can manually trigger transition
          setTimeout(() => {
            window.location.href = `/collection/progress/${flowResponse.id}`;
          }, 2000);
          return; // Exit early to prevent infinite loop
        }
      }

      console.log(
        `🎯 Collection flow ${flowResponse.id} ready, triggering questionnaire generation...`,
      );

      // Execute the flow to trigger CrewAI agents for questionnaire generation
      try {
        console.log(
          "🚀 Executing collection flow to start questionnaire generation...",
        );
        const executeResult = await collectionFlowApi.executeFlowPhase(
          flowResponse.id,
        );
        console.log("✅ Flow execution started:", executeResult);
      } catch (executeError: unknown) {
        console.error("❌ Failed to execute collection flow:", executeError);

        const error = executeError as { message?: string; response?: { data?: { detail?: string } } };
        // If the error indicates the MFO flow doesn't exist, the collection flow is corrupted
        if (
          error?.message?.includes("Flow not found") ||
          error?.response?.data?.detail?.includes("Flow not found")
        ) {
          console.error(
            "🔴 Collection flow is corrupted (missing MFO flow). Deleting and recreating...",
          );

          // Delete the corrupted flow
          try {
            await collectionFlowApi.deleteFlow(flowResponse.id, true);
            console.log("✅ Deleted corrupted flow");
          } catch (deleteError) {
            console.error("Failed to delete corrupted flow:", deleteError);
          }

          // Throw error to trigger flow recreation
          throw new Error(
            "Collection flow was corrupted. Please refresh the page to create a new flow.",
          );
        }

        // For other errors, continue - the flow might already be running
        console.warn(
          "⚠️ Continuing despite execution error - flow might already be running",
        );
      }

      // Only wait for agents if there's existing data to analyze
      console.log(
        "🔍 Checking for existing questionnaires from previous sessions...",
      );

      // Check flow status first to see if agents are working or failed
      let flowStatus: CollectionFlowStatusResponse;
      try {
        flowStatus = await collectionFlowApi.getFlowStatus();

        // If we get a status, it means there's already an active flow
        if (flowStatus.flow_id && flowStatus.flow_id !== flowResponse.id) {
          console.warn("⚠️ Another active flow exists:", flowStatus.flow_id);
          // Use the existing flow instead
          flowResponse = await collectionFlowApi.getFlowDetails(
            flowStatus.flow_id,
          );
          // CRITICAL FIX: Use centralized flow ID update
          updateFlowId(flowResponse.id);
        }

        // If flow shows error, use fallback immediately
        if (flowStatus.status === "error" || flowStatus.status === "failed") {
          console.warn("⚠️ CrewAI agents failed, using fallback questionnaire");
          throw new Error(
            "Agent processing failed - using default questionnaire",
          );
        }
      } catch (statusError: unknown) {
        // If status check fails with 500 (multiple flows), we should handle it gracefully
        const error = statusError as { status?: number };
        if (error?.status === 500) {
          console.warn(
            "⚠️ Multiple active flows detected, continuing with current flow",
          );
        } else if (error?.status !== 404) {
          console.error("❌ Failed to check flow status:", statusError);
        }
      }

      // Trigger modal if callback provided
      if (onQuestionnaireGenerationStart && !hasExistingData) {
        onQuestionnaireGenerationStart();
      }

      console.log(
        "⏳ Waiting for CrewAI agents to process through phases and generate questionnaires...",
      );
      console.log(
        "   Expected phases: PLATFORM_DETECTION -> AUTOMATED_COLLECTION -> GAP_ANALYSIS -> QUESTIONNAIRE_GENERATION",
      );

      // Use the polling hook to wait for questionnaires
      let agentQuestionnaires: CollectionQuestionnaire[] = [];
      let timeoutReached = false;

      try {
        const pollingResult = await polling.pollForQuestionnaires(
          flowResponse.id,
          flowResponse
        );
        agentQuestionnaires = pollingResult.questionnaires;
        timeoutReached = pollingResult.timeoutReached;
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.warn(
          "⚠️ Agent processing failure, proceeding with fallback:",
          errorMessage,
        );
        // Don't throw here - let the fallback logic handle it below
      }

      // Handle timeout or no questionnaires generated
      if (agentQuestionnaires.length === 0 || timeoutReached) {
        console.warn(
          "⚠️ No questionnaires generated within timeout period. Using fallback form.",
        );

        // Use a local fallback adaptive form to allow user to proceed
        const fallback = createFallbackFormData(applicationId || null);
        setState((prev) => ({
          ...prev,
          formData: fallback,
          questionnaires: [],
          isLoading: false,
          error: null, // Clear any previous errors since we have a fallback
        }));

        toast({
          title: "Fallback Form Loaded",
          description: `CrewAI agents are taking longer than expected. Using a basic adaptive form to begin collection.`,
          variant: "default",
        });
        return;
      }

      // Convert CrewAI-generated questionnaires to AdaptiveFormData format
      let adaptiveFormData;
      try {
        adaptiveFormData = convertQuestionnairesToFormData(
          agentQuestionnaires[0],
          applicationId,
        );
      } catch (conversionError: unknown) {
        console.error(
          "❌ Failed to convert agent questionnaire to form data:",
          conversionError,
        );
        const errorMessage = conversionError instanceof Error ? conversionError.message : String(conversionError);
        throw new Error(
          `Failed to convert agent-generated questionnaire to form format: ${errorMessage}`,
        );
      }

      // Validate the converted form data
      if (!validateFormDataStructure(adaptiveFormData)) {
        console.error(
          "❌ Generated form data structure validation failed:",
          adaptiveFormData,
        );
        throw new Error(
          "Generated form data structure is invalid. The questionnaire may be missing required fields or sections.",
        );
      }

      setState((prev) => ({
        ...prev,
        formData: adaptiveFormData,
        questionnaires: agentQuestionnaires,
      }));

      console.log("✅ Successfully loaded agent-generated adaptive form");

      toast({
        title: "Adaptive Form Ready",
        description: `CrewAI agents generated ${agentQuestionnaires.length} questionnaire(s) based on gap analysis.`,
      });
    } catch (error: unknown) {
      console.error("❌ Failed to initialize adaptive collection:", error);

      // Create a more user-friendly error message
      let userMessage = "Failed to initialize collection flow.";
      let shouldUseFallback = false;

      const errorObj = error as { message?: string };
      if (errorObj?.message) {
        if (
          errorObj.message.includes("timeout") ||
          errorObj.message.includes("HTTP polling timeout")
        ) {
          userMessage = `Collection initialization timed out. Using fallback form to allow you to proceed.`;
          shouldUseFallback = true;
        } else if (errorObj.message.includes("questionnaire")) {
          userMessage =
            "The system is generating custom questionnaires. This may take a moment. Using a basic form to allow you to continue.";
          shouldUseFallback = true;
        } else if (errorObj.message.includes("generation failed") || errorObj.message.includes("Agent returned")) {
          userMessage =
            "Questionnaire generation is in progress. You can use this basic form while we prepare custom questions based on your data gaps.";
          shouldUseFallback = true;
        } else if (errorObj.message.includes("permission")) {
          userMessage =
            "Permission denied. You do not have access to create collection flows.";
        } else if (errorObj.message.includes("Multiple active")) {
          userMessage =
            "Multiple active collection flows detected. Please manage existing flows first.";
        } else {
          userMessage = errorObj.message;
          // For unknown errors, provide fallback if it's not an auth/permission issue
          shouldUseFallback =
            !errorObj.message.includes("permission") &&
            !errorObj.message.includes("auth");
        }
      }

      // If we should use fallback, provide it instead of showing error
      if (shouldUseFallback) {
        console.warn(
          "⚠️ Using fallback form due to initialization error:",
          userMessage,
        );

        const fallback = createFallbackFormData(applicationId || null);
        setState((prev) => ({
          ...prev,
          formData: fallback,
          questionnaires: [],
          isLoading: false,
          error: null, // Clear error since we have a working fallback
        }));

        toast({
          title: "Form Ready",
          description: userMessage,
          variant: "default",
        });

        return; // Exit early with fallback, don't throw error
      }

      // For non-fallback errors, show error state
      const enhancedError = new Error(userMessage);
      if (error instanceof Error) {
        (enhancedError as Error & { cause?: Error }).cause = error;
      }

      setState((prev) => ({ ...prev, error: enhancedError, isLoading: false }));

      // Only show toast for non-409 errors to avoid spam
      if (
        !errorObj?.message?.includes("409") &&
        !errorObj?.message?.includes("Conflict")
      ) {
        toast({
          title: "Failed to Load Adaptive Forms",
          description: userMessage,
          variant: "destructive",
        });
      } else {
        // For 409 conflicts, show a more helpful message without toast spam
        console.log(
          "⚠️ 409 Conflict detected - existing flow found, showing management UI",
        );
      }

      // Throw error for non-fallback cases
      throw enhancedError;
    } finally {
      // Always ensure loading state is cleared
      setState((prev) => ({ ...prev, isLoading: false }));

      // Clear any pending timers
      console.log("✨ Collection workflow initialization completed");
    }
  }, [
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    blockingFlows.length,
    state.isLoading,
    urlFlowId,
    setCurrentFlow,
    applicationId,
    user,
    toast,
    updateFlowId,
    onQuestionnaireGenerationStart,
    polling,
    setState,
  ]);

  return {
    initializeFlow,
  };
}
