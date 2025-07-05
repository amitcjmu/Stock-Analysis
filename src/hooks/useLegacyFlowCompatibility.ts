/**
 * Legacy Flow Compatibility Hook
 * MFO-081: Create backward compatibility wrappers
 * 
 * Provides backward compatibility for existing components
 * while migrating to the Master Flow Orchestrator
 */

import { useEffect, useCallback } from 'react';
import { useFlow } from './useFlow';
import { FlowStatus, CreateFlowRequest } from '../types/flow';

// Legacy hook interfaces for backward compatibility
export interface LegacyDiscoveryFlowHook {
  discoveryFlow: any;
  isLoading: boolean;
  error: string | null;
  createDiscoveryFlow: (config: any) => Promise<any>;
  executePhase: (flowId: string, phase: string, data: any) => Promise<any>;
  getFlowStatus: (flowId: string) => Promise<any>;
  pauseFlow: (flowId: string) => Promise<void>;
  resumeFlow: (flowId: string) => Promise<void>;
}

export interface LegacyAssessmentFlowHook {
  assessmentFlow: any;
  isLoading: boolean;
  error: string | null;
  createAssessmentFlow: (config: any) => Promise<any>;
  executePhase: (flowId: string, phase: string, data: any) => Promise<any>;
  getFlowStatus: (flowId: string) => Promise<any>;
}

/**
 * Legacy Discovery Flow Hook (MFO-081)
 * Provides backward compatibility for existing discovery flow components
 * 
 * @deprecated Use useFlow or useDiscoveryFlow instead
 */
export function useUnifiedDiscoveryFlow(): LegacyDiscoveryFlowHook {
  const [state, actions] = useFlow();

  useEffect(() => {
    console.warn(
      'useUnifiedDiscoveryFlow is deprecated. ' +
      'Please migrate to useFlow or useDiscoveryFlow for better performance and features.'
    );
  }, []);

  // Legacy create discovery flow
  const createDiscoveryFlow = useCallback(async (config: any) => {
    try {
      // Transform legacy config to new format
      const createRequest: CreateFlowRequest = {
        flow_type: 'discovery',
        flow_name: config.flow_name || config.name || 'Discovery Flow',
        configuration: {
          discovery: {
            enable_real_time_validation: config.enable_validation !== false,
            data_sources: config.data_sources || [],
            mapping_templates: config.mapping_templates || [],
            asset_templates: config.asset_templates || []
          },
          auto_retry: config.auto_retry !== false,
          max_retries: config.max_retries || 3,
          timeout_minutes: config.timeout_minutes || 30,
          agent_collaboration: config.agent_collaboration !== false
        },
        initial_state: config.initial_data || config.data || {},
        metadata: config.metadata || {}
      };

      const flow = await actions.createFlow(createRequest);
      
      // Transform to legacy format
      return {
        flow_id: flow.flow_id,
        session_id: flow.flow_id, // Legacy compatibility
        status: flow.status,
        flow_details: flow,
        discovery_data: flow.metadata
      };
    } catch (error) {
      console.error('Legacy createDiscoveryFlow error:', error);
      throw error;
    }
  }, [actions]);

  // Legacy execute phase
  const executePhase = useCallback(async (flowId: string, phase: string, data: any) => {
    try {
      const result = await actions.executePhase(flowId, {
        phase_name: phase,
        phase_input: data
      });

      // Transform to legacy format
      return {
        status: 'success',
        phase_result: result,
        next_phase: result.next_phase,
        flow_updated: true
      };
    } catch (error) {
      console.error('Legacy executePhase error:', error);
      throw error;
    }
  }, [actions]);

  // Legacy get flow status
  const getFlowStatus = useCallback(async (flowId: string) => {
    try {
      const flow = await actions.getFlowStatus(flowId);
      
      // Transform to legacy format
      return {
        flow_id: flow.flow_id,
        session_id: flow.flow_id, // Legacy compatibility
        status: flow.status,
        current_phase: flow.current_phase,
        progress: flow.progress_percentage,
        phases: flow.phases,
        errors: flow.errors,
        discovery_data: flow.metadata,
        flow_details: flow
      };
    } catch (error) {
      console.error('Legacy getFlowStatus error:', error);
      throw error;
    }
  }, [actions]);

  // Legacy pause/resume (direct passthrough)
  const pauseFlow = useCallback(async (flowId: string) => {
    await actions.pauseFlow(flowId, 'Legacy pause operation');
  }, [actions]);

  const resumeFlow = useCallback(async (flowId: string) => {
    await actions.resumeFlow(flowId);
  }, [actions]);

  return {
    discoveryFlow: state.flow ? {
      flow_id: state.flow.flow_id,
      session_id: state.flow.flow_id,
      status: state.flow.status,
      current_phase: state.flow.current_phase,
      progress: state.flow.progress_percentage,
      discovery_data: state.flow.metadata
    } : null,
    isLoading: state.isLoading || state.isCreating || state.isExecuting,
    error: state.error?.message || null,
    createDiscoveryFlow,
    executePhase,
    getFlowStatus,
    pauseFlow,
    resumeFlow
  };
}

