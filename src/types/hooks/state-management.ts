/**
 * State Management Hook Types
 * 
 * Type definitions for state management hooks including global state,
 * local state, context management, and state persistence patterns.
 */

import { ReactNode } from 'react';

// Global State Hook Types
export interface UseGlobalStateParams<T> {
  key: string;
  initialValue?: T;
  persist?: boolean;
  serializer?: StateSerializer<T>;
  validator?: StateValidator<T>;
  onStateChange?: (newState: T, previousState: T) => void;
  onError?: (error: Error) => void;
}

export interface UseGlobalStateReturn<T> {
  state: T;
  setState: (newState: T | ((prevState: T) => T)) => void;
  resetState: () => void;
  subscribe: (listener: StateListener<T>) => () => void;
  getSnapshot: () => T;
  persist: () => void;
  restore: () => void;
  clear: () => void;
}

// Store Hook Types
export interface UseStoreParams<T = any> {
  store: Store<T>;
  selector?: StateSelector<T, any>;
  equalityFn?: EqualityFn;
  suspense?: boolean;
}

export interface UseStoreReturn<T, R = T> {
  data: R;
  actions: StoreActions<T>;
  dispatch: StoreDispatch<T>;
  subscribe: (listener: StateListener<R>) => () => void;
  getState: () => T;
  getSnapshot: () => R;
}

// Reducer Hook Types
export interface UseReducerWithMiddlewareParams<TState, TAction> {
  reducer: Reducer<TState, TAction>;
  initialState: TState | (() => TState);
  middleware?: Middleware<TState, TAction>[];
  onStateChange?: (state: TState, action: TAction) => void;
  onError?: (error: Error, action: TAction) => void;
  devTools?: boolean;
}

export interface UseReducerWithMiddlewareReturn<TState, TAction> {
  state: TState;
  dispatch: Dispatch<TAction>;
  replaceReducer: (nextReducer: Reducer<TState, TAction>) => void;
  getState: () => TState;
  subscribe: (listener: StateListener<TState>) => () => void;
  history: StateHistory<TState, TAction>;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}

// Context Hook Types
export interface UseContextStateParams<T> {
  context: React.Context<ContextValue<T>>;
  selector?: StateSelector<T, any>;
  equalityFn?: EqualityFn;
}

export interface UseContextStateReturn<T, R = T> {
  data: R;
  actions: ContextActions<T>;
  provider: ContextProviderComponent<T>;
  consumer: ContextConsumerComponent<T>;
}

export interface CreateContextStateParams<T> {
  name: string;
  initialState: T;
  actions?: ContextActionCreators<T>;
  middleware?: ContextMiddleware<T>[];
  persist?: boolean;
  devTools?: boolean;
}

export interface CreateContextStateReturn<T> {
  Provider: ContextProviderComponent<T>;
  useContext: () => ContextValue<T>;
  useSelector: <R>(selector: StateSelector<T, R>) => R;
  useActions: () => ContextActions<T>;
  useDispatch: () => ContextDispatch<T>;
}

// Async State Hook Types
export interface UseAsyncStateParams<T> {
  asyncFunction: () => Promise<T>;
  dependencies?: any[];
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onSettled?: (data: T | undefined, error: Error | null) => void;
  retryConfig?: AsyncRetryConfig;
  abortOnUnmount?: boolean;
}

export interface UseAsyncStateReturn<T> {
  data: T | undefined;
  error: Error | null;
  loading: boolean;
  success: boolean;
  idle: boolean;
  execute: () => Promise<void>;
  reset: () => void;
  abort: () => void;
  retry: () => Promise<void>;
  retryCount: number;
}

// Computed State Hook Types
export interface UseComputedStateParams<T, R> {
  computeFn: (state: T) => R;
  dependencies: any[];
  equalityFn?: EqualityFn<R>;
  lazy?: boolean;
  memoize?: boolean;
  debugLabel?: string;
}

export interface UseComputedStateReturn<R> {
  value: R;
  recompute: () => void;
  invalidate: () => void;
  isStale: boolean;
  lastComputed: number;
  computeCount: number;
}

// State Machine Hook Types
export interface UseStateMachineParams<TContext, TEvent> {
  machine: StateMachine<TContext, TEvent>;
  context?: TContext;
  actions?: StateMachineActions<TContext, TEvent>;
  guards?: StateMachineGuards<TContext, TEvent>;
  devTools?: boolean;
}

export interface UseStateMachineReturn<TContext, TEvent, TState = string> {
  state: TState;
  context: TContext;
  can: (event: TEvent) => boolean;
  send: (event: TEvent) => void;
  matches: (state: TState) => boolean;
  hasTag: (tag: string) => boolean;
  nextEvents: TEvent[];
  history: StateMachineHistory<TContext, TEvent, TState>;
  service: StateMachineService<TContext, TEvent>;
}

