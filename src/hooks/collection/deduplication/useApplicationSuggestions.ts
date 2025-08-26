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
  // Safely extract options with proper validation
  const {
    maxResults = 8,
    debounceMs = 300,
    confidenceThresholds,
    cacheResults = true,
  } = options || {};

  // Validate numeric options
  const safeMaxResults = typeof maxResults === 'number' && isFinite(maxResults) && maxResults > 0 ? maxResults : 8;
  const safeDebounceMs = typeof debounceMs === 'number' && isFinite(debounceMs) && debounceMs >= 0 ? debounceMs : 300;

  const { client, engagement } = useAuth();
  const [suggestions, setSuggestions] = useState<ApplicationSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');

  // Refs for managing debouncing and cancellation
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const cacheRef = useRef<Map<string, { suggestions: ApplicationSuggestion[]; timestamp: number }>>(
    new Map()
  );

  // Cache duration (5 minutes)
  const CACHE_DURATION = 5 * 60 * 1000;

  // Clear any pending timeouts on unmount and ensure proper cleanup
  useEffect(() => {
    // Capture ref values at effect setup time
    const currentCache = cacheRef.current;

    return () => {
      // Clear debounce timeout
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }

      // Abort any pending requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }

      // Clear cache if needed
      if (currentCache) {
        currentCache.clear();
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
  }, [cacheResults, CACHE_DURATION]);

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

  // Perform the actual search with enhanced validation
  const performSearch = useCallback(async (query: string): Promise<ApplicationSuggestion[]> => {
    // Validate authentication context
    if (!client?.id || !engagement?.id) {
      throw new Error('Client and engagement must be available');
    }

    // Validate query
    if (!query || typeof query !== 'string' || query.trim().length < 2) {
      return [];
    }

    const trimmedQuery = query.trim();

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      // Check cache first
      const cached = getCachedSuggestions(trimmedQuery);
      if (cached) {
        return cached;
      }

      // Perform API search
      const searchRequest: SimilaritySearchRequest = {
        query: trimmedQuery,
        client_account_id: client.id,
        engagement_id: engagement.id,
        min_confidence: confidenceThresholds?.min_confidence || 0.4,
        max_results: safeMaxResults,
        include_variants: true,
      };

      const response = await canonicalApplicationsApi.searchSimilar(searchRequest);

      // Safely extract suggestions with validation
      const suggestions: ApplicationSuggestion[] = Array.isArray(response?.suggestions) ? response.suggestions : [];

      // Filter by confidence if thresholds are provided
      const filteredSuggestions = confidenceThresholds
        ? suggestions.filter(s => {
            return s && typeof s.confidence_score === 'number' &&
                   s.confidence_score >= (confidenceThresholds.suggestion_dropdown || 0.6);
          })
        : suggestions.filter(s => s && typeof s.confidence_score === 'number');

      // Cache the results
      cacheSuggestions(trimmedQuery, filteredSuggestions);

      return filteredSuggestions;
    } catch (error: unknown) {
      // Don't treat aborted requests as errors
      const isAbortError = (error instanceof Error && error.name === 'AbortError') ||
                          (error && typeof error === 'object' && 'code' in error && error.code === 'AbortError');
      if (isAbortError) {
        return [];
      }
      // Re-throw with more context
      const errorMessage = error instanceof Error ? error.message : 'Failed to search for application suggestions';
      throw new Error(errorMessage);
    }
  }, [client, engagement, safeMaxResults, confidenceThresholds, getCachedSuggestions, cacheSuggestions]);

  // Debounced search function with enhanced validation
  const searchSuggestions = useCallback(async (query: string): Promise<void> => {
    // Validate query parameter
    if (typeof query !== 'string') {
      console.warn('useApplicationSuggestions: searchSuggestions called with non-string query');
      return;
    }

    // Clear existing timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }

    // Clear error state
    setError(null);
    setCurrentQuery(query);

    // If query is too short, clear suggestions immediately
    const trimmedQuery = query.trim();
    if (trimmedQuery.length < 2) {
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
      } catch (error: unknown) {
        console.error('Failed to fetch application suggestions:', error);

        setCurrentQuery(current => {
          if (current === query) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load suggestions';
            setError(errorMessage);
            setSuggestions([]);
            setIsLoading(false);
          }
          return current;
        });
      }
    }, safeDebounceMs);
  }, [safeDebounceMs, performSearch]);

  // Clear suggestions with proper cleanup
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setError(null);
    setIsLoading(false);
    setCurrentQuery('');

    // Clear debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }

    // Abort any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
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
