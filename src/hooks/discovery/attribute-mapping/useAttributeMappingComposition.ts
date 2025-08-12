import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '../../useUnifiedDiscoveryFlow';
import { useFlowDetection } from './useFlowDetection';
import { useFieldMappings } from './useFieldMappings';
import { useImportData } from './useImportData';
import { useCriticalAttributes } from './useCriticalAttributes';
import { useAttributeMappingActions } from './useAttributeMappingActions';
import { useAttributeMappingState } from './useAttributeMappingState';
import { flowRecoveryService } from '../../../services/flow-recovery';
import type { AttributeMappingLogicResult } from './types';

/**
 * Main composition hook that combines all specialized attribute mapping hooks
 * Maintains the same API as the original useAttributeMappingLogic hook
 */
export const useAttributeMappingComposition = (): AttributeMappingLogicResult => {
  const navigate = useNavigate();

  // Phase transition interception state
  const [isInterceptingTransition, setIsInterceptingTransition] = useState(false);
  const [transitionIntercepted, setTransitionIntercepted] = useState(false);

  // 1. Flow Detection with recovery support
  const flowDetection = useFlowDetection();
  const {
    finalFlowId,
    effectiveFlowId,
    isRecovering,
    recoveryProgress,
    recoveryError,
    recoveredFlowId,
    triggerFlowRecovery
  } = flowDetection;

  // 2. Import Data
  const importDataHook = useImportData(finalFlowId);
  const { importData } = importDataHook;

  // 3. Unified Discovery Flow
  const {
    flowState: flow,
    isLoading: isFlowLoading,
    error: flowError,
    executeFlowPhase: updatePhase,
    refreshFlow: refresh
  } = useUnifiedDiscoveryFlow(finalFlowId);

  // Get field mapping data from unified flow (for legacy compatibility)
  // Backend returns 'field_mappings' (with 's'), not 'field_mapping'
  const fieldMappingData = flow?.field_mappings || flow?.field_mapping;

  // 4. Field Mappings
  const fieldMappingsHook = useFieldMappings(importData, fieldMappingData);
  const { fieldMappings, realFieldMappings } = fieldMappingsHook;

  // 5. Critical Attributes
  const criticalAttributesHook = useCriticalAttributes(
    finalFlowId,
    realFieldMappings,
    fieldMappings,
    fieldMappingData
  );
  const { criticalAttributes } = criticalAttributesHook;

  // 6. Actions
  const actions = useAttributeMappingActions(
    flow,
    fieldMappings,
    refresh,
    fieldMappingsHook.refetchFieldMappings
  );

  // 7. State Management
  const state = useAttributeMappingState(
    fieldMappings,
    realFieldMappings,
    fieldMappingData,
    flow,
    flowDetection.flowList,
    effectiveFlowId,
    isFlowLoading,
    flowDetection.isFlowListLoading,
    importDataHook.isImportDataLoading,
    fieldMappingsHook.isFieldMappingsLoading,
    flowError,
    flowDetection.flowListError,
    importDataHook.importDataError,
    fieldMappingsHook.fieldMappingsError
  );

  // Phase transition interception - validate flow readiness before allowing attribute mapping
  useEffect(() => {
    const interceptTransition = async () => {
      if (!finalFlowId || transitionIntercepted || isInterceptingTransition) return;

      console.log(`🛡️ [useAttributeMappingComposition] Intercepting transition to attribute mapping for flow: ${finalFlowId}`);

      try {
        setIsInterceptingTransition(true);

        // Call the flow recovery service to check if transition should be allowed
        const result = await flowRecoveryService.interceptTransition(
          finalFlowId,
          'data_import',
          'attribute_mapping'
        );

        setTransitionIntercepted(true);

        if (!result.allowTransition && result.redirectPath) {
          console.log(`🔄 [useAttributeMappingComposition] Transition blocked, redirecting to: ${result.redirectPath}`);
          navigate(result.redirectPath);
          return;
        }

        if (!result.flowReadiness.canProceedToAttributeMapping) {
          console.warn(`⚠️ [useAttributeMappingComposition] Flow not ready for attribute mapping:`, result.flowReadiness);

          // If data import is not complete, redirect to data import
          if (!result.flowReadiness.dataImportComplete) {
            console.log(`🔄 [useAttributeMappingComposition] Redirecting to data import due to incomplete data import`);
            navigate('/discovery/cmdb-import');
            return;
          }
        }

        console.log(`✅ [useAttributeMappingComposition] Transition allowed to attribute mapping`);

      } catch (error) {
        console.error(`❌ [useAttributeMappingComposition] Phase transition interception failed:`, error);
        // Allow transition to continue on error to avoid blocking users
        setTransitionIntercepted(true);
      } finally {
        setIsInterceptingTransition(false);
      }
    };

    if (finalFlowId) {
      interceptTransition();
    }
  }, [finalFlowId, navigate, transitionIntercepted, isInterceptingTransition]);

  // Debug import data loading - removed to prevent console spam
  const refetchAgentic = useCallback(() => {
    return Promise.all([refresh(), fieldMappingsHook.refetchFieldMappings()]);
  }, [refresh, fieldMappingsHook]);

  const refetchClarifications = useCallback(() => {
    return Promise.resolve();
  }, []);

  return {
    // Data
    agenticData: state.agenticData,
    fieldMappings,
    crewAnalysis: state.crewAnalysis,
    mappingProgress: state.mappingProgress,
    criticalAttributes,

    // Flow state
    flowState: flow, // Keep backward compatibility
    flow,
    flowId: flow?.flow_id || effectiveFlowId,
    dataImportId: flow?.data_import_id || effectiveFlowId, // Add data_import_id
    availableDataImports: state.availableDataImports,
    selectedDataImportId: state.selectedDataImportId,

    // Auto-detection info
    urlFlowId: flowDetection.urlFlowId,
    autoDetectedFlowId: flowDetection.autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow: flowDetection.hasEffectiveFlow,
    flowList: flowDetection.flowList,

    // Loading states
    isAgenticLoading: state.isAgenticLoading,
    isFlowStateLoading: state.isFlowStateLoading,
    isAnalyzing: state.isAnalyzing,

    // Error states
    agenticError: state.agenticError,
    flowStateError: state.flowStateError,

    // Action handlers
    handleTriggerFieldMappingCrew: actions.handleTriggerFieldMappingCrew,
    handleApproveMapping: actions.handleApproveMapping,
    handleRejectMapping: actions.handleRejectMapping,
    handleMappingChange: actions.handleMappingChange,
    handleAttributeUpdate: actions.handleAttributeUpdate,
    handleDataImportSelection: actions.handleDataImportSelection,
    refetchAgentic,
    refetchCriticalAttributes: criticalAttributesHook.refetchCriticalAttributes,
    canContinueToDataCleansing: actions.canContinueToDataCleansing,
    checkMappingApprovalStatus: actions.checkMappingApprovalStatus,

    // Flow status
    hasActiveFlow: state.hasActiveFlow,
    currentPhase: state.currentPhase,
    flowProgress: state.flowProgress,

    // Agent clarifications
    agentClarifications: state.agentClarifications,
    isClarificationsLoading: state.isClarificationsLoading,
    clarificationsError: state.clarificationsError,
    refetchClarifications,

    // Flow recovery state
    isRecovering,
    recoveryProgress,
    recoveryError,
    recoveredFlowId,
    triggerFlowRecovery,
    isInterceptingTransition,
    transitionIntercepted
  };
};
