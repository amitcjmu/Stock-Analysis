/**
 * LEGACY - MARKED FOR ARCHIVAL
 *
 * Unified Flow Hook for Master Flow Orchestrator
 * MFO-074: Create unified flow hook for all flow types
 *
 * ⚠️ DEPRECATED: This hook uses legacy FlowService and should be migrated
 * to use masterFlowService.ts and related hooks like useUnifiedDiscoveryFlow.
 * This file is marked for archival to avoid confusion.
 *
 * Use: hooks that import from /services/api/masterFlowService.ts instead
 */

import { useState, useRef } from 'react'
import { useEffect, useCallback } from 'react'
import { FlowService } from '../services/FlowService';
import type { FlowStatus, FlowType, CreateFlowRequest, ExecutePhaseRequest } from '../types/flow';
import { flowToast } from '../utils/toast';

export interface UseFlowOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  onError?: (error: Error) => void;
  onSuccess?: (data: FlowStatus | FlowStatus[]) => void;
}

export interface FlowHookState {
  // Flow data
  flow: FlowStatus | null;
  flows: FlowStatus[];

  // Loading states
  isLoading: boolean;
  isCreating: boolean;
  isExecuting: boolean;
  isRefreshing: boolean;

  // Error states
  error: Error | null;
  lastError: Error | null;

  // Status
  isPolling: boolean;
  lastUpdated: Date | null;
}

export interface FlowHookActions {
  // Flow operations
  createFlow: (request: CreateFlowRequest) => Promise<FlowStatus>;
  executePhase: (flowId: string, request: ExecutePhaseRequest) => Promise<unknown>;
  pauseFlow: (flowId: string, reason?: string) => Promise<void>;
  resumeFlow: (flowId: string) => Promise<void>;
  deleteFlow: (flowId: string, reason?: string) => Promise<void>;

  // Data operations
  refreshFlow: (flowId: string) => Promise<void>;
  refreshFlows: () => Promise<void>;
  getFlowStatus: (flowId: string) => Promise<FlowStatus>;

  // Polling operations
  startPolling: (flowId: string) => void;
  stopPolling: () => void;

  // State operations
  clearError: () => void;
  reset: () => void;
}

/**
 * Unified flow management hook (MFO-074)
 * Supports all flow types with type-safe operations
 */
