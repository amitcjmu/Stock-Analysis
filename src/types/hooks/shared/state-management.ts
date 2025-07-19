/**
 * State Management Hook Types
 * 
 * Hook interfaces for state management including storage, toggle, counter, and list hooks.
 */

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