/**
 * Validation handlers for adaptive form flow
 * Manages field changes and validation state updates
 *
 * PRESERVED FROM ORIGINAL: Lines 1113-1136 of useAdaptiveFormFlow.ts
 */

import { useCallback } from "react";
import type { FormFieldValue } from "@/types/shared/form-types";
import type { FormValidationResult } from "@/components/collection/types";
import type { CollectionFormData } from "@/components/collection/types";
import type { AdaptiveFormFlowState } from "./types";

export interface UseValidationProps {
  state: AdaptiveFormFlowState;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
}

export interface UseValidationReturn {
  handleFieldChange: (fieldId: string, value: FormFieldValue) => void;
  handleValidationChange: (newValidation: FormValidationResult) => void;
}

export function useValidation({
  state,
  setState,
}: UseValidationProps): UseValidationReturn {
  /**
   * Handle field value changes - wrapped in useCallback for performance
   * PRESERVED FROM ORIGINAL: Lines 1113-1126
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
   * PRESERVED FROM ORIGINAL: Lines 1129-1136
   */
  const handleValidationChange = useCallback(
    (newValidation: FormValidationResult): void => {
      setState((prev) => ({ ...prev, validation: newValidation }));
    },
    // setState is intentionally omitted - React guarantees setState is stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  return {
    handleFieldChange,
    handleValidationChange,
  };
}
