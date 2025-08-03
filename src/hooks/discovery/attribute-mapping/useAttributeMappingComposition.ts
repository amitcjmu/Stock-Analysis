import { useCallback, useEffect } from 'react';
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
  // 1. Flow Detection
  const flowDetection = useFlowDetection();
  const { finalFlowId, effectiveFlowId } = flowDetection;

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

  // Debug import data loading (only in development to reduce console spam)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      if (importDataHook.importDataError) {
        console.error('❌ Import data error:', importDataHook.importDataError);
      }

      if (importData && !importDataHook.isImportDataLoading) {
        console.log('✅ Import data available:', {
          import_id: importData?.import_metadata?.import_id,
          flow_id: importData?.flow_id,
          status: importData?.status,
          has_metadata: !!importData?.import_metadata,
          metadata_keys: importData?.import_metadata ? Object.keys(importData.import_metadata) : []
        });
      }
    }
  }, [importData?.flow_id, importDataHook.importDataError, importDataHook.isImportDataLoading]); // Reduced dependencies

  const refetchAgentic = useCallback(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🔄 Refreshing agentic data and field mappings');
    }
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
    refetchClarifications
  };
};
