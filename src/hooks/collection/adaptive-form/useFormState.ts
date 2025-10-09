/**
 * Form state management hook for adaptive form flow
 * Manages state, refs, and centralized flow ID updates
 *
 * PRESERVED FROM ORIGINAL: Lines 215-256 of useAdaptiveFormFlow.ts
 */

import { useState, useRef, useCallback } from "react";
import type { AdaptiveFormFlowState } from "./types";

export interface UseFormStateReturn {
  state: AdaptiveFormFlowState;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
  currentFlowIdRef: React.MutableRefObject<string | null>;
  updateFlowId: (newFlowId: string | null) => void;
}

export function useFormState(initialFlowId: string | null): UseFormStateReturn {
  // CRITICAL FIX: Single source of truth for flow ID
  // Flow state - use ref to prevent infinite loops with flow ID updates
  const currentFlowIdRef = useRef<string | null>(initialFlowId);

  // Main form state
  const [state, setState] = useState<AdaptiveFormFlowState>({
    formData: null,
    formValues: {},
    validation: null,
    flowId: initialFlowId, // Initialize with URL flow ID
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

  // CRITICAL FIX: Centralized flow ID management
  // This function ensures all flow ID updates go through a single point
  const updateFlowId = useCallback((newFlowId: string | null) => {
    if (newFlowId && newFlowId !== currentFlowIdRef.current) {
      console.log("🔄 Updating flow ID:", {
        from: currentFlowIdRef.current,
        to: newFlowId
      });
      currentFlowIdRef.current = newFlowId;
      setState((prev) => ({ ...prev, flowId: newFlowId }));
    }
  }, []);

  return {
    state,
    setState,
    currentFlowIdRef,
    updateFlowId,
  };
}
