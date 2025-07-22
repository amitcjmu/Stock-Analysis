/**
 * Base Hook Patterns
 * 
 * Base interfaces and patterns used across async and mutation hooks.
 */

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
  onSuccess?: (data: unknown) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: any | undefined, error: Error | null) => void;
  select?: (data: unknown) => any;
  initialData?: unknown;
  initialDataUpdatedAt?: number | (() => number);
  placeholderData?: unknown;
  keepPreviousData?: boolean;
  structuralSharing?: boolean | ((oldData: any, newData: unknown) => any);
  useErrorBoundary?: boolean | ((error: Error, query: unknown) => boolean);
  meta?: Record<string, any>;
}

export interface BaseAsyncHookReturn<TData = any, TError = Error> {
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
  refetch: (options?: unknown) => Promise<any>;
  remove: () => void;
}

export interface BaseMutationHookParams<TData = any, TError = Error, TVariables = any, TContext = any> {
  mutationFn?: (variables: TVariables) => Promise<TData>;
  onMutate?: (variables: TVariables) => Promise<TContext | void> | TContext | void;
  onSuccess?: (data: TData, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onError?: (error: TError, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  retry?: boolean | number | ((failureCount: number, error: TError) => boolean);
  retryDelay?: number | ((retryAttempt: number, error: TError) => number);
  useErrorBoundary?: boolean | ((error: TError, variables: TVariables, context: TContext | undefined) => boolean);
  meta?: Record<string, any>;
}

export interface BaseMutationHookReturn<TData = any, TError = Error, TVariables = any, TContext = any> {
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
  mutate: (variables: TVariables, options?: unknown) => void;
  mutateAsync: (variables: TVariables, options?: unknown) => Promise<TData>;
  reset: () => void;
  context: TContext | undefined;
  variables: TVariables | undefined;
}