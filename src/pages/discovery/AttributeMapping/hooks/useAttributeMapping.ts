import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAttributeMappingLogic } from '../../../../hooks/discovery/useAttributeMappingLogic';
import { useAttributeMappingNavigation } from '../../../../hooks/discovery/useAttributeMappingNavigation';
import type { AttributeMappingState, AttributeMappingActions, NavigationState, SessionInfo } from '../types';

export const useAttributeMapping = () => {
  // Navigation state
  const [activeTab, setActiveTab] = useState<'mappings' | 'data' | 'critical'>('critical');
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
    canContinueToDataCleansing,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
  } = useAttributeMappingLogic();

  // Navigation logic
  const { handleContinueToDataCleansing } = useAttributeMappingNavigation(
    flowState,
    mappingProgress
  );

  // Computed state
  const isLoading = (isFlowStateLoading && !flowState) || isAgenticLoading;
  const hasError = !!(flowStateError || agenticError);
  const errorMessage = flowStateError?.message || agenticError?.message;
  const hasData = !!(agenticData?.attributes?.length || fieldMappings?.length);
  const isFlowNotFound = errorMessage?.includes('Flow not found') || errorMessage?.includes('404');
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
    flowList
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