/**
 * Shared Hook Types
 * 
 * Common hook patterns and utilities used across the application.
 * Provides base interfaces and reusable hook patterns.
 */

import { ReactNode } from 'react';

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
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: any | undefined, error: Error | null) => void;
  select?: (data: any) => any;
  initialData?: any;
  initialDataUpdatedAt?: number | (() => number);
  placeholderData?: any;
  keepPreviousData?: boolean;
  structuralSharing?: boolean | ((oldData: any, newData: any) => any);
  useErrorBoundary?: boolean | ((error: Error, query: any) => boolean);
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
  refetch: (options?: any) => Promise<any>;
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
  mutate: (variables: TVariables, options?: any) => void;
  mutateAsync: (variables: TVariables, options?: any) => Promise<TData>;
  reset: () => void;
  context: TContext | undefined;
  variables: TVariables | undefined;
}

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

// UI state hooks
export interface UseDisclosureParams {
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onToggle?: (isOpen: boolean) => void;
}

export interface UseDisclosureReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getButtonProps: (props?: any) => any;
  getDisclosureProps: (props?: any) => any;
}

export interface UseModalParams {
  defaultIsOpen?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onOverlayClick?: () => void;
  onEscapeKeyDown?: (event: KeyboardEvent) => void;
}

export interface UseModalReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getModalProps: (props?: any) => any;
  getOverlayProps: (props?: any) => any;
  getDialogProps: (props?: any) => any;
}

export interface UseTooltipParams {
  placement?: 'top' | 'bottom' | 'left' | 'right';
  offset?: number;
  delay?: number | { open?: number; close?: number };
  closeOnClick?: boolean;
  closeOnMouseDown?: boolean;
  disabled?: boolean;
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface UseTooltipReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getTriggerProps: (props?: any) => any;
  getTooltipProps: (props?: any) => any;
  getArrowProps: (props?: any) => any;
}

export interface UseDropdownParams {
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end';
  offset?: number;
  closeOnSelect?: boolean;
  closeOnBlur?: boolean;
  closeOnEsc?: boolean;
  autoSelect?: boolean;
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onSelect?: (value: any) => void;
}

export interface UseDropdownReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  selectedIndex: number;
  setSelectedIndex: (index: number) => void;
  getTriggerProps: (props?: any) => any;
  getMenuProps: (props?: any) => any;
  getItemProps: (props?: any, index?: number) => any;
}

// Form hooks
export interface UseFormParams<TFieldValues = any> {
  mode?: 'onSubmit' | 'onBlur' | 'onChange' | 'onTouched' | 'all';
  reValidateMode?: 'onSubmit' | 'onBlur' | 'onChange';
  defaultValues?: Partial<TFieldValues>;
  resolver?: any;
  context?: any;
  criteriaMode?: 'firstError' | 'all';
  shouldFocusError?: boolean;
  shouldUnregister?: boolean;
  shouldUseNativeValidation?: boolean;
  delayError?: number;
  onSubmit?: (data: TFieldValues, event?: any) => void | Promise<void>;
  onError?: (errors: any, event?: any) => void;
  onReset?: (data?: TFieldValues) => void;
  onInvalid?: (errors: any, event?: any) => void;
}

export interface UseFormReturn<TFieldValues = any> {
  control: any;
  handleSubmit: (onValid: (data: TFieldValues, event?: any) => void | Promise<void>, onInvalid?: (errors: any, event?: any) => void) => (event?: any) => Promise<void>;
  reset: (values?: Partial<TFieldValues>, options?: any) => void;
  setError: (name: string, error: any, options?: any) => void;
  clearErrors: (name?: string | string[]) => void;
  setValue: (name: string, value: any, options?: any) => void;
  getValue: (name: string) => any;
  getValues: (names?: string | string[]) => any;
  trigger: (name?: string | string[]) => Promise<boolean>;
  unregister: (name?: string | string[], options?: any) => void;
  watch: (name?: string | string[] | ((data: any, options: any) => any), defaultValue?: any) => any;
  formState: FormState<TFieldValues>;
  register: (name: string, options?: any) => any;
}