// Persistent State Hook Types
export interface UsePersistentStateParams<T> {
  key: string;
  initialValue: T;
  storage?: StorageAdapter;
  serializer?: StateSerializer<T>;
  validator?: StateValidator<T>;
  syncAcrossTabs?: boolean;
  debounceMs?: number;
  onRestore?: (value: T) => void;
  onPersist?: (value: T) => void;
  onError?: (error: Error) => void;
}

export interface UsePersistentStateReturn<T> {
  value: T;
  setValue: (newValue: T | ((prevValue: T) => T)) => void;
  resetValue: () => void;
  removeValue: () => void;
  rehydrate: () => void;
  isPersisting: boolean;
  isRehydrating: boolean;
  lastPersisted?: number;
  lastRehydrated?: number;
}

// Optimistic State Hook Types
export interface UseOptimisticStateParams<T> {
  initialState: T;
  onCommit?: (optimisticState: T, finalState: T) => void;
  onRollback?: (rollbackState: T, error: Error) => void;
  onConflict?: (optimisticState: T, serverState: T) => T;
  timeout?: number;
}

export interface UseOptimisticStateReturn<T> {
  state: T;
  optimisticState: T | undefined;
  isPending: boolean;
  isOptimistic: boolean;
  hasConflict: boolean;
  setState: (newState: T | ((prevState: T) => T)) => void;
  optimisticUpdate: (update: T | ((prevState: T) => T)) => Promise<void>;
  commit: (finalState: T) => void;
  rollback: () => void;
  resolve: (serverState: T) => void;
  conflicts: OptimisticConflict<T>[];
}

// State History Hook Types
export interface UseStateHistoryParams<T> {
  initialState: T;
  maxHistorySize?: number;
  debounceMs?: number;
  shouldSaveToHistory?: (currentState: T, newState: T) => boolean;
  onUndo?: (state: T) => void;
  onRedo?: (state: T) => void;
  onHistoryChange?: (history: StateHistoryEntry<T>[]) => void;
}

export interface UseStateHistoryReturn<T> {
  state: T;
  setState: (newState: T | ((prevState: T) => T)) => void;
  undo: () => void;
  redo: () => void;
  goToState: (index: number) => void;
  clearHistory: () => void;
  canUndo: boolean;
  canRedo: boolean;
  historyIndex: number;
  history: StateHistoryEntry<T>[];
  future: StateHistoryEntry<T>[];
}

// Synchronized State Hook Types
export interface UseSynchronizedStateParams<T> {
  channel: string;
  initialState: T;
  conflictResolution?: ConflictResolutionStrategy<T>;
  syncDebounceMs?: number;
  onSync?: (incomingState: T, currentState: T) => void;
  onConflict?: (localState: T, remoteState: T) => void;
  serializer?: StateSerializer<T>;
  validator?: StateValidator<T>;
}

export interface UseSynchronizedStateReturn<T> {
  state: T;
  setState: (newState: T | ((prevState: T) => T)) => void;
  sync: () => void;
  forceSync: (state: T) => void;
  isSyncing: boolean;
  lastSync?: number;
  conflicts: SyncConflict<T>[];
  resolveConflict: (resolution: T) => void;
  peers: SyncPeer[];
}

// Form State Hook Types
export interface UseFormStateParams<T extends Record<string, any>> {
  initialValues: T;
  validate?: FormValidator<T>;
  onSubmit?: (values: T) => void | Promise<void>;
  onError?: (errors: FormErrors<T>) => void;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  resetOnSubmit?: boolean;
  submitOnEnter?: boolean;
}

export interface UseFormStateReturn<T extends Record<string, any>> {
  values: T;
  errors: FormErrors<T>;
  touched: FormTouched<T>;
  dirty: boolean;
  valid: boolean;
  submitting: boolean;
  submitCount: number;
  setValue: <K extends keyof T>(field: K, value: T[K]) => void;
  setValues: (values: Partial<T>) => void;
  setError: <K extends keyof T>(field: K, error: string) => void;
  setErrors: (errors: FormErrors<T>) => void;
  setTouched: <K extends keyof T>(field: K, touched?: boolean) => void;
  setFieldTouched: (touched: FormTouched<T>) => void;
  resetForm: (values?: T) => void;
  resetField: <K extends keyof T>(field: K) => void;
  validateForm: () => Promise<boolean>;
  validateField: <K extends keyof T>(field: K) => Promise<boolean>;
  submitForm: () => Promise<void>;
  getFieldProps: <K extends keyof T>(field: K) => FieldProps<T[K]>;
  getFieldMeta: <K extends keyof T>(field: K) => FieldMeta;
}

// Supporting Types
export interface Store<T> {
  getState: () => T;
  setState: (newState: T | ((prevState: T) => T)) => void;
  subscribe: (listener: StateListener<T>) => () => void;
  destroy: () => void;
}

