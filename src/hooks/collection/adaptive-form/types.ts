/**
 * Type definitions and utilities for adaptive form flow
 * Extracted from useAdaptiveFormFlow.ts for better modularity
 */

import type {
  AdaptiveFormData,
  CollectionFormData,
  FormValidationResult,
} from "@/components/collection/types";
import type {
  FormFieldValue,
  ValidationResult,
} from "@/types/shared/form-types";

// ============================================================================
// INTERFACES
// ============================================================================

export interface FormQuestion {
  id: string;
  question: string;
  type: "text" | "select" | "radio" | "checkbox" | "textarea" | "number";
  required?: boolean;
  options?: string[];
  validation?: ValidationResult;
}

export interface UseAdaptiveFormFlowOptions {
  applicationId?: string | null;
  flowId?: string | null;
  autoInitialize?: boolean;
  onQuestionnaireGenerationStart?: () => void;
}

export interface CollectionQuestionnaire {
  id: string;
  flow_id: string;
  title: string;
  description?: string;
  questions: FormQuestion[];
  created_at: string;
  updated_at: string;
  status: "draft" | "active" | "completed";
}

export interface AdaptiveFormFlowState {
  formData: AdaptiveFormData | null;
  formValues: CollectionFormData;
  validation: FormValidationResult | null;
  flowId: string | null;
  questionnaires: CollectionQuestionnaire[];
  isLoading: boolean;
  isSaving: boolean;
  isCompleted: boolean;
  error: Error | null;
  // New polling state fields
  isPolling: boolean;
  completionStatus: "pending" | "ready" | "fallback" | "failed" | null;
  statusLine: string | null;
  // Enhanced error recovery
  canRetry: boolean;
  isStuck: boolean;
  stuckReason: string | null;
}

export interface AdaptiveFormFlowActions {
  initializeFlow: () => Promise<void>;
  handleFieldChange: (fieldId: string, value: FormFieldValue) => void;
  handleValidationChange: (newValidation: FormValidationResult) => void;
  handleSave: () => Promise<void>;
  handleSubmit: (data: CollectionFormData) => Promise<void>;
  resetFlow: () => void;
  retryFlow: () => Promise<void>;
  forceRefresh: () => Promise<void>;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Extract existing responses from questionnaire to populate form values
 * Handles both array and object response formats for backward compatibility
 *
 * PRESERVED FROM ORIGINAL: Lines 54-133 of useAdaptiveFormFlow.ts
 */
export function extractExistingResponses(
  questionnaire: CollectionQuestionnaire,
): CollectionFormData {
  const responses: CollectionFormData = {};

  try {
    // Check if questionnaire has responses_collected field
    const responsesData = (
      questionnaire as unknown as { responses_collected?: unknown }
    ).responses_collected;

    if (!responsesData) {
      console.log("📝 No existing responses found in questionnaire");
      return responses;
    }

    let latestPayload: unknown = null;

    // Handle different response formats
    if (Array.isArray(responsesData)) {
      // Array format: get the latest submission
      const latestSubmission = responsesData[responsesData.length - 1];
      latestPayload = (latestSubmission as { payload?: unknown })?.payload;
    } else if (typeof responsesData === "object" && responsesData !== null) {
      const responsesObj = responsesData as Record<string, unknown>;
      // Object format: check for latest_submission or history
      if ((responsesObj.latest_submission as { payload?: unknown })?.payload) {
        latestPayload = (
          responsesObj.latest_submission as { payload?: unknown }
        ).payload;
      } else if (responsesObj.history && Array.isArray(responsesObj.history)) {
        const latestFromHistory =
          responsesObj.history[responsesObj.history.length - 1];
        latestPayload = (latestFromHistory as { payload?: unknown })?.payload;
      } else {
        // Direct payload format
        latestPayload = responsesData;
      }
    }

    if (
      latestPayload &&
      typeof latestPayload === "object" &&
      latestPayload !== null
    ) {
      // Convert the payload to form values format
      const payloadObj = latestPayload as Record<string, unknown>;
      Object.keys(payloadObj).forEach((fieldId) => {
        const value = payloadObj[fieldId];

        // Handle different value types appropriately
        if (value !== null && value !== undefined) {
          // Convert to the expected FormFieldValue type
          if (
            typeof value === "string" ||
            typeof value === "number" ||
            typeof value === "boolean"
          ) {
            responses[fieldId] = value;
          } else if (Array.isArray(value)) {
            // Handle array values (e.g., multi-select)
            responses[fieldId] = value;
          } else if (typeof value === "object") {
            // Handle object values (convert to JSON string for text fields)
            responses[fieldId] = JSON.stringify(value);
          }
        }
      });

      console.log(
        `📝 Extracted ${Object.keys(responses).length} existing responses from questionnaire`,
      );
    }
  } catch (error) {
    console.error("❌ Failed to extract existing responses:", error);
    // Return empty responses if extraction fails
  }

  return responses;
}
