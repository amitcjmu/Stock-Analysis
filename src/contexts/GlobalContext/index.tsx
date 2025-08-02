import React, { useReducer, useEffect, useRef, useCallback, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type {
  GlobalContextType,
  GlobalContextProviderProps,
  Notification,
  PerformanceMetrics,
} from './types';
import { GlobalState, GlobalAction, FeatureFlags } from './types';
import {
  globalReducer,
  createInitialState,
  selectIsAuthenticated,
  selectIsAdmin,
  selectHasContext,
} from './reducer';
import {
  contextStorage,
  preferencesStorage,
  featureFlagsStorage,
  maintainStorage,
} from './storage';
import { performanceMonitor } from '../../utils/performance/monitoring';
import { apiCall } from '../../config/api';
import { contextCache } from '../../utils/api/contextCache';
import { batchedStorage } from '../../utils/storage/batchedStorage';
import type { User, Client, Engagement, Flow } from '../AuthContext/types';
import { GlobalContext } from './context';

/**
 * Global Context Provider - Consolidates all app state management
 */
export const GlobalContextProvider: React.FC<GlobalContextProviderProps> = ({
  children,
  initialFeatureFlags = {},
  enablePerformanceMonitoring = process.env.NODE_ENV === 'development',
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
        payload: initialFeatureFlags,
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
          },
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
          },
        });

        // OPTIMIZATION: Background prefetch of recent contexts
        // Note: Prefetch will be handled in a separate effect to avoid circular dependencies

        performanceMonitor.markEnd('auth-initialization', { source: 'api' });
      } else {
        throw new Error('No user found in context response');
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      dispatch({
        type: 'AUTH_INIT_ERROR',
        payload: error instanceof Error ? error.message : 'Authentication failed',
      });
      performanceMonitor.markEnd('auth-initialization', { error: true });
    }
  }, [state.auth.isInitialized]);

  // Login function
  const login = useCallback(
    async (email: string, password: string): Promise<User> => {
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
            payload: response.user,
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
          payload: errorMessage,
        });
        performanceMonitor.markEnd('user-login', { error: true });
        throw error;
      }
    },
    [initializeAuth]
  );

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

  // Context switching functions - Optimized with parallel loading and cache-first approach
  const switchClient = useCallback(
    async (clientId: string, clientData?: Client): Promise<void> => {
      performanceMonitor.markStart('switch-client');
      dispatch({ type: 'CONTEXT_UPDATE_START' });

      try {
        // OPTIMIZATION 1: Parallel data loading with cache-first approach
        const [clientResult, engagementsResult, cachedEngagementsResult] = await Promise.allSettled(
          [
            // Load client data (cache-first)
            clientData
              ? Promise.resolve({ client: clientData, fromCache: false })
              : (async () => {
                  const cachedClient = await contextCache.getCachedClient(clientId);
                  if (cachedClient) {
                    return { client: cachedClient, fromCache: true };
                  }
                  const response = await apiCall(
                    `/api/v1/context-establishment/clients/${clientId}`
                  );
                  await contextCache.setCachedClient(clientId, response.client);
                  return { client: response.client, fromCache: false };
                })(),

            // Pre-load engagements for the client in parallel
            (async () => {
              const cachedEngagements = await contextCache.getCachedEngagements(clientId);
              if (cachedEngagements) {
                return { engagements: cachedEngagements, fromCache: true };
              }
              try {
                const response = await apiCall(
                  `/api/v1/context-establishment/clients/${clientId}/engagements`
                );
                await contextCache.setCachedEngagements(clientId, response.engagements || []);
                return { engagements: response.engagements || [], fromCache: false };
              } catch (error) {
                console.warn('Failed to pre-load engagements:', error);
                return { engagements: [], fromCache: false };
              }
            })(),

            // Background query cache warming
            queryClient
              .prefetchQuery({
                queryKey: ['engagements', clientId],
                queryFn: () =>
                  apiCall(`/api/v1/context-establishment/clients/${clientId}/engagements`),
                staleTime: 5 * 60 * 1000, // 5 minutes
              })
              .catch(() => null), // Don't fail on prefetch errors
          ]
        );

        // Extract client data
        const client = clientResult.status === 'fulfilled' ? clientResult.value.client : null;

        if (!client) {
          throw new Error('Client not found');
        }

        // OPTIMIZATION 2: Optimistic UI update before storage
        dispatch({ type: 'CONTEXT_SWITCH_CLIENT', payload: client });

        // OPTIMIZATION 3: Batched storage operations (non-blocking)
        const contextData = {
          user: state.auth.user,
          client,
          engagement: null, // Clear engagement when switching clients
          flow: null, // Clear flow when switching clients
        };

        // Use batched storage for better performance
        await Promise.allSettled([
          batchedStorage.queueOperation('global_context_v1', {
            ...contextData,
            timestamp: Date.now(),
            version: 'v1',
          }),
          // Also update the traditional storage for compatibility
          contextStorage.setContextData(contextData),
        ]);

        // OPTIMIZATION 4: Batch query invalidations
        const invalidationPromises = [
          queryClient.invalidateQueries({ queryKey: ['engagements'] }),
          queryClient.invalidateQueries({ queryKey: ['flows'] }),
        ];

        // Don't await invalidations - let them happen in background
        Promise.allSettled(invalidationPromises).catch(console.warn);

        // OPTIMIZATION 5: Background pre-fetching for likely next actions
        if (
          engagementsResult.status === 'fulfilled' &&
          engagementsResult.value.engagements.length > 0
        ) {
          // Pre-fetch the most recent engagement's flows in background
          const recentEngagement = engagementsResult.value.engagements[0];
          setTimeout(() => {
            contextCache.getCachedFlows(recentEngagement.id).catch(() => {
              // Background prefetch of flows
              apiCall(`/api/v1/context-establishment/engagements/${recentEngagement.id}/flows`)
                .then((response) =>
                  contextCache.setCachedFlows(recentEngagement.id, response.flows || [])
                )
                .catch(console.warn);
            });
          }, 100);
        }

        performanceMonitor.markEnd('switch-client', {
          clientId,
          fromCache: clientResult.status === 'fulfilled' ? clientResult.value.fromCache : false,
          preloadedEngagements:
            engagementsResult.status === 'fulfilled'
              ? engagementsResult.value.engagements.length
              : 0,
        });
      } catch (error) {
        dispatch({
          type: 'CONTEXT_UPDATE_ERROR',
          payload: error instanceof Error ? error.message : 'Failed to switch client',
        });
        performanceMonitor.markEnd('switch-client', { error: true });
        throw error;
      }
    },
    [state.auth.user, queryClient]
  );

  const switchEngagement = useCallback(
    async (engagementId: string, engagementData?: Engagement): Promise<void> => {
      performanceMonitor.markStart('switch-engagement');
      dispatch({ type: 'CONTEXT_UPDATE_START' });

      try {
        // OPTIMIZATION 1: Parallel data loading with cache-first approach
        const [engagementResult, flowsResult] = await Promise.allSettled([
          // Load engagement data (cache-first)
          engagementData
            ? Promise.resolve({ engagement: engagementData, fromCache: false })
            : (async () => {
                const cachedEngagement = await contextCache.getCachedEngagement(engagementId);
                if (cachedEngagement) {
                  return { engagement: cachedEngagement, fromCache: true };
                }
                const response = await apiCall(
                  `/api/v1/context-establishment/engagements/${engagementId}`
                );
                await contextCache.setCachedEngagement(engagementId, response.engagement);
                return { engagement: response.engagement, fromCache: false };
              })(),

          // Pre-load flows for the engagement in parallel
          (async () => {
            const cachedFlows = await contextCache.getCachedFlows(engagementId);
            if (cachedFlows) {
              return { flows: cachedFlows, fromCache: true };
            }
            try {
              const response = await apiCall(
                `/api/v1/context-establishment/engagements/${engagementId}/flows`
              );
              await contextCache.setCachedFlows(engagementId, response.flows || []);
              return { flows: response.flows || [], fromCache: false };
            } catch (error) {
              console.warn('Failed to pre-load flows:', error);
              return { flows: [], fromCache: false };
            }
          })(),
        ]);

        // Extract engagement data
        const engagement =
          engagementResult.status === 'fulfilled' ? engagementResult.value.engagement : null;

        if (!engagement) {
          throw new Error('Engagement not found');
        }

        // OPTIMIZATION 2: Optimistic UI update before storage
        dispatch({ type: 'CONTEXT_SWITCH_ENGAGEMENT', payload: engagement });

        // OPTIMIZATION 3: Batched storage operations (non-blocking)
        const contextData = {
          user: state.auth.user,
          client: state.context.client,
          engagement,
          flow: null, // Clear flow when switching engagements
        };

        // Use batched storage for better performance
        await Promise.allSettled([
          batchedStorage.queueOperation('global_context_v1', {
            ...contextData,
            timestamp: Date.now(),
            version: 'v1',
          }),
          // Also update the traditional storage for compatibility
          contextStorage.setContextData(contextData),
        ]);

        // OPTIMIZATION 4: Background query invalidations (non-blocking)
        queryClient.invalidateQueries({ queryKey: ['flows'] }).catch(console.warn);

        // OPTIMIZATION 5: Pre-fetch query cache for flows
        if (flowsResult.status === 'fulfilled' && flowsResult.value.flows.length > 0) {
          queryClient.setQueryData(['flows', engagementId], flowsResult.value.flows);

          // Pre-fetch the most recent flow's details in background
          const recentFlow = flowsResult.value.flows[0];
          setTimeout(() => {
            apiCall(`/api/v1/flows/${recentFlow.id}`)
              .then((response) => contextCache.setCachedFlow(recentFlow.id, response.flow))
              .catch(console.warn);
          }, 100);
        }

        performanceMonitor.markEnd('switch-engagement', {
          engagementId,
          fromCache:
            engagementResult.status === 'fulfilled' ? engagementResult.value.fromCache : false,
          preloadedFlows: flowsResult.status === 'fulfilled' ? flowsResult.value.flows.length : 0,
        });
      } catch (error) {
        dispatch({
          type: 'CONTEXT_UPDATE_ERROR',
          payload: error instanceof Error ? error.message : 'Failed to switch engagement',
        });
        performanceMonitor.markEnd('switch-engagement', { error: true });
        throw error;
      }
    },
    [state.auth.user, state.context.client, queryClient]
  );

  const switchFlow = useCallback(
    async (flowId: string, flowData?: Flow): Promise<void> => {
      performanceMonitor.markStart('switch-flow');
      dispatch({ type: 'CONTEXT_UPDATE_START' });

      try {
        // OPTIMIZATION 1: Cache-first approach for flow data
        const flow = await (async () => {
          if (flowData) {
            return { flow: flowData, fromCache: false };
          }

          const cachedFlow = await contextCache.getCachedFlow(flowId);
          if (cachedFlow) {
            return { flow: cachedFlow, fromCache: true };
          }

          const response = await apiCall(`/api/v1/flows/${flowId}`);
          await contextCache.setCachedFlow(flowId, response.flow);
          return { flow: response.flow, fromCache: false };
        })();

        if (!flow.flow) {
          throw new Error('Flow not found');
        }

        // OPTIMIZATION 2: Optimistic UI update
        dispatch({ type: 'CONTEXT_SWITCH_FLOW', payload: flow.flow });

        // OPTIMIZATION 3: Batched storage operations (non-blocking)
        const contextData = {
          user: state.auth.user,
          client: state.context.client,
          engagement: state.context.engagement,
          flow: flow.flow,
        };

        // Use batched storage for better performance
        await Promise.allSettled([
          batchedStorage.queueOperation('global_context_v1', {
            ...contextData,
            timestamp: Date.now(),
            version: 'v1',
          }),
          // Also update the traditional storage for compatibility
          contextStorage.setContextData(contextData),
        ]);

        performanceMonitor.markEnd('switch-flow', {
          flowId,
          fromCache: flow.fromCache,
        });
      } catch (error) {
        dispatch({
          type: 'CONTEXT_UPDATE_ERROR',
          payload: error instanceof Error ? error.message : 'Failed to switch flow',
        });
        performanceMonitor.markEnd('switch-flow', { error: true });
        throw error;
      }
    },
    [state.auth.user, state.context.client, state.context.engagement]
  );

  // Context pre-fetching for performance optimization
  const prefetchUserContext = useCallback(
    async (
      userId: string,
      recentClientIds: string[] = [],
      recentEngagementIds: string[] = []
    ): Promise<void> => {
      try {
        // Background prefetch of recent contexts
        await contextCache.prefetchContext(userId, recentClientIds, recentEngagementIds);

        // Pre-warm query cache for common operations
        const prefetchPromises = [
          ...recentClientIds.slice(0, 3).map((clientId) =>
            queryClient
              .prefetchQuery({
                queryKey: ['engagements', clientId],
                queryFn: () =>
                  apiCall(`/api/v1/context-establishment/clients/${clientId}/engagements`),
                staleTime: 5 * 60 * 1000, // 5 minutes
              })
              .catch(() => null)
          ),
          ...recentEngagementIds.slice(0, 3).map((engagementId) =>
            queryClient
              .prefetchQuery({
                queryKey: ['flows', engagementId],
                queryFn: () =>
                  apiCall(`/api/v1/context-establishment/engagements/${engagementId}/flows`),
                staleTime: 3 * 60 * 1000, // 3 minutes
              })
              .catch(() => null)
          ),
        ];

        // Execute prefetch in background without blocking
        Promise.allSettled(prefetchPromises).catch(console.warn);
      } catch (error) {
        console.warn('Context prefetch failed:', error);
      }
    },
    [queryClient]
  );

  // Cache invalidation with context cache integration
  const invalidateCache = useCallback(
    (keys: string[]): void => {
      keys.forEach((key) => {
        dispatch({ type: 'CACHE_ADD_PENDING_INVALIDATION', payload: key });
        queryClient.invalidateQueries({ queryKey: [key] });

        // Also invalidate context cache for related data
        if (key.includes('client')) {
          const clientId = key.replace(/.*client[s]?[_-]?/, '');
          if (clientId) contextCache.invalidateClientCache(clientId);
        }
        if (key.includes('engagement')) {
          const engagementId = key.replace(/.*engagement[s]?[_-]?/, '');
          if (engagementId) contextCache.invalidateEngagementCache(engagementId);
        }
      });

      // Clear pending invalidations after processing
      setTimeout(() => {
        dispatch({ type: 'CACHE_CLEAR_PENDING_INVALIDATIONS' });
      }, 1000);
    },
    [queryClient]
  );

  // Notification management
  const addNotification = useCallback(
    (notification: Omit<Notification, 'id' | 'timestamp'>): void => {
      dispatch({ type: 'UI_ADD_NOTIFICATION', payload: notification });

      // Auto-remove notification after duration
      if (notification.duration) {
        setTimeout(() => {
          // We'll need the notification ID, which will be generated in the reducer
          // This is a simplified implementation - in practice, we'd store the ID
        }, notification.duration);
      }
    },
    []
  );

  const removeNotification = useCallback((id: string): void => {
    dispatch({ type: 'UI_REMOVE_NOTIFICATION', payload: id });
  }, []);

  // Performance metrics update
  const updatePerformanceMetrics = useCallback(
    (metrics: Partial<PerformanceMetrics>): void => {
      if (state.featureFlags.enablePerformanceMonitoring) {
        dispatch({ type: 'PERFORMANCE_UPDATE_METRICS', payload: metrics });
      }
    },
    [state.featureFlags.enablePerformanceMonitoring]
  );

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

  // Background prefetch for authenticated users
  useEffect(() => {
    if (isAuthenticated && state.auth.user) {
      // Delay prefetch to not block initial rendering
      const prefetchTimer = setTimeout(() => {
        // Get recent clients/engagements from storage or API response
        const storedContext = contextStorage.getContextData();
        if (storedContext) {
          // For now, we'll prefetch based on current context
          // In a real implementation, this would come from user preferences or API
          const recentClientIds = storedContext.client ? [storedContext.client.id] : [];
          const recentEngagementIds = storedContext.engagement ? [storedContext.engagement.id] : [];

          prefetchUserContext(state.auth.user.id, recentClientIds, recentEngagementIds).catch(
            console.warn
          );
        }
      }, 1000); // 1 second delay

      return () => clearTimeout(prefetchTimer);
    }
  }, [isAuthenticated, state.auth.user, prefetchUserContext]);

  // Cleanup on unmount - flush pending storage operations
  useEffect(() => {
    return () => {
      batchedStorage.flush().catch(console.warn);
    };
  }, []);

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    (): GlobalContextType => ({
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
      prefetchUserContext,
    }),
    [
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
      prefetchUserContext,
    ]
  );

  return (
    <GlobalContext.Provider value={contextValue}>
      {state.auth.isInitialized ? (
        children
      ) : (
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

// Hooks are exported from ./hooks/index.ts

// Export types
export type { GlobalState, GlobalAction, GlobalContextType } from './types';
