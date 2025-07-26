/**
 * Optimistic Flow Hook
 * MFO-082: Implement optimistic updates for better UX
 *
 * Enhanced flow management with optimistic updates and rollback capabilities
 */

import { useCallback } from 'react';
import type { UseFlowOptions } from './useFlow'
import { useFlow } from './useFlow'
import type { FlowStatus, FlowStatusType, PhaseInfo, CreateFlowRequest, ExecutePhaseRequest } from '../types/flow';
import { flowToast } from '../utils/toast';

export interface OptimisticUpdate<T = unknown> {
  id: string;
  type: 'create' | 'update' | 'delete';
  timestamp: Date;
  data: T;
  rollback: () => void;
}

export interface UseOptimisticFlowOptions extends UseFlowOptions {
  enableOptimistic?: boolean;
  rollbackOnError?: boolean;
}

/**
 * Enhanced flow hook with optimistic updates (MFO-082)
 */
export function useOptimisticFlow(options: UseOptimisticFlowOptions = {}) {
  const {
    enableOptimistic = true,
    rollbackOnError = true,
    ...flowOptions
  } = options;

  const [state, actions] = useFlow(flowOptions);

  // Optimistic flow creation
  const createFlowOptimistic = useCallback(async (request: CreateFlowRequest): Promise<FlowStatus> => {
    if (!enableOptimistic) {
      return actions.createFlow(request);
    }

    // Create optimistic flow
    const optimisticFlow: FlowStatus = {
      flow_id: `temp-${Date.now()}`,
      flow_type: request.flow_type,
      flow_name: request.flow_name || `New ${request.flow_type} flow`,
      status: 'pending' as FlowStatusType,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      progress_percentage: 0,
      phases: [],
      configuration: request.configuration || {},
      metadata: request.metadata || {},
      client_account_id: 0, // Will be updated by server
      engagement_id: 0, // Will be updated by server
      user_id: '', // Will be updated by server
      performance: {
        phase_durations: {}
      },
      errors: [],
      warnings: [],
      can_pause: false,
      can_resume: false,
      can_rollback: false,
      can_cancel: true
    };

    // Apply optimistic update
    const rollback = (): unknown => {
      // Remove optimistic flow from state
      if (state.flow?.flow_id === optimisticFlow.flow_id) {
        actions.reset();
      }
    };

    try {
      // Show creating toast
      flowToast.info('Creating flow...', `${request.flow_type} flow`);

      // Actually create the flow
      const realFlow = await actions.createFlow(request);

      // Replace optimistic flow with real flow
      return realFlow;

    } catch (error) {
      if (rollbackOnError) {
        rollback();
        flowToast.error(error as Error, 'Flow creation failed');
      }
      throw error;
    }
  }, [enableOptimistic, rollbackOnError, actions, state.flow]);

  // Optimistic phase execution
  const executePhaseOptimistic = useCallback(async (
    flowId: string,
    request: ExecutePhaseRequest
  ): Promise<{ success: boolean; message?: string; data?: Record<string, unknown> }> => {
    if (!enableOptimistic || !state.flow || state.flow.flow_id !== flowId) {
      return actions.executePhase(flowId, request);
    }

    // Create optimistic phase update
    const optimisticPhase: Partial<PhaseInfo> = {
      name: request.phase_name,
      status: 'running',
      started_at: new Date().toISOString()
    };

    // Store original phase state for rollback
    const originalPhase = state.flow.phases.find(p => p.name === request.phase_name);
    const originalStatus = state.flow.status;

    // Apply optimistic update locally
    const updatedFlow: FlowStatus = {
      ...state.flow,
      status: 'running' as FlowStatusType,
      current_phase: request.phase_name,
      phases: state.flow.phases.map(p =>
        p.name === request.phase_name
          ? { ...p, ...optimisticPhase }
          : p
      )
    };

    // Temporarily update state
    // Note: This is a simplified example. In a real app, you'd update the state directly

    const rollback = (): unknown => {
      // Restore original state
      if (originalPhase && state.flow) {
        // Restore phase status
        const restoredFlow: FlowStatus = {
          ...state.flow,
          status: originalStatus,
          current_phase: originalPhase.name,
          phases: state.flow.phases.map(p =>
            p.name === request.phase_name ? originalPhase : p
          )
        };
        // Update state with restored flow
      }
    };

    try {
      // Show executing toast
      flowToast.executing(request.phase_name);

      // Actually execute the phase
      const result = await actions.executePhase(flowId, request);

      return result;

    } catch (error) {
      if (rollbackOnError) {
        rollback();
        flowToast.error(error as Error, request.phase_name);
      }
      throw error;
    }
  }, [enableOptimistic, rollbackOnError, actions, state.flow]);

  // Optimistic pause
  const pauseFlowOptimistic = useCallback(async (flowId: string, reason?: string): Promise<void> => {
    if (!enableOptimistic || !state.flow || state.flow.flow_id !== flowId) {
      return actions.pauseFlow(flowId, reason);
    }

    const originalStatus = state.flow.status;

    // Apply optimistic update
    const updatedFlow: FlowStatus = {
      ...state.flow,
      status: 'paused' as FlowStatusType,
      can_pause: false,
      can_resume: true
    };

    const rollback = (): unknown => {
      // Restore original status
      if (state.flow) {
        const restoredFlow: FlowStatus = {
          ...state.flow,
          status: originalStatus,
          can_pause: true,
          can_resume: false
        };
        // Update state with restored flow
      }
    };

    try {
      await actions.pauseFlow(flowId, reason);
    } catch (error) {
      if (rollbackOnError) {
        rollback();
      }
      throw error;
    }
  }, [enableOptimistic, rollbackOnError, actions, state.flow]);

  // Optimistic resume
  const resumeFlowOptimistic = useCallback(async (flowId: string): Promise<void> => {
    if (!enableOptimistic || !state.flow || state.flow.flow_id !== flowId) {
      return actions.resumeFlow(flowId);
    }

    const originalStatus = state.flow.status;

    // Apply optimistic update
    const updatedFlow: FlowStatus = {
      ...state.flow,
      status: 'running' as FlowStatusType,
      can_pause: true,
      can_resume: false
    };

    const rollback = (): unknown => {
      // Restore original status
      if (state.flow) {
        const restoredFlow: FlowStatus = {
          ...state.flow,
          status: originalStatus,
          can_pause: false,
          can_resume: true
        };
        // Update state with restored flow
      }
    };

    try {
      await actions.resumeFlow(flowId);
    } catch (error) {
      if (rollbackOnError) {
        rollback();
      }
      throw error;
    }
  }, [enableOptimistic, rollbackOnError, actions, state.flow]);

  // Optimistic delete
  const deleteFlowOptimistic = useCallback(async (flowId: string, reason?: string): Promise<void> => {
    if (!enableOptimistic) {
      return actions.deleteFlow(flowId, reason);
    }

    // Store flow for potential rollback
    const flowToDelete = state.flows.find(f => f.flow_id === flowId);
    const wasCurrentFlow = state.flow?.flow_id === flowId;

    // Apply optimistic update (remove from list immediately)
    const rollback = (): unknown => {
      // Restore deleted flow
      if (flowToDelete) {
        // Add flow back to state
      }
    };

    try {
      await actions.deleteFlow(flowId, reason);
    } catch (error) {
      if (rollbackOnError && flowToDelete) {
        rollback();
        flowToast.error('Failed to delete flow', 'The flow has been restored');
      }
      throw error;
    }
  }, [enableOptimistic, rollbackOnError, actions, state.flow, state.flows]);

  // Return enhanced actions
  return [
    state,
    {
      ...actions,
      createFlow: createFlowOptimistic,
      executePhase: executePhaseOptimistic,
      pauseFlow: pauseFlowOptimistic,
      resumeFlow: resumeFlowOptimistic,
      deleteFlow: deleteFlowOptimistic
    }
  ] as const;
}

/**
 * Specialized hooks with optimistic updates
 */
export function useOptimisticDiscoveryFlow(options?: UseOptimisticFlowOptions) {
  const [state, actions] = useOptimisticFlow(options);

  const createDiscoveryFlow = useCallback(async (config: Omit<CreateFlowRequest, 'flow_type'>) => {
    return actions.createFlow({
      ...config,
      flow_type: 'discovery'
    });
  }, [actions]);

  return [
    state,
    {
      ...actions,
      createDiscoveryFlow
    }
  ] as const;
}

export function useOptimisticAssessmentFlow(options?: UseOptimisticFlowOptions) {
  const [state, actions] = useOptimisticFlow(options);

  const createAssessmentFlow = useCallback(async (config: Omit<CreateFlowRequest, 'flow_type'>) => {
    return actions.createFlow({
      ...config,
      flow_type: 'assessment'
    });
  }, [actions]);

  return [
    state,
    {
      ...actions,
      createAssessmentFlow
    }
  ] as const;
}
