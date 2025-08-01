import type { GlobalState, GlobalAction, PerformanceMetrics } from './types';

// Initial state
export const createInitialState = (enablePerformanceMonitoring = false): GlobalState => ({
  auth: {
    user: null,
    isLoading: true,
    isInitialized: false,
    isLoginInProgress: false,
    error: null,
    isDemoMode: false,
  },
  context: {
    client: null,
    engagement: null,
    flow: null,
    isLoading: false,
    error: null,
    lastFetchTime: null,
  },
  ui: {
    sidebarOpen: false,
    notifications: [],
    isLoading: false,
    theme: 'auto',
  },
  cache: {
    isEnabled: false,
    isConnected: false,
    lastSyncTime: null,
    pendingInvalidations: [],
  },
  performance: {
    renderCount: 0,
    lastRenderTime: 0,
    averageRenderTime: 0,
    cacheHitRate: 0,
    apiCallCount: 0,
  },
  featureFlags: {
    useRedisCache: process.env.NODE_ENV === 'production',
    enablePerformanceMonitoring,
    useWebSocketSync: true,
    enableContextDebugging: process.env.NODE_ENV === 'development',
    useProgressiveHydration: true,
  },
});

// Helper function to update performance metrics
const updatePerformanceMetrics = (
  current: PerformanceMetrics,
  updates: Partial<PerformanceMetrics>
): PerformanceMetrics => {
  const newMetrics = { ...current, ...updates };

  // Update render count and calculate average render time
  if (updates.lastRenderTime !== undefined) {
    newMetrics.renderCount = current.renderCount + 1;
    newMetrics.averageRenderTime =
      (current.averageRenderTime * (current.renderCount - 1) + updates.lastRenderTime) /
      newMetrics.renderCount;
  }

  return newMetrics;
};

