/**
 * Migrated Unified Discovery Flow Hook
 * MFO-084: Update Discovery components to use unified flow system
 * 
 * This is a migration wrapper that adapts the existing useUnifiedDiscoveryFlow
 * to use the new Master Flow Orchestrator hooks
 */

import { useMemo, useCallback } from 'react';
import { useDiscoveryFlow } from './useFlow';
import { flowToast } from '../utils/toast';
import { FlowStatus, PhaseInfo } from '../types/flow';

interface UseUnifiedDiscoveryFlowReturn {
  flowState: any | null;
  isLoading: boolean;
  error: Error | null;
  isHealthy: boolean;
  initializeFlow: (data: any) => Promise<any>;
  executeFlowPhase: (phase: string) => Promise<any>;
  getPhaseData: (phase: string) => any;
  isPhaseComplete: (phase: string) => boolean;
  canProceedToPhase: (phase: string) => boolean;
  refreshFlow: () => Promise<void>;
  isExecutingPhase: boolean;
  flowId: string | null;
}

/**
 * Migration adapter for existing Discovery components
 * Maps the old API to the new Master Flow Orchestrator API
 */
export function useUnifiedDiscoveryFlow(): UseUnifiedDiscoveryFlowReturn {
  // Use the new unified flow hook
  const [state, actions] = useDiscoveryFlow({
    autoRefresh: true,
    refreshInterval: 5000,
    onError: (error) => flowToast.error(error),
    onSuccess: (data) => console.log('Flow operation successful:', data)
  });

  // Map flow status to legacy format
  const flowState = useMemo(() => {
    if (!state.flow) return null;

    const flow = state.flow;
    
    // Convert new flow format to legacy format
    return {
      flow_id: flow.flow_id,
      client_account_id: flow.client_account_id,
      engagement_id: flow.engagement_id,
      user_id: flow.user_id,
      current_phase: flow.current_phase || '',
      phase_completion: flow.phases.reduce((acc, phase) => ({
        ...acc,
        [phase.name]: phase.status === 'completed'
      }), {}),
      crew_status: flow.crew_status || {},
      raw_data: flow.metadata?.raw_data || [],
      field_mappings: flow.metadata?.field_mappings || {},
      cleaned_data: flow.metadata?.cleaned_data || [],
      asset_inventory: flow.metadata?.asset_inventory || {},
      dependencies: flow.metadata?.dependencies || {},
      technical_debt: flow.metadata?.technical_debt || {},
      status: flow.status,
      progress_percentage: flow.progress_percentage,
      errors: flow.errors.map(e => e.error_message),
      warnings: flow.warnings.map(w => w.warning_message),
      created_at: flow.created_at,
      updated_at: flow.updated_at
    };
  }, [state.flow]);

  // Initialize flow adapter
  const initializeFlow = useCallback(async (data: any) => {
    try {
      const flow = await actions.createDiscoveryFlow({
        flow_name: data.flow_name || 'Discovery Flow',
        configuration: {
          discovery: {
            enable_real_time_validation: true,
            data_sources: data.data_sources || [],
            mapping_templates: data.mapping_templates || [],
            asset_templates: data.asset_templates || []
          }
        },
        initial_state: data,
        metadata: {
          source: 'unified_discovery_flow',
          ...data
        }
      });

      return {
        flow_id: flow.flow_id,
        status: 'initialized',
        message: 'Flow initialized successfully'
      };
    } catch (error) {
      throw error;
    }
  }, [actions]);

  // Execute phase adapter
  const executeFlowPhase = useCallback(async (phase: string) => {
    if (!state.flow) {
      throw new Error('No active flow');
    }

    try {
      const result = await actions.executePhase(state.flow.flow_id, {
        phase_name: phase,
        phase_input: {
          // Map legacy phase data to new format
          source: 'unified_discovery_flow'
        }
      });

      return result;
    } catch (error) {
      throw error;
    }
  }, [state.flow, actions]);

  // Get phase data
  const getPhaseData = useCallback((phase: string) => {
    if (!state.flow) return null;

    const phaseInfo = state.flow.phases.find(p => p.name === phase);
    if (!phaseInfo) return null;

    // Return phase outputs or metadata
    return phaseInfo.outputs || state.flow.metadata?.[phase] || null;
  }, [state.flow]);

  // Check if phase is complete
  const isPhaseComplete = useCallback((phase: string): boolean => {
    if (!state.flow) return false;

    const phaseInfo = state.flow.phases.find(p => p.name === phase);
    return phaseInfo?.status === 'completed' || false;
  }, [state.flow]);

  // Check if can proceed to phase
  const canProceedToPhase = useCallback((phase: string): boolean => {
    if (!state.flow) return false;

    const phaseInfo = state.flow.phases.find(p => p.name === phase);
    if (!phaseInfo) return false;

    // Check if all previous required phases are complete
    const previousPhases = state.flow.phases.filter(p => p.order < phaseInfo.order && p.required);
    return previousPhases.every(p => p.status === 'completed');
  }, [state.flow]);

  // Refresh flow
  const refreshFlow = useCallback(async () => {
    if (state.flow) {
      await actions.refreshFlow(state.flow.flow_id);
    }
  }, [state.flow, actions]);

  // Determine health status
  const isHealthy = useMemo(() => {
    if (!state.flow) return true;
    return state.flow.errors.length === 0 && state.flow.status !== 'failed';
  }, [state.flow]);

  return {
    flowState,
    isLoading: state.isLoading || state.isRefreshing,
    error: state.error,
    isHealthy,
    initializeFlow,
    executeFlowPhase,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    refreshFlow,
    isExecutingPhase: state.isExecuting,
    flowId: state.flow?.flow_id || null
  };
}

/**
 * Export as default for drop-in replacement
 */
export default useUnifiedDiscoveryFlow;