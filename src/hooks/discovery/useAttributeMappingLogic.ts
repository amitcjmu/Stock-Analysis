import { useCallback, useEffect, useMemo, useState } from 'react';
import { useDiscoveryFlowV2, useDiscoveryFlowList } from './useDiscoveryFlowV2';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_CONFIG, apiCall } from '../../config/api';
import { useAttributeMappingFlowDetection } from './useDiscoveryFlowAutoDetection';

export const useAttributeMappingLogic = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  
  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    flowListError,
    hasEffectiveFlow
  } = useAttributeMappingFlowDetection();

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
  
  // Debug logging - moved after fieldMappings declaration
  
  // Extract data with proper type checking and safe access
  const agenticData = useMemo(() => {
    try {
      if (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.attributes) {
        return { attributes: Array.isArray(fieldMappingData.attributes) ? fieldMappingData.attributes : [] };
      }
      return { attributes: [] };
    } catch (error) {
      console.error('Error extracting agenticData:', error);
      return { attributes: [] };
    }
  }, [fieldMappingData]);
  
  // Use field mappings from flow state if available, otherwise fall back to database mappings
  const fieldMappings = useMemo(() => {
    // First try to get mappings from flow state
    if (fieldMappingData && fieldMappingData.mappings) {
      // Convert the mappings object to array format expected by frontend
      const mappingsObj = fieldMappingData.mappings;
      const flowStateMappings = Object.entries(mappingsObj).map(([sourceField, mapping]: [string, any]) => ({
        id: `mapping-${sourceField}`,
        sourceField: mapping.source_column || sourceField,
        targetAttribute: mapping.asset_field || sourceField,
        confidence: (mapping.confidence || 0) / 100, // Convert to 0-1 range
        mapping_type: mapping.match_type || 'ai_suggested',
        sample_values: [],
        status: 'pending', // Ensure mappings are editable
        ai_reasoning: `AI mapped ${mapping.source_column} to ${mapping.asset_field} with ${mapping.confidence}% confidence`,
        is_user_defined: false,
        user_feedback: null,
        validation_method: mapping.pattern_matched || 'semantic_analysis',
        is_validated: false
      }));
      console.log('🔄 Using flow state mappings:', flowStateMappings);
      return flowStateMappings;
    }
    // Fall back to real field mappings from separate API call
    console.log('🔄 Using database mappings:', realFieldMappings || []);
    return realFieldMappings || [];
  }, [fieldMappingData, realFieldMappings]);
  
  // Debug logging - moved here after fieldMappings is declared
  useEffect(() => {
    if (flow) {
      console.log('🔍 Flow data available:', {
        flow_id: flow.flow_id,
        status: flow.status,
        has_field_mapping: !!flow.field_mapping,
        field_mapping_keys: flow.field_mapping ? Object.keys(flow.field_mapping) : [],
        fieldMappings_length: fieldMappings?.length,
        realFieldMappings_length: realFieldMappings?.length
      });
    }
  }, [flow, fieldMappings, realFieldMappings]);
  
  const crewAnalysis = useMemo(() => {
    try {
      // For now, return empty array since analysis is an object, not array of crew analysis
      return [];
    } catch (error) {
      console.error('Error extracting crewAnalysis:', error);
      return [];
    }
  }, []);
  
  const mappingProgress = useMemo(() => {
    try {
      // Use progress from flow state if available
      if (fieldMappingData && fieldMappingData.progress) {
        return {
          total: fieldMappingData.progress.total || 0,
          mapped: fieldMappingData.progress.mapped || 0,
          critical_mapped: fieldMappingData.progress.critical_mapped || 0,
          pending: (fieldMappingData.progress.total || 0) - (fieldMappingData.progress.mapped || 0)
        };
      }
      
      // Otherwise calculate from field mappings
      const total = fieldMappings?.length || 0;
      const approved = fieldMappings?.filter((m: any) => m.status === 'approved').length || 0;
      const suggested = fieldMappings?.filter((m: any) => m.status === 'suggested').length || 0;
      const pending = fieldMappings?.filter((m: any) => m.status === 'pending').length || 0;
      
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
  }, [fieldMappingData, fieldMappings]);
  
  const criticalAttributes = useMemo(() => {
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
  }, [fieldMappingData]);

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
      
      // Find the mapping to get source and target field names
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }
      
      // Use the new field-based API endpoint
      const result = await apiCall(`/data-import/mappings/approve-by-field`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          source_field: mapping.sourceField,
          target_field: mapping.targetAttribute,
          import_id: effectiveFlowId // This should be the import ID
        })
      });
      
      console.log('✅ Mapping approved successfully:', result);
      
      // Refresh both flow data and field mappings
      await Promise.all([refresh(), refetchFieldMappings()]);
      
      // Show success message
      if (typeof window !== 'undefined') {
        console.log(`Mapping approved: ${result.message || 'Mapping approved successfully'}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);
      // Could add error toast notification here
    }
  }, [fieldMappings, effectiveFlowId, refresh, refetchFieldMappings, getAuthHeaders]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);
      
      // Find the mapping to get source and target field names
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }
      
      // Use the new field-based API endpoint
      const result = await apiCall(`/data-import/mappings/reject-by-field`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          source_field: mapping.sourceField,
          target_field: mapping.targetAttribute,
          rejection_reason: rejectionReason || 'User rejected this mapping',
          import_id: effectiveFlowId // This should be the import ID
        })
      });
      
      console.log('✅ Mapping rejected successfully:', result);
      
      // Refresh both flow data and field mappings
      await Promise.all([refresh(), refetchFieldMappings()]);
      
      // Show success message
      if (typeof window !== 'undefined') {
        console.log(`Mapping rejected: ${result.message || 'Mapping rejected successfully'}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to reject mapping:', error);
      // Could add error toast notification here
    }
  }, [fieldMappings, effectiveFlowId, refresh, refetchFieldMappings, getAuthHeaders]);

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

  // Move canContinueToDataCleansing after all data is declared to avoid forward reference
  const canContinueToDataCleansing = useCallback(() => {
    // Check if flow phase is complete
    if (flow?.phases?.attribute_mapping === true) {
      return true;
    }
    
    // Check if sufficient field mappings are approved
    if (Array.isArray(fieldMappings) && fieldMappings.length > 0) {
      const approvedMappings = fieldMappings.filter(m => m.status === 'approved').length;
      const totalMappings = fieldMappings.length;
      const completionPercentage = (approvedMappings / totalMappings) * 100;
      
      // Allow continuation if at least 80% of mappings are approved
      console.log(`🔍 Field mapping completion: ${approvedMappings}/${totalMappings} (${completionPercentage.toFixed(1)}%)`);
      return completionPercentage >= 80;
    }
    
    // Check mapping progress from the stats
    if (mappingProgress?.completion_percentage) {
      console.log(`🔍 Mapping progress completion: ${mappingProgress.completion_percentage}%`);
      return mappingProgress.completion_percentage >= 80;
    }
    
    return false;
  }, [flow, fieldMappings, mappingProgress]);

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
          status: mapping.status === 'suggested' ? 'pending' : mapping.status || 'pending', // Ensure editable
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