export function useFlow(options: UseFlowOptions = {}): [FlowHookState, FlowHookActions] {
  const {
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
    onError,
    onSuccess
  } = options;

  // State management
  const [state, setState] = useState<FlowHookState>({
    flow: null,
    flows: [],
    isLoading: false,
    isCreating: false,
    isExecuting: false,
    isRefreshing: false,
    error: null,
    lastError: null,
    isPolling: false,
    lastUpdated: null
  });

  // Refs for cleanup and polling
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Initialize FlowService
  const flowService = FlowService.getInstance();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Error handling
  const handleError = useCallback((error: Error) => {
    if (!mountedRef.current) return;

    setState(prev => ({
      ...prev,
      error,
      lastError: error,
      isLoading: false,
      isCreating: false,
      isExecuting: false,
      isRefreshing: false
    }));

    // Show toast notification for errors
    flowToast.error(error);

    if (onError) {
      onError(error);
    }
  }, [onError]);

  // Success handling
  const handleSuccess = useCallback((data: FlowStatus | FlowStatus[]) => {
    if (!mountedRef.current) return;

    setState(prev => ({
      ...prev,
      error: null,
      lastUpdated: new Date()
    }));

    if (onSuccess) {
      onSuccess(data);
    }
  }, [onSuccess]);

  // MFO-075: Implement flow creation with type safety
  const createFlow = useCallback(async (request: CreateFlowRequest): Promise<FlowStatus> => {
    setState(prev => ({ ...prev, isCreating: true, error: null }));

    try {
      const flowResponse = await flowService.createFlow(request);

      if (!mountedRef.current) return flowResponse;

      setState(prev => ({
        ...prev,
        flow: flowResponse,
        flows: [...prev.flows, flowResponse],
        isCreating: false
      }));

      // Show success toast
      flowToast.created(request.flow_type, flowResponse.flow_id);

      handleSuccess(flowResponse);
      return flowResponse;

    } catch (error) {
      handleError(error as Error);
      throw error;
    }
  }, [flowService, handleError, handleSuccess]);

  // MFO-076: Implement flow execution with phase handling
  const executePhase = useCallback(async (flowId: string, request: ExecutePhaseRequest): Promise<{ success: boolean; message?: string; data?: Record<string, unknown> }> => {
    setState(prev => ({ ...prev, isExecuting: true, error: null }));

    try {
      const result = await flowService.executePhase(flowId, request);

      if (!mountedRef.current) return result;

      // Update flow status after execution
      const updatedFlow = await flowService.getFlowStatus(flowId);

      setState(prev => ({
        ...prev,
        flow: prev.flow?.flow_id === flowId ? updatedFlow : prev.flow,
        flows: prev.flows.map(f => f.flow_id === flowId ? updatedFlow : f),
        isExecuting: false
      }));

      // Show phase completion toast
      flowToast.phaseCompleted(request.phase_name);

      handleSuccess(result);
      return result;

    } catch (error) {
      handleError(error as Error);
      throw error;
    }
  }, [flowService, handleError, handleSuccess]);

  // Flow control operations
  const pauseFlow = useCallback(async (flowId: string, reason?: string): Promise<void> => {
    try {
      await flowService.pauseFlow(flowId, reason);

      if (!mountedRef.current) return;

      // Refresh flow status
      await refreshFlow(flowId);

      // Show pause toast
      flowToast.paused(flowId);

      handleSuccess({ action: 'pause', flowId });

    } catch (error) {
      handleError(error as Error);
      throw error;
    }
  }, [flowService, handleError, handleSuccess]);

  const resumeFlow = useCallback(async (flowId: string): Promise<void> => {
    try {
      await flowService.resumeFlow(flowId);

      if (!mountedRef.current) return;

      // Refresh flow status
      await refreshFlow(flowId);

      // Show resume toast
      flowToast.resumed(flowId);

      handleSuccess({ action: 'resume', flowId });

    } catch (error) {
      handleError(error as Error);
      throw error;
    }
  }, [flowService, handleError, handleSuccess]);

  const deleteFlow = useCallback(async (flowId: string, reason?: string): Promise<void> => {
    try {
      await flowService.deleteFlow(flowId, reason);

      if (!mountedRef.current) return;

      setState(prev => ({
        ...prev,
        flow: prev.flow?.flow_id === flowId ? null : prev.flow,
        flows: prev.flows.filter(f => f.flow_id !== flowId)
      }));

      // Show delete toast
      flowToast.deleted(flowId);

      handleSuccess({ action: 'delete', flowId });

    } catch (error) {
      handleError(error as Error);
      throw error;
    }
  }, [flowService, handleError, handleSuccess]);

  // Data refresh operations
  const refreshFlow = useCallback(async (flowId: string): Promise<void> => {
    setState(prev => ({ ...prev, isRefreshing: true, error: null }));

    try {
      const updatedFlow = await flowService.getFlowStatus(flowId);

      if (!mountedRef.current) return;

      setState(prev => ({
        ...prev,
        flow: prev.flow?.flow_id === flowId ? updatedFlow : prev.flow,
        flows: prev.flows.map(f => f.flow_id === flowId ? updatedFlow : f),
        isRefreshing: false,
        lastUpdated: new Date()
      }));

    } catch (error) {
      handleError(error as Error);
    }
  }, [flowService, handleError]);

  const refreshFlows = useCallback(async (): Promise<void> => {
    setState(prev => ({ ...prev, isRefreshing: true, error: null }));

    try {
      const flows = await flowService.getFlows();

      if (!mountedRef.current) return;

      setState(prev => ({
        ...prev,
        flows,
        isRefreshing: false,
        lastUpdated: new Date()
      }));

    } catch (error) {
      handleError(error as Error);
    }
  }, [flowService, handleError]);

  const getFlowStatus = useCallback(async (flowId: string): Promise<FlowStatus> => {
    try {
      const flow = await flowService.getFlowStatus(flowId);

      if (!mountedRef.current) return flow;

      setState(prev => ({
        ...prev,
        flow: prev.flow?.flow_id === flowId ? flow : prev.flow,
        flows: prev.flows.map(f => f.flow_id === flowId ? flow : f),
        lastUpdated: new Date()
      }));

      return flow;

    } catch (error) {
      handleError(error as Error);
      throw error;
    }
  }, [flowService, handleError]);

  // MFO-077: Implement status polling with real-time updates
  const startPolling = useCallback((flowId: string): void => {
    // Stop existing polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    setState(prev => ({ ...prev, isPolling: true }));

    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 3;

    pollIntervalRef.current = setInterval(async () => {
      if (!mountedRef.current) return;

      try {
        await refreshFlow(flowId);
        consecutiveErrors = 0; // Reset on success
      } catch (error) {
        consecutiveErrors++;
        console.warn(`Polling error (${consecutiveErrors}/${maxConsecutiveErrors}):`, error);

        // Stop polling after too many consecutive errors
        if (consecutiveErrors >= maxConsecutiveErrors) {
          console.error('Too many polling errors, stopping auto-refresh');
          stopPolling();
          setState(prev => ({
            ...prev,
            error: 'Auto-refresh stopped due to repeated errors. Please refresh manually.'
          }));
        }
      }
    }, refreshInterval);
  }, [refreshFlow, refreshInterval, stopPolling]);

  const stopPolling = useCallback((): void => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    setState(prev => ({ ...prev, isPolling: false }));
  }, []);

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh && state.flow) {
      startPolling(state.flow.flow_id);
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [autoRefresh, state.flow, startPolling, stopPolling]);

  // Utility operations
  const clearError = useCallback((): void => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const reset = useCallback((): void => {
    stopPolling();
    setState({
      flow: null,
      flows: [],
      isLoading: false,
      isCreating: false,
      isExecuting: false,
      isRefreshing: false,
      error: null,
      lastError: null,
      isPolling: false,
      lastUpdated: null
    });
  }, [stopPolling]);

  // Actions object
  const actions: FlowHookActions = {
    createFlow,
    executePhase,
    pauseFlow,
    resumeFlow,
    deleteFlow,
    refreshFlow,
    refreshFlows,
    getFlowStatus,
    startPolling,
    stopPolling,
    clearError,
    reset
  };

  return [state, actions];
}

