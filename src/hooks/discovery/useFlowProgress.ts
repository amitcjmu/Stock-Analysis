import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';
import { pollingManager } from '@/lib/polling-manager';

export interface FlowProgressUpdate {
  flow_id: string;
  phase: string;
  progress: number;
  status: 'processing' | 'completed' | 'awaiting_approval' | 'awaiting_input' | 'error' | 'failed';
  message: string;
  is_processing: boolean;
  awaiting_user_input: boolean;
  requires_navigation?: boolean;
  navigation_target?: string;
  agent_activity?: {
    agent: string;
    activity: string;
    details: Record<string, unknown>;
    timestamp: string;
  };
  error?: {
    message: string;
    phase: string;
    is_recoverable: boolean;
    timestamp: string;
  };
  timestamp: string;
}

interface UseFlowProgressOptions {
  flowId: string | null;
  autoNavigate?: boolean;
  onProgressUpdate?: (update: FlowProgressUpdate) => void;
  onPhaseComplete?: (phase: string) => void;
  onError?: (error: FlowProgressUpdate['error']) => void;
}

/**
 * Hook for real-time flow progress tracking via HTTP polling
 *
 * This hook uses HTTP polling to receive updates about CrewAI flow execution
 * progress. Designed for Vercel/Railway deployment where WebSockets are not available.
 *
 * Polling Strategy:
 * - Active polling (5s) when agents are processing
 * - Reduced polling (15s) when waiting for user input
 * - No polling when flow is complete or failed
 */
