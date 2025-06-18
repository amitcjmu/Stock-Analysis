import { useEffect, useState, useRef, useCallback } from 'react';

interface AgentCollaborationEvent {
  event_type: 'agent_collaboration_event';
  session_id: string;
  data: {
    from_agent: string;
    to_agent: string;
    collaboration_type: string;
    message: string;
    insights_shared: any;
  };
  timestamp: string;
}

interface CrewStatusUpdate {
  event_type: 'crew_status_update';
  session_id: string;
  data: {
    crew: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    progress: number;
    agent_updates: Array<{
      agent: string;
      status: string;
      current_task: string;
    }>;
  };
  timestamp: string;
}

interface MemoryInsightEvent {
  event_type: 'memory_insight_stored';
  session_id: string;
  data: {
    insight_type: string;
    crew: string;
    memory_key: string;
    relevance_score: number;
  };
  timestamp: string;
}

interface PhaseCompletionEvent {
  event_type: 'phase_completion';
  session_id: string;
  data: {
    phase: string;
    crew: string;
    success_criteria_met: boolean;
    next_phase: string;
    completion_summary: any;
  };
  timestamp: string;
}

interface PerformanceAlertEvent {
  event_type: 'performance_alert';
  session_id: string;
  data: {
    alert_type: 'memory_high' | 'execution_slow' | 'collaboration_low';
    severity: 'info' | 'warning' | 'error';
    message: string;
    affected_crew: string;
  };
  timestamp: string;
}

type WebSocketEvent = 
  | AgentCollaborationEvent 
  | CrewStatusUpdate 
  | MemoryInsightEvent 
  | PhaseCompletionEvent 
  | PerformanceAlertEvent;

interface UseWebSocketMonitoringReturn {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  events: WebSocketEvent[];
  latestEvent: WebSocketEvent | null;
  agentCollaborations: AgentCollaborationEvent[];
  crewUpdates: CrewStatusUpdate[];
  memoryInsights: MemoryInsightEvent[];
  phaseCompletions: PhaseCompletionEvent[];
  performanceAlerts: PerformanceAlertEvent[];
  clearEvents: () => void;
  reconnect: () => void;
  sendMessage: (message: any) => void;
}

export const useWebSocketMonitoring = (sessionId: string | null): UseWebSocketMonitoringReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<WebSocketEvent | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Derived state for different event types
  const agentCollaborations = events.filter(e => e.event_type === 'agent_collaboration_event') as AgentCollaborationEvent[];
  const crewUpdates = events.filter(e => e.event_type === 'crew_status_update') as CrewStatusUpdate[];
  const memoryInsights = events.filter(e => e.event_type === 'memory_insight_stored') as MemoryInsightEvent[];
  const phaseCompletions = events.filter(e => e.event_type === 'phase_completion') as PhaseCompletionEvent[];
  const performanceAlerts = events.filter(e => e.event_type === 'performance_alert') as PerformanceAlertEvent[];

  const connectWebSocket = useCallback(() => {
    if (!sessionId) {
      console.log('🔌 No session ID available for WebSocket connection');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING || wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('🔌 WebSocket already connecting or connected');
      return;
    }

    try {
      setConnectionStatus('connecting');
      
      // Determine WebSocket URL based on environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/discovery-flow/${sessionId}`;
      
      console.log('🔌 Connecting to Discovery Flow WebSocket:', wsUrl);
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('✅ Discovery Flow WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        
        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Heartbeat every 30 seconds
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);
          
          // Handle heartbeat response
          if (data.type === 'pong') {
            console.log('💓 WebSocket heartbeat pong received');
            return;
          }
          
          // Process Discovery Flow events
          if (data.event_type && data.session_id === sessionId) {
            const wsEvent = data as WebSocketEvent;
            
            setEvents(prev => {
              // Keep only last 100 events to prevent memory issues
              const newEvents = [...prev, wsEvent].slice(-100);
              return newEvents;
            });
            
            setLatestEvent(wsEvent);
            
            // Log different event types
            switch (wsEvent.event_type) {
              case 'crew_status_update':
                console.log(`🚀 Crew Update: ${wsEvent.data.crew} - ${wsEvent.data.status} (${wsEvent.data.progress}%)`);
                break;
              case 'agent_collaboration_event':
                console.log(`🤝 Agent Collaboration: ${wsEvent.data.from_agent} → ${wsEvent.data.to_agent}`);
                break;
              case 'memory_insight_stored':
                console.log(`🧠 Memory Insight: ${wsEvent.data.insight_type} from ${wsEvent.data.crew}`);
                break;
              case 'phase_completion':
                console.log(`✅ Phase Completed: ${wsEvent.data.phase} by ${wsEvent.data.crew}`);
                break;
              case 'performance_alert':
                console.log(`⚠️ Performance Alert: ${wsEvent.data.alert_type} - ${wsEvent.data.message}`);
                break;
              default:
                console.log('📨 Unknown WebSocket event:', wsEvent);
            }
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('🔌 Discovery Flow WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }
        
        // Attempt to reconnect if not intentionally closed
        if (event.code !== 1000 && sessionId) {
          console.log('🔄 Attempting to reconnect in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('❌ Discovery Flow WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [sessionId]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const reconnect = useCallback(() => {
    disconnectWebSocket();
    setTimeout(() => {
      connectWebSocket();
    }, 1000);
  }, [disconnectWebSocket, connectWebSocket]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      console.log('📤 WebSocket message sent:', message);
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message:', message);
    }
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatestEvent(null);
  }, []);

  // Connect when sessionId becomes available
  useEffect(() => {
    if (sessionId) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [sessionId, connectWebSocket, disconnectWebSocket]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return {
    isConnected,
    connectionStatus,
    events,
    latestEvent,
    agentCollaborations,
    crewUpdates,
    memoryInsights,
    phaseCompletions,
    performanceAlerts,
    clearEvents,
    reconnect,
    sendMessage
  };
}; 