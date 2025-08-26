import { useState, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { canonicalApplicationsApi } from '@/services/api/canonical-applications';
import type {
  SimilarityMatch,
  SimilaritySearchRequest,
  DEFAULT_DEDUPLICATION_CONFIG,
  DuplicateDecision,
} from '@/types/collection/canonical-applications';

interface UseDuplicateDetectionOptions {
  confidenceThresholds?: typeof DEFAULT_DEDUPLICATION_CONFIG.confidence_thresholds;
  autoTriggerThreshold?: number; // Automatically trigger modal above this threshold
  onDuplicateDetected?: (matches: SimilarityMatch[]) => void;
  onDecisionMade?: (decision: DuplicateDecision, matches: SimilarityMatch[], selectedMatch?: SimilarityMatch) => void;
}

interface UseDuplicateDetectionReturn {
  duplicateMatches: SimilarityMatch[];
  isDuplicateDetected: boolean;
  isChecking: boolean;
  error: string | null;
  checkForDuplicates: (query: string) => Promise<SimilarityMatch[]>;
  clearDuplicateState: () => void;
  processDuplicateDecision: (
    decision: DuplicateDecision,
    selectedMatch?: SimilarityMatch
  ) => Promise<void>;
}

/**
 * useDuplicateDetection Hook
 *
 * Manages duplicate detection logic, including checking for potential duplicates,
 * managing detection state, and processing user decisions about duplicates.
 */
export const useDuplicateDetection = (
  options: UseDuplicateDetectionOptions = {}
): UseDuplicateDetectionReturn => {
  const {
    confidenceThresholds,
    autoTriggerThreshold = 0.8,
    onDuplicateDetected,
    onDecisionMade,
  } = options;

  const { client, engagement } = useAuth();
  const [duplicateMatches, setDuplicateMatches] = useState<SimilarityMatch[]>([]);
  const [isDuplicateDetected, setIsDuplicateDetected] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref to track the last checked query to avoid duplicate checks
  const lastCheckedQueryRef = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check for duplicates
  const checkForDuplicates = useCallback(async (query: string): Promise<SimilarityMatch[]> => {
    if (!client || !engagement) {
      console.warn('Cannot check for duplicates: client and engagement must be available');
      return [];
    }

    const trimmedQuery = query.trim();
    if (trimmedQuery.length < 2) {
      return [];
    }

    // Avoid duplicate checks for the same query
    if (lastCheckedQueryRef.current === trimmedQuery) {
      return duplicateMatches;
    }

    setIsChecking(true);
    setError(null);
    lastCheckedQueryRef.current = trimmedQuery;

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const searchRequest: SimilaritySearchRequest = {
        query: trimmedQuery,
        client_account_id: client.id,
        engagement_id: engagement.id,
        min_confidence: confidenceThresholds?.duplicate_warning || autoTriggerThreshold,
        max_results: 5, // Limit for duplicate detection
        include_variants: true,
      };

      const response = await canonicalApplicationsApi.searchSimilar(searchRequest);

      // Filter matches that are above the duplicate warning threshold
      const potentialDuplicates = response.matches.filter(
        match => match.confidence_score >= (confidenceThresholds?.duplicate_warning || autoTriggerThreshold)
      );

      // Sort by confidence score (highest first)
      const sortedMatches = potentialDuplicates.sort(
        (a, b) => b.confidence_score - a.confidence_score
      );

      setDuplicateMatches(sortedMatches);
      setIsDuplicateDetected(sortedMatches.length > 0);

      if (sortedMatches.length > 0) {
        console.log(`🔍 Detected ${sortedMatches.length} potential duplicates for "${trimmedQuery}"`);
        onDuplicateDetected?.(sortedMatches);
      }

      return sortedMatches;
    } catch (error: any) {
      // Don't treat aborted requests as errors
      if (error.name === 'AbortError') {
        return [];
      }

      console.error('Error checking for duplicates:', error);
      setError(error.message || 'Failed to check for duplicates');
      return [];
    } finally {
      setIsChecking(false);
    }
  }, [
    client,
    engagement,
    confidenceThresholds,
    autoTriggerThreshold,
    duplicateMatches,
    onDuplicateDetected,
  ]);

  // Clear duplicate state
  const clearDuplicateState = useCallback(() => {
    setDuplicateMatches([]);
    setIsDuplicateDetected(false);
    setError(null);
    setIsChecking(false);
    lastCheckedQueryRef.current = '';

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Process user decision about duplicates
  const processDuplicateDecision = useCallback(async (
    decision: DuplicateDecision,
    selectedMatch?: SimilarityMatch
  ): Promise<void> => {
    try {
      console.log(`📝 Processing duplicate decision: ${decision}`, {
        selectedMatch: selectedMatch?.canonical_application.canonical_name,
        totalMatches: duplicateMatches.length,
      });

      // Call the decision callback if provided
      onDecisionMade?.(decision, duplicateMatches, selectedMatch);

      // Clear the duplicate state after processing
      clearDuplicateState();
    } catch (error: any) {
      console.error('Error processing duplicate decision:', error);
      setError(error.message || 'Failed to process duplicate decision');
      throw error;
    }
  }, [duplicateMatches, onDecisionMade, clearDuplicateState]);

  // Clean up on unmount
  React.useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Clear state when client or engagement changes
  React.useEffect(() => {
    clearDuplicateState();
  }, [client?.id, engagement?.id, clearDuplicateState]);

  return {
    duplicateMatches,
    isDuplicateDetected,
    isChecking,
    error,
    checkForDuplicates,
    clearDuplicateState,
    processDuplicateDecision,
  };
};