// Helper function to generate unique notification ID
const generateNotificationId = (): string => {
  return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// Main reducer
export function globalReducer(state: GlobalState, action: GlobalAction): GlobalState {
  switch (action.type) {
    // Auth actions
    case 'AUTH_INIT_START':
      return {
        ...state,
        auth: {
          ...state.auth,
          isLoading: true,
          error: null,
        },
      };

    case 'AUTH_INIT_SUCCESS':
      return {
        ...state,
        auth: {
          ...state.auth,
          user: action.payload.user,
          isLoading: false,
          isInitialized: true,
          error: null,
          isDemoMode: action.payload.user.id.includes('demo') || action.payload.user.email.includes('demo'),
        },
        context: {
          ...state.context,
          client: action.payload.client || null,
          engagement: action.payload.engagement || null,
          flow: action.payload.flow || null,
          lastFetchTime: Date.now(),
          error: null,
        },
      };

    case 'AUTH_INIT_ERROR':
      return {
        ...state,
        auth: {
          ...state.auth,
          isLoading: false,
          isInitialized: true,
          error: action.payload,
        },
      };

    case 'AUTH_LOGIN_START':
      return {
        ...state,
        auth: {
          ...state.auth,
          isLoginInProgress: true,
          error: null,
        },
      };

    case 'AUTH_LOGIN_SUCCESS':
      return {
        ...state,
        auth: {
          ...state.auth,
          user: action.payload,
          isLoginInProgress: false,
          isInitialized: true,
          error: null,
          isDemoMode: action.payload.id.includes('demo') || action.payload.email.includes('demo'),
        },
      };

    case 'AUTH_LOGIN_ERROR':
      return {
        ...state,
        auth: {
          ...state.auth,
          isLoginInProgress: false,
          error: action.payload,
        },
      };

    case 'AUTH_LOGOUT':
      return {
        ...createInitialState(state.featureFlags.enablePerformanceMonitoring),
        auth: {
          ...createInitialState(state.featureFlags.enablePerformanceMonitoring).auth,
          isInitialized: true,
        },
        featureFlags: state.featureFlags,
        performance: state.performance, // Keep performance metrics across logout
      };

    // Context actions
    case 'CONTEXT_UPDATE_START':
      return {
        ...state,
        context: {
          ...state.context,
          isLoading: true,
          error: null,
        },
      };

    case 'CONTEXT_UPDATE_SUCCESS':
      return {
        ...state,
        context: {
          ...state.context,
          client: action.payload.client || state.context.client,
          engagement: action.payload.engagement || state.context.engagement,
          flow: action.payload.flow || state.context.flow,
          isLoading: false,
          error: null,
          lastFetchTime: Date.now(),
        },
      };

    case 'CONTEXT_UPDATE_ERROR':
      return {
        ...state,
        context: {
          ...state.context,
          isLoading: false,
          error: action.payload,
        },
      };

    case 'CONTEXT_SWITCH_CLIENT':
      return {
        ...state,
        context: {
          ...state.context,
          client: action.payload,
          // Clear engagement and flow when switching clients
          engagement: null,
          flow: null,
          lastFetchTime: Date.now(),
        },
      };

    case 'CONTEXT_SWITCH_ENGAGEMENT':
      return {
        ...state,
        context: {
          ...state.context,
          engagement: action.payload,
          // Clear flow when switching engagements
          flow: null,
          lastFetchTime: Date.now(),
        },
      };

    case 'CONTEXT_SWITCH_FLOW':
      return {
        ...state,
        context: {
          ...state.context,
          flow: action.payload,
          lastFetchTime: Date.now(),
        },
      };

    // UI actions
    case 'UI_TOGGLE_SIDEBAR':
      return {
        ...state,
        ui: {
          ...state.ui,
          sidebarOpen: !state.ui.sidebarOpen,
        },
      };

    case 'UI_SET_THEME':
      return {
        ...state,
        ui: {
          ...state.ui,
          theme: action.payload,
        },
      };

    case 'UI_ADD_NOTIFICATION': {
      const newNotification = {
        ...action.payload,
        id: generateNotificationId(),
        timestamp: Date.now(),
      };
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: [...state.ui.notifications, newNotification],
        },
      };
    }

    case 'UI_REMOVE_NOTIFICATION':
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: state.ui.notifications.filter(n => n.id !== action.payload),
        },
      };

    case 'UI_SET_LOADING':
      return {
        ...state,
        ui: {
          ...state.ui,
          isLoading: action.payload,
        },
      };

    // Cache actions
    case 'CACHE_SET_STATUS':
      return {
        ...state,
        cache: {
          ...state.cache,
          isEnabled: action.payload.isEnabled,
          isConnected: action.payload.isConnected,
        },
      };

    case 'CACHE_UPDATE_SYNC_TIME':
      return {
        ...state,
        cache: {
          ...state.cache,
          lastSyncTime: Date.now(),
        },
      };

    case 'CACHE_ADD_PENDING_INVALIDATION':
      return {
        ...state,
        cache: {
          ...state.cache,
          pendingInvalidations: [...state.cache.pendingInvalidations, action.payload],
        },
      };

    case 'CACHE_CLEAR_PENDING_INVALIDATIONS':
      return {
        ...state,
        cache: {
          ...state.cache,
          pendingInvalidations: [],
        },
      };

    // Performance actions
    case 'PERFORMANCE_UPDATE_METRICS':
      return {
        ...state,
        performance: updatePerformanceMetrics(state.performance, action.payload),
      };

    // Feature flags actions
    case 'FEATURE_FLAGS_UPDATE':
      return {
        ...state,
        featureFlags: {
          ...state.featureFlags,
          ...action.payload,
        },
      };

    default:
      if (process.env.NODE_ENV === 'development') {
        console.warn('Unknown action type:', (action as { type: string }).type);
      }
      return state;
  }
}

// Selectors for computed values
export const selectIsAuthenticated = (state: GlobalState): boolean => {
  return !!state.auth.user && state.auth.isInitialized;
};

export const selectIsAdmin = (state: GlobalState): boolean => {
  return state.auth.user?.role === 'admin';
};

export const selectHasContext = (state: GlobalState): boolean => {
  return !!(state.context.client || state.context.engagement || state.context.flow);
};

export const selectCurrentUserId = (state: GlobalState): string | null => {
  return state.auth.user?.id || null;
};

export const selectCurrentClientId = (state: GlobalState): string | null => {
  return state.context.client?.id || null;
};

export const selectCurrentEngagementId = (state: GlobalState): string | null => {
  return state.context.engagement?.id || null;
};

export const selectCurrentFlowId = (state: GlobalState): string | null => {
  return state.context.flow?.id || null;
};