export interface FormState<TFieldValues = any> {
  isDirty: boolean;
  isLoading: boolean;
  isSubmitted: boolean;
  isSubmitSuccessful: boolean;
  isSubmitting: boolean;
  isValidating: boolean;
  isValid: boolean;
  submitCount: number;
  dirtyFields: Partial<Record<string, boolean>>;
  touchedFields: Partial<Record<string, boolean>>;
  errors: any;
  defaultValues?: Partial<TFieldValues>;
}

export interface UseFieldParams {
  name: string;
  defaultValue?: any;
  rules?: any;
  shouldUnregister?: boolean;
  disabled?: boolean;
}

export interface UseFieldReturn {
  field: {
    name: string;
    value: any;
    onChange: (value: any) => void;
    onBlur: () => void;
    ref: any;
  };
  fieldState: {
    invalid: boolean;
    isTouched: boolean;
    isDirty: boolean;
    error?: any;
  };
  formState: FormState;
}

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

// Data fetching hooks
export interface UsePaginationParams {
  initialPage?: number;
  initialPageSize?: number;
  total?: number;
  onPageChange?: (page: number, pageSize: number) => void;
}

export interface UsePaginationReturn {
  currentPage: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  isFirstPage: boolean;
  isLastPage: boolean;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setTotal: (total: number) => void;
  nextPage: () => void;
  previousPage: () => void;
  firstPage: () => void;
  lastPage: () => void;
  goToPage: (page: number) => void;
  getPageNumbers: (delta?: number) => number[];
}

export interface UseSortingParams<T> {
  initialSortBy?: string;
  initialSortOrder?: 'asc' | 'desc';
  onSort?: (sortBy: string, sortOrder: 'asc' | 'desc', data: T[]) => void;
}

export interface UseSortingReturn<T> {
  sortBy: string | null;
  sortOrder: 'asc' | 'desc';
  sort: (data: T[]) => T[];
  setSortBy: (field: string) => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  toggleSortOrder: () => void;
  resetSort: () => void;
  isSorted: boolean;
  getSortedData: (data: T[]) => T[];
}

export interface UseFilteringParams<T> {
  initialFilters?: Record<string, any>;
  onFilter?: (filters: Record<string, any>, data: T[]) => void;
}

export interface UseFilteringReturn<T> {
  filters: Record<string, any>;
  setFilter: (key: string, value: any) => void;
  removeFilter: (key: string) => void;
  clearFilters: () => void;
  hasFilters: boolean;
  filter: (data: T[]) => T[];
  getFilteredData: (data: T[]) => T[];
}

export interface UseSearchParams<T> {
  searchFields?: string[];
  caseSensitive?: boolean;
  onSearch?: (query: string, results: T[]) => void;
}

export interface UseSearchReturn<T> {
  query: string;
  setQuery: (query: string) => void;
  clearQuery: () => void;
  hasQuery: boolean;
  search: (data: T[]) => T[];
  getSearchResults: (data: T[]) => T[];
  highlightMatches: (text: string) => ReactNode[];
}

// Event hooks
export interface UseKeyboardParams {
  keys: string | string[];
  onKeyDown?: (event: KeyboardEvent) => void;
  onKeyUp?: (event: KeyboardEvent) => void;
  preventDefault?: boolean;
  stopPropagation?: boolean;
  target?: EventTarget | null;
  enabled?: boolean;
}

export interface UseKeyboardReturn {
  isPressed: boolean;
  pressedKeys: Set<string>;
  addKey: (key: string) => void;
  removeKey: (key: string) => void;
  clearKeys: () => void;
}

export interface UseClickAwayParams {
  onClickAway: (event: Event) => void;
  mouseEvent?: 'click' | 'mousedown' | 'mouseup';
  touchEvent?: 'touchstart' | 'touchend';
  enabled?: boolean;
}

