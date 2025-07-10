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

  // Enhanced loading state - consider more loading scenarios
  const isLoading = (isFlowStateLoading && !flowState) || 
                   isAgenticLoading || 
                   // Also loading if we have an effective flow but no data yet and no errors
                   (effectiveFlowId && !hasError && !agenticData && !fieldMappings?.length);
  const hasError = !!(flowStateError || agenticError);
  const errorMessage = flowStateError?.message || agenticError?.message;
  // Enhanced data availability check - be more comprehensive about what constitutes "data"
  const hasData = !!(
    agenticData?.attributes?.length || 
    fieldMappings?.length ||
    // Also consider flow state data as valid if present
    (flowState && (flowState.field_mappings?.length || flowState.data_import_completed)) ||
    // Or if we have an effective flow and import data but just haven't processed field mappings yet
    (effectiveFlowId && availableDataImports?.length > 0)
  );
  
  // Debug data availability
  console.log('🔍 AttributeMapping Data Check:', {
    hasData,
    agenticDataAttributes: agenticData?.attributes?.length || 0,
    fieldMappingsLength: fieldMappings?.length || 0,
    flowStateFieldMappings: flowState?.field_mappings?.length || 0,
    flowStateDataImportCompleted: flowState?.data_import_completed,
    availableDataImportsLength: availableDataImports?.length || 0,
    isLoading,
    isAgenticLoading,
    hasError,
    errorMessage,
    effectiveFlowId,
    hasEffectiveFlow
  });
  
  // Enhanced flow detection - more lenient approach
  const isFlowNotFound = errorMessage?.includes('Flow not found') || 
                        errorMessage?.includes('404') ||
                        // Only consider flow not found if we have no effective flow AND no loading states AND explicitly no flows
                        (!effectiveFlowId && !isLoading && !isAgenticLoading && flowList && flowList.length === 0 && !urlFlowId);
  
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