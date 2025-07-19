/**
 * Async Operations Hook Types
 * 
 * Hook interfaces for async operations including async execution, debouncing, throttling, intervals, and timeouts.
 */

// Async operation hooks
export interface UseAsyncParams<T> {
  asyncFunction: () => Promise<T>;
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: T | undefined, error: Error | null) => void;
}

export interface UseAsyncReturn<T> {
  data: T | undefined;
  error: Error | null;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
  execute: () => Promise<void>;
  reset: () => void;
}

export interface UseDebounceParams<T> {
  value: T;
  delay: number;
  leading?: boolean;
  trailing?: boolean;
  maxWait?: number;
}

export interface UseDebounceReturn<T> {
  debouncedValue: T;
  cancel: () => void;
  flush: () => void;
  isPending: () => boolean;
}

export interface UseThrottleParams<T> {
  value: T;
  delay: number;
  leading?: boolean;
  trailing?: boolean;
}

export interface UseThrottleReturn<T> {
  throttledValue: T;
  cancel: () => void;
  flush: () => void;
}

export interface UseIntervalParams {
  callback: () => void;
  delay: number | null;
  immediate?: boolean;
  leading?: boolean;
}

export interface UseIntervalReturn {
  start: () => void;
  stop: () => void;
  toggle: () => void;
  isActive: boolean;
}

export interface UseTimeoutParams {
  callback: () => void;
  delay: number | null;
  immediate?: boolean;
}

export interface UseTimeoutReturn {
  start: (overrideDelay?: number) => void;
  stop: () => void;
  restart: (overrideDelay?: number) => void;
  isActive: boolean;
}