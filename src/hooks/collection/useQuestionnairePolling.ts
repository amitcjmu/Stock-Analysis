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
  onReady?: (_questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFallback?: (_questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFailed?: (_errorMessage: string) => void;
}

const MAX_POLL_ATTEMPTS = 12; // 1 minute max at 5 second intervals
const MAX_RETRY_ATTEMPTS = 3; // Allow up to 3 manual retries
const RETRY_DELAY_BASE = 2000; // Base delay for exponential backoff

export const useQuestionnairePolling = ({
  flowId,
  enabled = true,
  onReady,
  onFallback,
  onFailed
}: QuestionnairePollingOptions): QuestionnairePollingState => {
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [completionStatus, setCompletionStatus] = useState<"pending" | "ready" | "fallback" | "failed" | null>(null);
  const [statusLine, setStatusLine] = useState<string | null>(null);
  const [pollAttempts, setPollAttempts] = useState(0);
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
          case 'ready':
            setIsPolling(false);
            setError(null);
            callbacksRef.current.onReady?.(questionnaires);
            break;

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
  const {
    data: questionnaires = [],
    isLoading,
    refetch
  } = useQuery({
    queryKey: ['questionnaires', flowId],
    queryFn: fetchQuestionnaires,
    enabled: enabled && !!flowId,
    // Polling configuration based on completion status
    refetchInterval: () => {
      // Only poll if status is pending and within attempt limits
      if (completionStatus === 'pending' && isPolling) {
        // Check if we're still within attempt limits
        if (pollAttempts < MAX_POLL_ATTEMPTS) {
          // Increment attempts for next poll
          setPollAttempts(prev => {
            const newAttempts = prev + 1;
            console.log('📊 Poll attempt', newAttempts, 'of', MAX_POLL_ATTEMPTS);
            return newAttempts;
          });
          return 5000; // Poll every 5 seconds
        } else {
          // We've reached max attempts, stop polling
          console.log('⏰ Max poll attempts reached, stopping polling');
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
  useEffect(() => {
    if (enabled && flowId && !questionnaires.length) {
      // Only check timeout if we're actually polling
      if (isPolling && pollAttempts >= MAX_POLL_ATTEMPTS) {
        console.log('⏰ Polling timeout reached after', pollAttempts, 'attempts');
        setIsPolling(false);
        setCompletionStatus('failed');
        setStatusLine('Questionnaire generation timed out. Please try again.');
        setError(new Error('Questionnaire generation timed out'));
        callbacksRef.current.onFailed?.('Questionnaire generation timed out. Please try again.');
      } else if (!isPolling && pollAttempts < MAX_POLL_ATTEMPTS) {
        // Start polling if not already polling and within attempt limits
        console.log('🔄 Starting questionnaire polling for flow:', flowId);
        setIsPolling(true);
        setError(null);
        setCompletionStatus('pending');
        setStatusLine('Checking questionnaire status...');
      }
    }
  }, [enabled, flowId, questionnaires.length, pollAttempts, isPolling]);

  // Reset poll attempts and polling state when flowId changes
  useEffect(() => {
    console.log('🔄 Flow ID changed, resetting polling state for:', flowId);
    setPollAttempts(0);
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
      setPollAttempts(0);
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