/**
 * Legacy Assessment Flow Hook (MFO-081)
 * Provides backward compatibility for existing assessment flow components
 * 
 * @deprecated Use useFlow or useAssessmentFlow instead
 */
export function useUnifiedAssessmentFlow(): LegacyAssessmentFlowHook {
  const [state, actions] = useFlow();

  useEffect(() => {
    console.warn(
      'useUnifiedAssessmentFlow is deprecated. ' +
      'Please migrate to useFlow or useAssessmentFlow for better performance and features.'
    );
  }, []);

  // Legacy create assessment flow
  const createAssessmentFlow = useCallback(async (config: any) => {
    try {
      const createRequest: CreateFlowRequest = {
        flow_type: 'assessment',
        flow_name: config.flow_name || config.name || 'Assessment Flow',
        configuration: {
          assessment: {
            assessment_depth: config.assessment_depth || 'standard',
            include_business_impact: config.include_business_impact !== false,
            risk_tolerance: config.risk_tolerance || 'medium',
            complexity_thresholds: config.complexity_thresholds || {}
          },
          auto_retry: config.auto_retry !== false,
          max_retries: config.max_retries || 3,
          timeout_minutes: config.timeout_minutes || 45,
          agent_collaboration: config.agent_collaboration !== false
        },
        initial_state: config.initial_data || config.data || {},
        metadata: config.metadata || {}
      };

      const flow = await actions.createFlow(createRequest);
      
      return {
        flow_id: flow.flow_id,
        session_id: flow.flow_id,
        status: flow.status,
        flow_details: flow,
        assessment_data: flow.metadata
      };
    } catch (error) {
      console.error('Legacy createAssessmentFlow error:', error);
      throw error;
    }
  }, [actions]);

  // Legacy execute phase
  const executePhase = useCallback(async (flowId: string, phase: string, data: any) => {
    try {
      const result = await actions.executePhase(flowId, {
        phase_name: phase,
        phase_input: data
      });

      return {
        status: 'success',
        phase_result: result,
        next_phase: result.next_phase,
        flow_updated: true
      };
    } catch (error) {
      console.error('Legacy executePhase error:', error);
      throw error;
    }
  }, [actions]);

  // Legacy get flow status
  const getFlowStatus = useCallback(async (flowId: string) => {
    try {
      const flow = await actions.getFlowStatus(flowId);
      
      return {
        flow_id: flow.flow_id,
        session_id: flow.flow_id,
        status: flow.status,
        current_phase: flow.current_phase,
        progress: flow.progress_percentage,
        phases: flow.phases,
        errors: flow.errors,
        assessment_data: flow.metadata,
        flow_details: flow
      };
    } catch (error) {
      console.error('Legacy getFlowStatus error:', error);
      throw error;
    }
  }, [actions]);

  return {
    assessmentFlow: state.flow ? {
      flow_id: state.flow.flow_id,
      session_id: state.flow.flow_id,
      status: state.flow.status,
      current_phase: state.flow.current_phase,
      progress: state.flow.progress_percentage,
      assessment_data: state.flow.metadata
    } : null,
    isLoading: state.isLoading || state.isCreating || state.isExecuting,
    error: state.error?.message || null,
    createAssessmentFlow,
    executePhase,
    getFlowStatus
  };
}

