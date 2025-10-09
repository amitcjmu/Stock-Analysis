/**
 * Save handler for adaptive form flow
 * Manages form progress saving to backend
 *
 * PRESERVED FROM ORIGINAL: Lines 1138-1225 of useAdaptiveFormFlow.ts
 */

import { useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import { apiCall } from "@/config/api";
import type { CollectionFormData } from "@/components/collection/types";
import type { AdaptiveFormFlowState } from "./types";

export interface UseSaveHandlerProps {
  state: AdaptiveFormFlowState;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
  applicationId?: string | null;
}

export interface UseSaveHandlerReturn {
  handleSave: (valuesToSave?: CollectionFormData) => Promise<void>;
}

export function useSaveHandler({
  state,
  setState,
  applicationId,
}: UseSaveHandlerProps): UseSaveHandlerReturn {
  const { toast } = useToast();

  /**
   * Save form progress - wrapped in useCallback to prevent unnecessary re-renders
   * PRESERVED FROM ORIGINAL: Lines 1138-1225
   */
  const handleSave = useCallback(async (valuesToSave?: CollectionFormData): Promise<void> => {
    const formValuesToUse = valuesToSave || state.formValues;

    console.log("🔴 SAVE BUTTON CLICKED - handleSave triggered", {
      hasFormData: !!state.formData,
      hasFlowId: !!state.flowId,
      flowId: state.flowId,
      formValues: formValuesToUse,
      usingProvidedValues: !!valuesToSave,
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
        responses: formValuesToUse,
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
  }, [
    state.formData,
    state.flowId,
    state.formValues,
    state.validation,
    state.questionnaires,
    applicationId,
    toast,
    setState,
  ]); // Dependencies for useCallback

  return {
    handleSave,
  };
}
