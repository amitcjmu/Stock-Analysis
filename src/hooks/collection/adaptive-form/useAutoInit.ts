/**
 * Auto-initialization effects for adaptive form flow
 * Manages automatic flow initialization with ref-based guards to prevent infinite loops
 *
 * PRESERVED FROM ORIGINAL: Lines 1714-1836 of useAdaptiveFormFlow.ts
 * CRITICAL: useEffect dependency arrays MUST remain exact to prevent infinite loops
 */

import { useState, useEffect } from "react";
import type { AdaptiveFormFlowState } from "./types";

export interface UseAutoInitProps {
  urlFlowId: string | null;
  autoInitialize: boolean;
  skipIncompleteCheck: boolean;
  checkingFlows: boolean;
  hasBlockingFlows: boolean;
  formData: AdaptiveFormFlowState["formData"];
  isLoading: boolean;
  error: Error | null;
  initializeFlow: () => Promise<void>;
  setState: React.Dispatch<React.SetStateAction<AdaptiveFormFlowState>>;
}

export interface UseAutoInitReturn {
  hasAttemptedInit: string | null;
  hasAttemptedNewFlowInit: boolean;
}

/**
 * Auto-initialization hook with ref-based guards
 * Handles both continuing flows (with urlFlowId) and new flow creation
 */
export function useAutoInit({
  urlFlowId,
  autoInitialize,
  skipIncompleteCheck,
  checkingFlows,
  hasBlockingFlows,
  formData,
  isLoading,
  error,
  initializeFlow,
  setState,
}: UseAutoInitProps): UseAutoInitReturn {
  // Track if we've attempted initialization for this flowId
  // PRESERVED FROM ORIGINAL: Line 1714
  const [hasAttemptedInit, setHasAttemptedInit] = useState<string | null>(null);

  // Track if we've attempted auto-init for new flows
  // PRESERVED FROM ORIGINAL: Line 1777
  const [hasAttemptedNewFlowInit, setHasAttemptedNewFlowInit] = useState(false);

  // Fetch questionnaires on mount if flowId exists (for continuing flows)
  // PRESERVED FROM ORIGINAL: Lines 1717-1774
  // CRITICAL: Dependency array MUST remain exact
  useEffect(() => {
    console.log("🔍 Checking continuing flow conditions:", {
      urlFlowId,
      autoInitialize,
      hasFormData: !!formData,
      isLoading,
      skipIncompleteCheck,
      checkingFlows,
      hasBlockingFlows,
      hasError: !!error,
      hasAttemptedInit,
      shouldInitialize:
        urlFlowId &&
        autoInitialize &&
        !formData &&
        !isLoading &&
        (skipIncompleteCheck || (!checkingFlows && !hasBlockingFlows)) &&
        !error &&
        hasAttemptedInit !== urlFlowId,
    });

    // CRITICAL FIX: Track initialization attempts to prevent infinite loops
    // Only initialize if we haven't already attempted for this specific flowId
    // When continuing a flow (skipIncompleteCheck=true), ignore blocking flows
    if (
      urlFlowId &&
      autoInitialize &&
      !formData &&
      !isLoading &&
      (skipIncompleteCheck || (!checkingFlows && !hasBlockingFlows)) &&
      !error &&
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
    formData,
    isLoading,
    skipIncompleteCheck,
    checkingFlows,
    hasBlockingFlows,
    error,
    hasAttemptedInit,
    initializeFlow,
    setState,
  ]); // CRITICAL: Do not modify this dependency array

  // Auto-initialize effect - Fixed to prevent infinite loops
  // PRESERVED FROM ORIGINAL: Lines 1780-1825
  // CRITICAL: Dependency array MUST remain exact
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
      !formData &&
      !isLoading &&
      !error &&
      !urlFlowId &&
      !hasAttemptedNewFlowInit
    ) {
      console.log("🚀 Auto-initializing new collection flow...", {
        hasFormData: !!formData,
        hasBlockingFlows,
        isLoading,
        hasError: !!error,
      });
      setHasAttemptedNewFlowInit(true); // Mark as attempted BEFORE initializing
      initializeFlow().catch((error) => {
        console.error("❌ Auto-initialization failed:", error);
        // Don't retry - let the user manually retry or handle the error
        setState((prev) => ({ ...prev, error, isLoading: false }));
      });
    }
  }, [
    urlFlowId,
    checkingFlows,
    hasBlockingFlows,
    autoInitialize,
    formData,
    isLoading,
    error,
    hasAttemptedNewFlowInit,
    initializeFlow,
    setState,
  ]); // CRITICAL: Do not modify this dependency array (includes hasAttemptedNewFlowInit to prevent loops)

  return {
    hasAttemptedInit,
    hasAttemptedNewFlowInit,
  };
}
