/**
 * WebSocket Hook for Cache Invalidation Events
 *
 * Provides real-time cache invalidation notifications from the backend
 * Redis cache system via WebSocket connections.
 *
 * CC Generated WebSocket Cache Events Hook
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { isCacheFeatureEnabled } from '@/constants/features';
import type {
  CacheInvalidationEvent,
  WebSocketCacheMessage,
  CacheEventType} from '@/types/websocket';
import {
  CACHE_EVENT_TYPES,
  WS_MESSAGE_TYPES,
  isWelcomeMessage,
  isCacheInvalidationMessage,
  isPingMessage,
  isStatsMessage,
  isSubscriptionUpdatedMessage,
  isErrorMessage
} from '@/types/websocket';

// Re-export types for convenience
export type { CacheInvalidationEvent, CacheEventType };
export { CACHE_EVENT_TYPES };

// Subscription callback type
export type CacheEventCallback = (event: CacheInvalidationEvent) => void;

// WebSocket state
interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connectionId: string | null;
  reconnectAttempts: number;
  lastEvent: CacheInvalidationEvent | null;
}

// Hook options
interface UseWebSocketOptions {
  clientAccountId?: string;
  engagementId?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  subscribedEvents?: CacheEventType[];
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: string) => void;
}

/**
 * WebSocket hook for cache invalidation events
 */
