/**
 * Migrated Assessment Flow Hook
 * MFO-085: Update Assessment components to use unified flow system
 * 
 * Migration wrapper that adapts existing assessment components to use
 * the new Master Flow Orchestrator system
 */

import { useMemo, useCallback } from 'react';
import { useAssessmentFlow as useNewAssessmentFlow } from './useFlow';
import { flowToast } from '../utils/toast';
import { FlowStatus } from '../types/flow';

interface AssessmentFlowState {
  flow_id: string;
  status: string;
  current_phase: string;
  applications: any[];
  business_impact: any;
  complexity_scores: any;
  six_r_decisions: any;
  dependencies: any;
  created_at: string;
  updated_at: string;
}

interface UseAssessmentFlowReturn {
  flowState: AssessmentFlowState | null;
  isLoading: boolean;
  error: Error | null;
  initializeAssessment: (applications: any[]) => Promise<any>;
  performBusinessImpactAnalysis: () => Promise<any>;
  calculateComplexityScores: () => Promise<any>;
  determineSixRStrategy: () => Promise<any>;
  mapDependencies: () => Promise<any>;
  getAssessmentResults: () => any;
  refreshAssessment: () => Promise<void>;
  isProcessing: boolean;
  flowId: string | null;
}

/**
 * Migration adapter for existing Assessment components
 * Provides backward compatibility while using new Master Flow Orchestrator
 */
export function useAssessmentFlow(): UseAssessmentFlowReturn {
  // Use the new unified assessment flow hook
  const [state, actions] = useNewAssessmentFlow({
    autoRefresh: true,
    refreshInterval: 5000,
    onError: (error) => flowToast.error(error),
    onSuccess: (data) => console.log('Assessment operation successful:', data)
  });

  // Map flow status to legacy assessment format
  const flowState = useMemo((): AssessmentFlowState | null => {
    if (!state.flow) return null;

    const flow = state.flow;
    
    return {
      flow_id: flow.flow_id,
      status: flow.status,
      current_phase: flow.current_phase || '',
      applications: flow.metadata?.applications || [],
      business_impact: flow.metadata?.business_impact || {},
      complexity_scores: flow.metadata?.complexity_scores || {},
      six_r_decisions: flow.metadata?.six_r_decisions || {},
      dependencies: flow.metadata?.dependencies || {},
      created_at: flow.created_at,
      updated_at: flow.updated_at
    };
  }, [state.flow]);

  // Initialize assessment flow
  const initializeAssessment = useCallback(async (applications: any[]) => {
    try {
      const flow = await actions.createAssessmentFlow({
        flow_name: `Assessment - ${new Date().toISOString()}`,
        configuration: {
          assessment: {
            assessment_depth: 'comprehensive',
            include_business_impact: true,
            risk_tolerance: 'medium',
            complexity_thresholds: {
              low: 30,
              medium: 60,
              high: 80
            }
          }
        },
        initial_state: {
          applications
        },
        metadata: {
          applications,
          source: 'assessment_flow'
        }
      });

      // Start polling for updates
      actions.startPolling(flow.flow_id);

      return {
        flow_id: flow.flow_id,
        status: 'initialized',
        message: 'Assessment flow initialized successfully'
      };
    } catch (error) {
      throw error;
    }
  }, [actions]);

  // Execute business impact analysis phase
  const performBusinessImpactAnalysis = useCallback(async () => {
    if (!state.flow) {
      throw new Error('No active assessment flow');
    }

    try {
      const result = await actions.executePhase(state.flow.flow_id, {
        phase_name: 'business_impact_analysis',
        phase_input: {
          applications: flowState?.applications || []
        }
      });

      return result;
    } catch (error) {
      throw error;
    }
  }, [state.flow, actions, flowState]);

  // Execute complexity calculation phase
  const calculateComplexityScores = useCallback(async () => {
    if (!state.flow) {
      throw new Error('No active assessment flow');
    }

    try {
      const result = await actions.executePhase(state.flow.flow_id, {
        phase_name: 'complexity_scoring',
        phase_input: {
          applications: flowState?.applications || [],
          business_impact: flowState?.business_impact || {}
        }
      });

      return result;
    } catch (error) {
      throw error;
    }
  }, [state.flow, actions, flowState]);

  // Execute 6R strategy determination phase
  const determineSixRStrategy = useCallback(async () => {
    if (!state.flow) {
      throw new Error('No active assessment flow');
    }

    try {
      const result = await actions.executePhase(state.flow.flow_id, {
        phase_name: 'six_r_determination',
        phase_input: {
          applications: flowState?.applications || [],
          complexity_scores: flowState?.complexity_scores || {},
          business_impact: flowState?.business_impact || {}
        }
      });

      return result;
    } catch (error) {
      throw error;
    }
  }, [state.flow, actions, flowState]);

  // Execute dependency mapping phase
  const mapDependencies = useCallback(async () => {
    if (!state.flow) {
      throw new Error('No active assessment flow');
    }

    try {
      const result = await actions.executePhase(state.flow.flow_id, {
        phase_name: 'dependency_mapping',
        phase_input: {
          applications: flowState?.applications || [],
          six_r_decisions: flowState?.six_r_decisions || {}
        }
      });

      return result;
    } catch (error) {
      throw error;
    }
  }, [state.flow, actions, flowState]);

  // Get assessment results
  const getAssessmentResults = useCallback(() => {
    if (!flowState) return null;

    return {
      applications: flowState.applications,
      business_impact: flowState.business_impact,
      complexity_scores: flowState.complexity_scores,
      six_r_decisions: flowState.six_r_decisions,
      dependencies: flowState.dependencies,
      summary: {
        total_applications: flowState.applications.length,
        by_six_r: Object.values(flowState.six_r_decisions || {}).reduce((acc: any, decision: any) => {
          acc[decision] = (acc[decision] || 0) + 1;
          return acc;
        }, {}),
        average_complexity: Object.values(flowState.complexity_scores || {}).reduce((sum: number, score: any) => 
          sum + (score.overall || 0), 0) / Object.keys(flowState.complexity_scores || {}).length || 0
      }
    };
  }, [flowState]);

  // Refresh assessment
  const refreshAssessment = useCallback(async () => {
    if (state.flow) {
      await actions.refreshFlow(state.flow.flow_id);
    }
  }, [state.flow, actions]);

  return {
    flowState,
    isLoading: state.isLoading || state.isRefreshing,
    error: state.error,
    initializeAssessment,
    performBusinessImpactAnalysis,
    calculateComplexityScores,
    determineSixRStrategy,
    mapDependencies,
    getAssessmentResults,
    refreshAssessment,
    isProcessing: state.isExecuting,
    flowId: state.flow?.flow_id || null
  };
}

/**
 * Export as default for drop-in replacement
 */
export default useAssessmentFlow;