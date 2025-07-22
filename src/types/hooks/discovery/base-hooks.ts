/**
 * Discovery Base Hook Types
 * 
 * Common base types and interfaces used across all discovery hooks.
 */

// Base hook types
export interface BaseHookParams {
  enabled?: boolean;
  suspense?: boolean;
  retry?: boolean | number;
  retryDelay?: number;
  staleTime?: number;
  cacheTime?: number;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  refetchInterval?: number;
  onSuccess?: (data: unknown) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: unknown, error: Error | null) => void;
}

export interface BaseHookReturn<T = unknown> {
  data: T | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isSuccess: boolean;
  isIdle: boolean;
  isFetching: boolean;
  isStale: boolean;
  refetch: () => Promise<unknown>;
  remove: () => void;
  status: 'idle' | 'loading' | 'error' | 'success';
  fetchStatus: 'idle' | 'fetching' | 'paused';
  dataUpdatedAt: number;
  errorUpdatedAt: number;
}

// Common export formats
export interface ExportFormat {
  type: 'csv' | 'excel' | 'json' | 'xml' | 'pdf';
  options?: ExportOptions;
}

export interface ExportOptions {
  includeHeaders?: boolean;
  includeMetadata?: boolean;
  compression?: boolean;
  format?: string;
}