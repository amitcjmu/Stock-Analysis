import { useCallback, useEffect, useMemo, useState } from 'react';
import { useUnifiedDiscoveryFlow } from '../useUnifiedDiscoveryFlow';
import { useDiscoveryFlowList, useAttributeMappingFlowDetection } from './useDiscoveryFlowAutoDetection';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_CONFIG, apiCall } from '../../config/api';

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

  // Use unified discovery flow with effective flow ID
  const {
    flowState: flow,
    isLoading: isFlowLoading,
    error: flowError,
    executeFlowPhase: updatePhase,
    refreshFlow: refresh
  } = useUnifiedDiscoveryFlow(effectiveFlowId);

  // Legacy hooks removed - these endpoints don't exist
  // Field mappings come from flow state instead
  const realFieldMappings = null;
  const isFieldMappingsLoading = false;
  const fieldMappingsError = null;
  const refetchFieldMappings = () => Promise.resolve();
  
  const agentClarifications = [];
  const isClarificationsLoading = false;
  const clarificationsError = null;
  const refetchClarifications = () => Promise.resolve();

  // Get field mapping data from unified flow (for legacy compatibility)
  // Backend returns 'field_mappings' (with 's'), not 'field_mapping'
  const fieldMappingData = flow?.field_mappings || flow?.field_mapping;
  
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
    if (fieldMappingData) {
      // Handle direct field mappings structure from backend
      if (typeof fieldMappingData === 'object' && !fieldMappingData.mappings) {
        // Backend returns field_mappings directly as object with confidence_scores
        const mappingsObj = { ...fieldMappingData };
        delete mappingsObj.confidence_scores; // Remove confidence_scores from main object
        
        const flowStateMappings = Object.entries(mappingsObj)
          .filter(([key, value]) => key !== 'confidence_scores')
          .map(([sourceField, targetField]: [string, any]) => ({
            id: `mapping-${sourceField}`,
            sourceField: sourceField === 'None' ? 'Unknown Field' : sourceField,
            targetAttribute: typeof targetField === 'string' ? targetField : String(targetField),
            confidence: fieldMappingData.confidence_scores?.[sourceField] || 0.5,
            mapping_type: 'ai_suggested',
            sample_values: [],
            status: 'pending', // Ensure mappings are editable
            ai_reasoning: `AI suggested mapping to ${targetField}`,
            is_user_defined: false,
            user_feedback: null,
            validation_method: 'semantic_analysis',
            is_validated: false
          }));
        console.log('🔄 Using direct field mappings:', flowStateMappings);
        return flowStateMappings;
      }
      
      // Handle structured mappings format
      if (fieldMappingData.mappings) {
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
        data_import_id: flow.data_import_id,
        status: flow.status,
        has_field_mapping: !!flow.field_mapping,
        has_field_mappings: !!flow.field_mappings,
        field_mapping_keys: flow.field_mapping ? Object.keys(flow.field_mapping) : [],
        field_mappings_keys: flow.field_mappings ? Object.keys(flow.field_mappings) : [],
        fieldMappings_length: fieldMappings?.length,
        realFieldMappings_length: realFieldMappings?.length,
        progress: flow.progress_percentage,
        current_phase: flow.current_phase
      });
      
      // Log the full flow object to see all properties
      console.log('📋 Full flow object:', flow);
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

  // Flow information
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
      console.log('🔄 Resuming CrewAI Flow from field mapping approval');
      if (flow?.flow_id) {
        // Use the correct resume endpoint for paused flows
        const result = await apiCall(`/discovery/flow/${flow.flow_id}/resume`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify({
            user_approval: true,
            approval_timestamp: new Date().toISOString(),
            notes: 'User triggered field mapping continuation'
          })
        });
        console.log('✅ CrewAI Flow resumed successfully:', result);
        
        // Refresh the flow data to get updated state
        await refresh();
      }
    } catch (error) {
      console.error('❌ Failed to resume CrewAI Flow:', error);
    }
  }, [flow, refresh, getAuthHeaders]);

  const handleApproveMapping = useCallback(async (mappingId: string) => {
    try {
      console.log(`✅ Approving mapping: ${mappingId}`);
      
      // Find the mapping
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }
      
      // For discovery flow field mappings, we don't approve individual mappings
      // The approval happens when the user clicks "Continue to Data Cleansing"
      // So we just update the local state to show it's approved
      console.log('ℹ️ Field mapping approval is handled when continuing to data cleansing phase');
      
      // Update local state to show the mapping as approved (visual feedback only)
      // The actual approval happens when resuming the flow
      if (typeof window !== 'undefined' && (window as any).showInfoToast) {
        (window as any).showInfoToast('Field mapping marked for approval. Click "Continue to Data Cleansing" to apply all mappings.');
      }
      
      // You could update local state here if needed for visual feedback
      // For example, marking the mapping with a checkmark
      
    } catch (error) {
      console.error('❌ Failed to process mapping approval:', error);
      
      // Show error toast if available
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to process mapping approval';
        (window as any).showErrorToast(errorMessage);
      }
    }
  }, [fieldMappings]);

  const handleRejectMapping = useCallback(async (mappingId: string, rejectionReason?: string) => {
    try {
      console.log(`❌ Rejecting mapping: ${mappingId}`);
      
      // For discovery flow field mappings, we don't reject individual mappings
      // The user should edit the mapping instead
      console.log('ℹ️ To change a field mapping, please edit it directly');
      
      // Show info message
      if (typeof window !== 'undefined' && (window as any).showInfoToast) {
        (window as any).showInfoToast('To change a field mapping, please edit it directly in the dropdown.');
      }
      
    } catch (error) {
      console.error('❌ Error in reject handler:', error);
    }
  }, []);

  const handleMappingChange = useCallback(async (mappingId: string, newTarget: string) => {
    try {
      console.log(`🔄 Changing mapping: ${mappingId} -> ${newTarget}`);
      
      // Find the mapping in the current data
      const mapping = fieldMappings.find((m: any) => m.id === mappingId);
      if (!mapping) {
        console.error('❌ Mapping not found:', mappingId);
        return;
      }
      
      // For discovery flow, field mapping changes are stored locally
      // and applied when the user clicks "Continue to Data Cleansing"
      console.log('ℹ️ Field mapping change will be applied when continuing to data cleansing phase');
      
      // Update local state to reflect the change
      // The parent component should handle this state update
      // For now, just show feedback
      if (typeof window !== 'undefined' && (window as any).showInfoToast) {
        (window as any).showInfoToast(`Field mapping updated: ${mapping.sourceField} → ${newTarget}`);
      }
      
    } catch (error) {
      console.error('❌ Failed to update mapping:', error);
      
      // Show error toast if available
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update mapping';
        (window as any).showErrorToast(errorMessage);
      }
      
      // Re-throw for component error handling
      throw error;
    }
  }, [fieldMappings]);

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
    flowId: flow?.flow_id || effectiveFlowId,
    dataImportId: flow?.data_import_id || effectiveFlowId, // Add data_import_id
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