/**
 * Legacy Data Import Hook (MFO-081)
 * Provides compatibility for data import operations
 * 
 * @deprecated Use FlowService.executePhase with 'data_import' phase instead
 */
export function useDataImport() {
  const [state, actions] = useFlow();

  useEffect(() => {
    console.warn(
      'useDataImport is deprecated. ' +
      'Use FlowService.executePhase with data_import phase instead.'
    );
  }, []);

  const importData = useCallback(async (flowId: string, importData: any) => {
    try {
      const result = await actions.executePhase(flowId, {
        phase_name: 'data_import',
        phase_input: {
          import_data: importData,
          validation_config: {
            strict_validation: true,
            auto_fix_errors: false
          }
        }
      });

      return {
        import_id: result.import_id || `import_${Date.now()}`,
        status: result.status || 'completed',
        imported_records: result.imported_records || 0,
        validation_errors: result.errors || [],
        import_summary: result.summary || {}
      };
    } catch (error) {
      console.error('Legacy importData error:', error);
      throw error;
    }
  }, [actions]);

  return {
    isImporting: state.isExecuting,
    error: state.error?.message || null,
    importData
  };
}

/**
 * Migration helper functions (MFO-081)
 */
export const migrationHelpers = {
  /**
   * Convert legacy session ID to flow ID
   */
  sessionIdToFlowId: (sessionId: string): string => {
    // If it's already a flow ID format, return as-is
    if (sessionId.startsWith('flow_') || sessionId.includes('-')) {
      return sessionId;
    }
    
    // Convert legacy session ID format
    if (sessionId.startsWith('disc_session_')) {
      return sessionId.replace('disc_session_', 'flow_discovery_');
    }
    
    if (sessionId.startsWith('assess_session_')) {
      return sessionId.replace('assess_session_', 'flow_assessment_');
    }
    
    return sessionId;
  },

  /**
   * Convert legacy configuration to new format
   */
  convertLegacyConfig: (legacyConfig: any, flowType: string): CreateFlowRequest => {
    const baseConfig: CreateFlowRequest = {
      flow_type: flowType as any,
      flow_name: legacyConfig.name || legacyConfig.flow_name || `${flowType} Flow`,
      configuration: {},
      initial_state: legacyConfig.initial_data || legacyConfig.data || {},
      metadata: legacyConfig.metadata || {}
    };

    // Flow-specific config transformations
    if (flowType === 'discovery') {
      baseConfig.configuration = {
        discovery: {
          enable_real_time_validation: legacyConfig.enable_validation !== false,
          data_sources: legacyConfig.data_sources || [],
          mapping_templates: legacyConfig.mapping_templates || []
        }
      };
    } else if (flowType === 'assessment') {
      baseConfig.configuration = {
        assessment: {
          assessment_depth: legacyConfig.depth || 'standard',
          include_business_impact: legacyConfig.include_business !== false
        }
      };
    }

    return baseConfig;
  },

  /**
   * Convert new flow status to legacy format
   */
  convertToLegacyFormat: (flow: FlowStatus): any => {
    return {
      flow_id: flow.flow_id,
      session_id: flow.flow_id, // For compatibility
      status: flow.status,
      current_phase: flow.current_phase,
      progress: flow.progress_percentage,
      phases: flow.phases,
      errors: flow.errors,
      data: flow.metadata,
      flow_details: flow,
      created_at: flow.created_at,
      updated_at: flow.updated_at
    };
  }
};

/**
 * Deprecation warning component
 */
export function DeprecationWarning({ 
  componentName, 
  replacement, 
  showWarning = true 
}: { 
  componentName: string; 
  replacement: string; 
  showWarning?: boolean; 
}) {
  useEffect(() => {
    if (showWarning && process.env.NODE_ENV === 'development') {
      console.warn(
        `🚨 DEPRECATION WARNING: ${componentName} is deprecated. ` +
        `Please migrate to ${replacement} for better performance and features. ` +
        `This component will be removed in a future version.`
      );
    }
  }, [componentName, replacement, showWarning]);

  return null;
}