/**
 * Custom hook for managing adaptive form flows
 *
 * REFACTORED: October 2025 - Modularized from 1872 LOC to <600 LOC
 * Extracted modules in src/hooks/collection/adaptive-form/:
 * - useFormState.ts - State management and flow ID handling
 * - useValidation.ts - Field changes and validation
 * - useSaveHandler.ts - Form progress saving
 * - useSubmitHandler.ts - Form submission logic
 * - usePolling.ts - HTTP polling for questionnaires (Railway-compatible, NO WebSockets)
 * - useFlowLifecycle.ts - Flow initialization and lifecycle
 * - useAutoInit.ts - Auto-initialization effects
 * - useQuestionnaireHandlers.ts - Questionnaire management
 *
 * PRESERVED CRITICAL PATTERNS:
 * - HTTP polling logic (NO WebSockets for Railway)
 * - Ref-based loop guards
 * - Exact useEffect dependency arrays
 * - Multi-tenant scoping (client_account_id, engagement_id)
 * - Snake_case field naming
 * - Centralized flow ID management
 */

import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useToast } from "@/components/ui/use-toast";
import { createFallbackFormData } from "@/utils/collection/formDataTransformation";

// Import flow management hooks
import {
  useCollectionFlowManagement,
  useActivelyIncompleteCollectionFlows,
} from "./useCollectionFlowManagement";
import { useQuestionnairePolling } from "./useQuestionnairePolling";

// Import modular hooks from adaptive-form module
import {
  useFormState,
  useValidation,
  useSaveHandler,
  useSubmitHandler,
  usePolling,
  useFlowLifecycle,
  useAutoInit,
} from "./adaptive-form";

// Import API services
import { collectionFlowApi } from "@/services/api/collection-flow";

// Import form data transformation utilities
import {
  convertQuestionnairesToFormData,
  validateFormDataStructure,
} from "@/utils/collection/formDataTransformation";

// Import types
import type {
  UseAdaptiveFormFlowOptions,
  AdaptiveFormFlowState,
  AdaptiveFormFlowActions,
  CollectionQuestionnaire,
} from "./adaptive-form/types";
import type { CollectionFormData } from "@/components/collection/types";

// Import auth context
import { useAuth } from "@/contexts/AuthContext";

// Import applications hook for UUID-to-name resolution
import { useApplications } from "@/hooks/useApplications";

/**
 * Main adaptive form flow hook - now composed from modular hooks
 * CRITICAL: 100% backward compatible with original implementation
 */
