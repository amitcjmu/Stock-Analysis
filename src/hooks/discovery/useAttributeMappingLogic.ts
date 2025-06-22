import { useCallback } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useAttributeMappingLogic = (urlSessionId?: string) => {
  // Use the unified discovery flow
  const {
    flowState,
    isLoading,
    error,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    executeFlowPhase,
    isExecutingPhase,
    refreshFlow
  } = useUnifiedDiscoveryFlow();

  // Get field mapping data from unified flow
  const fieldMappingData = getPhaseData('field_mapping');
  
  // Extract data with proper type checking
  const agenticData = (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.attributes) 
    ? { attributes: fieldMappingData.attributes } 
    : { attributes: [] };
  
  const fieldMappings = (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.mappings) 
    ? fieldMappingData.mappings 
    : [];
  
  const crewAnalysis = (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.analysis) 
    ? fieldMappingData.analysis 
    : {};
  
  const mappingProgress = (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.progress) 
    ? fieldMappingData.progress 
    : { total: 0, mapped: 0, critical_mapped: 0 };
  
  const criticalAttributes = (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.critical_attributes) 
    ? fieldMappingData.critical_attributes 
    : [];

  // Session and flow information
  const sessionId = flowState?.session_id || urlSessionId;
  const flowId = flowState?.flow_id;
  const availableDataImports: any[] = []; // TODO: Implement data import management
  const selectedDataImportId = null;

  // Loading states
  const isAgenticLoading = isLoading;
  const isFlowStateLoading = isLoading;
  const isAnalyzing = isExecutingPhase;

  // Error states
  const agenticError = error;
  const flowStateError = error;

  // Action handlers
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    await executeFlowPhase('field_mapping');
  }, [executeFlowPhase]);

  const refetchAgentic = useCallback(async () => {
    await refreshFlow();
  }, [refreshFlow]);

  const canContinueToDataCleansing = useCallback(() => {
    return canProceedToPhase('data_cleansing');
  }, [canProceedToPhase]);

  // Placeholder handlers for UI interactions
  const handleApproveMapping = useCallback(() => {
    // TODO: Implement mapping approval logic
    console.log('Mapping approved');
  }, []);

  const handleRejectMapping = useCallback(() => {
    // TODO: Implement mapping rejection logic
    console.log('Mapping rejected');
  }, []);

  const handleAttributeUpdate = useCallback(() => {
    // TODO: Implement attribute update logic
    console.log('Attribute updated');
  }, []);

  const handleDataImportSelection = useCallback(() => {
    // TODO: Implement data import selection logic
    console.log('Data import selected');
  }, []);

  return {
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    sessionId,
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
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    canContinueToDataCleansing,
  };
}; 