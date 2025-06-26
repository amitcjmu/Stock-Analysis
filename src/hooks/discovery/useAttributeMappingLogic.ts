import { useCallback, useEffect, useMemo } from 'react';
import { useDiscoveryFlowV2, useDiscoveryFlowList } from './useDiscoveryFlowV2';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_CONFIG } from '../../config/api';

export const useAttributeMappingLogic = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  
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
  
  // Extract data with proper type checking and safe access
  const agenticData = (() => {
    try {
      if (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.attributes) {
        return { attributes: Array.isArray(fieldMappingData.attributes) ? fieldMappingData.attributes : [] };
      }
      return { attributes: [] };
    } catch (error) {
      console.error('Error extracting agenticData:', error);
      return { attributes: [] };
    }
  })();
  
  const fieldMappings = (() => {
    try {
      if (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.mappings && typeof fieldMappingData.mappings === 'object') {
        return Object.entries(fieldMappingData.mappings).map(([targetField, mapping]: [string, any], index: number) => ({
          id: `mapping_${index}`, // Add required id field
          sourceField: mapping?.source_column || targetField,
          targetAttribute: mapping?.asset_field || targetField,
          confidence: Math.min(1, Math.max(0, (mapping?.confidence || 0) / 100)), // Normalize to 0-1 range
          mapping_type: mapping?.match_type || 'direct',
          sample_values: mapping?.sample_values || [], // Ensure it's always an array
          status: 'pending',
          ai_reasoning: mapping?.reasoning || `AI suggested mapping based on field similarity`
        }));
      }
      return [];
    } catch (error) {
      console.error('Error extracting fieldMappings:', error);
      return [];
    }
  })();
  
  const crewAnalysis = (() => {
    try {
      // For now, return empty array since analysis is an object, not array of crew analysis
      return [];
    } catch (error) {
      console.error('Error extracting crewAnalysis:', error);
      return [];
    }
  })();
  
  const mappingProgress = (() => {
    try {
      if (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.progress && typeof fieldMappingData.progress === 'object') {
        return {
          total: fieldMappingData.progress.total || 0,
          mapped: fieldMappingData.progress.mapped || 0,
          critical_mapped: fieldMappingData.progress.critical_mapped || 0
        };
      }
      return { total: 0, mapped: 0, critical_mapped: 0 };
    } catch (error) {
      console.error('Error extracting mappingProgress:', error);
      return { total: 0, mapped: 0, critical_mapped: 0 };
    }
  })();
  
  const criticalAttributes = (() => {
    try {
      if (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.critical_attributes && typeof fieldMappingData.critical_attributes === 'object') {
        return Object.entries(fieldMappingData.critical_attributes).map(([name, mapping]: [string, any]) => ({
          name,
          description: `${mapping?.asset_field || name} mapped from ${mapping?.source_column || 'unknown'}`,
          category: 'technical', // Default category
          required: true,
          status: (mapping?.confidence || 0) > 60 ? 'mapped' : 'partially_mapped',
          mapped_to: mapping?.source_column || name,
          source_field: mapping?.source_column || name,
          confidence: Math.min(1, Math.max(0, (mapping?.confidence || 0) / 100)), // Convert to 0-1 range safely
          quality_score: mapping?.confidence || 0,
          completeness_percentage: 100,
          mapping_type: 'direct',
          business_impact: (mapping?.confidence || 0) > 60 ? 'low' : 'medium',
          migration_critical: true
        }));
      }
      return [];
    } catch (error) {
      console.error('Error extracting criticalAttributes:', error);
      return [];
    }
  })();

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
      console.log('🔄 Resuming CrewAI Flow at attribute_mapping phase');
      if (flow?.flow_id) {
        // Use the new CrewAI Flow resume functionality instead of just marking phase complete
        const unifiedDiscoveryService = (await import('../../services/discoveryUnifiedService')).default;
        const result = await unifiedDiscoveryService.resumeFlowAtPhase(
          flow.flow_id, 
          'attribute_mapping',
          { trigger: 'user_requested', phase: 'attribute_mapping' }
        );
        console.log('✅ CrewAI Flow resumed at attribute_mapping phase:', result);
        
        // Refresh the flow data to get updated state
        await refresh();
      }
    } catch (error) {
      console.error('❌ Failed to resume CrewAI Flow at attribute_mapping phase:', error);
    }
  }, [flow, refresh]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`✅ Approving mapping: ${mappingId}`);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/data-import/field-mapping/mappings/${mappingId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to approve mapping');
      }
      
      const result = await response.json();
      console.log('✅ Mapping approved successfully:', result);
      
      // Refresh the data to show updated status
      await refresh();
      
      // Show success message
      if (typeof window !== 'undefined') {
        // Could add toast notification here
        console.log(`Mapping approved: ${result.message}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);
      // Could add error toast notification here
    }
  }, [refresh, getAuthHeaders]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/data-import/field-mapping/mappings/${mappingId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          rejection_reason: rejectionReason || 'User rejected this mapping'
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reject mapping');
      }
      
      const result = await response.json();
      console.log('✅ Mapping rejected successfully:', result);
      
      // Refresh the data to show updated status
      await refresh();
      
      // Show success message
      if (typeof window !== 'undefined') {
        // Could add toast notification here
        console.log(`Mapping rejected: ${result.message}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to reject mapping:', error);
      // Could add error toast notification here
    }
  }, [refresh, getAuthHeaders]);

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

  const checkMappingApprovalStatus = useCallback(async (dataImportId: string) => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/data-import/field-mapping/mappings/approval-status/${dataImportId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to check approval status');
      }
      
      const result = await response.json();
      return result;
      
    } catch (error) {
      console.error('❌ Failed to check mapping approval status:', error);
      return null;
    }
  }, [getAuthHeaders]);

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
    checkMappingApprovalStatus,
    
    // Flow status
    hasActiveFlow: !!flow,
    currentPhase: flow?.next_phase,
    flowProgress: flow?.progress_percentage || 0
  };
}; 