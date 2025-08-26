import { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { canonicalApplicationsApi } from '@/services/api/canonical-applications';
import type {
  ApplicationSuggestion,
  SimilaritySearchRequest,
  DEFAULT_DEDUPLICATION_CONFIG,
} from '@/types/collection/canonical-applications';

interface UseApplicationSuggestionsOptions {
  maxResults?: number;
  debounceMs?: number;
  confidenceThresholds?: typeof DEFAULT_DEDUPLICATION_CONFIG.confidence_thresholds;
  cacheResults?: boolean;
}

interface UseApplicationSuggestionsReturn {
  suggestions: ApplicationSuggestion[];
  isLoading: boolean;
  error: string | null;
  searchSuggestions: (query: string) => Promise<void>;
  clearSuggestions: () => void;
  refreshSuggestions: () => Promise<void>;
}

/**
 * useApplicationSuggestions Hook
 *
 * Manages real-time application suggestions with debouncing, caching, and error handling.
 * Provides autocomplete functionality for the ApplicationInputField component.
 */
export const useApplicationSuggestions = (
  options: UseApplicationSuggestionsOptions = {}
): UseApplicationSuggestionsReturn => {
  const {
    maxResults = 8,
    debounceMs = 300,
    confidenceThresholds,
    cacheResults = true,
  } = options;

  const { client, engagement } = useAuth();
  const [suggestions, setSuggestions] = useState<ApplicationSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');

  // Refs for managing debouncing and cancellation
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const cacheRef = useRef<Map<string, { suggestions: ApplicationSuggestion[]; timestamp: number }>>(
    new Map()
  );

  // Cache duration (5 minutes)
  const CACHE_DURATION = 5 * 60 * 1000;

  // Clear any pending timeouts on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Check cache for existing results
  const getCachedSuggestions = useCallback((query: string): ApplicationSuggestion[] | null => {
    if (!cacheResults) return null;

    const cacheKey = query.toLowerCase().trim();
    const cached = cacheRef.current.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.suggestions;
    }

    return null;
  }, [cacheResults]);

  // Cache suggestions
  const cacheSuggestions = useCallback((query: string, suggestions: ApplicationSuggestion[]) => {
    if (!cacheResults) return;

    const cacheKey = query.toLowerCase().trim();
    cacheRef.current.set(cacheKey, {
      suggestions,
      timestamp: Date.now(),
    });

    // Clean up old cache entries (keep max 50 entries)
    if (cacheRef.current.size > 50) {
      const oldestKeys = Array.from(cacheRef.current.entries())
        .sort(([, a], [, b]) => a.timestamp - b.timestamp)
        .slice(0, cacheRef.current.size - 50)
        .map(([key]) => key);

      oldestKeys.forEach(key => cacheRef.current.delete(key));
    }
  }, [cacheResults]);

  // Perform the actual search
  const performSearch = useCallback(async (query: string): Promise<ApplicationSuggestion[]> => {
    if (!client || !engagement) {
      throw new Error('Client and engagement must be available');
    }

    if (query.length < 2) {
      return [];
    }

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      // Check cache first
      const cached = getCachedSuggestions(query);
      if (cached) {
        return cached;
      }

      // Perform API search
      const searchRequest: SimilaritySearchRequest = {
        query: query.trim(),
        client_account_id: client.id,
        engagement_id: engagement.id,
        min_confidence: confidenceThresholds?.min_confidence || 0.4,
        max_results: maxResults,
        include_variants: true,
      };

      const response = await canonicalApplicationsApi.searchSimilar(searchRequest);

      // Convert similarity matches to suggestions
      const suggestions: ApplicationSuggestion[] = response.suggestions || [];

      // Filter by confidence if thresholds are provided
      const filteredSuggestions = confidenceThresholds
        ? suggestions.filter(s => s.confidence_score >= (confidenceThresholds.suggestion_dropdown || 0.6))
        : suggestions;

      // Cache the results
      cacheSuggestions(query, filteredSuggestions);

      return filteredSuggestions;
    } catch (error: any) {
      // Don't treat aborted requests as errors
      if (error.name === 'AbortError') {
        return [];
      }
      throw error;
    }
  }, [client, engagement, maxResults, confidenceThresholds, getCachedSuggestions, cacheSuggestions]);

  // Debounced search function
  const searchSuggestions = useCallback(async (query: string): Promise<void> => {
    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Clear error state
    setError(null);
    setCurrentQuery(query);

    // If query is too short, clear suggestions immediately
    if (query.trim().length < 2) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    // Set loading state
    setIsLoading(true);

    // Set up debounced execution
    debounceTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await performSearch(query);

        // Only update if this is still the current query
        setCurrentQuery(current => {
          if (current === query) {
            setSuggestions(results);
            setIsLoading(false);
          }
          return current;
        });
      } catch (error: any) {
        console.error('Failed to fetch application suggestions:', error);

        setCurrentQuery(current => {
          if (current === query) {
            setError(error.message || 'Failed to load suggestions');
            setSuggestions([]);
            setIsLoading(false);
          }
          return current;
        });
      }
    }, debounceMs);
  }, [debounceMs, performSearch]);

  // Clear suggestions
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setError(null);
    setIsLoading(false);
    setCurrentQuery('');

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Refresh current suggestions
  const refreshSuggestions = useCallback(async (): Promise<void> => {
    if (currentQuery.trim().length >= 2) {
      await searchSuggestions(currentQuery);
    }
  }, [currentQuery, searchSuggestions]);

  // Clear cache when client or engagement changes
  useEffect(() => {
    cacheRef.current.clear();
    clearSuggestions();
  }, [client?.id, engagement?.id, clearSuggestions]);

  return {
    suggestions,
    isLoading,
    error,
    searchSuggestions,
    clearSuggestions,
    refreshSuggestions,
  };
};