export const useWebSocket = (options: UseWebSocketOptions = {}): {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  connectionId: string | null;
  reconnectAttempts: number;
  canReconnect: boolean;
  lastEvent: WebSocketCacheMessage | null;
  connect: () => void;
  disconnect: () => void;
  subscribe: (eventType: string, callback: (event: WebSocketCacheMessage) => void) => () => void;
  updateSubscription: (events: string[]) => boolean;
  sendMessage: (message: Partial<WebSocketCacheMessage>) => boolean;
  getStats: () => boolean;
  isFeatureEnabled: boolean;
} => {
  const {
    clientAccountId,
    engagementId,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    subscribedEvents = [
      CACHE_EVENT_TYPES.CACHE_INVALIDATION,
      CACHE_EVENT_TYPES.USER_CONTEXT_CHANGED,
      CACHE_EVENT_TYPES.FIELD_MAPPINGS_UPDATED,
      CACHE_EVENT_TYPES.FLOW_STATE_CHANGED,
      CACHE_EVENT_TYPES.ENGAGEMENT_MODIFIED,
      CACHE_EVENT_TYPES.ASSET_INVENTORY_UPDATED
    ],
    onConnect,
    onDisconnect,
    onError
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    connectionId: null,
    reconnectAttempts: 0,
    lastEvent: null
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const eventCallbacksRef = useRef<Map<string, Set<CacheEventCallback>>>(new Map());
  const reconnectAttemptsRef = useRef<number>(0);
  const lastConnectionAttemptRef = useRef<number>(0);
  const connectionHealthRef = useRef<'healthy' | 'degraded' | 'failed'>('healthy');

  // Get auth token for WebSocket connection
  const getAuthToken = useCallback(() => {
    try {
      return localStorage.getItem('auth_token') || '';
    } catch {
      return '';
    }
  }, []);

  // Get client account ID from storage if not provided
  const getClientAccountId = useCallback(() => {
    if (clientAccountId) return clientAccountId;

    try {
      const client = localStorage.getItem('auth_client');
      if (client && client !== 'null') {
        const clientData = JSON.parse(client);
        return clientData?.id || 'demo-client';
      }
    } catch {
      // Ignore parsing errors
    }
    return 'demo-client';
  }, [clientAccountId]);

  // Build WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Fix: Use backend port 8000 instead of frontend port
    const host = window.location.hostname;
    const port = process.env.NODE_ENV === 'development' ? '8000' : window.location.port || '8000';
    const clientId = getClientAccountId();
    const token = getAuthToken();

    let url = `${protocol}//${host}:${port}/api/v1/ws-cache/events?client_account_id=${clientId}`;

    if (engagementId) {
      url += `&engagement_id=${engagementId}`;
    }

    if (token) {
      url += `&token=${encodeURIComponent(token)}`;
    }

    return url;
  }, [getClientAccountId, getAuthToken, engagementId]);

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Clear ping interval
  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Start ping interval to respond to server pings
  const startPingInterval = useCallback(() => {
    clearPingInterval();
    // No automatic pinging - just respond to server pings
  }, [clearPingInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Check if WebSocket cache is enabled
    if (!isCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE')) {
      return; // Silent return to prevent console spam
    }

    if (wsRef.current?.readyState === WebSocket.OPEN || state.isConnecting) {
      return;
    }

    // Throttle connection attempts to prevent spam
    const now = Date.now();
    const timeSinceLastAttempt = now - lastConnectionAttemptRef.current;
    const minConnectionInterval = 30000; // 30 seconds minimum between attempts

    if (timeSinceLastAttempt < minConnectionInterval) {
      return; // Silent throttling to prevent console spam
    }

    lastConnectionAttemptRef.current = now;
    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const url = getWebSocketUrl();
      // Only log connection attempts when debug is specifically enabled
      if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_DEBUG')) {
        console.log('🔗 Connecting to WebSocket cache events:', url);
      }

      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_DEBUG')) {
          console.log('✅ WebSocket cache events connected');
        }

        // Reset reconnect attempts on successful connection
        reconnectAttemptsRef.current = 0;
        connectionHealthRef.current = 'healthy';

        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0
        }));

        startPingInterval();
        onConnect?.();

        // Subscribe to events
        if (wsRef.current?.readyState === WebSocket.OPEN && subscribedEvents.length > 0) {
          wsRef.current.send(JSON.stringify({
            type: 'subscribe',
            events: subscribedEvents
          }));
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketCacheMessage = JSON.parse(event.data);

          if (isWelcomeMessage(message)) {
            console.log('👋 WebSocket welcome:', message.data);
            setState(prev => ({
              ...prev,
              connectionId: message.data.connection_id
            }));
          } else if (isCacheInvalidationMessage(message)) {
            console.log('🔄 Cache invalidation event:', message.data);
            const cacheEvent = message.data;

            setState(prev => ({ ...prev, lastEvent: cacheEvent }));

            // Trigger event callbacks
            const eventType = cacheEvent.event_type;
            const callbacks = eventCallbacksRef.current.get(eventType);
            if (callbacks) {
              callbacks.forEach(callback => {
                try {
                  callback(cacheEvent);
                } catch (error) {
                  console.error('Error in cache event callback:', error);
                }
              });
            }

            // Also trigger generic callbacks
            const genericCallbacks = eventCallbacksRef.current.get('*');
            if (genericCallbacks) {
              genericCallbacks.forEach(callback => {
                try {
                  callback(cacheEvent);
                } catch (error) {
                  console.error('Error in generic cache event callback:', error);
                }
              });
            }
          } else if (isPingMessage(message)) {
            // Respond to ping with pong
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              const pongMessage = {
                type: WS_MESSAGE_TYPES.PONG,
                data: { timestamp: new Date().toISOString() }
              };
              wsRef.current.send(JSON.stringify(pongMessage));
            }
          } else if (isSubscriptionUpdatedMessage(message)) {
            console.log('📋 Subscription updated:', message.data);
          } else if (isStatsMessage(message)) {
            console.log('📊 WebSocket stats:', message.data);
          } else if (isErrorMessage(message)) {
            console.error('❌ WebSocket error:', message.data);
            setState(prev => ({ ...prev, error: message.data.message }));
            onError?.(message.data.message);
          } else {
            console.log('❓ Unknown WebSocket message type:', message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        connectionHealthRef.current = 'failed';

        if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_DEBUG')) {
          console.error('❌ WebSocket error:', error);
        }

        const errorMessage = 'WebSocket connection error';
        setState(prev => ({ ...prev, error: errorMessage }));
        onError?.(errorMessage);
      };

      wsRef.current.onclose = (event) => {
        if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_DEBUG')) {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        }

        // Update connection health based on close code
        if (event.code === 1000) {
          connectionHealthRef.current = 'healthy'; // Clean close
        } else if (event.code >= 1001 && event.code <= 1015) {
          connectionHealthRef.current = 'degraded'; // Temporary issues
        } else {
          connectionHealthRef.current = 'failed'; // Serious issues
        }

        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          connectionId: null
        }));

        clearPingInterval();
        onDisconnect?.();

        // Attempt to reconnect if enabled and not a clean close
        if (autoReconnect && event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const currentAttempt = reconnectAttemptsRef.current;

          // Only log reconnection attempts if debug is enabled (reduce spam)
          if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_DEBUG')) {
            console.log(`🔄 Attempting reconnect ${currentAttempt + 1}/${maxReconnectAttempts}`);
          }

          // Increment reconnect attempts
          reconnectAttemptsRef.current += 1;
          setState(prev => ({ ...prev, reconnectAttempts: reconnectAttemptsRef.current }));

          // Adjust backoff based on connection health
          let baseDelay = reconnectInterval;
          if (connectionHealthRef.current === 'failed') {
            baseDelay *= 2; // Longer delays for failed connections
          }

          // Use exponential backoff with longer delays to reduce spam
          const backoffDelay = baseDelay * Math.pow(2, currentAttempt);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, Math.min(backoffDelay, 300000)); // Cap at 5 minutes for failed connections
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_DEBUG')) {
            console.warn(`🚫 Max WebSocket reconnection attempts (${maxReconnectAttempts}) reached. Giving up.`);
          }
          connectionHealthRef.current = 'failed';
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: 'Failed to create WebSocket connection'
      }));
    }
  }, [
    state.isConnecting,
    getWebSocketUrl,
    startPingInterval,
    clearPingInterval,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect,
    maxReconnectAttempts,
    reconnectInterval,
    subscribedEvents
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    clearPingInterval();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    // Reset reconnect attempts
    reconnectAttemptsRef.current = 0;

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null,
      connectionId: null,
      reconnectAttempts: 0
    }));
  }, [clearReconnectTimeout, clearPingInterval]);

  // Subscribe to cache events
  const subscribe = useCallback((eventType: CacheEventType | '*', callback: CacheEventCallback) => {
    if (!eventCallbacksRef.current.has(eventType)) {
      eventCallbacksRef.current.set(eventType, new Set());
    }
    eventCallbacksRef.current.get(eventType).add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = eventCallbacksRef.current.get(eventType);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          eventCallbacksRef.current.delete(eventType);
        }
      }
    };
  }, []);

  // Send message to WebSocket
  const sendMessage = useCallback((message: Partial<WebSocketCacheMessage>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  // Update subscription
  const updateSubscription = useCallback((events: CacheEventType[]) => {
    return sendMessage({
      type: WS_MESSAGE_TYPES.SUBSCRIPTION_UPDATED,
      data: { subscribed_events: events }
    });
  }, [sendMessage]);

  // Get connection stats
  const getStats = useCallback(() => {
    return sendMessage({ type: WS_MESSAGE_TYPES.STATS });
  }, [sendMessage]);

  // Auto-connect on mount if feature is enabled (disabled by default to prevent spam)
  useEffect(() => {
    // Commented out to prevent automatic connections that cause console spam
    // if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE')) {
    //   connect();
    // }

    return () => {
      disconnect();
    };
  }, [disconnect]); // Removed connect dependency to prevent loops

  // Cleanup on unmount
  useEffect(() => {
    const callbacks = eventCallbacksRef.current;
    return () => {
      disconnect();
      callbacks.clear();
    };
  }, [disconnect]);

  return {
    // Connection state
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    error: state.error,
    connectionId: state.connectionId,
    reconnectAttempts: state.reconnectAttempts,
    canReconnect: autoReconnect && state.reconnectAttempts < maxReconnectAttempts,

    // Last received event
    lastEvent: state.lastEvent,

    // Connection controls
    connect,
    disconnect,

    // Event subscription
    subscribe,
    updateSubscription,

    // Utilities
    sendMessage,
    getStats,

    // Feature flag status
    isFeatureEnabled: isCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE')
  };
};

export default useWebSocket;
