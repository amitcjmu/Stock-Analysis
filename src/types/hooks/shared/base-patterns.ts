/**
 * Base Hook Patterns
 *
 * Base interfaces and patterns used across async and mutation hooks.
 *
 * These types provide proper React hook patterns with generic constraints,
 * replacing 'any' types with specific interfaces for better type safety.
 */

import type { BaseMetadata } from '../../shared/metadata-types';

/**
 * Generic query selector function type
 */
export type QuerySelector<TQueryData, TData> = (data: TQueryData) => TData;

/**
 * Generic mutation options type
 */
export interface MutationOptions<TData = unknown, TError = Error, TVariables = unknown, TContext = unknown> {
  onMutate?: (variables: TVariables) => Promise<TContext | void> | TContext | void;
  onSuccess?: (data: TData, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onError?: (error: TError, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
}

/**
 * Generic refetch options interface
 */
export interface RefetchOptions {
  throwOnError?: boolean;
  cancelRefetch?: boolean;
}

/**
 * Generic query data with metadata
 */
export interface QueryData<TData = unknown> {
  data: TData;
  metadata?: BaseMetadata;
}

// Base hook patterns
export interface BaseAsyncHookParams {
  enabled?: boolean;
  suspense?: boolean;
  retry?: boolean | number | ((failureCount: number, error: Error) => boolean);
  retryDelay?: number | ((retryAttempt: number, error: Error) => number);
  staleTime?: number;
  cacheTime?: number;
  refetchOnMount?: boolean | 'always';
  refetchOnWindowFocus?: boolean | 'always';
  refetchOnReconnect?: boolean | 'always';
  refetchInterval?: number | false;
  refetchIntervalInBackground?: boolean;
  notifyOnChangeProps?: string[] | 'all' | (() => string[] | 'all');
  onSuccess?: <TData>(data: TData) => void;
  onError?: (error: Error) => void;
  onSettled?: <TData>(data: TData | undefined, error: Error | null) => void;
  select?: <TQueryData, TData>(data: TQueryData) => TData;
  initialData?: unknown;
  initialDataUpdatedAt?: number | (() => number);
  placeholderData?: unknown;
  keepPreviousData?: boolean;
  structuralSharing?: boolean | (<TData>(oldData: TData, newData: TData) => TData);
  useErrorBoundary?: boolean | ((error: Error, query: QueryData) => boolean);
  meta?: BaseMetadata;
}

export interface BaseAsyncHookReturn<TData = unknown, TError = Error> {
  data: TData | undefined;
  error: TError | null;
  isError: boolean;
  isIdle: boolean;
  isLoading: boolean;
  isLoadingError: boolean;
  isRefetchError: boolean;
  isSuccess: boolean;
  status: 'idle' | 'loading' | 'error' | 'success';
  dataUpdatedAt: number;
  errorUpdatedAt: number;
  failureCount: number;
  failureReason: TError | null;
  errorUpdateCount: number;
  isFetched: boolean;
  isFetchedAfterMount: boolean;
  isFetching: boolean;
  isRefetching: boolean;
  isStale: boolean;
  isPlaceholderData: boolean;
  isPreviousData: boolean;
  refetch: (options?: RefetchOptions) => Promise<BaseAsyncHookReturn<TData, TError>>;
  remove: () => void;
}

export interface BaseMutationHookParams<TData = unknown, TError = Error, TVariables = unknown, TContext = unknown> extends MutationOptions<TData, TError, TVariables, TContext> {
  mutationFn?: (variables: TVariables) => Promise<TData>;
  retry?: boolean | number | ((failureCount: number, error: TError) => boolean);
  retryDelay?: number | ((retryAttempt: number, error: TError) => number);
  useErrorBoundary?: boolean | ((error: TError, variables: TVariables, context: TContext | undefined) => boolean);
  meta?: BaseMetadata;
}

export interface BaseMutationHookReturn<TData = unknown, TError = Error, TVariables = unknown, TContext = unknown> {
  data: TData | undefined;
  error: TError | null;
  isError: boolean;
  isIdle: boolean;
  isLoading: boolean;
  isPaused: boolean;
  isSuccess: boolean;
  status: 'idle' | 'loading' | 'error' | 'success';
  failureCount: number;
  failureReason: TError | null;
  mutate: (variables: TVariables, options?: MutationOptions<TData, TError, TVariables, TContext>) => void;
  mutateAsync: (variables: TVariables, options?: MutationOptions<TData, TError, TVariables, TContext>) => Promise<TData>;
  reset: () => void;
  context: TContext | undefined;
  variables: TVariables | undefined;
}
