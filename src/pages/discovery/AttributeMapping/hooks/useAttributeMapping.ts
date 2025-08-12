import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAttributeMappingLogic } from '../../../../hooks/discovery/attribute-mapping';
import { useAttributeMappingNavigation } from '../../../../hooks/discovery/useAttributeMappingNavigation';
import type { AttributeMappingState, AttributeMappingActions, NavigationState, SessionInfo } from '../types';

export const useAttributeMapping = (): JSX.Element => {
  // Navigation state
  const [activeTab, setActiveTab] = useState<'mappings' | 'data' | 'critical'>('mappings');
  const { flowId: urlFlowId } = useParams<{ flowId?: string }>();

  // Business logic hooks
  const {
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    flowId,
    availableDataImports,
    selectedDataImportId,
    isAgenticLoading,
    isFlowStateLoading,
    isAnalyzing,
    agenticError,
    flowStateError,
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    refetchCriticalAttributes,
    canContinueToDataCleansing,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    flowList,
    // Flow recovery state
    isRecovering,
    recoveryProgress,
    recoveryError,
    recoveredFlowId,
    triggerFlowRecovery,
    // Multi-flow blocking state
    blockingFlows,
    hasMultipleBlockingFlows,
    refreshFlowState,
  } = useAttributeMappingLogic();

  // Navigation logic
  const { handleContinueToDataCleansing } = useAttributeMappingNavigation(
    flowState,
    mappingProgress
  );

  // Error state check (define first to avoid temporal dead zone)
  const hasError = !!(flowStateError || agenticError);
  const errorMessage = flowStateError?.message || agenticError?.message;

  // Enhanced loading state - consider more loading scenarios
  const isLoading = (isFlowStateLoading && !flowState) ||
                   isAgenticLoading ||
                   // Also loading if we have an effective flow but no data yet and no errors
                   (effectiveFlowId && !hasError && !agenticData && !fieldMappings?.length);
  // Enhanced data availability check - be more comprehensive about what constitutes "data"
  const hasData = !!(
    agenticData?.attributes?.length ||
    fieldMappings?.length ||
    // Also consider flow state data as valid if present
    (flowState && (flowState.field_mappings?.length || flowState.data_import_completed)) ||
    // Or if we have an effective flow and import data but just haven't processed field mappings yet
    (effectiveFlowId && availableDataImports?.length > 0) ||
    // Consider having flows as having potential data
    (flowList && flowList.length > 0)
  );

  // Debug data availability - removed to prevent console spam

  // Enhanced flow detection - more lenient approach
  const isFlowNotFound = (errorMessage?.includes('Flow not found') ||
                        errorMessage?.includes('404')) ||
                        // Only consider flow not found if we have completed loading AND explicitly no flows found AND no effective flow
                        (!isLoading && !isAgenticLoading && !isFlowStateLoading &&
                         flowList !== undefined && flowList.length === 0 &&
                         !effectiveFlowId && !urlFlowId &&
                         hasEffectiveFlow === false);

  const hasSessionData = flowId || flowState;
  const hasUploadedData = agenticData?.attributes && agenticData.attributes.length > 0;

  // Session info object
  const sessionInfo: SessionInfo = {
    flowId,
    availableDataImports,
    selectedDataImportId,
    hasMultipleSessions: availableDataImports.length > 1
  };

  // State object
  const state: AttributeMappingState = {
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    flowId,
    availableDataImports,
    selectedDataImportId,
    isAgenticLoading,
    isFlowStateLoading,
    isAnalyzing,
    agenticError,
    flowStateError,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    flowList,
    // Flow recovery state
    isRecovering,
    recoveryProgress,
    recoveryError,
    recoveredFlowId,
    triggerFlowRecovery,
    // Multi-flow blocking state
    blockingFlows,
    hasMultipleBlockingFlows,
    refreshFlowState
  };

  // Actions object
  const actions: AttributeMappingActions = {
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    refetchCriticalAttributes,
    canContinueToDataCleansing
  };

  // Navigation object
  const navigation: NavigationState = {
    activeTab,
    setActiveTab
  };

  return {
    // Core state
    state,
    actions,
    navigation,

    // Computed state
    isLoading,
    hasError,
    errorMessage,
    hasData,
    isFlowNotFound,
    hasSessionData,
    hasUploadedData,
    sessionInfo,

    // Navigation actions
    handleContinueToDataCleansing,

    // URL params
    urlFlowId
  };
};