export interface StoreActions<T> {
  [key: string]: (...args: any[]) => void;
}

export interface ContextValue<T> {
  state: T;
  actions: ContextActions<T>;
  dispatch: ContextDispatch<T>;
}

export interface ContextActions<T> {
  [key: string]: (...args: any[]) => void;
}

export interface StateMachine<TContext, TEvent> {
  id: string;
  initial: string;
  context: TContext;
  states: StateMachineStates;
  on?: StateMachineTransitions<TEvent>;
}

export interface StateMachineStates {
  [key: string]: StateMachineState;
}

export interface StateMachineState {
  entry?: string | string[];
  exit?: string | string[];
  on?: StateMachineTransitions<any>;
  meta?: any;
  tags?: string[];
}

export interface StateMachineTransitions<TEvent> {
  [K in keyof TEvent]: string | StateMachineTransition;
}

export interface StateMachineTransition {
  target: string;
  guard?: string;
  actions?: string | string[];
  cond?: (context: any, event: any) => boolean;
}

export interface StateMachineActions<TContext, TEvent> {
  [key: string]: (context: TContext, event: TEvent) => TContext;
}

export interface StateMachineGuards<TContext, TEvent> {
  [key: string]: (context: TContext, event: TEvent) => boolean;
}

export interface StateMachineHistory<TContext, TEvent, TState> {
  states: TState[];
  events: TEvent[];
  context: TContext[];
  current: number;
}

export interface StateMachineService<TContext, TEvent> {
  start: () => void;
  stop: () => void;
  send: (event: TEvent) => void;
  subscribe: (listener: (state: any) => void) => () => void;
}

export interface StorageAdapter {
  getItem: (key: string) => string | null | Promise<string | null>;
  setItem: (key: string, value: string) => void | Promise<void>;
  removeItem: (key: string) => void | Promise<void>;
  clear?: () => void | Promise<void>;
}

export interface StateSerializer<T> {
  serialize: (state: T) => string;
  deserialize: (serialized: string) => T;
}

export interface StateValidator<T> {
  validate: (state: T) => boolean;
  schema?: any;
}

export interface StateHistory<TState, TAction> {
  past: StateHistoryEntry<TState>[];
  present: TState;
  future: StateHistoryEntry<TState>[];
  actions: TAction[];
}

export interface StateHistoryEntry<T> {
  state: T;
  timestamp: number;
  action?: any;
}

export interface OptimisticConflict<T> {
  optimisticState: T;
  serverState: T;
  timestamp: number;
  resolved: boolean;
}

export interface SyncConflict<T> {
  localState: T;
  remoteState: T;
  timestamp: number;
  peer: SyncPeer;
  resolved: boolean;
}

export interface SyncPeer {
  id: string;
  name?: string;
  lastSeen: number;
  active: boolean;
}

export interface AsyncRetryConfig {
  attempts: number;
  delay: number | ((attempt: number) => number);
  condition?: (error: Error) => boolean;
  onRetry?: (attempt: number, error: Error) => void;
}

export interface FormErrors<T> {
  [K in keyof T]?: string;
}

export interface FormTouched<T> {
  [K in keyof T]?: boolean;
}

export interface FieldProps<T> {
  name: string;
  value: T;
  onChange: (value: T) => void;
  onBlur: () => void;
}

export interface FieldMeta {
  touched: boolean;
  error?: string;
  valid: boolean;
  dirty: boolean;
}

export interface ContextProviderComponent<T> {
  (props: { children: ReactNode; initialState?: T }): JSX.Element;
}

export interface ContextConsumerComponent<T> {
  (props: { children: (value: ContextValue<T>) => ReactNode }): JSX.Element;
}

// Type Aliases
export type StateListener<T> = (newState: T, previousState: T) => void;
export type StateSelector<T, R> = (state: T) => R;
export type EqualityFn<T = any> = (a: T, b: T) => boolean;
export type Reducer<TState, TAction> = (state: TState, action: TAction) => TState;
export type Dispatch<TAction> = (action: TAction) => void;
export type Middleware<TState, TAction> = (store: MiddlewareStore<TState, TAction>) => (next: Dispatch<TAction>) => Dispatch<TAction>;
export type StoreDispatch<T> = (action: any) => void;
export type ContextDispatch<T> = (action: any) => void;
export type ContextActionCreators<T> = Record<string, (...args: any[]) => any>;
export type ContextMiddleware<T> = (store: any) => (next: any) => (action: any) => any;
export type FormValidator<T> = (values: T) => FormErrors<T> | Promise<FormErrors<T>>;
export type ConflictResolutionStrategy<T> = 'local' | 'remote' | 'merge' | ((local: T, remote: T) => T);

export interface MiddlewareStore<TState, TAction> {
  getState: () => TState;
  dispatch: Dispatch<TAction>;
}