export interface UseClickAwayReturn {
  ref: React.RefObject<HTMLElement>;
}

export interface UseHoverParams {
  onHoverStart?: (event: MouseEvent) => void;
  onHoverEnd?: (event: MouseEvent) => void;
  delay?: number;
  restMs?: number;
}

export interface UseHoverReturn {
  ref: React.RefObject<HTMLElement>;
  isHovered: boolean;
}

export interface UseFocusParams {
  onFocus?: (event: FocusEvent) => void;
  onBlur?: (event: FocusEvent) => void;
  within?: boolean;
}

export interface UseFocusReturn {
  ref: React.RefObject<HTMLElement>;
  isFocused: boolean;
  isFocusedWithin: boolean;
}

// Media and viewport hooks
export interface UseMediaQueryParams {
  query: string;
  defaultMatches?: boolean;
  noSsr?: boolean;
}

export interface UseMediaQueryReturn {
  matches: boolean;
  media: string;
}

export interface UseBreakpointParams {
  breakpoints?: Record<string, number>;
  defaultBreakpoint?: string;
}

export interface UseBreakpointReturn {
  breakpoint: string;
  isAbove: (breakpoint: string) => boolean;
  isBelow: (breakpoint: string) => boolean;
  isOnly: (breakpoint: string) => boolean;
  isBetween: (min: string, max: string) => boolean;
}

export interface UseViewportParams {
  debounce?: number;
}

export interface UseViewportReturn {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  orientation: 'portrait' | 'landscape';
}

// Performance hooks
export interface UseMemoizedParams<T> {
  factory: () => T;
  deps: any[];
  compare?: (prev: T, next: T) => boolean;
}

export interface UseMemoizedReturn<T> {
  value: T;
  reset: () => void;
  isStale: boolean;
}

export interface UseVirtualizedParams<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  containerHeight: number;
  overscan?: number;
  scrollTop?: number;
  onScroll?: (scrollTop: number) => void;
}

export interface UseVirtualizedReturn<T> {
  virtualItems: VirtualItem<T>[];
  totalHeight: number;
  startIndex: number;
  endIndex: number;
  scrollToIndex: (index: number, align?: 'start' | 'center' | 'end' | 'auto') => void;
  scrollToOffset: (offset: number) => void;
  measureElement: (index: number, element: HTMLElement) => void;
}

export interface VirtualItem<T> {
  index: number;
  start: number;
  end: number;
  size: number;
  item: T;
}

// Utility hooks
export interface UsePreviousReturn<T> {
  previous: T | undefined;
}

export interface UseLatestReturn<T> {
  current: T;
}

export interface UseConstantReturn<T> {
  value: T;
}

export interface UseForceUpdateReturn {
  forceUpdate: () => void;
  updateCount: number;
}

export interface UseIsomorphicLayoutEffectReturn {
  // No return value - this is just useLayoutEffect in browser, useEffect in SSR
}

export interface UseComposedRefsReturn {
  composedRef: React.RefCallback<any>;
}

export interface UseControllableStateParams<T> {
  value?: T;
  defaultValue?: T;
  onChange?: (value: T) => void;
  shouldUpdate?: (prev: T, next: T) => boolean;
}

export interface UseControllableStateReturn<T> {
  value: T;
  setValue: (value: T | ((prev: T) => T)) => void;
  isControlled: boolean;
}

// Error handling hooks
export interface UseErrorBoundaryParams {
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  resetOnPropsChange?: boolean;
  resetKeys?: any[];
  onReset?: () => void;
}

export interface UseErrorBoundaryReturn {
  error: Error | null;
  resetError: () => void;
  captureError: (error: Error) => void;
}

export interface UseAsyncErrorParams {
  onError?: (error: Error) => void;
  resetOnNewAsyncOperation?: boolean;
}

export interface UseAsyncErrorReturn {
  error: Error | null;
  captureError: (error: Error) => void;
  resetError: () => void;
}