/**
 * Specialized hook for discovery flows
 * MFO-074: Flow type-specific hook
 */
export function useDiscoveryFlow(options?: UseFlowOptions): [AssessmentFlowState, AssessmentFlowActions & { createDiscoveryFlow: (config: Omit<CreateFlowRequest, 'flow_type'>) => Promise<AssessmentFlow> }] {
  const [state, actions] = useFlow(options);

  const createDiscoveryFlow = useCallback(async (config: Omit<CreateFlowRequest, 'flow_type'>) => {
    return actions.createFlow({
      ...config,
      flow_type: 'discovery' as FlowType
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

/**
 * Specialized hook for assessment flows
 * MFO-074: Flow type-specific hook
 */
export function useAssessmentFlow(options?: UseFlowOptions): [AssessmentFlowState, AssessmentFlowActions & { createAssessmentFlow: (config: Omit<CreateFlowRequest, 'flow_type'>) => Promise<AssessmentFlow> }] {
  const [state, actions] = useFlow(options);

  const createAssessmentFlow = useCallback(async (config: Omit<CreateFlowRequest, 'flow_type'>) => {
    return actions.createFlow({
      ...config,
      flow_type: 'assessment' as FlowType
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

/**
 * Hook for multiple flows management
 * MFO-074: Multi-flow management
 */
export function useFlows(flowType?: FlowType, options?: UseFlowOptions): readonly [AssessmentFlowState & { flows: AssessmentFlow[]; isLoading: boolean }, AssessmentFlowActions & { loadFlows: () => Promise<void> }] {
  const [state, actions] = useFlow(options);
  const [isLoadingFlows, setIsLoadingFlows] = useState(false);

  const loadFlows = useCallback(async () => {
    setIsLoadingFlows(true);
    try {
      await actions.refreshFlows();
    } finally {
      setIsLoadingFlows(false);
    }
  }, [actions]);

  // Filter flows by type if specified
  const filteredFlows = flowType
    ? state.flows.filter(flow => flow.flow_type === flowType)
    : state.flows;

  // Load flows on mount
  useEffect(() => {
    loadFlows();
  }, [loadFlows]);

  return [
    {
      ...state,
      flows: filteredFlows,
      isLoading: isLoadingFlows || state.isLoading
    },
    {
      ...actions,
      loadFlows
    }
  ] as const;
}
