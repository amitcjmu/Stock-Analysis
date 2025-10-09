/**
 * Submit handler for adaptive form flow
 * Handles complex form submission logic including asset selection and questionnaire responses
 *
 * PRESERVED FROM ORIGINAL: Lines 1228-1589 of useAdaptiveFormFlow.ts
 */

import { useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import type { CollectionFormData } from "@/components/collection/types";
import type { AdaptiveFormFlowState } from "./types";
import { collectionFlowApi } from "@/services/api/collection-flow";
import { convertQuestionnaireToFormData } from "@/utils/collection/formDataTransformation";

export interface UseSubmitHandlerProps {
  state: AdaptiveFormFlowState;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
  applicationId?: string | null;
  updateFlowId: (newFlowId: string | null) => void;
}

export interface UseSubmitHandlerReturn {
  handleSubmit: (data: CollectionFormData) => Promise<void>;
}

export function useSubmitHandler({
  state,
  setState,
  applicationId,
  updateFlowId,
}: UseSubmitHandlerProps): UseSubmitHandlerReturn {
  const { toast } = useToast();

  /**
   * Submit the completed form
   * CRITICAL FIX: Add submission guard to prevent race conditions
   * PRESERVED FROM ORIGINAL: Lines 1228-1589
   */
  const handleSubmit = useCallback(async (data: CollectionFormData): Promise<void> => {
    // CRITICAL FIX: Prevent double submission
    if (state.isLoading) {
      console.log("⚠️ Form submission already in progress, ignoring...");
      return;
    }

    // CRITICAL FIX: Asset selection forms don't use validation state
    // Check if this is an asset selection form (bootstrap_asset_selection)
    const questionnaireId = state.questionnaires?.[0]?.id || '';
    const isAssetSelectionForm = questionnaireId === "bootstrap_asset_selection";

    if (!isAssetSelectionForm && !state.validation?.isValid) {
      toast({
        title: "Validation Required",
        description:
          "Please complete all required fields and resolve validation errors.",
        variant: "destructive",
      });
      return;
    }

    if (!state.flowId || state.questionnaires.length === 0) {
      toast({
        title: "Collection Flow Not Ready",
        description:
          "CrewAI collection flow is not properly initialized. Please refresh and try again.",
        variant: "destructive",
      });
      return;
    }

    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      // Submit responses to the CrewAI-generated questionnaire
      // Note: questionnaireId was already extracted above for validation check

      // For bootstrap questionnaires, when submitted, mark as 100% complete
      const isBootstrapForm = questionnaireId.startsWith("bootstrap_");
      const completionPercentage = isBootstrapForm
        ? 100
        : state.validation?.completionPercentage || 0;

      // Extract a single asset_id only when applicable (non-asset-selection forms)
      // Prevent type mismatch: asset_id should be a single string, not an array
      let assetId: string | null = null;
      if (questionnaireId !== "bootstrap_asset_selection" && typeof data?.asset_id === "string") {
        assetId = data.asset_id;
      }

      const submissionData = {
        responses: data,
        form_metadata: {
          form_id: state.formData?.formId,
          application_id: applicationId,
          ...(assetId ? { asset_id: assetId } : {}), // Only include when a single ID is present
          completion_percentage: completionPercentage,
          confidence_score: state.validation?.overallConfidenceScore,
          submitted_at: new Date().toISOString(),
        },
        validation_results: state.validation,
      };

      console.log(
        `🚀 Submitting adaptive form responses to CrewAI questionnaire ${questionnaireId}`,
      );

      let submitResponse;

      // CRITICAL FIX: Use correct API endpoint for asset selection
      if (questionnaireId === "bootstrap_asset_selection") {
        // Extract selected asset IDs from the form data
        // The adaptive form stores checkbox values under question_1, not selected_assets
        let selectedAssetIds = Array.isArray(data.selected_assets)
          ? data.selected_assets
          : [];

        // If selected_assets is empty, check for question_1 (adaptive form field)
        if (selectedAssetIds.length === 0 && data.question_1) {
          // question_1 contains the selected checkbox values (display text like "Asset Name (ID: uuid)")
          const rawValues = Array.isArray(data.question_1)
            ? data.question_1
            : [data.question_1].filter(Boolean);

          // Extract IDs from display text format "Asset Name (ID: uuid)"
          selectedAssetIds = rawValues.map(value => {
            const match = String(value).match(/\(ID:\s*([a-f0-9-]+)\)/);
            if (match) {
              return match[1].trim();
            }
            // Fallback: if no ID pattern found, return null to be filtered out
            return null;
          }).filter(Boolean) as string[];
        }

        console.log(`🎯 Asset selection detected (questionnaire ID: ${questionnaireId}), submitting ${selectedAssetIds.length} selected assets via applications endpoint`);
        console.log('📋 Selected asset IDs:', selectedAssetIds);
        console.log('📝 Full form data:', data);

        // Use the applications endpoint instead of questionnaire response endpoint
        submitResponse = await collectionFlowApi.updateFlowApplications(
          state.flowId,
          selectedAssetIds
        );
        console.log('✅ Asset selection API response:', submitResponse);
      } else {
        // Use regular questionnaire response endpoint for non-asset-selection questionnaires
        submitResponse = await collectionFlowApi.submitQuestionnaireResponse(
          state.flowId,
          questionnaireId,
          submissionData,
        );
      }

      // CRITICAL FIX: Use centralized flow ID update for response flow ID
      const actualFlowId = submitResponse.flow_id || state.flowId;
      if (actualFlowId !== state.flowId) {
        updateFlowId(actualFlowId);
      }

      // Special handling for asset selection submission
      if (questionnaireId === "bootstrap_asset_selection" ||
          questionnaireId === "00000000-0000-0000-0000-000000000001") {
        // Asset selection returns a different response structure
        // Check for success status from the applications endpoint
        // CRITICAL FIX: Match actual backend response structure from collection_applications.py
        // Backend returns: { success: true, selected_application_count: number, mfo_execution_triggered: boolean, ... }
        if (submitResponse.success === true &&
            (submitResponse.selected_application_count > 0 || submitResponse.selected_applications > 0)) {
          console.log("🎯 Asset selection successful, gap analysis triggered");
          console.log("📋 Asset selection response:", submitResponse);
          console.log("🔑 Flow IDs - state.flowId:", state.flowId, "| actualFlowId:", actualFlowId, "| response.flow_id:", submitResponse.flow_id);

          toast({
            title: "Assets Selected Successfully",
            description: `Gap analysis started for ${submitResponse.selected_application_count || submitResponse.selected_applications} asset(s)`,
          });

          // CRITICAL FIX: Navigate to gaps grid instead of polling for questionnaires
          // Backend automatically triggers gap analysis after asset selection (see phase_transition.py line 62)
          // Gap analysis takes ~67ms for tier_1 or 300+ seconds for tier_2

          // IMPORTANT: Use collection_flow_id from response, NOT master_flow_id
          // The backend returns collection_flow.id as flow_id in the response
          const collectionFlowId = submitResponse.flow_id || actualFlowId;
          console.log("🎯 Using collection_flow_id for navigation:", collectionFlowId);

          // Security: Validate flow ID to prevent open redirect vulnerability
          const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
          if (!collectionFlowId || !uuidRegex.test(collectionFlowId)) {
            console.error("❌ Invalid flow ID received from backend:", collectionFlowId);
            toast({
              title: "Navigation Error",
              description: "Invalid flow ID received. Please try again.",
              variant: "destructive",
            });
            return;
          }

          // Wait a moment for gap analysis to complete, then navigate to gaps grid
          const waitTime = 2000; // 2 seconds to allow tier_1 gap analysis to complete
          console.log(`⏳ Waiting ${waitTime}ms for gap analysis to complete before navigating to gaps grid...`);

          setTimeout(() => {
            console.log("✅ Navigating to gap analysis grid with flow_id:", collectionFlowId);
            // Navigate to gaps grid - use window.location to ensure clean page load
            window.location.href = `/collection/gap-analysis/${collectionFlowId}`;
          }, waitTime);

          // Update state to show loading while waiting
          setState((prev) => ({
            ...prev,
            isLoading: true,
          }));

          return; // Exit early for asset selection
        } else {
          throw new Error("Asset selection failed or returned unexpected response");
        }
      }

      toast({
        title: "Adaptive Form Submitted Successfully",
        description:
          "CrewAI agents are processing your responses and will continue the collection flow.",
      });

      console.log(
        "✅ Form submitted successfully, CrewAI agents will continue processing",
      );

      // Refresh questionnaires after successful submission to get the next set
      console.log(
        "🔄 Refreshing questionnaires to check for follow-up questions...",
      );

      // Wait a moment for the backend to process and generate new questionnaires
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Re-fetch questionnaires to get the next set using the actual flow_id
      if (actualFlowId) {
        try {
          const updatedQuestionnaires =
            await collectionFlowApi.getFlowQuestionnaires(actualFlowId);
          console.log(
            `📋 Retrieved ${updatedQuestionnaires.length} questionnaires after submission`,
          );

          setState((prev) => ({
            ...prev,
            questionnaires: updatedQuestionnaires,
            flowId: actualFlowId, // Update to use the correct flow_id from response
          }));

          // If we have new questionnaires, load the first one
          if (updatedQuestionnaires.length > 0) {
            const nextQuestionnaire =
              updatedQuestionnaires.find(
                (q) =>
                  q.completion_status === "pending" ||
                  q.completion_status === "in_progress",
              ) || updatedQuestionnaires[0];

            if (nextQuestionnaire) {
              console.log(
                `📝 Loading next questionnaire: ${nextQuestionnaire.id}`,
              );

              // Convert the questionnaire to form data format
              const nextFormData =
                convertQuestionnaireToFormData(nextQuestionnaire);

              // CRITICAL FIX: Fetch saved responses from API instead of extracting from questionnaire object
              // Responses are stored in collection_questionnaire_responses table, not in the questionnaire
              let existingResponses: CollectionFormData = {};
              try {
                const savedResponsesData =
                  await collectionFlowApi.getQuestionnaireResponses(
                    actualFlowId,
                    nextQuestionnaire.id,
                  );

                if (
                  savedResponsesData?.responses &&
                  Object.keys(savedResponsesData.responses).length > 0
                ) {
                  existingResponses = savedResponsesData.responses;
                  console.log(
                    `📝 Loaded ${Object.keys(existingResponses).length} saved responses from API:`,
                    existingResponses,
                  );
                } else {
                  console.log("📝 No existing responses found for this questionnaire");
                }
              } catch (err) {
                console.warn(
                  "Failed to fetch saved responses, form will start empty:",
                  err,
                );
              }

              setState((prev) => ({
                ...prev,
                formData: nextFormData,
                formValues: existingResponses, // Load existing responses if available
                validation: null,
              }));

              // Show appropriate toast based on whether this is a new or existing questionnaire
              if (Object.keys(existingResponses).length > 0) {
                toast({
                  title: "Questionnaire Loaded",
                  description: `Loaded your previously saved responses. You can review and update them.`,
                });
              } else {
                toast({
                  title: "Next Section Ready",
                  description: `Please continue with: ${nextQuestionnaire.title || "Next questionnaire"}`,
                });
              }
            }
          } else {
            // No more questionnaires returned - collection is complete
            console.log(
              "✅ No more questionnaires - collection flow is complete",
            );

            // CRITICAL FIX: Automatically transition to assessment flow after collection completes
            // This ensures the collection flow properly triggers the assessment phase
            try {
              console.log("🔄 Triggering automatic transition to assessment flow...");
              const transitionResult = await collectionFlowApi.transitionToAssessment(actualFlowId);

              console.log("✅ Transition successful:", transitionResult);

              setState((prev) => ({ ...prev, isCompleted: true }));

              toast({
                title: "Collection Complete - Assessment Ready",
                description: `Your data has been collected successfully. Transitioning to assessment flow...`,
              });

              // Redirect to assessment flow 6R review page (default entry point)
              setTimeout(() => {
                window.location.href = `/assessment/${transitionResult.assessment_flow_id}/sixr-review`;
              }, 2000);

            } catch (transitionError) {
              console.error("❌ Failed to transition to assessment:", transitionError);

              // Fallback to collection complete state if transition fails
              setState((prev) => ({ ...prev, isCompleted: true }));

              // Check if this was a bootstrap form completion
              if (isBootstrapForm) {
                toast({
                  title: "Application Details Saved",
                  description:
                    "Application information has been saved successfully! You can manually start the assessment phase.",
                  variant: "default",
                });
              } else {
                toast({
                  title: "Collection Complete",
                  description:
                    "All required information has been collected. You can manually start the assessment phase.",
                  variant: "default",
                });
              }

              // Fallback: Redirect to collection progress page
              setTimeout(() => {
                window.location.href = `/collection/progress/${actualFlowId}`;
              }, 2000);
            }
          }
        } catch (refreshError) {
          console.error("Failed to refresh questionnaires:", refreshError);
          toast({
            title: "Warning",
            description:
              "Form submitted successfully, but unable to load next section. Please refresh the page.",
            variant: "default",
          });
        }
      }
    } catch (error: unknown) {
      console.error("❌ Adaptive form submission failed:", error);

      const errorMessage =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Failed to submit adaptive form responses.";

      toast({
        title: "Adaptive Form Submission Failed",
        description: `Error: ${errorMessage}`,
        variant: "destructive",
      });
    } finally {
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  }, [
    state.isLoading,
    state.validation,
    state.flowId,
    state.questionnaires,
    state.formData,
    applicationId,
    updateFlowId,
    toast,
  ]);

  return {
    handleSubmit,
  };
}
