import { useEffect, useRef } from 'react';

interface UseAutoExecutionProps {
  flow: {
    raw_data?: unknown[];
    phases_completed?: string[];
    phase_completion?: { data_cleansing?: boolean };
    status?: string;
    current_phase?: string;
  } | null;
  isExecutingPhase: boolean;
  hasTriggeredInventory: boolean;
  assetsLength: number;
  executeFlowPhase: (phase: string, params: unknown) => Promise<void>;
  refetchAssets: () => void;
  refreshFlow: () => void;
  executionError: string | null;
  setHasTriggeredInventory: (value: boolean) => void;
  setExecutionError: (value: string | null) => void;
  setShowCleansingRequiredBanner: (value: boolean) => void;
}

/**
 * CRITICAL: Auto-execution hook with retry state machine and exponential backoff
 * Lines 523-648 from InventoryContent.tsx
 *
 * This hook MUST preserve:
 * - Ref-based loop guards (attemptCountRef)
 * - Exact useEffect dependency arrays
 * - HTTP polling logic
 * - Retry state machine with exponential backoff
 */
export const useAutoExecution = ({
  flow,
  isExecutingPhase,
  hasTriggeredInventory,
  assetsLength,
  executeFlowPhase,
  refetchAssets,
  refreshFlow,
  executionError,
  setHasTriggeredInventory,
  setExecutionError,
  setShowCleansingRequiredBanner
}: UseAutoExecutionProps) => {
  // CRITICAL: Ref-based loop guard - MUST preserve
  const attemptCountRef = useRef(0);
  const maxRetryAttempts = 3;

  // Auto-execute asset inventory phase if conditions are met with proper gating and error handling
  useEffect(() => {
    // Use setTimeout to delay execution until after page render
    const timeoutId = setTimeout(() => {
      // CRITICAL CONDITIONS: All must be true for auto-execution
      const hasRawData = flow && flow.raw_data && flow.raw_data.length > 0;
      const hasNoAssets = assetsLength === 0;
      // FIX #447: Backend returns phases_completed as array, not phase_completion object
      // Support both data formats for backward compatibility
      const dataCleansingCompleted =
        flow?.phases_completed?.includes('data_cleansing') ||
        flow?.phase_completion?.data_cleansing === true;
      // FIX #447 Priority 3: Filter out deleted flows
      const flowNotDeleted = flow?.status !== 'deleted';
      const notExecuting = !isExecutingPhase;
      const notTriggered = !hasTriggeredInventory;
      const withinRetryLimit = attemptCountRef.current < maxRetryAttempts;

      // Clear any previous execution errors when conditions change
      if (hasRawData && hasNoAssets && dataCleansingCompleted && !executionError) {
        setExecutionError(null);
        setShowCleansingRequiredBanner(false);
      }

      // Log the conditions for debugging
      console.log('🔍 Auto-execute conditions (gated):', {
        hasRawData,
        rawDataCount: flow?.raw_data?.length || 0,
        hasNoAssets,
        dataCleansingCompleted,
        flowNotDeleted,
        flowStatus: flow?.status,
        notExecuting,
        notTriggered,
        withinRetryLimit,
        attemptCount: attemptCountRef.current,
        currentPhase: flow?.current_phase,
        phaseCompletion: flow?.phase_completion,
        phasesCompleted: flow?.phases_completed
      });

      // GATED AUTO-EXECUTION: Only execute when ALL conditions are met
      const shouldAutoExecute = hasRawData &&
                               hasNoAssets &&
                               dataCleansingCompleted &&
                               flowNotDeleted &&
                               notExecuting &&
                               notTriggered &&
                               withinRetryLimit;

      if (shouldAutoExecute) {
        console.log('🚀 Auto-executing asset inventory phase (gated execution)...');
        setHasTriggeredInventory(true);
        attemptCountRef.current += 1;

        executeFlowPhase('asset_inventory', {
          trigger: 'auto',
          source: 'inventory_page_gated_auto_execution'
        }).then(() => {
          console.log('✅ Asset inventory phase execution initiated');
          // Reset attempt counter on success
          attemptCountRef.current = 0;
          // Refetch after a delay
          setTimeout(() => {
            refetchAssets();
            refreshFlow();
          }, 3000);
        }).catch(error => {
          console.error('❌ Failed to auto-execute asset inventory phase:', error);

          // Parse error response for specific handling
          let errorCode = null;

          try {
            if (error?.response?.data?.error_code) {
              errorCode = error.response.data.error_code;
            } else if (error?.message && error.message.includes('422')) {
              errorCode = 'CLEANSING_REQUIRED';
            }
          } catch (parseError) {
            console.warn('Could not parse error response:', parseError);
          }

          if (errorCode === 'CLEANSING_REQUIRED') {
            // 422 CLEANSING_REQUIRED: Do NOT reset hasTriggeredInventory, show banner
            console.log('🚨 Data cleansing required - stopping auto-execution');
            setExecutionError('Data cleansing must be completed before generating asset inventory.');
            setShowCleansingRequiredBanner(true);
            // Do NOT reset hasTriggeredInventory to prevent retry loop
          } else {
            // Handle HTTP status codes for retry logic
            const httpStatus = error?.response?.status || 0;

            if (httpStatus === 429 || (httpStatus >= 500 && httpStatus < 600)) {
              // Transient errors: 429 (rate limit) or 5xx (server errors)
              if (attemptCountRef.current < maxRetryAttempts) {
                const backoffDelay = Math.min(1000 * Math.pow(2, attemptCountRef.current - 1), 30000);
                console.log(`🔄 Transient error (${httpStatus}), will retry in ${backoffDelay}ms (attempt ${attemptCountRef.current}/${maxRetryAttempts})`);

                setTimeout(() => {
                  setHasTriggeredInventory(false); // Allow retry
                }, backoffDelay);
              } else {
                console.log(`❌ Max retry attempts (${maxRetryAttempts}) reached for transient error`);
                setExecutionError(`Server temporarily unavailable. Please try again later. (Status: ${httpStatus})`);
              }
            } else if (httpStatus === 401 || httpStatus === 403) {
              // Authentication/Authorization errors: Do not retry
              console.log(`❌ Authentication error (${httpStatus}) - no retry`);
              setExecutionError(`Authentication error. Please refresh the page and try again.`);
              // Do NOT reset hasTriggeredInventory
            } else {
              // Other errors: Do not retry but reset for manual retry
              console.log(`❌ Non-retryable error: ${error.message}`);
              setExecutionError(`Execution failed: ${error.message}`);
              setHasTriggeredInventory(false); // Allow manual retry
            }
          }
        });
      }
    }, 1500); // 1.5 second delay to ensure page is fully rendered

    // Cleanup timeout on unmount
    return () => clearTimeout(timeoutId);
  }, [flow, isExecutingPhase, hasTriggeredInventory, assetsLength, executeFlowPhase, refetchAssets, refreshFlow, executionError, setExecutionError, setHasTriggeredInventory, setShowCleansingRequiredBanner]);

  return {
    attemptCountRef,
    maxRetryAttempts
  };
};
