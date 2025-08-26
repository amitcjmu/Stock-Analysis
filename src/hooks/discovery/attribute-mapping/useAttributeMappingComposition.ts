import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUnifiedDiscoveryFlow } from '../../useUnifiedDiscoveryFlow';
import { useFlowDetection } from './useFlowDetection';
import { useFieldMappings } from './useFieldMappings';
import { useImportData } from './useImportData';
import { useCriticalAttributes } from './useCriticalAttributes';
import { useAttributeMappingActions } from './useAttributeMappingActions';
import { useAttributeMappingState } from './useAttributeMappingState';
import type { AttributeMappingLogicResult } from './types';

/**
 * Main composition hook that combines all specialized attribute mapping hooks
 * Maintains the same API as the original useAttributeMappingLogic hook
 */
export const useAttributeMappingComposition = (): AttributeMappingLogicResult => {
  const navigate = useNavigate();


  // 1. Flow Detection
  const flowDetection = useFlowDetection();
  const {
    finalFlowId,
    effectiveFlowId
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

  // 4. Field Mappings - pass flow_id for proper MFO integration
  const fieldMappingsHook = useFieldMappings(importData, fieldMappingData, finalFlowId);
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


  // Debug import data loading - removed to prevent console spam
  // Avoid auto-refetch cascades on navigation; let user-triggered actions control refresh
  const refetchAgentic = useCallback(() => {
    return Promise.all([refresh(), fieldMappingsHook.refetchFieldMappings()]);
  }, [refresh, fieldMappingsHook]);

  const refetchClarifications = useCallback(() => {
    return Promise.resolve();
  }, []);

  // Refresh function for after flow cleanup
  const refreshFlowState = useCallback(async () => {
    console.log(`🔄 [useAttributeMappingComposition] Refreshing flow state after cleanup`);

    // Refresh all data
    await Promise.all([
      refresh(),
      fieldMappingsHook.refetchFieldMappings(),
      flowDetection.refetchFlows?.() // If flow detection has a refresh method
    ]);
  }, [refresh, fieldMappingsHook, flowDetection]);

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

    refreshFlowState
  };
};
