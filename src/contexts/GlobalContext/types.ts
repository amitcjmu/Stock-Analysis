import type { ReactNode } from 'react';
import type { User, Client, Engagement, Flow } from '../AuthContext/types';

// Performance monitoring types
export interface PerformanceMetrics {
  renderCount: number;
  lastRenderTime: number;
  averageRenderTime: number;
  cacheHitRate: number;
  apiCallCount: number;
}

// Cache state types
export interface CacheState {
  isEnabled: boolean;
  isConnected: boolean;
  lastSyncTime: number | null;
  pendingInvalidations: string[];
}

// Feature flags
export interface FeatureFlags {
  useRedisCache: boolean;
  enablePerformanceMonitoring: boolean;
  useWebSocketSync: boolean;
  enableContextDebugging: boolean;
  useProgressiveHydration: boolean;
}

// UI state
export interface UIState {
  sidebarOpen: boolean;
  notifications: Notification[];
  isLoading: boolean;
  theme: 'light' | 'dark' | 'auto';
}

// Notification type
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  duration?: number;
  timestamp: number;
}

// Main global state interface
export interface GlobalState {
  auth: {
    user: User | null;
    isLoading: boolean;
    isInitialized: boolean;
    isLoginInProgress: boolean;
    error: string | null;
    isDemoMode: boolean;
  };
  context: {
    client: Client | null;
    engagement: Engagement | null;
    flow: Flow | null;
    isLoading: boolean;
    error: string | null;
    lastFetchTime: number | null;
  };
  ui: UIState;
  cache: CacheState;
  performance: PerformanceMetrics;
  featureFlags: FeatureFlags;
}

// Action types for the reducer
export type GlobalAction =
  | { type: 'AUTH_INIT_START' }
  | { type: 'AUTH_INIT_SUCCESS'; payload: { user: User; client?: Client; engagement?: Engagement; flow?: Flow } }
  | { type: 'AUTH_INIT_ERROR'; payload: string }
  | { type: 'AUTH_LOGIN_START' }
  | { type: 'AUTH_LOGIN_SUCCESS'; payload: User }
  | { type: 'AUTH_LOGIN_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'CONTEXT_UPDATE_START' }
  | { type: 'CONTEXT_UPDATE_SUCCESS'; payload: { client?: Client; engagement?: Engagement; flow?: Flow } }
  | { type: 'CONTEXT_UPDATE_ERROR'; payload: string }
  | { type: 'CONTEXT_SWITCH_CLIENT'; payload: Client }
  | { type: 'CONTEXT_SWITCH_ENGAGEMENT'; payload: Engagement }
  | { type: 'CONTEXT_SWITCH_FLOW'; payload: Flow }
  | { type: 'UI_TOGGLE_SIDEBAR' }
  | { type: 'UI_SET_THEME'; payload: UIState['theme'] }
  | { type: 'UI_ADD_NOTIFICATION'; payload: Notification }
  | { type: 'UI_REMOVE_NOTIFICATION'; payload: string }
  | { type: 'UI_SET_LOADING'; payload: boolean }
  | { type: 'CACHE_SET_STATUS'; payload: { isEnabled: boolean; isConnected: boolean } }
  | { type: 'CACHE_UPDATE_SYNC_TIME' }
  | { type: 'CACHE_ADD_PENDING_INVALIDATION'; payload: string }
  | { type: 'CACHE_CLEAR_PENDING_INVALIDATIONS' }
  | { type: 'PERFORMANCE_UPDATE_METRICS'; payload: Partial<PerformanceMetrics> }
  | { type: 'FEATURE_FLAGS_UPDATE'; payload: Partial<FeatureFlags> };

// Context type
export interface GlobalContextType {
  state: GlobalState;
  dispatch: React.Dispatch<GlobalAction>;
  // Computed values
  readonly isAuthenticated: boolean;
  readonly isAdmin: boolean;
  readonly hasContext: boolean;
  // Actions
  initializeAuth: () => Promise<void>;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  switchClient: (clientId: string, clientData?: Client) => Promise<void>;
  switchEngagement: (engagementId: string, engagementData?: Engagement) => Promise<void>;
  switchFlow: (flowId: string, flowData?: Flow) => Promise<void>;
  invalidateCache: (keys: string[]) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  updatePerformanceMetrics: (metrics: Partial<PerformanceMetrics>) => void;
  getAuthHeaders: () => Record<string, string>;
}

// Provider props
export interface GlobalContextProviderProps {
  children: ReactNode;
  initialFeatureFlags?: Partial<FeatureFlags>;
  enablePerformanceMonitoring?: boolean;
}

// Context storage interface
export interface ContextStorageData {
  user: User | null;
  client: Client | null;
  engagement: Engagement | null;
  flow: Flow | null;
  timestamp: number;
  version: string;
}

// WebSocket message types for cache invalidation
export interface CacheInvalidationMessage {
  type: 'cache_invalidation';
  keys: string[];
  timestamp: number;
  source: string;
}

// Performance monitoring configuration
export interface PerformanceConfig {
  enabled: boolean;
  sampleRate: number; // 0-1, percentage of events to sample
  reportInterval: number; // milliseconds
  maxMetricsHistory: number;
}
