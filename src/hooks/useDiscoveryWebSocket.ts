import { useState, useEffect, useRef, useCallback } from 'react';

export interface WebSocketMessage {
  type: 'flow_status' | 'agent_message' | 'collaboration_event' | 'system_metric' | 'crew_update' | 'memory_update' | 'planning_update';
  payload: any;
  timestamp: string;
  flow_id?: string;
}

export interface FlowStatusUpdate {
  flow_id: string;
  status: string;
  progress: number;
  current_phase: string;
  crew_updates: Array<{
    name: string;
    status: string;
    progress: number;
    current_task?: string;
  }>;
}

export interface AgentMessageUpdate {
  flow_id: string;
  agent_name: string;
  agent_role: string;
  is_manager: boolean;
  message_type: string;
  content: string;
  target_agent?: string;
  crew: string;
  metadata: Record<string, any>;
}

export interface CollaborationEventUpdate {
  flow_id: string;
  event_type: string;
  source_agent: string;
  source_crew: string;
  target_agent?: string;
  target_crew?: string;
  description: string;
  success: boolean;
  impact_score: number;
}

export interface SystemMetricUpdate {
  metric_type: 'memory' | 'performance' | 'collaboration' | 'general';
  values: Record<string, number>;
  alerts?: Array<{
    type: 'info' | 'warning' | 'error';
    message: string;
  }>;
}

export interface UseDiscoveryWebSocketOptions {
  url?: string;
  flowId?: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface UseDiscoveryWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  connect: () => void;
  disconnect: () => void;
  subscribe: (flowId: string) => void;
  unsubscribe: (flowId: string) => void;
  // Typed message handlers
  onFlowStatusUpdate: (callback: (update: FlowStatusUpdate) => void) => () => void;
  onAgentMessage: (callback: (message: AgentMessageUpdate) => void) => () => void;
  onCollaborationEvent: (callback: (event: CollaborationEventUpdate) => void) => () => void;
  onSystemMetricUpdate: (callback: (metrics: SystemMetricUpdate) => void) => () => void;
}

const useDiscoveryWebSocket = (options: UseDiscoveryWebSocketOptions = {}): UseDiscoveryWebSocketReturn => {
  const {
    url = process.env.NODE_ENV === 'production' 
      ? 'wss://your-railway-app.railway.app/ws/discovery' 
      : 'ws://localhost:8000/ws/discovery',
    flowId,
    reconnectAttempts = 5,
    reconnectDelay = 1000,
    onConnect,
    onDisconnect,
    onError,
    onMessage
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const subscribedFlows = useRef<Set<string>>(new Set());
  
  // Message handlers
  const flowStatusHandlers = useRef<Set<(update: FlowStatusUpdate) => void>>(new Set());
  const agentMessageHandlers = useRef<Set<(message: AgentMessageUpdate) => void>>(new Set());
  const collaborationEventHandlers = useRef<Set<(event: CollaborationEventUpdate) => void>>(new Set());
  const systemMetricHandlers = useRef<Set<(metrics: SystemMetricUpdate) => void>>(new Set());

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    if (isConnecting) {
      console.log('WebSocket connection already in progress');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectCount.current = 0;
        
        // Re-subscribe to flows after reconnection
        subscribedFlows.current.forEach(flowId => {
          sendSubscription(flowId);
        });

        onConnect?.();
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        
        onDisconnect?.();

        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && reconnectCount.current < reconnectAttempts) {
          scheduleReconnect();
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        setIsConnecting(false);
        onError?.(error);
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);

          // Route message to appropriate handlers
          switch (message.type) {
            case 'flow_status':
              flowStatusHandlers.current.forEach(handler => handler(message.payload));
              break;
            case 'agent_message':
              agentMessageHandlers.current.forEach(handler => handler(message.payload));
              break;
            case 'collaboration_event':
              collaborationEventHandlers.current.forEach(handler => handler(message.payload));
              break;
            case 'system_metric':
              systemMetricHandlers.current.forEach(handler => handler(message.payload));
              break;
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setError('Failed to create WebSocket connection');
      setIsConnecting(false);
    }
  }, [url, reconnectAttempts, onConnect, onDisconnect, onError, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    subscribedFlows.current.clear();
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }

    reconnectCount.current++;
    const delay = reconnectDelay * Math.pow(2, reconnectCount.current - 1); // Exponential backoff

    console.log(`Scheduling reconnect attempt ${reconnectCount.current} in ${delay}ms`);
    
    reconnectTimer.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect, reconnectDelay]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }, []);

  const sendSubscription = useCallback((flowId: string) => {
    sendMessage({
      type: 'subscribe',
      flow_id: flowId,
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  const subscribe = useCallback((flowId: string) => {
    subscribedFlows.current.add(flowId);
    if (isConnected) {
      sendSubscription(flowId);
    }
  }, [isConnected, sendSubscription]);

  const unsubscribe = useCallback((flowId: string) => {
    subscribedFlows.current.delete(flowId);
    if (isConnected) {
      sendMessage({
        type: 'unsubscribe',
        flow_id: flowId,
        timestamp: new Date().toISOString()
      });
    }
  }, [isConnected, sendMessage]);

  // Typed message handlers
  const onFlowStatusUpdate = useCallback((callback: (update: FlowStatusUpdate) => void) => {
    flowStatusHandlers.current.add(callback);
    return () => {
      flowStatusHandlers.current.delete(callback);
    };
  }, []);

  const onAgentMessage = useCallback((callback: (message: AgentMessageUpdate) => void) => {
    agentMessageHandlers.current.add(callback);
    return () => {
      agentMessageHandlers.current.delete(callback);
    };
  }, []);

  const onCollaborationEvent = useCallback((callback: (event: CollaborationEventUpdate) => void) => {
    collaborationEventHandlers.current.add(callback);
    return () => {
      collaborationEventHandlers.current.delete(callback);
    };
  }, []);

  const onSystemMetricUpdate = useCallback((callback: (metrics: SystemMetricUpdate) => void) => {
    systemMetricHandlers.current.add(callback);
    return () => {
      systemMetricHandlers.current.delete(callback);
    };
  }, []);

  // Auto-connect on mount and auto-subscribe if flowId provided
  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  useEffect(() => {
    if (flowId) {
      subscribe(flowId);
      return () => unsubscribe(flowId);
    }
  }, [flowId, subscribe, unsubscribe]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    onFlowStatusUpdate,
    onAgentMessage,
    onCollaborationEvent,
    onSystemMetricUpdate
  };
};

export default useDiscoveryWebSocket; 