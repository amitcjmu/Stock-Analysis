/**
 * Collection Workflow WebSocket Hook
 *
 * Provides real-time updates for collection workflow initialization
 * with fallback to polling when WebSocket is unavailable.
 */

import { useEffect, useCallback, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

interface CollectionWorkflowEvent {
  type: 'workflow_status' | 'questionnaire_ready' | 'agent_progress' | 'workflow_error';
  flowId: string;
  data: {
    status?: string;
    phase?: string;
    progress?: number;
    message?: string;
    questionnaire_count?: number;
    error?: string;
  };
}

interface UseCollectionWorkflowWebSocketOptions {
  flowId?: string;
  enabled?: boolean;
  onWorkflowUpdate?: (event: CollectionWorkflowEvent) => void;
  onQuestionnaireReady?: (event: CollectionWorkflowEvent) => void;
  onError?: (error: string) => void;
}

export const useCollectionWorkflowWebSocket = (
  options: UseCollectionWorkflowWebSocketOptions = {}
) => {
  const { flowId, enabled = true, onWorkflowUpdate, onQuestionnaireReady, onError } = options;

  const [isWebSocketActive, setIsWebSocketActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<CollectionWorkflowEvent | null>(null);

  // Use the main WebSocket hook
  const {
    isConnected: wsConnected,
    subscribe,
    sendMessage,
    lastEvent
  } = useWebSocket({
    enabled: enabled && !!flowId,
    autoReconnect: true,
    maxReconnectAttempts: 3
  });

  // Handle WebSocket connection status
  useEffect(() => {
    setIsWebSocketActive(wsConnected && !!flowId && enabled);
  }, [wsConnected, flowId, enabled]);

  // Subscribe to collection workflow events
  useEffect(() => {
    if (!isWebSocketActive || !flowId) {
      return;
    }

    console.log('🔌 Setting up WebSocket subscription for collection workflow:', flowId);

    // Subscribe to workflow-specific events
    const unsubscribeWorkflow = subscribe('collection_workflow_updated', (event) => {
      try {
        const workflowEvent = event.data as CollectionWorkflowEvent;

        // Filter events for our specific flow
        if (workflowEvent.flowId !== flowId) {
          return;
        }

        console.log('📡 Collection workflow WebSocket event:', workflowEvent);
        setLastUpdate(workflowEvent);

        // Handle different event types
        switch (workflowEvent.type) {
          case 'questionnaire_ready':
            console.log('✅ Questionnaire ready event received via WebSocket');
            onQuestionnaireReady?.(workflowEvent);
            break;

          case 'workflow_status':
            console.log('📊 Workflow status update via WebSocket:', workflowEvent.data.status);
            onWorkflowUpdate?.(workflowEvent);
            break;

          case 'agent_progress':
            console.log('🤖 Agent progress update via WebSocket:', workflowEvent.data.phase);
            onWorkflowUpdate?.(workflowEvent);
            break;

          case 'workflow_error':
            console.error('❌ Workflow error event via WebSocket:', workflowEvent.data.error);
            onError?.(workflowEvent.data.error || 'Workflow error occurred');
            break;
        }
      } catch (error) {
        console.error('Failed to process collection workflow WebSocket event:', error);
      }
    });

    // Subscribe to general collection events
    const unsubscribeCollection = subscribe('collection_updated', (event) => {
      try {
        const collectionEvent = event.data as { flow_id: string; status: string; phase: string };

        if (collectionEvent.flow_id !== flowId) {
          return;
        }

        console.log('📡 General collection update via WebSocket:', collectionEvent);

        const workflowEvent: CollectionWorkflowEvent = {
          type: 'workflow_status',
          flowId: collectionEvent.flow_id,
          data: {
            status: collectionEvent.status,
            phase: collectionEvent.phase
          }
        };

        setLastUpdate(workflowEvent);
        onWorkflowUpdate?.(workflowEvent);
      } catch (error) {
        console.error('Failed to process collection update WebSocket event:', error);
      }
    });

    // Send initial subscription message to backend
    const subscriptionMessage = {
      type: 'subscribe',
      events: ['collection_workflow_updated', 'collection_updated'],
      filters: {
        flow_id: flowId
      }
    };

    if (sendMessage(subscriptionMessage)) {
      console.log('📤 Sent WebSocket subscription for collection workflow:', flowId);
    }

    return () => {
      console.log('🔌 Cleaning up WebSocket subscriptions for workflow:', flowId);
      unsubscribeWorkflow();
      unsubscribeCollection();
    };
  }, [isWebSocketActive, flowId, subscribe, sendMessage, onWorkflowUpdate, onQuestionnaireReady, onError]);

  // Utility function to request workflow status update
  const requestStatusUpdate = useCallback(() => {
    if (!isWebSocketActive || !flowId) {
      return false;
    }

    const requestMessage = {
      type: 'request_status',
      flow_id: flowId
    };

    return sendMessage(requestMessage);
  }, [isWebSocketActive, flowId, sendMessage]);

  return {
    // Connection status
    isWebSocketActive,
    wsConnected,

    // Latest data
    lastUpdate,
    lastEvent,

    // Actions
    requestStatusUpdate,

    // For debugging
    flowId
  };
};

export default useCollectionWorkflowWebSocket;
