import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';

export interface WebSocketMessage {
  type: 'analysis_progress' | 'analysis_complete' | 'analysis_error' | 'parameter_update' | 'agent_activity' | 'bulk_job_update';
  data: unknown;
  timestamp: string;
  analysis_id?: number;
  job_id?: string;
}

export interface AnalysisProgressUpdate {
  analysis_id: number;
  step: string;
  progress: number;
  status: 'running' | 'completed' | 'failed';
  message?: string;
  agent_name?: string;
  estimated_time_remaining?: number;
}

export interface BulkJobUpdate {
  job_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  completed_applications: number;
  failed_applications: number;
  current_application?: string;
  estimated_time_remaining?: number;
}

export interface AgentActivity {
  analysis_id: number;
  agent_name: string;
  activity: string;
  status: 'started' | 'completed' | 'failed';
  timestamp: string;
  details?: unknown;
}

interface UseSixRWebSocketOptions {
  analysisId?: number;
  jobId?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
  reconnectAttempts: number;
}

export const useSixRWebSocket = (options: UseSixRWebSocketOptions = {}) => {
  const {
    analysisId,
    jobId,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage,
    onError,
    onConnect,
    onDisconnect
  } = options;

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    lastMessage: null,
    reconnectAttempts: 0
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Build WebSocket URL based on analysis ID or job ID
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const baseUrl = `${protocol}//${host}/api/v1/ws`;
    
    if (analysisId) {
      return `${baseUrl}/sixr/${analysisId}`;
    } else if (jobId) {
      return `${baseUrl}/bulk/${jobId}`;
    } else {
      return `${baseUrl}/sixr/general`;
    }
  }, [analysisId, jobId]);

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Clear heartbeat interval
  const clearHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Start heartbeat to keep connection alive
  const startHeartbeat = useCallback(() => {
    clearHeartbeat();
    // DISABLED: No automatic heartbeat polling
    console.log('🔇 DISABLED: WebSocket heartbeat polling disabled');
  }, [clearHeartbeat]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || state.isConnecting) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const url = getWebSocketUrl();
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0
        }));
        
        startHeartbeat();
        onConnect?.();
        
        // Send initial subscription message
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'subscribe',
            analysis_id: analysisId,
            job_id: jobId
          }));
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          setState(prev => ({ ...prev, lastMessage: message }));
          onMessage?.(message);

          // Handle different message types with notifications
          switch (message.type) {
            case 'analysis_complete':
              toast.success('Analysis completed successfully!', {
                description: `Analysis for ${message.data.application_name} is ready for review.`
              });
              break;
            
            case 'analysis_error':
              toast.error('Analysis failed', {
                description: message.data.error || 'An error occurred during analysis.'
              });
              break;
            
            case 'bulk_job_update':
              const jobUpdate = message.data as BulkJobUpdate;
              if (jobUpdate.status === 'completed') {
                toast.success('Bulk analysis job completed!', {
                  description: `Processed ${jobUpdate.completed_applications} applications.`
                });
              } else if (jobUpdate.status === 'failed') {
                toast.error('Bulk analysis job failed', {
                  description: `${jobUpdate.failed_applications} applications failed to process.`
                });
              }
              break;
            
            case 'agent_activity':
              const activity = message.data as AgentActivity;
              if (activity.status === 'failed') {
                toast.warning(`Agent ${activity.agent_name} encountered an issue`, {
                  description: activity.activity
                });
              }
              break;
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        setState(prev => ({ ...prev, error: 'WebSocket connection error' }));
        onError?.(error);
      };

      wsRef.current.onclose = (event) => {
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false
        }));
        
        clearHeartbeat();
        onDisconnect?.();

        // Attempt to reconnect if enabled and not a clean close
        if (autoReconnect && event.code !== 1000 && state.reconnectAttempts < maxReconnectAttempts) {
          setState(prev => ({ ...prev, reconnectAttempts: prev.reconnectAttempts + 1 }));
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

    } catch (error) {
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: 'Failed to create WebSocket connection'
      }));
    }
  }, [
    state.isConnecting,
    state.reconnectAttempts,
    getWebSocketUrl,
    startHeartbeat,
    onConnect,
    onMessage,
    onError,
    onDisconnect,
    autoReconnect,
    maxReconnectAttempts,
    reconnectInterval,
    analysisId,
    jobId
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    clearHeartbeat();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0
    }));
  }, [clearReconnectTimeout, clearHeartbeat]);

  // Send message through WebSocket
  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  // Subscribe to specific analysis or job updates
  const subscribe = useCallback((targetAnalysisId?: number, targetJobId?: string) => {
    return sendMessage({
      type: 'subscribe',
      analysis_id: targetAnalysisId,
      job_id: targetJobId
    });
  }, [sendMessage]);

  // Unsubscribe from updates
  const unsubscribe = useCallback((targetAnalysisId?: number, targetJobId?: string) => {
    return sendMessage({
      type: 'unsubscribe',
      analysis_id: targetAnalysisId,
      job_id: targetJobId
    });
  }, [sendMessage]);

  // Auto-connect on mount and when dependencies change
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [analysisId, jobId]); // Only reconnect when IDs change

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // Connection state
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    error: state.error,
    reconnectAttempts: state.reconnectAttempts,
    
    // Last received message
    lastMessage: state.lastMessage,
    
    // Connection controls
    connect,
    disconnect,
    
    // Message handling
    sendMessage,
    subscribe,
    unsubscribe,
    
    // Connection info
    canReconnect: autoReconnect && state.reconnectAttempts < maxReconnectAttempts
  };
}; 