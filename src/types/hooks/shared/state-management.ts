/**
 * State Management Hook Types
 *
 * Hook interfaces for state management including storage, toggle, counter, and list hooks.
 *
 * These types provide comprehensive React hook patterns for state management
 * with proper generic constraints and type safety.
 */

import type { Dispatch, SetStateAction } from 'react';
import type { BaseMetadata } from '../../shared/metadata-types';

// State management hooks
export interface UseLocalStorageParams<T> {
  key: string;
  defaultValue?: T;
  serializer?: {
    read: (value: string) => T;
    write: (value: T) => string;
  };
  syncAcrossTabs?: boolean;
  onError?: (error: Error) => void;
}

export interface UseLocalStorageReturn<T> {
  value: T;
  setValue: (value: T | ((prev: T) => T)) => void;
  removeValue: () => void;
  isLoading: boolean;
  error: Error | null;
}

export interface UseSessionStorageParams<T> {
  key: string;
  defaultValue?: T;
  serializer?: {
    read: (value: string) => T;
    write: (value: T) => string;
  };
  onError?: (error: Error) => void;
}

export interface UseSessionStorageReturn<T> {
  value: T;
  setValue: (value: T | ((prev: T) => T)) => void;
  removeValue: () => void;
  isLoading: boolean;
  error: Error | null;
}

export interface UseToggleParams {
  defaultValue?: boolean;
  onChange?: (value: boolean) => void;
}

export interface UseToggleReturn {
  value: boolean;
  toggle: () => void;
  setTrue: () => void;
  setFalse: () => void;
  setValue: (value: boolean) => void;
}

export interface UseCounterParams {
  initialValue?: number;
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
}

export interface UseCounterReturn {
  count: number;
  increment: (amount?: number) => void;
  decrement: (amount?: number) => void;
  reset: () => void;
  setCount: (value: number | ((prev: number) => number)) => void;
}

export interface UseListParams<T> {
  initialList?: T[];
  onChange?: (list: T[]) => void;
  getKey?: (item: T) => string | number;
}

export interface UseListReturn<T> {
  list: T[];
  isEmpty: boolean;
  length: number;
  first: T | undefined;
  last: T | undefined;
  set: (newList: T[]) => void;
  push: (...items: T[]) => void;
  pop: () => T | undefined;
  shift: () => T | undefined;
  unshift: (...items: T[]) => void;
  insert: (index: number, ...items: T[]) => void;
  remove: (index: number) => T | undefined;
  removeBy: (predicate: (item: T) => boolean) => T[];
  update: (index: number, item: T) => void;
  updateBy: (predicate: (item: T) => boolean, item: T) => void;
  clear: () => void;
  filter: (predicate: (item: T) => boolean) => void;
  sort: (compareFn?: (a: T, b: T) => number) => void;
  reverse: () => void;
  move: (fromIndex: number, toIndex: number) => void;
  replace: (oldItem: T, newItem: T) => boolean;
  find: (predicate: (item: T) => boolean) => T | undefined;
  findIndex: (predicate: (item: T) => boolean) => number;
  includes: (item: T) => boolean;
  some: (predicate: (item: T) => boolean) => boolean;
  every: (predicate: (item: T) => boolean) => boolean;
}

// Advanced state management patterns

/**
 * Reducer action with type safety
 */
export interface ReducerAction<TType extends string = string, TPayload = unknown> {
  type: TType;
  payload?: TPayload;
  meta?: BaseMetadata;
}

/**
 * Generic state reducer function
 */
export type StateReducer<TState, TAction extends ReducerAction> = (state: TState, action: TAction) => TState;

/**
 * Use reducer hook parameters
 */
export interface UseReducerParams<TState, TAction extends ReducerAction> {
  reducer: StateReducer<TState, TAction>;
  initialState: TState;
  init?: (initial: TState) => TState;
}

/**
 * Use reducer hook return type
 */
export interface UseReducerReturn<TState, TAction extends ReducerAction> {
  state: TState;
  dispatch: Dispatch<TAction>;
}

/**
 * State with optimistic updates
 */
export interface OptimisticState<TData> {
  data: TData;
  optimisticData?: TData;
  isOptimistic: boolean;
  rollback: () => void;
}

/**
 * Use optimistic state parameters
 */
export interface UseOptimisticParams<TData> {
  initialData: TData;
  updateFn?: (currentData: TData, optimisticData: TData) => TData;
}

/**
 * Use optimistic state return
 */
export interface UseOptimisticReturn<TData> extends OptimisticState<TData> {
  setOptimisticData: (data: TData) => void;
  commitOptimisticData: () => void;
}

/**
 * Async state hook parameters
 */
export interface UseAsyncStateParams<TData, TError = Error> {
  initialData?: TData;
  onSuccess?: (data: TData) => void;
  onError?: (error: TError) => void;
}

/**
 * Async state hook return
 */
export interface UseAsyncStateReturn<TData, TError = Error> {
  data: TData | undefined;
  error: TError | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  execute: (asyncFn: () => Promise<TData>) => Promise<TData>;
  reset: () => void;
}

/**
 * State synchronization parameters
 */
export interface UseStateSyncParams<TState> {
  key: string;
  initialState: TState;
  storage?: 'localStorage' | 'sessionStorage' | 'memory';
  syncAcrossTabs?: boolean;
  serializer?: {
    serialize: (value: TState) => string;
    deserialize: (value: string) => TState;
  };
}

/**
 * State synchronization return
 */
export interface UseStateSyncReturn<TState> {
  state: TState;
  setState: Dispatch<SetStateAction<TState>>;
  clearState: () => void;
  isSynced: boolean;
}
