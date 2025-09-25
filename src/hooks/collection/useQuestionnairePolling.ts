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
  checkStatus: () => void;
}

export interface QuestionnairePollingOptions {
  flowId: string;
  enabled?: boolean;
  onReady?: (_questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFallback?: (_questionnaires: AdaptiveQuestionnaireResponse[]) => void;
  onFailed?: (_errorMessage: string) => void;
}

const MAX_POLL_ATTEMPTS = 12; // 1 minute max at 5 second intervals

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
          throw err;
        }
      }

      setError(err as Error);
      setIsPolling(false);
      setCompletionStatus('failed');
      setStatusLine('Failed to fetch questionnaire status');
      throw err;
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
      if (completionStatus === 'pending' && isPolling && pollAttempts < MAX_POLL_ATTEMPTS) {
        setPollAttempts(prev => prev + 1);
        return 5000; // Poll every 5 seconds
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
    if (enabled && flowId && !questionnaires.length && pollAttempts < MAX_POLL_ATTEMPTS) {
      console.log('🔄 Starting questionnaire polling for flow:', flowId);
      setIsPolling(true);
      setError(null);
      setCompletionStatus('pending');
      setStatusLine('Checking questionnaire status...');
      // Reset poll attempts when starting fresh
      if (pollAttempts === 0) {
        setPollAttempts(0);
      }
    } else if (pollAttempts >= MAX_POLL_ATTEMPTS) {
      setIsPolling(false);
      setCompletionStatus('failed');
      setStatusLine('Questionnaire generation timed out. Please try again.');
      setError(new Error('Questionnaire generation timed out'));
      callbacksRef.current.onFailed?.('Questionnaire generation timed out. Please try again.');
    }
  }, [enabled, flowId, questionnaires.length, pollAttempts]);

  // Reset poll attempts when flowId changes
  useEffect(() => {
    setPollAttempts(0);
  }, [flowId]);

  // Expose method to manually trigger a status check
  const checkStatus = useCallback(() => {
    if (flowId) {
      refetch();
    }
  }, [flowId, refetch]);

  return {
    questionnaires,
    isPolling: isPolling || isLoading,
    error,
    completionStatus,
    statusLine,
    checkStatus
  };
};
