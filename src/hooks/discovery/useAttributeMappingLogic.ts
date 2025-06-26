import { useCallback, useEffect, useMemo, useState } from 'react';
import { useDiscoveryFlowV2, useDiscoveryFlowList } from './useDiscoveryFlowV2';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_CONFIG, apiCall } from '../../config/api';

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

  // Get real field mappings from database instead of flow state
  const {
    fieldMappings: realFieldMappings,
    isLoading: isFieldMappingsLoading,
    error: fieldMappingsError,
    refetch: refetchFieldMappings
  } = useRealFieldMappings();

  // Get agent clarifications from database
  const {
    clarifications: agentClarifications,
    isLoading: isClarificationsLoading,
    error: clarificationsError,
    refetch: refetchClarifications
  } = useAgentClarifications();

  // Get field mapping data from unified flow (for legacy compatibility)
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
  
  // Use real field mappings from database instead of flow state
  const fieldMappings = realFieldMappings;
  
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
      // Calculate progress from real field mappings
      const total = realFieldMappings.length;
      const approved = realFieldMappings.filter((m: any) => m.status === 'approved').length;
      const suggested = realFieldMappings.filter((m: any) => m.status === 'suggested').length;
      const pending = realFieldMappings.filter((m: any) => m.status === 'pending').length;
      
      return {
        total: total,
        mapped: approved,
        critical_mapped: approved, // Assume all approved mappings are critical for now
        pending: suggested + pending
      };
    } catch (error) {
      console.error('Error calculating mappingProgress:', error);
      return { total: 0, mapped: 0, critical_mapped: 0, pending: 0 };
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

  // Loading states - include flow list loading and field mappings loading
  const isAgenticLoading = isFlowLoading || isFlowListLoading || isFieldMappingsLoading;
  const isFlowStateLoading = isFlowLoading || isFlowListLoading;
  const isAnalyzing = isFlowLoading || isFieldMappingsLoading;

  // Error states - combine flow, flow list, and field mappings errors
  const agenticError = flowError || flowListError || fieldMappingsError;
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
      
      const result = await apiCall(`/data-import/mappings/${mappingId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      console.log('✅ Mapping approved successfully:', result);
      
      // Refresh both flow data and field mappings
      await Promise.all([refresh(), refetchFieldMappings()]);
      
      // Show success message
      if (typeof window !== 'undefined') {
        // Could add toast notification here
        console.log(`Mapping approved: ${result.message}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);
      // Could add error toast notification here
    }
  }, [refresh, refetchFieldMappings, getAuthHeaders]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);
      
      const result = await apiCall(`/data-import/mappings/${mappingId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          rejection_reason: rejectionReason || 'User rejected this mapping'
        })
      });
      
      console.log('✅ Mapping rejected successfully:', result);
      
      // Refresh both flow data and field mappings
      await Promise.all([refresh(), refetchFieldMappings()]);
      
      // Show success message
      if (typeof window !== 'undefined') {
        // Could add toast notification here
        console.log(`Mapping rejected: ${result.message}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to reject mapping:', error);
      // Could add error toast notification here
    }
  }, [refresh, refetchFieldMappings, getAuthHeaders]);

  const handleMappingChange = useCallback(async (mappingId: string, newTarget: string) => {
    try {
      console.log(`🔄 Changing mapping: ${mappingId} -> ${newTarget}`);
      
      // Find the mapping in the current data
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }
      
      // Call the backend to update the mapping
      const result = await apiCall(`/data-import/mappings/${mappingId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          target_field: newTarget,
          is_user_defined: true,
          status: 'suggested' // Reset to suggested after user change
        })
      });
      
      console.log('✅ Mapping updated successfully:', result);
      
      // Refresh both flow data and field mappings
      await Promise.all([refresh(), refetchFieldMappings()]);
      
    } catch (error) {
      console.error('❌ Failed to update mapping:', error);
    }
  }, [fieldMappings, refresh, refetchFieldMappings, getAuthHeaders]);

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
    console.log('🔄 Refreshing agentic data and field mappings');
    return Promise.all([refresh(), refetchFieldMappings()]);
  }, [refresh, refetchFieldMappings]);

  const canContinueToDataCleansing = useCallback(() => {
    return flow?.phases?.attribute_mapping === true;
  }, [flow]);

  const checkMappingApprovalStatus = useCallback(async (dataImportId: string) => {
    try {
      const result = await apiCall(`/data-import/mappings/approval-status/${dataImportId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
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
    handleMappingChange,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    canContinueToDataCleansing,
    checkMappingApprovalStatus,
    
    // Flow status
    hasActiveFlow: !!flow,
    currentPhase: flow?.next_phase,
    flowProgress: flow?.progress_percentage || 0,
    
    // Agent clarifications
    agentClarifications,
    isClarificationsLoading,
    clarificationsError,
    refetchClarifications
  };
};

// New hook to fetch real field mappings from database
const useRealFieldMappings = () => {
  const { getAuthHeaders } = useAuth();
  const [fieldMappings, setFieldMappings] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchFieldMappings = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CONTEXT_FIELD_MAPPINGS, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      if (result.success && result.mappings) {
        // Transform the database mappings to match frontend interface
        const transformedMappings = result.mappings.map((mapping: any) => ({
          id: mapping.id,
          sourceField: mapping.sourceField,
          targetAttribute: mapping.targetAttribute,
          confidence: mapping.confidence,
          mapping_type: mapping.mapping_type || 'direct',
          sample_values: mapping.sample_values || [],
          status: mapping.status || 'suggested',
          ai_reasoning: mapping.ai_reasoning || `AI suggested mapping based on field similarity`,
          is_user_defined: mapping.is_user_defined || false,
          user_feedback: mapping.user_feedback,
          created_at: mapping.created_at,
          validation_method: mapping.validation_method,
          is_validated: mapping.is_validated || false
        }));
        
        setFieldMappings(transformedMappings);
        console.log(`✅ Loaded ${transformedMappings.length} real field mappings from database`);
      } else {
        console.warn('No field mappings returned from API');
        setFieldMappings([]);
      }
      
    } catch (err: any) {
      console.error('❌ Failed to fetch field mappings:', err);
      setError(err.message);
      setFieldMappings([]);
    } finally {
      setIsLoading(false);
    }
  }, [getAuthHeaders]);

  // Auto-fetch on mount
  useEffect(() => {
    fetchFieldMappings();
  }, [fetchFieldMappings]);

  return {
    fieldMappings,
    isLoading,
    error,
    refetch: fetchFieldMappings
  };
};

// New hook to fetch agent clarifications from database
const useAgentClarifications = () => {
  const { getAuthHeaders } = useAuth();
  const [clarifications, setClarifications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchClarifications = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_CLARIFICATIONS, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      if (result.status === 'success' && result.page_data && result.page_data.pending_questions) {
        setClarifications(result.page_data.pending_questions);
        console.log(`✅ Loaded ${result.page_data.pending_questions.length} agent clarifications`);
      } else {
        console.warn('No agent clarifications returned from API');
        setClarifications([]);
      }
      
    } catch (err: any) {
      console.error('❌ Failed to fetch agent clarifications:', err);
      setError(err.message);
      setClarifications([]);
    } finally {
      setIsLoading(false);
    }
  }, [getAuthHeaders]);

  // Auto-fetch on mount
  useEffect(() => {
    fetchClarifications();
  }, [fetchClarifications]);

  return {
    clarifications,
    isLoading,
    error,
    refetch: fetchClarifications
  };
}; 