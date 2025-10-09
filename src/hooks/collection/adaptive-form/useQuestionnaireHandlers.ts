/**
 * Questionnaire handler functions for adaptive form flow
 * Handles field changes, validation, save, reset, retry, and refresh operations
 *
 * PRESERVED FROM ORIGINAL: Lines 1115-1136, 1141-1222, 1594-1711 of useAdaptiveFormFlow.ts
 */

import { useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import type { FormFieldValue } from "@/types/shared/form-types";
import type { FormValidationResult, CollectionFormData } from "@/components/collection/types";
import type { AdaptiveFormFlowState } from "./types";
import { collectionFlowApi } from "@/services/api/collection-flow";
import { apiCall } from "@/config/api";
import {
  convertQuestionnairesToFormData,
  validateFormDataStructure,
} from "@/utils/collection/formDataTransformation";

export interface UseQuestionnaireHandlersProps {
  state: AdaptiveFormFlowState;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
  applicationId?: string | null;
  currentFlowIdRef: React.MutableRefObject<string | null>;
  setCurrentFlow: (flow: CollectionFlow | null) => void;
  initializeFlow: () => Promise<void>;
}

export interface UseQuestionnaireHandlersReturn {
  handleFieldChange: (fieldId: string, value: FormFieldValue) => void;
  handleValidationChange: (newValidation: FormValidationResult) => void;
  handleSave: () => Promise<void>;
  resetFlow: () => void;
  retryFlow: () => Promise<void>;
  forceRefresh: () => Promise<void>;
}

export function useQuestionnaireHandlers({
  state,
  setState,
  applicationId,
  currentFlowIdRef,
  setCurrentFlow,
  initializeFlow,
}: UseQuestionnaireHandlersProps): UseQuestionnaireHandlersReturn {
  const { toast } = useToast();

  /**
   * Handle field value changes - wrapped in useCallback for performance
   * PRESERVED FROM ORIGINAL: Lines 1115-1126
   */
  const handleFieldChange = useCallback(
    (fieldId: string, value: FormFieldValue): void => {
      setState((prev) => ({
        ...prev,
        formValues: {
          ...prev.formValues,
          [fieldId]: value,
        },
      }));
    },
    // setState is intentionally omitted - React guarantees setState is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  /**
   * Handle validation result changes - wrapped in useCallback for performance
   * PRESERVED FROM ORIGINAL: Lines 1131-1136
   */
  const handleValidationChange = useCallback(
    (newValidation: FormValidationResult): void => {
      setState((prev) => ({ ...prev, validation: newValidation }));
    },
    // setState is intentionally omitted - React guarantees setState is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  /**
   * Save form progress - wrapped in useCallback to prevent unnecessary re-renders
   * PRESERVED FROM ORIGINAL: Lines 1141-1222
   */
  const handleSave = useCallback(async (): Promise<void> => {
    console.log("🔴 SAVE BUTTON CLICKED - handleSave triggered", {
      hasFormData: !!state.formData,
      hasFlowId: !!state.flowId,
      flowId: state.flowId,
      formValues: state.formValues,
      timestamp: new Date().toISOString(),
    });

    if (!state.formData || !state.flowId) {
      console.error("❌ Cannot save: Missing formData or flowId", {
        formData: state.formData,
        flowId: state.flowId,
      });
      return;
    }

    setState((prev) => ({ ...prev, isSaving: true }));

    try {
      // Get the first questionnaire (assuming single questionnaire for now)
      const questionnaire = state.questionnaires?.[0];
      const questionnaireId = questionnaire?.id || "default-questionnaire";

      console.log("📋 Preparing to save questionnaire:", {
        questionnaireId,
        hasQuestionnaire: !!questionnaire,
        totalQuestionnaires: state.questionnaires?.length || 0,
      });

      // Prepare the submission data in the format expected by the backend
      const submissionData = {
        responses: state.formValues,
        form_metadata: {
          form_id: state.formData.formId,
          application_id: applicationId || null,
          completion_percentage: state.validation?.completionPercentage || 0,
          confidence_score: state.validation?.overallConfidenceScore || 0,
          submitted_at: new Date().toISOString(),
        },
        validation_results: {
          isValid: state.validation?.isValid || false,
          fieldResults: state.validation?.fieldResults || {},
        },
      };

      // Submit the questionnaire responses to the backend
      const endpoint = `/collection/flows/${state.flowId}/questionnaires/${questionnaireId}/responses`;
      console.log("🚀 Submitting to endpoint:", endpoint, {
        submissionData,
      });

      const response = await apiCall(endpoint, {
        method: "POST",
        body: JSON.stringify(submissionData),
      });

      console.log("💾 Questionnaire responses saved successfully:", response);

      toast({
        title: "Progress Saved",
        description: "Your form progress has been saved successfully.",
      });
    } catch (error) {
      console.error("Failed to save progress:", error);
      toast({
        title: "Save Failed",
        description: "Failed to save progress. Please try again.",
        variant: "destructive",
      });
    } finally {
      setState((prev) => ({ ...prev, isSaving: false }));
    }
    // setState is intentionally omitted - React guarantees setState is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    state.formData,
    state.flowId,
    state.formValues,
    state.validation,
    state.questionnaires,
    applicationId,
    toast,
  ]);

  /**
   * Reset the flow state
   * PRESERVED FROM ORIGINAL: Lines 1594-1616
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
   * PRESERVED FROM ORIGINAL: Lines 1621-1650
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
    // setState is intentionally omitted - React guarantees setState is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initializeFlow, toast]);

  /**
   * Force refresh questionnaires and flow state
   * PRESERVED FROM ORIGINAL: Lines 1655-1711
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
  }, [state.flowId, applicationId, toast]);

  return {
    handleFieldChange,
    handleValidationChange,
    handleSave,
    resetFlow,
    retryFlow,
    forceRefresh,
  };
}
