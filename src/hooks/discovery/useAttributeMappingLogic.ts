import { useCallback, useEffect, useMemo } from 'react';
import { useDiscoveryFlowV2, useDiscoveryFlowList } from './useDiscoveryFlowV2';
import { useLocation, useNavigate } from 'react-router-dom';

export const useAttributeMappingLogic = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  
  // Extract flow ID from URL path if provided
  const urlFlowId = useMemo(() => {
    const match = pathname.match(/\/discovery\/attribute-mapping\/([^\/]+)/);
    return match ? match[1] : null;
  }, [pathname]);

  // Get list of active flows for context-based auto-detection
  const { data: flowList, isLoading: isFlowListLoading, error: flowListError } = useDiscoveryFlowList();

  // Auto-detect the most relevant flow for attribute mapping
  const autoDetectedFlowId = useMemo(() => {
    if (!flowList || flowList.length === 0) return null;
    
    // Priority 1: Flow currently in attribute_mapping phase
    const attributeMappingFlow = flowList.find((flow: any) => 
      flow.current_phase === 'attribute_mapping' || 
      flow.next_phase === 'attribute_mapping'
    );
    if (attributeMappingFlow) return attributeMappingFlow.flow_id;
    
    // Priority 2: Flow with attribute_mapping completed but has field mapping data
    const completedAttributeMappingFlow = flowList.find((flow: any) => 
      flow.phases?.attribute_mapping === true && 
      flow.status === 'running'
    );
    if (completedAttributeMappingFlow) return completedAttributeMappingFlow.flow_id;
    
    // Priority 3: Any running flow (might have processed data)
    const runningFlow = flowList.find((flow: any) => 
      flow.status === 'running' || flow.status === 'active'
    );
    if (runningFlow) return runningFlow.flow_id;
    
    // Priority 4: Most recent flow (even if completed)
    const sortedFlows = [...flowList].sort((a: any, b: any) => 
      new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()
    );
    return sortedFlows[0]?.flow_id || null;
  }, [flowList]);

  // Use URL flow ID if provided, otherwise use auto-detected flow ID
  const effectiveFlowId = urlFlowId || autoDetectedFlowId;

  // Use V2 discovery flow with effective flow ID
  const {
    flow,
    isLoading: isFlowLoading,
    error: flowError,
    updatePhase,
    refresh
  } = useDiscoveryFlowV2(effectiveFlowId);

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
  const sessionId = effectiveFlowId;
  const availableDataImports = flowList || [];
  const selectedDataImportId = effectiveFlowId;

  // Loading states - include flow list loading
  const isAgenticLoading = isFlowLoading || isFlowListLoading;
  const isFlowStateLoading = isFlowLoading || isFlowListLoading;
  const isAnalyzing = isFlowLoading;

  // Error states - combine flow and flow list errors
  const agenticError = flowError || flowListError;
  const flowStateError = flowError || flowListError;

  // Action handlers
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      console.log('🔄 Triggering field mapping crew execution');
      if (flow?.flow_id) {
        await updatePhase('field_mapping', { trigger_crew: true });
      }
    } catch (error) {
      console.error('❌ Failed to trigger field mapping crew:', error);
    }
  }, [flow, updatePhase]);

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
      // Navigate to the selected flow
      navigate(`/discovery/attribute-mapping/${importId}`);
    } catch (error) {
      console.error('❌ Failed to select data import:', error);
    }
  }, [navigate]);

  const refetchAgentic = useCallback(() => {
    console.log('🔄 Refreshing agentic data');
    return refresh();
  }, [refresh]);

  const canContinueToDataCleansing = useCallback(() => {
    return flow?.phases?.attribute_mapping === true;
  }, [flow]);

  return {
    // Data
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    
    // Flow state
    flowState: flow, // Keep backward compatibility
    flow,
    sessionId,
    flowId: flow?.flow_id,
    availableDataImports,
    selectedDataImportId,
    
    // Auto-detection info
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    
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
    hasActiveFlow: !!flow,
    currentPhase: flow?.next_phase,
    flowProgress: flow?.progress_percentage || 0
  };
}; 