export const useFlowProgress = ({
  flowId,
  autoNavigate = true,
  onProgressUpdate,
  onPhaseComplete,
  onError
}: UseFlowProgressOptions) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [progress, setProgress] = useState<FlowProgressUpdate | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [pollingError, setPollingError] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdateRef = useRef<string | null>(null);
  const pollIdRef = useRef<string | null>(null);

  // Fetch flow status
  const fetchFlowStatus = useCallback(async () => {
    if (!flowId) return;

    try {
      // Fixed: Use unified-discovery endpoint instead of legacy discovery endpoint (Issue #222)
      // This ensures we call the correct API that's registered in router_registry.py
      const response = await apiCall<any>(`/api/v1/unified-discovery/flows/${flowId}/status`, {
        method: 'GET'
      });

      console.log(`🔍 Flow status response for ${flowId}:`, response);

      if (response.success && response.data) {
        const data = response.data;

        // Convert API response to progress update format
        const update: FlowProgressUpdate = {
          flow_id: flowId,
          phase: data.current_phase || data.phase || 'unknown',
          progress: data.progress_percentage || data.progress || 0,
          status: mapWorkflowStatus(data.workflow_status || data.status),
          message: data.message || data.status_message || '',
          is_processing: data.is_processing || data.workflow_status === 'processing',
          awaiting_user_input: data.awaiting_user_approval || data.awaiting_user_input || false,
          requires_navigation: data.requires_navigation,
          navigation_target: data.navigation_target,
          timestamp: new Date().toISOString()
        };

        // Check for agent activity
        if (data.agent_activity) {
          update.agent_activity = data.agent_activity;
        }

        // Check for errors
        if (data.error || data.error_message) {
          update.error = {
            message: data.error_message || data.error || 'Unknown error',
            phase: data.current_phase || 'unknown',
            is_recoverable: data.is_recoverable !== false,
            timestamp: new Date().toISOString()
          };
        }

        // Deduplicate updates
        const updateKey = `${update.phase}-${update.progress}-${update.status}`;
        if (lastUpdateRef.current !== updateKey) {
          lastUpdateRef.current = updateKey;
          setProgress(update);

          // Call callbacks
          if (onProgressUpdate) {
            onProgressUpdate(update);
          }

          if (update.status === 'completed' && onPhaseComplete) {
            onPhaseComplete(update.phase);
          }

          if (update.error && onError) {
            onError(update.error);
          }

          // Handle UI notifications
          handleProgressNotifications(update);
        }

        // Adjust polling frequency based on status
        adjustPollingFrequency(update);
      }
    } catch (error) {
      console.error(`❌ Failed to fetch flow status for ${flowId}:`, error);

      // Provide more specific error messages for common issues
      if (error?.status === 404) {
        setPollingError(`Flow ${flowId} not found. The flow may have been completed or removed.`);
      } else if (error?.status === 429) {
        setPollingError('Rate limited. Polling will retry automatically.');
      } else if (error?.message?.includes('discovery/flows')) {
        setPollingError('API endpoint error. Please check if the discovery flow API is available.');
      } else {
        setPollingError(`Failed to fetch flow status: ${error?.message || 'Unknown error'}`);
      }
    }
  }, [flowId, onProgressUpdate, onPhaseComplete, onError]);

  // Map workflow status to our status type
  const mapWorkflowStatus = (status: string): FlowProgressUpdate['status'] => {
    switch (status) {
      case 'processing':
      case 'running':
      case 'in_progress':
        return 'processing';
      case 'completed':
      case 'success':
        return 'completed';
      case 'waiting_for_approval':
      case 'paused_for_field_mapping_approval':
        return 'awaiting_approval';
      case 'awaiting_input':
      case 'paused':
        return 'awaiting_input';
      case 'error':
        return 'error';
      case 'failed':
        return 'failed';
      default:
        return 'processing';
    }
  };

  // Handle progress notifications
  const handleProgressNotifications = useCallback((update: FlowProgressUpdate) => {
    // Show notifications for important state changes
    if (update.status === 'awaiting_approval' || update.status === 'awaiting_input') {
      toast.info(update.message || 'User input required', {
        duration: 10000,
        action: update.requires_navigation ? {
          label: 'Go to Page',
          onClick: () => {
            if (update.navigation_target) {
              navigate(update.navigation_target);
            }
          }
        } : undefined
      });

      // Auto-navigate if enabled
      if (autoNavigate && update.requires_navigation && update.navigation_target) {
        setTimeout(() => {
          navigate(update.navigation_target);
        }, 2000);
      }
    }

    // Show error notifications
    if (update.status === 'error' || update.status === 'failed') {
      toast.error(update.message || 'Flow execution error', {
        duration: 10000,
        description: update.error?.is_recoverable
          ? 'The system will attempt to recover automatically.'
          : 'Manual intervention may be required.'
      });
    }

    // Show agent activity in development mode
    if (process.env.NODE_ENV === 'development' && update.agent_activity) {
      console.log(`🤖 ${update.agent_activity.agent}: ${update.agent_activity.activity}`);
    }
  }, [autoNavigate, navigate]);

  // Adjust polling frequency based on flow status
  const adjustPollingFrequency = useCallback((update: FlowProgressUpdate) => {
    // Stop polling if flow is complete or failed
    if (update.status === 'completed' || update.status === 'failed') {
      stopPolling();
      return;
    }

    // Use different intervals based on status
    const currentInterval = update.is_processing ? 5000 : 15000; // 5s for active, 15s for waiting

    // Update polling interval if needed
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(() => {
      fetchFlowStatus();
    }, currentInterval);
  }, [fetchFlowStatus]);

  // Start polling
  const startPolling = useCallback(() => {
    if (!flowId || !user) {
      return;
    }

    // Register with polling manager
    const pollId = `flow-progress-${flowId}`;
    pollIdRef.current = pollId;

    const registered = pollingManager.register({
      id: pollId,
      component: 'useFlowProgress',
      endpoint: `/api/v1/unified-discovery/flows/${flowId}/status`,
      interval: 5000, // Start with 5 second polling
      maxRetries: 3,
      enabled: true
    });

    if (registered) {
      setIsPolling(true);
      setPollingError(null);

      // Initial fetch
      fetchFlowStatus();

      // Start polling interval
      pollingIntervalRef.current = setInterval(() => {
        fetchFlowStatus();
      }, 5000);

      console.log(`✅ Started polling for flow ${flowId}`);
    } else {
      setPollingError('Unable to start polling - limit reached');
    }
  }, [flowId, user, fetchFlowStatus]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    if (pollIdRef.current) {
      pollingManager.stop(pollIdRef.current);
      pollIdRef.current = null;
    }

    setIsPolling(false);
    console.log(`⏹️ Stopped polling for flow ${flowId}`);
  }, [flowId]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchFlowStatus();
  }, [fetchFlowStatus]);

  // Setup and cleanup
  useEffect(() => {
    if (flowId && user) {
      startPolling();
    }

    return () => {
      stopPolling();
    };
  }, [flowId, user, startPolling, stopPolling]);

  return {
    progress,
    isPolling,
    pollingError,
    refresh,
    isProcessing: progress?.is_processing || false,
    awaitingUserInput: progress?.awaiting_user_input || false,
    currentPhase: progress?.phase || null,
    progressPercentage: progress?.progress || 0
  };
};
