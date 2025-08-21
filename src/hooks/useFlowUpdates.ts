import { useState, useRef } from 'react'
import { useEffect, useCallback, useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext';

export interface FlowUpdate {
  flow_id: string;
  status: string;
  phase: string;
  progress: number;
  message?: string;
  error?: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

interface UseFlowUpdatesState {
  data: FlowUpdate | null;
  isLoading: boolean;
  isConnected: boolean;
  connectionType: 'sse' | 'polling' | 'disconnected';
  error: string | null;
  lastUpdate: Date | null;
}

interface UseFlowUpdatesOptions {
  pollingInterval?: number;
  maxRetries?: number;
  retryDelay?: number;
  enableSSE?: boolean;
  enablePolling?: boolean;
}

const DEFAULT_OPTIONS: UseFlowUpdatesOptions = {
  pollingInterval: 5000, // 5 seconds
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  enableSSE: true,
  enablePolling: true,
};

export function useFlowUpdates(
  flowId: string | null | undefined,
  options: UseFlowUpdatesOptions = {}
): UseFlowUpdatesState & {
  refetch: () => void;
  disconnect: () => void;
  reconnect: () => void;
} {
  const { token, clientAccountId, engagementId } = useAuth();
  const [state, setState] = useState<UseFlowUpdatesState>({
    data: null,
    isLoading: true,
    isConnected: false,
    connectionType: 'disconnected',
    error: null,
    lastUpdate: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const etagRef = useRef<string | null>(null);
  const lastResponseRef = useRef<FlowUpdate | null>(null);
  const isMountedRef = useRef(true);

  const mergedOptions = useMemo(
    () => ({ ...DEFAULT_OPTIONS, ...options }),
    [options]
  );

  // Helper to update state safely
  const safeSetState = useCallback((updater: Partial<UseFlowUpdatesState>) => {
    if (isMountedRef.current) {
      setState(prev => ({ ...prev, ...updater }));
    }
  }, []);

  // Build headers with auth and tenant context
  const getHeaders = useCallback(() => {
    const headers: HeadersInit = {
      'Authorization': `Bearer ${token}`,
      'X-Client-Account-ID': clientAccountId?.toString() || '',
      'X-Engagement-ID': engagementId?.toString() || '',
    };

    // Add ETag header for conditional requests during polling
    if (etagRef.current) {
      headers['If-None-Match'] = etagRef.current;
    }

    return headers;
  }, [token, clientAccountId, engagementId]);

  // Parse and update flow data
  const updateFlowData = useCallback((data: FlowUpdate) => {
    lastResponseRef.current = data;
    safeSetState({
      data,
      lastUpdate: new Date(),
      error: null,
    });
  }, [safeSetState]);

  // SSE Connection
  const connectSSE = useCallback(() => {
    if (!flowId || !token || !mergedOptions.enableSSE) return;

    try {
      safeSetState({ isLoading: true, error: null });

      const sseUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/unified-discovery/flow/${flowId}/events`;

      // Create EventSource
      // Note: Native EventSource doesn't support custom headers
      // We'll need to pass auth token as query param or use cookies
      if (typeof window !== 'undefined' && window.EventSource) {
        eventSourceRef.current = new EventSource(sseUrl, {
          withCredentials: true,
        });
      } else {
        console.warn('EventSource not available');
        return;
      }

      eventSourceRef.current.onopen = () => {
        console.log(`SSE connected for flow ${flowId}`);
        retryCountRef.current = 0;
        safeSetState({
          isConnected: true,
          connectionType: 'sse',
          isLoading: false,
          error: null,
        });
      };

      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as FlowUpdate;
          updateFlowData(data);
        } catch (error) {
          console.error('Failed to parse SSE message:', error);
        }
      };

      eventSourceRef.current.onerror = (error) => {
        console.error('SSE error:', error);
        eventSourceRef.current?.close();
        eventSourceRef.current = null;

        // Retry SSE connection or fall back to polling
        if (retryCountRef.current < mergedOptions.maxRetries) {
          retryCountRef.current++;
          const delay = mergedOptions.retryDelay * Math.pow(2, retryCountRef.current - 1);

          console.log(`Retrying SSE connection in ${delay}ms (attempt ${retryCountRef.current})`);

          setTimeout(() => {
            if (isMountedRef.current) {
              connectSSE();
            }
          }, delay);
        } else {
          console.log('SSE max retries reached, falling back to polling');
          safeSetState({
            isConnected: false,
            connectionType: 'disconnected',
            error: 'SSE connection failed',
          });

          // Fall back to polling
          if (mergedOptions.enablePolling && startPollingRef.current) {
            startPollingRef.current();
          }
        }
      };

      // Custom event handlers for specific flow events
      eventSourceRef.current.addEventListener('flow-completed', (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        updateFlowData({ ...data, status: 'completed' });
      });

      eventSourceRef.current.addEventListener('flow-error', (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        updateFlowData({ ...data, status: 'error' });
      });

    } catch (error) {
      console.error('Failed to establish SSE connection:', error);
      safeSetState({
        error: error instanceof Error ? error.message : 'Failed to connect',
        isLoading: false,
      });

      // Fall back to polling
      if (mergedOptions.enablePolling && startPollingRef.current) {
        startPollingRef.current();
      }
    }
  }, [flowId, token, mergedOptions, safeSetState, updateFlowData]);

  // Smart Polling with ETag support
  const pollStatus = useCallback(async () => {
    if (!flowId || !token) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/unified-discovery/flow/${flowId}/status`,
        {
          method: 'GET',
          headers: getHeaders(),
        }
      );

      // Handle 304 Not Modified (no changes since last ETag)
      if (response.status === 304) {
        console.log('No changes since last update (304)');
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Store ETag for next request
      const newEtag = response.headers.get('ETag');
      if (newEtag) {
        etagRef.current = newEtag;
      }

      // Update only if data has changed
      if (JSON.stringify(data) !== JSON.stringify(lastResponseRef.current)) {
        updateFlowData(data);
      }

      safeSetState({
        isConnected: true,
        connectionType: 'polling',
        isLoading: false,
        error: null,
      });

    } catch (error) {
      console.error('Polling error:', error);
      safeSetState({
        error: error instanceof Error ? error.message : 'Polling failed',
        isConnected: false,
        connectionType: 'disconnected',
      });
    }
  }, [flowId, token, getHeaders, updateFlowData, safeSetState]);

  // Forward declare startPolling
  const startPollingRef = useRef<() => void>();

  // Start polling
  const startPolling = useCallback(() => {
    if (!mergedOptions.enablePolling) return;

    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    console.log(`Starting polling for flow ${flowId} with interval ${mergedOptions.pollingInterval}ms`);

    // Initial poll
    pollStatus();

    // Set up interval
    pollingIntervalRef.current = setInterval(() => {
      if (isMountedRef.current) {
        pollStatus();
      }
    }, mergedOptions.pollingInterval);

    safeSetState({
      connectionType: 'polling',
    });
  }, [flowId, mergedOptions, pollStatus, safeSetState]);

  // Store reference for use in connectSSE
  startPollingRef.current = startPolling;

  // Disconnect all connections
  const disconnect = useCallback(() => {
    // Close SSE
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Clear polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // Reset state
    retryCountRef.current = 0;
    etagRef.current = null;

    safeSetState({
      isConnected: false,
      connectionType: 'disconnected',
    });
  }, [safeSetState]);

  // Reconnect
  const reconnect = useCallback(() => {
    disconnect();

    if (mergedOptions.enableSSE) {
      connectSSE();
    } else if (mergedOptions.enablePolling && startPollingRef.current) {
      startPollingRef.current();
    }
  }, [disconnect, connectSSE, mergedOptions]);

  // Manual refetch
  const refetch = useCallback(() => {
    if (state.connectionType === 'polling' || !state.isConnected) {
      pollStatus();
    }
  }, [state.connectionType, state.isConnected, pollStatus]);

  // Main effect to manage connections
  useEffect(() => {
    isMountedRef.current = true;

    if (flowId && token && clientAccountId && engagementId) {
      // Try SSE first, fall back to polling
      if (mergedOptions.enableSSE) {
        connectSSE();
      } else if (mergedOptions.enablePolling && startPollingRef.current) {
        startPollingRef.current();
      }
    }

    return () => {
      isMountedRef.current = false;
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flowId, token, clientAccountId, engagementId]); // Don't include all dependencies to avoid reconnection loops

  return {
    ...state,
    refetch,
    disconnect,
    reconnect,
  };
}

// Export types for external use
export type { FlowUpdate, UseFlowUpdatesState, UseFlowUpdatesOptions };
