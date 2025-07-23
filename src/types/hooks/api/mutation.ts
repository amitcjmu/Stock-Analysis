/**
 * Mutation Hook Types
 * 
 * Hook types for data modification operations including
 * mutations with optimistic updates and query invalidation.
 */

import type {
  BaseMutationHookParams,
  BaseMutationHookReturn
} from '../shared/base-patterns';

// Mutation Hook Types
export interface UseMutationParams<TData = unknown, TError = Error, TVariables = unknown, TContext = unknown> 
  extends BaseMutationHookParams<TData, TError, TVariables, TContext> {
  endpoint: string;
  method: 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  baseURL?: string;
  timeout?: number;
  withCredentials?: boolean;
  optimisticUpdate?: OptimisticUpdateConfig<TData, TVariables>;
  invalidateQueries?: string[];
  updateQueries?: Array<QueryUpdateConfig<TData, TVariables>>;
  onMutate?: (variables: TVariables) => Promise<TContext | void> | TContext | void;
  onSuccess?: (data: TData, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onError?: (error: TError, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: TContext | undefined) => Promise<void> | void;
}

export interface UseMutationReturn<TData = unknown, TError = Error, TVariables = unknown, TContext = unknown> 
  extends BaseMutationHookReturn<TData, TError, TVariables, TContext> {
  data: TData | undefined;
  error: TError | null;
  isIdle: boolean;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  isPaused: boolean;
  status: 'idle' | 'loading' | 'error' | 'success';
  failureCount: number;
  failureReason: TError | null;
  mutate: (variables: TVariables, options?: MutateOptions<TData, TError, TVariables, TContext>) => void;
  mutateAsync: (variables: TVariables, options?: MutateOptions<TData, TError, TVariables, TContext>) => Promise<TData>;
  reset: () => void;
  context: TContext | undefined;
  variables: TVariables | undefined;
}

// Supporting Types
export interface OptimisticUpdateConfig<TData, TVariables> {
  updater: (variables: TVariables) => TData;
  rollback?: (previous: TData, error: Error) => TData;
}

export interface QueryUpdateConfig<TData, TVariables> {
  queryKey: string;
  updater: (previous: unknown, variables: TVariables, response: TData) => unknown;
}

export interface MutateOptions<TData, TError, TVariables, TContext> {
  onSuccess?: (data: TData, variables: TVariables, context: TContext | undefined) => void;
  onError?: (error: TError, variables: TVariables, context: TContext | undefined) => void;
  onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables, context: TContext | undefined) => void;
}