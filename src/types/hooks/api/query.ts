/**
 * Query Hook Types
 *
 * Hook types for data fetching operations including standard queries
 * and infinite/paginated queries.
 */

import type { UseApiParams } from './core'
import type { UseApiReturn } from './core'

// Query Hook Types
export interface UseQueryParams<TParams = unknown> extends UseApiParams<TParams> {
  queryKey: string | string[];
  dependencies?: unknown[];
  enabled?: boolean;
  retryOnMount?: boolean;
  backgroundRefetch?: boolean;
  pollingInterval?: number;
  onSuccess?: <TData>(data: TData) => void;
  onError?: (error: Error) => void;
  onSettled?: <TData>(data: TData | undefined, error: Error | null) => void;
  select?: <TData>(data: TData) => TData;
  keepPreviousData?: boolean;
  suspense?: boolean;
}

export interface UseQueryReturn<TData = unknown, TError = Error> extends UseApiReturn<TData, TError> {
  data: TData | undefined;
  error: TError | null;
  isLoading: boolean;
  isFetching: boolean;
  isError: boolean;
  isSuccess: boolean;
  isIdle: boolean;
  isStale: boolean;
  isPlaceholderData: boolean;
  isPreviousData: boolean;
  dataUpdatedAt: number;
  errorUpdatedAt: number;
  failureCount: number;
  refetch: (options?: RefetchOptions) => Promise<UseQueryReturn<TData, TError>>;
  remove: () => void;
  cancel: () => void;
}

// Infinite Query Hook Types
export interface UseInfiniteQueryParams<TParams = unknown> extends UseQueryParams<TParams> {
  getNextPageParam: <TData>(lastPage: TData, allPages: TData[]) => unknown;
  getPreviousPageParam?: <TData>(firstPage: TData, allPages: TData[]) => unknown;
  maxPages?: number;
  initialPageParam?: unknown;
}

export interface UseInfiniteQueryReturn<TData = unknown, TError = Error> extends Omit<UseQueryReturn<TData, TError>, 'data'> {
  data: InfiniteData<TData> | undefined;
  fetchNextPage: (options?: FetchNextPageOptions) => Promise<UseInfiniteQueryReturn<TData, TError>>;
  fetchPreviousPage: (options?: FetchPreviousPageOptions) => Promise<UseInfiniteQueryReturn<TData, TError>>;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  isFetchingNextPage: boolean;
  isFetchingPreviousPage: boolean;
}

// Supporting Types
export interface RefetchOptions {
  throwOnError?: boolean;
  cancelRefetch?: boolean;
}

export interface InfiniteData<TData> {
  pages: TData[];
  pageParams: unknown[];
}

export interface FetchNextPageOptions {
  pageParam?: unknown;
  throwOnError?: boolean;
}

export interface FetchPreviousPageOptions {
  pageParam?: unknown;
  throwOnError?: boolean;
}
