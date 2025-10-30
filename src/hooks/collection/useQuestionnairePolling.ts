/**
 * Custom hook for handling questionnaire polling with completion status
 *
 * Implements the new polling logic from questionnaire-generation-fix-plan.md:
 * - Poll every 5 seconds when completion_status === 'pending'
 * - Stop polling when status is 'ready', 'fallback', or 'failed'
 * - Display appropriate UI states based on completion_status
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { collectionFlowApi } from '@/services/api/collection-flow';
import type { AdaptiveQuestionnaireResponse } from '@/services/api/collection-flow';

export interface QuestionnairePollingState {
  questionnaires: AdaptiveQuestionnaireResponse[];
  isPolling: boolean;
  error: Error | null;
  completionStatus: "pending" | "ready" | "fallback" | "failed" | null;
  statusLine: string | null;
  retryCount: number;
  canRetry: boolean;
  checkStatus: () => void;
  retryPolling: () => void;
}

export interface QuestionnairePollingOptions {
  flowId: string;
  enabled?: boolean;
  currentPhase?: string | null; // Deprecated (Issue #806): No longer used, kept for backward compatibility
  onReady?: (_questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFallback?: (_questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFailed?: (_errorMessage: string) => void;
}

const POLLING_INTERVAL_MS = 5000; // 5 seconds (CRITICAL: Fast polling to catch questionnaire ready status)
const TOTAL_POLLING_TIMEOUT_MS = 12 * 60 * 1000; // 12 minutes total timeout
const MAX_RETRY_ATTEMPTS = 3; // Allow up to 3 manual retries
const RETRY_DELAY_BASE = 2000; // Base delay for exponential backoff

export const useQuestionnairePolling = ({
  flowId,
  enabled = true,
  currentPhase = null,
  onReady,
  onFallback,
  onFailed
}: QuestionnairePollingOptions): QuestionnairePollingState => {
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [completionStatus, setCompletionStatus] = useState<"pending" | "ready" | "fallback" | "failed" | null>(null);
  const [statusLine, setStatusLine] = useState<string | null>(null);
  const pollStartTimeRef = useRef<number | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const callbacksRef = useRef({ onReady, onFallback, onFailed });

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = { onReady, onFallback, onFailed };
  }, [onReady, onFallback, onFailed]);

  // Function to fetch questionnaires and check completion status
  const fetchQuestionnaires = useCallback(async (): Promise<AdaptiveQuestionnaireResponse[]> => {
    if (!flowId) {
      throw new Error('Flow ID is required');
    }

    try {
      const questionnaires = await collectionFlowApi.getFlowQuestionnaires(flowId);
      console.log('📋 Fetched questionnaires:', questionnaires);

      // If we have questionnaires, use them immediately
      if (questionnaires.length > 0) {
        const firstQuestionnaire = questionnaires[0];

        // Check if this is a bootstrap questionnaire for asset selection
        if (firstQuestionnaire.id === 'bootstrap_asset_selection') {
          console.log('🎯 Bootstrap questionnaire detected - using immediately');
          setIsPolling(false);
          setError(null);
          setCompletionStatus('ready');
          setStatusLine('Asset selection questionnaire ready');
          callbacksRef.current.onReady?.(questionnaires);
          return questionnaires;
        }

        // For regular questionnaires, check completion status if provided
        const status = firstQuestionnaire.completion_status;
        const statusMessage = firstQuestionnaire.status_line;

        // If no completion_status field, treat as ready
        if (!status) {
          console.log('✅ Questionnaire ready (no status field)');
          setIsPolling(false);
          setError(null);
          setCompletionStatus('ready');
          setStatusLine(statusMessage || 'Questionnaire ready');
          callbacksRef.current.onReady?.(questionnaires);
          return questionnaires;
        }

        setCompletionStatus(status);
        setStatusLine(statusMessage || null);

        console.log(`📊 Questionnaire completion status: ${status}`, {
          statusLine: statusMessage,
          questionnaireCount: questionnaires.length
        });

        // Handle different completion statuses
        switch (status) {
          case 'ready': {
            // CRITICAL FIX: Verify questions array is populated before transitioning to ready
            // Backend may set status='ready' slightly before questions are committed
            const hasQuestions = firstQuestionnaire.questions && firstQuestionnaire.questions.length > 0;

            if (hasQuestions) {
              console.log(`✅ Questionnaire ready with ${firstQuestionnaire.questions.length} questions`);
              setIsPolling(false);
              setError(null);
              callbacksRef.current.onReady?.(questionnaires);
            } else {
              // Status is 'ready' but questions not yet populated - continue polling
              console.log('⏳ Status is ready but questions not yet available, continuing to poll...');
              setIsPolling(true);
              setCompletionStatus('pending'); // Keep in pending state
              setStatusLine('Finalizing questionnaire...');
            }
            break;
          }

          case 'fallback':
            setIsPolling(false);
            setError(null);
            callbacksRef.current.onFallback?.(questionnaires);
            break;

          case 'failed': {
            setIsPolling(false);
            const errorMessage = statusMessage || 'Questionnaire generation failed';
            setError(new Error(errorMessage));
            callbacksRef.current.onFailed?.(errorMessage);
            break;
          }

          case 'pending':
            // Continue polling only if explicitly pending
            setIsPolling(true);
            setError(null);
            break;

          default:
            // Unknown status - treat as ready
            console.log('✅ Questionnaire ready (unknown status)');
            setIsPolling(false);
            setError(null);
            callbacksRef.current.onReady?.(questionnaires);
            break;
        }
      } else {
        // No questionnaires found - could mean still generating or error
        setCompletionStatus('pending');
        setStatusLine('Generating questionnaire...');
        setIsPolling(true);
      }

      return questionnaires;
    } catch (err) {
      console.error('❌ Failed to fetch questionnaires:', err);

      // Handle specific error cases
      if (err && typeof err === 'object' && 'code' in err) {
        const error = err as { code: string; status?: number };
        if (error.code === 'no_applications_selected' && error.status === 422) {
          // This is a specific error case, not a polling failure
          setError(err as Error);
          setIsPolling(false);
          setCompletionStatus('failed');
          setStatusLine('No applications selected for collection. Please select assets first.');
          throw err;
        }
      }

      // Categorize errors for better user experience
      const errorMessage = err instanceof Error ? err.message : String(err);
      let userFriendlyMessage = 'Failed to fetch questionnaire status';
      let canRetryError = true;

      if (errorMessage.includes('Network Error') || errorMessage.includes('fetch')) {
        userFriendlyMessage = 'Network connection error. Please check your connection and try again.';
      } else if (errorMessage.includes('timeout')) {
        userFriendlyMessage = 'Request timed out. The server may be busy, please try again.';
      } else if (errorMessage.includes('500') || errorMessage.includes('Internal Server Error')) {
        userFriendlyMessage = 'Server error occurred. Please try again in a moment.';
      } else if (errorMessage.includes('404') || errorMessage.includes('Not Found')) {
        userFriendlyMessage = 'Flow not found. The collection flow may have been removed.';
        canRetryError = false;
      } else if (errorMessage.includes('403') || errorMessage.includes('Forbidden')) {
        userFriendlyMessage = 'Access denied. You may not have permission to access this flow.';
        canRetryError = false;
      }

      setError(err as Error);
      setIsPolling(false);
      setCompletionStatus('failed');
      setStatusLine(userFriendlyMessage);

      // Don't throw if it's a retryable error to allow graceful handling
      if (!canRetryError) {
        throw err;
      }
    }
  }, [flowId]);;

  // Use React Query for data fetching with conditional polling
  // CRITICAL FIX (Issue #806): Removed phase dependency to prevent race condition
  // The completion_status field in the API response is sufficient to determine readiness.
  // Phase checking adds unnecessary complexity and creates stale prop issues when
  // the phase query terminates before updating the currentPhase prop.
  const shouldEnablePolling = enabled && !!flowId;

  const {
    data: questionnaires = [],
    isLoading,
    refetch
  } = useQuery({
    queryKey: ['questionnaires', flowId],
    queryFn: fetchQuestionnaires,
    enabled: shouldEnablePolling,
    // Polling configuration based on completion status
    refetchInterval: () => {
      // CRITICAL FIX (Issue #863): Continue polling while isPolling is true
      // The completionStatus state may be stale (from previous fetch), so we rely on
      // isPolling flag which is set to false inside fetchQuestionnaires when status becomes 'ready'
      if (isPolling) {
        // Initialize polling start time on first poll
        if (pollStartTimeRef.current === null) {
          pollStartTimeRef.current = Date.now();
        }

        // Calculate elapsed time
        const elapsedTime = Date.now() - pollStartTimeRef.current;

        // Check if we're still within the total timeout
        if (elapsedTime < TOTAL_POLLING_TIMEOUT_MS) {
          const elapsedSeconds = Math.round(elapsedTime / 1000);
          const totalSeconds = TOTAL_POLLING_TIMEOUT_MS / 1000;
          console.log(`📊 Polling (elapsed: ${elapsedSeconds}s / ${totalSeconds}s) @ useQuestionnairePolling`);
          return POLLING_INTERVAL_MS;
        } else {
          // We've reached the total timeout, stop polling
          console.log('⏰ Total polling timeout reached, stopping polling');
          return false;
        }
      }
      return false; // Stop polling
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    // Keep data for 30 seconds to prevent unnecessary re-fetching
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000, // 5 minutes cache time
    retry: (failureCount, error) => {
      // Don't retry on specific errors
      if (error && typeof error === 'object' && 'code' in error) {
        const typedError = error as { code: string; status?: number };
        if (typedError.code === 'no_applications_selected' && typedError.status === 422) {
          return false;
        }
      }
      // Retry up to 3 times for other errors
      return failureCount < 3;
    }
  });

  // Start polling when enabled and we have a flow ID
  // Simplified polling logic (Issue #806): No phase checks, rely on completion_status
  useEffect(() => {
    if (!shouldEnablePolling) {
      return;
    }

    if (enabled && flowId && !questionnaires.length) {
      // Check if polling has timed out based on elapsed time
      if (isPolling && pollStartTimeRef.current !== null) {
        const elapsedTime = Date.now() - pollStartTimeRef.current;
        if (elapsedTime >= TOTAL_POLLING_TIMEOUT_MS) {
          console.log('⏰ Polling timeout reached after', Math.round(elapsedTime / 1000), 'seconds');
          setIsPolling(false);
          setCompletionStatus('failed');
          setStatusLine('Questionnaire generation timed out. Please try again.');
          setError(new Error('Questionnaire generation timed out'));
          callbacksRef.current.onFailed?.('Questionnaire generation timed out. Please try again.');
        }
      } else if (!isPolling && pollStartTimeRef.current === null) {
        // Start polling if not already polling
        console.log('🔄 Starting questionnaire polling for flow:', flowId);
        pollStartTimeRef.current = Date.now();
        setIsPolling(true);
        setError(null);
        setCompletionStatus('pending');
        setStatusLine('Checking questionnaire status...');
      }
    }
  }, [enabled, flowId, questionnaires.length, isPolling, shouldEnablePolling]);

  // Reset polling state when flowId changes
  useEffect(() => {
    console.log('🔄 Flow ID changed, resetting polling state for:', flowId);
    pollStartTimeRef.current = null;  // Reset polling start time
    setRetryCount(0);  // Reset retry count on flow change
    setIsPolling(false);
    setError(null);
    setCompletionStatus(null);
    setStatusLine(null);
  }, [flowId]);

  // Expose method to manually trigger a status check
  const checkStatus = useCallback(() => {
    if (flowId) {
      refetch();
    }
  }, [flowId, refetch]);

  // Expose method to retry polling after failure
  const retryPolling = useCallback(() => {
    if (retryCount < MAX_RETRY_ATTEMPTS) {
      console.log(`🔄 Retrying questionnaire polling (attempt ${retryCount + 1}/${MAX_RETRY_ATTEMPTS})`);
      setRetryCount(prev => prev + 1);
      pollStartTimeRef.current = null;  // Reset polling start time for retry
      setError(null);
      setIsPolling(true);
      setCompletionStatus('pending');
      setStatusLine('Retrying questionnaire status check...');
      refetch();
    }
  }, [retryCount, refetch]);

  const canRetry = retryCount < MAX_RETRY_ATTEMPTS && completionStatus === 'failed' && !!error;

  return {
    questionnaires,
    isPolling: isPolling || isLoading,
    error,
    completionStatus,
    statusLine,
    retryCount,
    canRetry,
    checkStatus,
    retryPolling
  };
};
