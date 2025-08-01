import React, { createContext, useContext, useReducer, useEffect, useRef, useCallback, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type {
  GlobalContextType,
  GlobalContextProviderProps,
  Notification,
  PerformanceMetrics
} from './types';
import {
  GlobalState,
  GlobalAction,
  FeatureFlags
} from './types';
import { globalReducer, createInitialState, selectIsAuthenticated, selectIsAdmin, selectHasContext } from './reducer';
import { contextStorage, preferencesStorage, featureFlagsStorage, maintainStorage } from './storage';
import { performanceMonitor } from '../../utils/performance/monitoring';
import { apiCall } from '../../config/api';
import type { User, Client, Engagement, Flow } from '../AuthContext/types';

// Create the context
const GlobalContext = createContext<GlobalContextType | undefined>(undefined);

/**
 * Global Context Provider - Consolidates all app state management
 */
export const GlobalContextProvider: React.FC<GlobalContextProviderProps> = ({
  children,
  initialFeatureFlags = {},
  enablePerformanceMonitoring = process.env.NODE_ENV === 'development'
}) => {
  const queryClient = useQueryClient();
  const initRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize state with feature flags
  const [state, dispatch] = useReducer(
    globalReducer,
    createInitialState(enablePerformanceMonitoring)
  );

  // Apply initial feature flags
  useEffect(() => {
    if (Object.keys(initialFeatureFlags).length > 0) {
      dispatch({
        type: 'FEATURE_FLAGS_UPDATE',
        payload: initialFeatureFlags
      });
    }
  }, [initialFeatureFlags]);

  // Memoized computed values
  const isAuthenticated = useMemo(() => selectIsAuthenticated(state), [state]);
  const isAdmin = useMemo(() => selectIsAdmin(state), [state]);
  const hasContext = useMemo(() => selectHasContext(state), [state]);

  // Initialize auth and context
  const initializeAuth = useCallback(async (): Promise<void> => {
    if (initRef.current || state.auth.isInitialized) return;
    initRef.current = true;

    performanceMonitor.markStart('auth-initialization');
    dispatch({ type: 'AUTH_INIT_START' });

    try {
      // Check stored context first
      const storedContext = contextStorage.getContextData();
      if (storedContext && contextStorage.isContextDataValid()) {
        dispatch({
          type: 'AUTH_INIT_SUCCESS',
          payload: {
            user: storedContext.user,
            client: storedContext.client || undefined,
            engagement: storedContext.engagement || undefined,
            flow: storedContext.flow || undefined,
          }
        });
        performanceMonitor.markEnd('auth-initialization', { source: 'cache' });
        return;
      }

      // Fetch fresh context from API
      const response = await apiCall('/api/v1/context/me', {}, false);

      if (response.user) {
        const contextData = {
          user: response.user,
          client: response.client || null,
          engagement: response.engagement || null,
          flow: response.flow || null,
        };

        // Store in session storage
        contextStorage.setContextData(contextData);

        dispatch({
          type: 'AUTH_INIT_SUCCESS',
          payload: {
            user: response.user,
            client: response.client,
            engagement: response.engagement,
            flow: response.flow,
          }
        });

        performanceMonitor.markEnd('auth-initialization', { source: 'api' });
      } else {
        throw new Error('No user found in context response');
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      dispatch({
        type: 'AUTH_INIT_ERROR',
        payload: error instanceof Error ? error.message : 'Authentication failed'
      });
      performanceMonitor.markEnd('auth-initialization', { error: true });
    }
  }, [state.auth.isInitialized]);

  // Login function
  const login = useCallback(async (email: string, password: string): Promise<User> => {
    performanceMonitor.markStart('user-login');
    dispatch({ type: 'AUTH_LOGIN_START' });

    try {
      const response = await apiCall('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (response.user) {
        dispatch({
          type: 'AUTH_LOGIN_SUCCESS',
          payload: response.user
        });

        // Initialize context after successful login
        await initializeAuth();

        performanceMonitor.markEnd('user-login', { success: true });
        return response.user;
      } else {
        throw new Error('Login failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({
        type: 'AUTH_LOGIN_ERROR',
        payload: errorMessage
      });
      performanceMonitor.markEnd('user-login', { error: true });
      throw error;
    }
  }, [initializeAuth]);

  // Logout function
  const logout = useCallback((): void => {
    performanceMonitor.markStart('user-logout');

    try {
      // Clear storage
      contextStorage.clearContextData();

      // Clear query cache
      queryClient.clear();

      // Close WebSocket connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      // Dispatch logout action
      dispatch({ type: 'AUTH_LOGOUT' });

      performanceMonitor.markEnd('user-logout');
    } catch (error) {
      console.error('Logout error:', error);
      performanceMonitor.markEnd('user-logout', { error: true });
    }
  }, [queryClient]);

  // Context switching functions
  const switchClient = useCallback(async (clientId: string, clientData?: Client): Promise<void> => {
    performanceMonitor.markStart('switch-client');
    dispatch({ type: 'CONTEXT_UPDATE_START' });

    try {
      let client = clientData;

      if (!client) {
        const response = await apiCall(`/api/v1/context-establishment/clients/${clientId}`);
        client = response.client;
      }

      if (client) {
        dispatch({ type: 'CONTEXT_SWITCH_CLIENT', payload: client });

        // Update stored context
        contextStorage.setContextData({
          user: state.auth.user,
          client,
          engagement: null, // Clear engagement when switching clients
          flow: null, // Clear flow when switching clients
        });

        // Invalidate related queries
        await queryClient.invalidateQueries({ queryKey: ['engagements'] });
        await queryClient.invalidateQueries({ queryKey: ['flows'] });

        performanceMonitor.markEnd('switch-client', { clientId });
      } else {
        throw new Error('Client not found');
      }
    } catch (error) {
      dispatch({
        type: 'CONTEXT_UPDATE_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to switch client'
      });
      performanceMonitor.markEnd('switch-client', { error: true });
      throw error;
    }
  }, [state.auth.user, queryClient]);

  const switchEngagement = useCallback(async (engagementId: string, engagementData?: Engagement): Promise<void> => {
    performanceMonitor.markStart('switch-engagement');
    dispatch({ type: 'CONTEXT_UPDATE_START' });

    try {
      let engagement = engagementData;

      if (!engagement) {
        const response = await apiCall(`/api/v1/context-establishment/engagements/${engagementId}`);
        engagement = response.engagement;
      }

      if (engagement) {
        dispatch({ type: 'CONTEXT_SWITCH_ENGAGEMENT', payload: engagement });

        // Update stored context
        contextStorage.setContextData({
          user: state.auth.user,
          client: state.context.client,
          engagement,
          flow: null, // Clear flow when switching engagements
        });

        // Invalidate related queries
        await queryClient.invalidateQueries({ queryKey: ['flows'] });

        performanceMonitor.markEnd('switch-engagement', { engagementId });
      } else {
        throw new Error('Engagement not found');
      }
    } catch (error) {
      dispatch({
        type: 'CONTEXT_UPDATE_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to switch engagement'
      });
      performanceMonitor.markEnd('switch-engagement', { error: true });
      throw error;
    }
  }, [state.auth.user, state.context.client, queryClient]);

  const switchFlow = useCallback(async (flowId: string, flowData?: Flow): Promise<void> => {
    performanceMonitor.markStart('switch-flow');
    dispatch({ type: 'CONTEXT_UPDATE_START' });

    try {
      let flow = flowData;

      if (!flow) {
        const response = await apiCall(`/api/v1/flows/${flowId}`);
        flow = response.flow;
      }

      if (flow) {
        dispatch({ type: 'CONTEXT_SWITCH_FLOW', payload: flow });

        // Update stored context
        contextStorage.setContextData({
          user: state.auth.user,
          client: state.context.client,
          engagement: state.context.engagement,
          flow,
        });

        performanceMonitor.markEnd('switch-flow', { flowId });
      } else {
        throw new Error('Flow not found');
      }
    } catch (error) {
      dispatch({
        type: 'CONTEXT_UPDATE_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to switch flow'
      });
      performanceMonitor.markEnd('switch-flow', { error: true });
      throw error;
    }
  }, [state.auth.user, state.context.client, state.context.engagement]);

  // Cache invalidation
  const invalidateCache = useCallback((keys: string[]): void => {
    keys.forEach(key => {
      dispatch({ type: 'CACHE_ADD_PENDING_INVALIDATION', payload: key });
      queryClient.invalidateQueries({ queryKey: [key] });
    });

    // Clear pending invalidations after processing
    setTimeout(() => {
      dispatch({ type: 'CACHE_CLEAR_PENDING_INVALIDATIONS' });
    }, 1000);
  }, [queryClient]);

  // Notification management
  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>): void => {
    dispatch({ type: 'UI_ADD_NOTIFICATION', payload: notification });

    // Auto-remove notification after duration
    if (notification.duration) {
      setTimeout(() => {
        // We'll need the notification ID, which will be generated in the reducer
        // This is a simplified implementation - in practice, we'd store the ID
      }, notification.duration);
    }
  }, []);

  const removeNotification = useCallback((id: string): void => {
    dispatch({ type: 'UI_REMOVE_NOTIFICATION', payload: id });
  }, []);

  // Performance metrics update
  const updatePerformanceMetrics = useCallback((metrics: Partial<PerformanceMetrics>): void => {
    if (state.featureFlags.enablePerformanceMonitoring) {
      dispatch({ type: 'PERFORMANCE_UPDATE_METRICS', payload: metrics });
    }
  }, [state.featureFlags.enablePerformanceMonitoring]);

  // Auth headers generation
  const getAuthHeaders = useCallback((): Record<string, string> => {
    const headers: Record<string, string> = {};

    if (state.auth.user) {
      headers['X-User-ID'] = state.auth.user.id;
    }

    if (state.context.client) {
      headers['X-Client-ID'] = state.context.client.id;
    }

    if (state.context.engagement) {
      headers['X-Engagement-ID'] = state.context.engagement.id;
    }

    if (state.context.flow) {
      headers['X-Flow-ID'] = state.context.flow.id;
    }

    return headers;
  }, [state.auth.user, state.context.client, state.context.engagement, state.context.flow]);

  // Initialize performance monitoring
  useEffect(() => {
    if (state.featureFlags.enablePerformanceMonitoring) {
      const unsubscribe = performanceMonitor.subscribe((metrics) => {
        updatePerformanceMetrics(metrics);
      });

      return unsubscribe;
    }
  }, [state.featureFlags.enablePerformanceMonitoring, updatePerformanceMetrics]);

  // WebSocket integration for real-time cache updates
  useEffect(() => {
    if (state.featureFlags.useWebSocketSync && isAuthenticated && !wsRef.current) {
      try {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/cache-invalidation`;

        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          dispatch({ type: 'CACHE_SET_STATUS', payload: { isEnabled: true, isConnected: true } });
        };

        wsRef.current.onclose = () => {
          dispatch({ type: 'CACHE_SET_STATUS', payload: { isEnabled: true, isConnected: false } });
        };

        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'cache_invalidation') {
              invalidateCache(message.keys);
            }
          } catch (error) {
            console.warn('Failed to parse WebSocket message:', error);
          }
        };
      } catch (error) {
        console.warn('Failed to establish WebSocket connection:', error);
      }
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [state.featureFlags.useWebSocketSync, isAuthenticated, invalidateCache]);

  // Storage maintenance
  useEffect(() => {
    const interval = setInterval(maintainStorage, 300000); // Every 5 minutes
    return () => clearInterval(interval);
  }, []);

  // Auto-initialization
  useEffect(() => {
    if (!state.auth.isInitialized && !initRef.current) {
      initializeAuth();
    }
  }, [state.auth.isInitialized, initializeAuth]);

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo((): GlobalContextType => ({
    state,
    dispatch,
    // Computed values
    isAuthenticated,
    isAdmin,
    hasContext,
    // Actions
    initializeAuth,
    login,
    logout,
    switchClient,
    switchEngagement,
    switchFlow,
    invalidateCache,
    addNotification,
    removeNotification,
    updatePerformanceMetrics,
    getAuthHeaders,
  }), [
    state,
    dispatch,
    isAuthenticated,
    isAdmin,
    hasContext,
    initializeAuth,
    login,
    logout,
    switchClient,
    switchEngagement,
    switchFlow,
    invalidateCache,
    addNotification,
    removeNotification,
    updatePerformanceMetrics,
    getAuthHeaders,
  ]);

  return (
    <GlobalContext.Provider value={contextValue}>
      {state.auth.isInitialized ? children : (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Initializing application...</p>
          </div>
        </div>
      )}
    </GlobalContext.Provider>
  );
};

/**
 * Hook to use the Global Context
 */
export const useGlobalContext = (): GlobalContextType => {
  const context = useContext(GlobalContext);
  if (context === undefined) {
    throw new Error('useGlobalContext must be used within a GlobalContextProvider');
  }
  return context;
};

/**
 * Hook to use auth state and actions
 */
export const useGlobalAuth = () => {
  const { state, login, logout, initializeAuth, isAuthenticated, isAdmin } = useGlobalContext();

  return {
    user: state.auth.user,
    isLoading: state.auth.isLoading,
    isInitialized: state.auth.isInitialized,
    error: state.auth.error,
    isDemoMode: state.auth.isDemoMode,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    initializeAuth,
  };
};

/**
 * Hook to use context state and actions
 */
export const useGlobalUserContext = () => {
  const {
    state,
    switchClient,
    switchEngagement,
    switchFlow,
    hasContext,
    getAuthHeaders
  } = useGlobalContext();

  return {
    client: state.context.client,
    engagement: state.context.engagement,
    flow: state.context.flow,
    isLoading: state.context.isLoading,
    error: state.context.error,
    hasContext,
    switchClient,
    switchEngagement,
    switchFlow,
    getAuthHeaders,
  };
};

/**
 * Hook to use performance monitoring
 */
export const useGlobalPerformance = () => {
  const { state, updatePerformanceMetrics } = useGlobalContext();

  return {
    metrics: state.performance,
    enabled: state.featureFlags.enablePerformanceMonitoring,
    updateMetrics: updatePerformanceMetrics,
  };
};

/**
 * Hook to use notifications
 */
export const useGlobalNotifications = () => {
  const { state, addNotification, removeNotification } = useGlobalContext();

  return {
    notifications: state.ui.notifications,
    addNotification,
    removeNotification,
  };
};

// Export types for convenience
export type { GlobalState, GlobalAction, GlobalContextType } from './types';
