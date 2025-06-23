import { useCallback, useEffect } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';

export const useAttributeMappingLogic = (urlSessionId?: string) => {
  // Use the unified discovery flow
  const {
    flowState,
    currentFlow,
    isLoading,
    error,
    getPhaseData,
    isPhaseComplete,
    canProceedToPhase,
    executeFlowPhase,
    isExecutingPhase,
    refreshFlow,
    sessionId: detectedSessionId,
    hasCurrentFlow,
    setSessionId
  } = useUnifiedDiscoveryFlow();

  // Handle URL session ID vs auto-detected session ID
  useEffect(() => {
    if (urlSessionId && urlSessionId !== detectedSessionId) {
      console.log(`🔄 Setting session ID from URL: ${urlSessionId}`);
      setSessionId(urlSessionId);
    }
  }, [urlSessionId, detectedSessionId, setSessionId]);

  // Determine the active session ID
  const activeSessionId = urlSessionId || detectedSessionId;

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
  const sessionId = activeSessionId;
  const flowId = flowState?.flow_id || currentFlow?.flow_id;
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
    try {
      console.log('🔄 Triggering field mapping crew execution');
      await executeFlowPhase('field_mapping', {}, {});
    } catch (error) {
      console.error('❌ Failed to trigger field mapping crew:', error);
    }
  }, [executeFlowPhase]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`✅ Approving mapping: ${mappingId}`);
      // TODO: Implement mapping approval logic
    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);
    }
  }, []);

  const handleRejectMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);
      // TODO: Implement mapping rejection logic
    } catch (error) {
      console.error('❌ Failed to reject mapping:', error);
    }
  }, []);

  const handleAttributeUpdate = useCallback(async (attributeId: string, updates: any) => {
    try {
      console.log(`🔄 Updating attribute: ${attributeId}`, updates);
      // TODO: Implement attribute update logic
    } catch (error) {
      console.error('❌ Failed to update attribute:', error);
    }
  }, []);

  const handleDataImportSelection = useCallback(async (importId: string) => {
    try {
      console.log(`🔄 Selecting data import: ${importId}`);
      // TODO: Implement data import selection logic
    } catch (error) {
      console.error('❌ Failed to select data import:', error);
    }
  }, []);

  const refetchAgentic = useCallback(() => {
    console.log('🔄 Refreshing agentic data');
    return refreshFlow();
  }, [refreshFlow]);

  const canContinueToDataCleansing = useCallback(() => {
    return isPhaseComplete('field_mapping') && canProceedToPhase('data_cleansing');
  }, [isPhaseComplete, canProceedToPhase]);

  return {
    // Data
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    
    // Flow state
    flowState,
    sessionId,
    flowId,
    availableDataImports,
    selectedDataImportId,
    
    // Loading states
    isAgenticLoading,
    isFlowStateLoading,
    isAnalyzing,
    
    // Error states
    agenticError,
    flowStateError,
    
    // Action handlers
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    canContinueToDataCleansing,
    
    // Flow status
    hasCurrentFlow,
    currentPhase: flowState?.current_phase || currentFlow?.current_phase,
    flowProgress: flowState?.progress_percentage || currentFlow?.progress_percentage || 0
  };
}; 