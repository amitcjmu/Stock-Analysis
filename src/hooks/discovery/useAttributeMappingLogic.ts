import { useCallback, useEffect, useMemo } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { useLocation, useNavigate } from 'react-router-dom';

export const useAttributeMappingLogic = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  
  // Extract flow ID from URL path
  const urlFlowId = useMemo(() => {
    const match = pathname.match(/\/discovery\/attribute-mapping\/([^\/]+)/);
    return match ? match[1] : null;
  }, [pathname]);

  // Use unified discovery flow with URL flow ID
  const {
    flow,
    isLoading: isFlowLoading,
    error: flowError,
    executePhase,
    refreshFlow,
    flowId,
    hasActiveFlow
  } = useUnifiedDiscoveryFlow(urlFlowId); // Pass URL flow ID directly

  // Get field mapping data from unified flow
  const fieldMappingData = flow?.field_mapping;
  
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
  const sessionId = urlFlowId;
  const availableDataImports: any[] = []; // TODO: Implement data import management
  const selectedDataImportId = null;

  // Loading states
  const isAgenticLoading = isFlowLoading;
  const isFlowStateLoading = isFlowLoading;
  const isAnalyzing = flow?.isExecutingPhase || false;

  // Error states
  const agenticError = flowError;
  const flowStateError = flowError;

  // Action handlers
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      console.log('🔄 Triggering field mapping crew execution');
      await executePhase('field_mapping', {}, {});
    } catch (error) {
      console.error('❌ Failed to trigger field mapping crew:', error);
    }
  }, [executePhase]);

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
    return flow?.isPhaseComplete('field_mapping') && flow?.canProceedToPhase('data_cleansing');
  }, [flow]);

  return {
    // Data
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    
    // Flow state
    flow,
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
    hasActiveFlow,
    currentPhase: flow?.current_phase || flow?.currentFlow?.current_phase,
    flowProgress: flow?.progress_percentage || flow?.currentFlow?.progress_percentage || 0
  };
}; 