export const useAdaptiveFormFlow = (
  options: UseAdaptiveFormFlowOptions = {},
): AdaptiveFormFlowState & AdaptiveFormFlowActions => {
  const {
    applicationId,
    flowId: optionsFlowId,
    autoInitialize = true,
    onQuestionnaireGenerationStart,
  } = options;

  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { setCurrentFlow, user } = useAuth();

  // Get applications list for UUID-to-name resolution in form data
  const { applications } = useApplications();

  // CRITICAL FIX: Single source of truth for flow ID
  // Get flow ID from URL params or options - this is our primary source
  const urlFlowId = searchParams.get("flowId") || optionsFlowId;

  // Collection flow management
  const { continueFlow, deleteFlow } = useCollectionFlowManagement();

  // Initialize state management with centralized flow ID updates
  const { state, setState, currentFlowIdRef, updateFlowId } = useFormState(urlFlowId || null);

  // Update flowId when URL changes
  useEffect(() => {
    if (urlFlowId && urlFlowId !== currentFlowIdRef.current) {
      console.log("📝 Flow ID updated from URL:", urlFlowId);
      updateFlowId(urlFlowId);
    }
  }, [urlFlowId, updateFlowId, currentFlowIdRef]);

  // Check for actively incomplete flows (INITIALIZED, RUNNING)
  // Per ADR-012, PAUSED flows are waiting for user input and should not block
  // CRITICAL FIX: Always call the hook but use skipIncompleteCheck for logic
  const skipIncompleteCheck = !!urlFlowId || !!currentFlowIdRef.current;
  const { data: incompleteFlows = [], isLoading: checkingFlows } =
    useActivelyIncompleteCollectionFlows(); // Always call the hook to maintain consistent hook order

  // Filter out the current flow from the blocking check
  // CRITICAL FIX: Only consider flows as blocking if we're NOT continuing a specific flow
  const blockingFlows = skipIncompleteCheck
    ? []
    : incompleteFlows.filter((flow) => {
        const flowIdToCheck = flow.flow_id || flow.id;
        // Never block if we're continuing a specific flow
        return (
          flowIdToCheck !== urlFlowId && flowIdToCheck !== currentFlowIdRef.current
        );
      });

  const hasBlockingFlows = blockingFlows.length > 0;

  // Initialize HTTP polling hook (Railway-compatible, NO WebSockets)
  const polling = usePolling({
    timeoutMs: 30000, // 30 seconds
    activePollingInterval: 2000, // 2s when active
    waitingPollingInterval: 5000, // 5s when waiting
  });

  // Initialize flow lifecycle management
  const { initializeFlow } = useFlowLifecycle({
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
  });

  // Initialize validation handlers
  const { handleFieldChange, handleValidationChange } = useValidation({
    state,
    setState,
  });

  // Initialize save handler
  const { handleSave } = useSaveHandler({
    state,
    setState,
    applicationId,
  });

  // Initialize submit handler
  const { handleSubmit } = useSubmitHandler({
    state,
    setState,
    applicationId,
    updateFlowId,
  });

  // CRITICAL FIX #677: Poll for flow phase to know when questionnaires are ready
  // Phase progression: gap_analysis → questionnaire_generation → manual_collection
  // Questionnaires are saved to DB BEFORE transition to manual_collection
  const { data: flowDetails } = useQuery({
    queryKey: ['collection-flow-phase', state.flowId],
    queryFn: async () => {
      if (!state.flowId) return null;
      return await collectionFlowApi.getFlowDetails(state.flowId);
    },
    enabled: !!state.flowId && !state.formData && !state.questionnaires?.length,
    refetchInterval: (data) => {
      // Keep polling phase every 2s until we reach manual_collection
      if (!data || data.current_phase === 'questionnaire_generation' || data.current_phase === 'gap_analysis') {
        return 2000; // 2 seconds
      }
      return false; // Stop when manual_collection is reached
    },
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    staleTime: 0, // Always fresh
  });

  const currentPhase = flowDetails?.current_phase || null;

  // Use the new questionnaire polling hook with completion_status support
  const questionnairePollingState = useQuestionnairePolling({
    flowId: state.flowId || '',
    enabled: !!state.flowId && !state.formData && !state.questionnaires?.length,
    currentPhase, // CRITICAL: Pass current phase to prevent race condition
    onReady: useCallback(async (questionnaires: CollectionQuestionnaire[]) => {
      console.log('🎉 Questionnaire ready from new polling hook:', questionnaires);
      // Convert questionnaires and update state - use timeout to prevent React warning
      if (questionnaires.length > 0) {
        try {
          const adaptiveFormData = convertQuestionnairesToFormData(
            questionnaires[0],
            applicationId,
            applications // FIX: Pass applications for UUID-to-name lookup
          );

          if (validateFormDataStructure(adaptiveFormData)) {
            // CRITICAL FIX: Fetch saved responses from database when loading questionnaire
            let existingResponses: CollectionFormData = {};
            if (state.flowId) {
              try {
                const savedResponsesData = await collectionFlowApi.getQuestionnaireResponses(
                  state.flowId,
                  questionnaires[0].id,
                );
                if (savedResponsesData?.responses && Object.keys(savedResponsesData.responses).length > 0) {
                  existingResponses = savedResponsesData.responses;
                  console.log(`📝 Loaded ${Object.keys(existingResponses).length} saved responses from database:`, existingResponses);
                } else {
                  console.log('📝 No saved responses found in database for this questionnaire');
                }
              } catch (err) {
                console.warn("Failed to fetch saved responses from database:", err);
              }
            }

            // Use setTimeout to prevent "Cannot update a component while rendering" warning
            setTimeout(() => {
              setState((prev) => ({
                ...prev,
                formData: adaptiveFormData,
                formValues: existingResponses, // Load saved responses from database
                questionnaires: questionnaires,
                isLoading: false,
                error: null
              }));
            }, 0);

            toast({
              title: existingResponses && Object.keys(existingResponses).length > 0
                ? "Saved Responses Loaded"
                : "Adaptive Form Ready",
              description: existingResponses && Object.keys(existingResponses).length > 0
                ? `Loaded your previously saved responses. You can review and update them.`
                : `Agent-generated questionnaire is ready for data collection.`,
            });
          }
        } catch (error) {
          console.error('Failed to convert questionnaire:', error);
        }
      }
    }, [applicationId, applications, toast, state.flowId, setState]),
    onFallback: useCallback(async (questionnaires: CollectionQuestionnaire[]) => {
      console.log('⚠️ Using fallback questionnaire from new polling hook:', questionnaires);

      // Handle fallback questionnaire - use timeout to prevent React warning
      if (questionnaires.length > 0) {
        try {
          const adaptiveFormData = convertQuestionnairesToFormData(
            questionnaires[0],
            applicationId,
            applications // FIX: Pass applications for UUID-to-name lookup
          );

          // CRITICAL FIX: Fetch saved responses from database for fallback questionnaire too
          let existingResponses: CollectionFormData = {};
          if (state.flowId) {
            try {
              const savedResponsesData = await collectionFlowApi.getQuestionnaireResponses(
                state.flowId,
                questionnaires[0].id,
              );
              if (savedResponsesData?.responses && Object.keys(savedResponsesData.responses).length > 0) {
                existingResponses = savedResponsesData.responses;
                console.log(`📝 Loaded ${Object.keys(existingResponses).length} saved responses from database:`, existingResponses);
              }
            } catch (err) {
              console.warn("Failed to fetch saved responses from database:", err);
            }
          }

          // Use setTimeout to prevent "Cannot update a component while rendering" warning
          setTimeout(() => {
            setState((prev) => ({
              ...prev,
              formData: adaptiveFormData,
              formValues: existingResponses, // Load saved responses from database
              questionnaires: questionnaires,
              isLoading: false,
              error: null
            }));
          }, 0);

          toast({
            title: "Bootstrap Form Loaded",
            description: existingResponses && Object.keys(existingResponses).length > 0
              ? "Using comprehensive template questionnaire. Your saved responses have been loaded."
              : "Using comprehensive template questionnaire while AI agents work in the background.",
            variant: "default",
          });
        } catch (error) {
          console.error('Failed to convert fallback questionnaire:', error);
        }
      } else {
        // CRITICAL FIX: Handle empty questionnaires array by creating local fallback
        console.warn('⚠️ Received empty questionnaires array in fallback, creating local fallback form');
        const fallback = createFallbackFormData(applicationId || null);

        setTimeout(() => {
          setState((prev) => ({
            ...prev,
            formData: fallback,
            questionnaires: [],
            isLoading: false,
            error: null
          }));
        }, 0);

        toast({
          title: "Basic Form Loaded",
          description: "Using basic questionnaire template. You can still collect data.",
          variant: "default",
        });
      }
    }, [applicationId, applications, toast, state.flowId, setState]),
    onFailed: useCallback((errorMessage: string) => {
      console.error('❌ Questionnaire generation failed:', errorMessage);
      // Enhanced error handling with retry capabilities
      setState((prev) => {
        if (prev.formData) {
          console.log('✅ Already have form data, skipping fallback');
          return prev;
        }

        // Determine if this is a retryable error
        const isRetryable = !errorMessage.includes('permission') &&
                           !errorMessage.includes('forbidden') &&
                           !errorMessage.includes('unauthorized');

        // Use local fallback but keep error info for retry
        const fallback = createFallbackFormData(applicationId || null);

        toast({
          title: "Fallback Form Loaded",
          description: `Questionnaire generation failed: ${errorMessage}. Using basic adaptive form.${isRetryable ? ' You can try again later.' : ''}`,
          variant: "default",
        });

        return {
          ...prev,
          formData: fallback,
          questionnaires: [],
          isLoading: false,
          error: new Error(errorMessage),
          canRetry: isRetryable,
          isStuck: true,
          stuckReason: errorMessage,
        };
      });
    }, [applicationId, toast, setState])
  });

  /**
   * Reset the flow state
   */
  const resetFlow = (): void => {
    setState({
      formData: null,
      formValues: {},
      validation: null,
      flowId: null,
      questionnaires: [],
      isLoading: false,
      isSaving: false,
      isCompleted: false,
      error: null,
      // New polling state fields
      isPolling: false,
      completionStatus: null,
      statusLine: null,
      // Enhanced error recovery
      canRetry: false,
      isStuck: false,
      stuckReason: null,
    });
    currentFlowIdRef.current = null;
    setCurrentFlow(null);
  };

  /**
   * Retry flow initialization after failure
   */
  const retryFlow = useCallback(async (): Promise<void> => {
    console.log('🔄 Retrying flow initialization...');
    setState(prev => ({
      ...prev,
      error: null,
      canRetry: false,
      isStuck: false,
      stuckReason: null,
      isLoading: true
    }));

    try {
      await initializeFlow();
      toast({
        title: "Retry Successful",
        description: "Flow initialization completed successfully.",
        variant: "default",
      });
    } catch (error) {
      console.error('❌ Retry failed:', error);
      setState(prev => ({
        ...prev,
        error: error as Error,
        canRetry: true,
        isStuck: true,
        stuckReason: (error as Error).message,
        isLoading: false
      }));
    }
  }, [initializeFlow, toast, setState]);

  /**
   * Force refresh questionnaires and flow state
   */
  const forceRefresh = useCallback(async (): Promise<void> => {
    if (!state.flowId) {
      console.warn('⚠️ No flow ID available for refresh');
      return;
    }

    console.log('🔄 Force refreshing flow state...');
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Re-fetch questionnaires
      const questionnaires = await collectionFlowApi.getFlowQuestionnaires(state.flowId);

      if (questionnaires.length > 0) {
        const adaptiveFormData = convertQuestionnairesToFormData(
          questionnaires[0],
          applicationId,
          applications // FIX: Pass applications for UUID-to-name lookup
        );

        if (validateFormDataStructure(adaptiveFormData)) {
          setState(prev => ({
            ...prev,
            formData: adaptiveFormData,
            questionnaires: questionnaires,
            isLoading: false,
            error: null,
            canRetry: false,
            isStuck: false,
            stuckReason: null,
          }));

          toast({
            title: "Refresh Successful",
            description: "Flow data has been refreshed successfully.",
          });
        } else {
          throw new Error('Refreshed questionnaire data structure is invalid');
        }
      } else {
        throw new Error('No questionnaires found after refresh');
      }
    } catch (error) {
      console.error('❌ Force refresh failed:', error);
      setState(prev => ({
        ...prev,
        error: error as Error,
        isLoading: false,
        canRetry: true,
      }));

      toast({
        title: "Refresh Failed",
        description: `Failed to refresh flow data: ${(error as Error).message}`,
        variant: "destructive",
      });
    }
  }, [state.flowId, applicationId, applications, toast, setState]);

  // Track if we've attempted initialization for this flowId
  const [hasAttemptedInit, setHasAttemptedInit] = useState<string | null>(null);

  // Fetch questionnaires on mount if flowId exists (for continuing flows)
  useEffect(() => {
    console.log("🔍 Checking continuing flow conditions:", {
      urlFlowId,
      autoInitialize,
      hasFormData: !!state.formData,
      isLoading: state.isLoading,
      skipIncompleteCheck,
      checkingFlows,
      hasBlockingFlows,
      hasError: !!state.error,
      hasAttemptedInit,
      shouldInitialize:
        urlFlowId &&
        autoInitialize &&
        !state.formData &&
        !state.isLoading &&
        (skipIncompleteCheck || (!checkingFlows && !hasBlockingFlows)) &&
        !state.error &&
        hasAttemptedInit !== urlFlowId,
    });

    // CRITICAL FIX: Track initialization attempts to prevent infinite loops
    // Only initialize if we haven't already attempted for this specific flowId
    // When continuing a flow (skipIncompleteCheck=true), ignore blocking flows
    if (
      urlFlowId &&
      autoInitialize &&
      !state.formData &&
      !state.isLoading &&
      (skipIncompleteCheck || (!checkingFlows && !hasBlockingFlows)) &&
      !state.error &&
      hasAttemptedInit !== urlFlowId
    ) {
      console.log(
        "🔄 FlowId provided, fetching questionnaires for existing flow:",
        urlFlowId,
      );
      setHasAttemptedInit(urlFlowId); // Mark as attempted BEFORE initializing
      initializeFlow().catch((error) => {
        console.error(
          "❌ Failed to fetch questionnaires for existing flow:",
          error,
        );
        setState((prev) => ({ ...prev, error, isLoading: false }));
      });
    }
  }, [
    urlFlowId,
    autoInitialize,
    state.formData,
    state.isLoading,
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    state.error,
    hasAttemptedInit,
    initializeFlow,
    setState,
  ]);

  // Track if we've attempted auto-init for new flows
  const [hasAttemptedNewFlowInit, setHasAttemptedNewFlowInit] = useState(false);

  // Auto-initialize effect - Fixed to prevent infinite loops
  useEffect(() => {
    // STOP INFINITE LOOPS: Only initialize once and handle errors gracefully
    // Only initialize if:
    // 1. Auto-initialize is enabled
    // 2. Not currently checking for flows
    // 3. No blocking flows exist
    // 4. We don't have form data yet
    // 5. Not currently loading
    // 6. No previous error exists (prevents retry loops)
    // 7. No flowId provided (for new flows only)
    // 8. Haven't already attempted initialization for new flow
    if (
      autoInitialize &&
      !checkingFlows &&
      !hasBlockingFlows &&
      !state.formData &&
      !state.isLoading &&
      !state.error &&
      !urlFlowId &&
      !hasAttemptedNewFlowInit
    ) {
      console.log("🚀 Auto-initializing new collection flow...", {
        hasFormData: !!state.formData,
        hasBlockingFlows,
        isLoading: state.isLoading,
        hasError: !!state.error,
      });
      setHasAttemptedNewFlowInit(true); // Mark as attempted BEFORE initializing
      initializeFlow().catch((error) => {
        console.error("❌ Auto-initialization failed:", error);
        // Don't retry - let the user manually retry or handle the error
        setState((prev) => ({ ...prev, error, isLoading: false }));
      });
    }
  }, [
    applicationId,
    urlFlowId,
    checkingFlows,
    hasBlockingFlows,
    autoInitialize,
    state.formData,
    state.isLoading,
    state.error,
    hasAttemptedNewFlowInit,
    initializeFlow,
    setState,
  ]); // Added hasAttemptedNewFlowInit to prevent loops

  // Cleanup effect
  useEffect(() => {
    return () => {
      // Clear the flow context when component unmounts
      setCurrentFlow(null);

      // Clear any pending timeouts or intervals
      console.log("🧹 Cleaning up collection workflow state");
    };
  }, [setCurrentFlow]);

  // CC: Debugging - Log hook return only when key values change
  React.useEffect(() => {
    console.log("🔍 useAdaptiveFormFlow state updated:", {
      hasHandleSave: typeof handleSave === "function",
      flowId: state.flowId,
      hasFormData: !!state.formData,
    });
  }, [state.flowId, state.formData, handleSave]); // Only log when key values change

  return {
    // State - merge main state with polling state
    ...state,
    // Override polling-related fields with data from the new polling hook
    isPolling: questionnairePollingState.isPolling,
    completionStatus: questionnairePollingState.completionStatus,
    statusLine: questionnairePollingState.statusLine,
    // Enhanced retry capabilities from polling
    canRetry: state.canRetry || questionnairePollingState.canRetry,

    // Actions
    initializeFlow,
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    resetFlow,
    retryFlow,
    forceRefresh,
    // Expose polling retry for direct questionnaire issues
    retryPolling: questionnairePollingState.retryPolling,
  };
};

// Re-export types for backward compatibility
export type {
  UseAdaptiveFormFlowOptions,
  AdaptiveFormFlowState,
  AdaptiveFormFlowActions,
  CollectionQuestionnaire,
  FormQuestion,
} from "./adaptive-form/types";
