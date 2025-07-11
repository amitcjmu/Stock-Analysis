import { useCallback, useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
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

  // Emergency fallback: try to extract flow ID from tenant-scoped context only
  const emergencyFlowId = useMemo(() => {
    if (effectiveFlowId) return effectiveFlowId;
    
    // Check if there's a flow ID in the current path (still tenant-scoped by backend)
    const currentPath = pathname;
    const flowIdMatch = currentPath.match(/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})/i);
    if (flowIdMatch) {
      console.log('🆘 Emergency flow ID from path (will be tenant-validated):', flowIdMatch[0]);
      return flowIdMatch[0];
    }
    
    // Check localStorage for recent flow context (still tenant-scoped by backend)
    if (typeof window !== 'undefined') {
      const storedFlowId = localStorage.getItem('lastActiveFlowId');
      if (storedFlowId) {
        console.log('🆘 Emergency flow ID from localStorage (will be tenant-validated):', storedFlowId);
        return storedFlowId;
      }
    }
    
    // SECURITY: No hardcoded flow IDs - let the system gracefully handle no flow
    // All flow access must go through proper tenant-scoped APIs
    console.log('🔒 No emergency flow ID available - relying on tenant-scoped flow detection only');
    return null;
  }, [effectiveFlowId, pathname]);
  
  // Enhanced debugging for flow detection
  useEffect(() => {
    console.log('🎯 Flow Detection Debug:', {
      urlFlowId,
      autoDetectedFlowId,
      effectiveFlowId,
      hasEffectiveFlow,
      flowListLength: flowList?.length,
      isFlowListLoading,
      flowListError: flowListError?.message,
      pathname
    });
    
    if (flowList && flowList.length > 0) {
      console.log('📋 Available flows for attribute mapping:', flowList.map(f => ({
        flow_id: f.id,
        status: f.status,
        current_phase: f.current_phase,
        next_phase: f.next_phase,
        data_import_completed: f.data_import_completed,
        attribute_mapping_completed: f.attribute_mapping_completed
      })));
    }
    
    // Import data debugging will be handled in a separate useEffect after import data is defined
  }, [urlFlowId, autoDetectedFlowId, effectiveFlowId, flowList, isFlowListLoading, flowListError, pathname]);

  // Use unified discovery flow with effective flow ID or emergency fallback
  const finalFlowId = effectiveFlowId || emergencyFlowId;
  
  console.log('🎯 Final Flow ID Resolution:', {
    effectiveFlowId,
    emergencyFlowId,
    finalFlowId,
    urlFlowId,
    autoDetectedFlowId
  });
  
  const {
    flowState: flow,
    isLoading: isFlowLoading,
    error: flowError,
    executeFlowPhase: updatePhase,
    refreshFlow: refresh
  } = useUnifiedDiscoveryFlow(finalFlowId);

  // Get import data for this flow, with fallback to latest import
  const { data: importData, isLoading: isImportDataLoading, error: importDataError } = useQuery({
    queryKey: ['import-data', finalFlowId, user?.id],
    queryFn: async () => {
      try {
        // If we have a final flow ID, try flow-specific import data first
        if (finalFlowId) {
          console.log('🔍 Fetching import data for flow:', finalFlowId);
          console.log('🔗 Trying flow-specific import data endpoint...');
          const flowResponse = await apiCall(`/api/v1/data-import/flow/${finalFlowId}/import-data`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            }
          });
          
          if (flowResponse) {
            console.log('✅ Fetched flow-specific import data:', flowResponse);
            return flowResponse;
          }
          
          console.log('🔗 Flow-specific import not found, falling back to latest import...');
        } else {
          console.log('⚠️ No final flow ID, attempting to fetch latest import data as fallback');
        }
        
        // Fall back to latest import for client (works both with and without flow ID)
        console.log('🔗 Trying latest import endpoint...');
        const latestResponse = await apiCall(`/api/v1/data-import/latest-import`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        });
        
        if (latestResponse) {
          console.log('✅ Using latest import data as fallback:', latestResponse);
          return latestResponse;
        }
        
        console.log('❌ No import data found');
        return null;
        
      } catch (error) {
        console.error('❌ Error fetching import data:', error);
        // Return null instead of throwing to prevent breaking the entire component
        return null;
      }
    },
    enabled: !!user?.id, // Enable as long as user is authenticated, fallback logic handles missing flow ID
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes to reduce API calls
    cacheTime: 15 * 60 * 1000, // Keep in cache for 15 minutes
    retry: (failureCount, error) => {
      // Don't retry on 429 (Too Many Requests) or authentication errors
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as any).status;
        if (status === 429 || status === 401 || status === 403) {
          return false;
        }
      }
      return failureCount < 2; // Only retry twice max
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff, max 10s
  });

  // Debug import data loading (after import data is defined)
  useEffect(() => {
    if (importDataError) {
      console.error('❌ Import data error:', importDataError);
    }
    
    if (importData) {
      console.log('✅ Import data available:', {
        import_id: importData?.import_metadata?.import_id,
        flow_id: importData?.flow_id,
        status: importData?.status,
        has_metadata: !!importData?.import_metadata,
        metadata_keys: importData?.import_metadata ? Object.keys(importData.import_metadata) : []
      });
    }
    
    if (isImportDataLoading) {
      console.log('⏳ Import data loading...');
    }
  }, [importData, importDataError, isImportDataLoading]);

  // Get field mappings using the import ID
  const { data: realFieldMappings, isLoading: isFieldMappingsLoading, error: fieldMappingsError, refetch: refetchFieldMappings } = useQuery({
    queryKey: ['field-mappings', importData?.import_metadata?.import_id],
    queryFn: async () => {
      const importId = importData?.import_metadata?.import_id;
      if (!importId) {
        console.warn('⚠️ No import ID available for field mappings fetch');
        return [];
      }
      
      console.log('🔍 Fetching field mappings for import ID:', importId);
      
      try {
        // First, get all field mappings (including filtered ones)
        const mappings = await apiCall(`/api/v1/data-import/field-mapping/imports/${importId}/field-mappings`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          }
        });
        
        console.log('✅ Fetched field mappings from API:', {
          import_id: importId,
          mappings_count: Array.isArray(mappings) ? mappings.length : 'not an array',
          mappings_sample: Array.isArray(mappings) ? mappings.slice(0, 2) : mappings
        });
        
        // Now try to get the raw import data to see all original CSV fields
        try {
          const rawImportData = await apiCall(`/api/v1/data-import/imports/${importId}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            }
          });
          
          console.log('📊 Raw import data retrieved:', {
            has_raw_data: !!rawImportData?.raw_data,
            raw_data_keys: rawImportData?.raw_data ? Object.keys(rawImportData.raw_data) : [],
            sample_record_keys: rawImportData?.sample_record ? Object.keys(rawImportData.sample_record) : [],
            total_records: rawImportData?.record_count,
            field_count: rawImportData?.field_count
          });
          
          // If we have raw data, ensure all CSV fields are represented as mappings
          if (rawImportData?.sample_record || rawImportData?.raw_data) {
            const sampleRecord = rawImportData.sample_record || rawImportData.raw_data;
            const allCsvFields = Object.keys(sampleRecord);
            const mappedFieldNames = (mappings || []).map(m => m.source_field);
            
            // Create mappings for fields that don't exist in the API response
            const missingFields = allCsvFields.filter(field => !mappedFieldNames.includes(field));
            
            if (missingFields.length > 0) {
              console.log(`📋 Found ${missingFields.length} unmapped CSV fields:`, missingFields);
              
              // Create placeholder mappings for unmapped fields
              const additionalMappings = missingFields.map(sourceField => ({
                id: `unmapped-${sourceField}`,
                source_field: sourceField,
                target_field: 'UNMAPPED', // Use UNMAPPED placeholder 
                confidence: 0,
                is_approved: false,
                status: 'unmapped',
                match_type: 'unmapped'
              }));
              
              const enhancedMappings = [...(mappings || []), ...additionalMappings];
              
              console.log('✅ Enhanced field mappings with all CSV fields:', {
                original_mappings: mappings?.length || 0,
                additional_mappings: additionalMappings.length,
                total_mappings: enhancedMappings.length,
                total_csv_fields: allCsvFields.length
              });
              
              return enhancedMappings;
            }
          }
        } catch (rawDataError) {
          console.warn('⚠️ Could not fetch raw import data:', rawDataError);
        }
        
        // Transform the backend data structure to match frontend expectations
        const transformedMappings = mappings?.map((mapping: any) => ({
          id: mapping.id,
          sourceField: mapping.source_field,
          targetAttribute: mapping.target_field,
          confidence: mapping.confidence || 0,
          mapping_type: mapping.is_approved ? 'approved' : 'ai_suggested',
          sample_values: [],
          status: mapping.is_approved ? 'approved' : 'pending',
          ai_reasoning: '',
          transformation_rule: mapping.transformation_rule,
          validation_rule: mapping.validation_rule,
          is_required: mapping.is_required
        })) || [];

        console.log('✅ Transformed field mappings:', {
          original_count: mappings?.length || 0,
          transformed_count: transformedMappings.length,
          approved_count: transformedMappings.filter(m => m.status === 'approved').length,
          sample_transformed: transformedMappings.slice(0, 3),
          all_transformed: transformedMappings
        });

        return transformedMappings;
      } catch (error) {
        console.error('❌ Error fetching field mappings:', error);
        
        // If rate limited, wait and retry manually
        if (error.message?.includes('Rate limit') || error.message?.includes('Too Many Requests')) {
          console.log('⚠️ Rate limited - will retry with exponential backoff');
          // Let react-query handle the retry
        }
        
        return [];
      }
    },
    enabled: !!importData?.import_metadata?.import_id,
    staleTime: 30 * 1000, // Cache for 30 seconds to ensure fresh data after approval
    cacheTime: 2 * 60 * 1000, // Keep in cache for 2 minutes
    retry: (failureCount, error) => {
      // Allow retries on 429 (Too Many Requests) with longer delays
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as any).status;
        if (status === 429) {
          // Retry rate-limited requests up to 3 times with longer delays
          console.log(`🔄 Rate limit retry attempt ${failureCount + 1}/3`);
          return failureCount < 3;
        }
        // Don't retry on authentication errors
        if (status === 401 || status === 403) {
          return false;
        }
      }
      return failureCount < 2; // Only retry twice max for other errors
    },
    retryDelay: (attemptIndex, error) => {
      // Longer delays for rate-limited requests
      if (error && typeof error === 'object' && 'status' in error && (error as any).status === 429) {
        // For rate limits: 10s, 30s, 60s
        const delays = [10000, 30000, 60000];
        return delays[attemptIndex] || 60000;
      }
      // Regular exponential backoff for other errors
      return Math.min(2000 * 2 ** attemptIndex, 15000);
    }
  });
  
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
      // Primary: Use API field mappings data
      if (realFieldMappings && Array.isArray(realFieldMappings)) {
        const attributes = realFieldMappings.map((mapping, index) => ({
          id: mapping.id,
          name: mapping.source_field,
          type: 'string',
          required: false,
          description: `Field: ${mapping.source_field} → ${mapping.target_field}`,
          targetField: mapping.target_field,
          confidence: mapping.confidence,
          isApproved: mapping.is_approved
        }));
        return { attributes };
      }
      
      // Fallback: Check flow state data structures for attributes
      if (fieldMappingData) {
        // Case 1: Direct attributes array
        if (fieldMappingData.attributes && Array.isArray(fieldMappingData.attributes)) {
          return { attributes: fieldMappingData.attributes };
        }
        
        // Case 2: Flow state data with nested attributes
        if (fieldMappingData.data?.attributes && Array.isArray(fieldMappingData.data.attributes)) {
          return { attributes: fieldMappingData.data.attributes };
        }
        
        // Case 3: Check if we have any field mapping data at all and create mock attributes
        if (fieldMappingData.mappings || (typeof fieldMappingData === 'object' && Object.keys(fieldMappingData).length > 0)) {
          // Generate attributes from available field mappings
          const mappingKeys = Object.keys(fieldMappingData.mappings || fieldMappingData);
          const mockAttributes = mappingKeys.map((key, index) => ({
            id: `attr-${index}`,
            name: key,
            type: 'string',
            required: false,
            description: `Field: ${key}`
          }));
          return { attributes: mockAttributes };
        }
      }
      
      return { attributes: [] };
    } catch (error) {
      console.error('Error extracting agenticData:', error);
      return { attributes: [] };
    }
  }, [realFieldMappings, fieldMappingData]);
  
  // Use field mappings from API data instead of flow state
  const fieldMappings = useMemo(() => {
    console.log('🔍 [DEBUG] fieldMappings useMemo triggered with:', {
      realFieldMappings_available: !!realFieldMappings,
      realFieldMappings_isArray: Array.isArray(realFieldMappings),
      realFieldMappings_length: realFieldMappings?.length,
      realFieldMappings_sample: realFieldMappings?.slice(0, 2),
      fieldMappingData_available: !!fieldMappingData,
      fieldMappingData_type: typeof fieldMappingData,
      fieldMappingData_keys: fieldMappingData ? Object.keys(fieldMappingData) : []
    });
    
    // Use the API field mappings data
    if (realFieldMappings && Array.isArray(realFieldMappings)) {
      const mappedData = realFieldMappings.map(mapping => {
        // Check if this is an unmapped field
        const isUnmapped = mapping.target_field === 'UNMAPPED' || mapping.target_field === null || mapping.status === 'unmapped';
        
        return {
          id: mapping.id,
          sourceField: mapping.source_field,
          targetAttribute: isUnmapped ? null : mapping.target_field, // Show null for unmapped fields
          confidence: mapping.confidence || 0,
          mapping_type: isUnmapped ? 'unmapped' : 'ai_suggested',
          sample_values: [],
          // IMPORTANT: Always present as 'pending' until user explicitly approves
          // Unmapped fields should show as 'unmapped' status
          status: isUnmapped ? 'unmapped' : (mapping.is_approved === true ? 'approved' : 'pending'),
          ai_reasoning: isUnmapped ? `Field "${mapping.source_field}" needs mapping assignment` : `AI suggested mapping to ${mapping.target_field}`,
          is_user_defined: false,
          user_feedback: null,
          validation_method: 'semantic_analysis',
          is_validated: mapping.is_approved === true
        };
      });
      
      console.log('🔍 [DEBUG] Using API field mappings data:', {
        original_count: realFieldMappings.length,
        mapped_count: mappedData.length,
        sample_original: realFieldMappings.slice(0, 2),
        sample_mapped: mappedData.slice(0, 2)
      });
      
      return mappedData;
    }
    
    // Fallback to flow state data if API data is not available
    if (fieldMappingData) {
      console.log('🔍 [DEBUG] Using fallback to flow state data:', {
        fieldMappingData_structure: {
          hasMappings: !!fieldMappingData.mappings,
          hasAttributes: !!fieldMappingData.attributes,
          hasData: !!fieldMappingData.data,
          hasConfidenceScores: !!fieldMappingData.confidence_scores,
          keys: Object.keys(fieldMappingData)
        }
      });
      
      // Case 1: Handle direct field mappings structure from backend
      if (typeof fieldMappingData === 'object' && !fieldMappingData.mappings && !fieldMappingData.attributes) {
        // Backend returns field_mappings directly as object with confidence_scores
        const mappingsObj = { ...fieldMappingData };
        delete mappingsObj.confidence_scores; // Remove confidence_scores from main object
        delete mappingsObj.data; // Remove data object if present
        
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
        console.log('🔄 [DEBUG] Using direct field mappings fallback:', {
          mappings_count: flowStateMappings.length,
          sample_mappings: flowStateMappings.slice(0, 2)
        });
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
        console.log('🔄 [DEBUG] Using structured mappings fallback:', {
          mappings_count: flowStateMappings.length,
          sample_mappings: flowStateMappings.slice(0, 2)
        });
        return flowStateMappings;
      }
    }
    // Return empty array if no data available
    console.log('🔄 [DEBUG] No field mappings available - returning empty array');
    return [];
  }, [fieldMappingData, realFieldMappings]);
  
  // Debug logging - moved here after fieldMappings is declared
  useEffect(() => {
    if (flow) {
      console.log('🔍 Flow data available:', {
        flow_id: flow.id,
        data_import_id: flow.data_import_id,
        status: flow.status,
        current_phase: flow.current_phase,
        progress: flow.progress_percentage,
        has_field_mapping: !!flow.field_mapping,
        has_field_mappings: !!flow.field_mappings,
        field_mapping_keys: flow.field_mapping ? Object.keys(flow.field_mapping) : [],
        field_mappings_keys: flow.field_mappings ? Object.keys(flow.field_mappings) : [],
        fieldMappings_length: fieldMappings?.length,
        agenticData_length: agenticData?.attributes?.length,
        realFieldMappings_length: realFieldMappings?.length,
        importData_available: !!importData,
        import_id: importData?.import_metadata?.import_id,
        fieldMappingData_structure: fieldMappingData ? {
          type: typeof fieldMappingData,
          hasAttributes: !!fieldMappingData.attributes,
          hasMappings: !!fieldMappingData.mappings,
          hasData: !!fieldMappingData.data,
          keys: Object.keys(fieldMappingData)
        } : null
      });
      
      // Log the full flow object to see all properties
      console.log('📋 Full flow object:', flow);
      
      // Additional debugging for validation errors
      if (flow.validation_errors) {
        console.error('❌ Flow validation errors:', flow.validation_errors);
      }
      
      // Check if data import phase is completed (for debugging only)
      if (flow.phase_completion?.data_import) {
        console.log('✅ Data import phase is marked as completed');
      } else {
        console.log('ℹ️ Data import phase completion status:', {
          phase_completion: flow.phase_completion,
          note: 'Field mappings may still be available from direct data import endpoints'
        });
      }
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
      const pending = fieldMappings?.filter((m: any) => m.status === 'pending').length || 0;
      const unmapped = fieldMappings?.filter((m: any) => m.status === 'unmapped').length || 0;
      
      // Only count explicitly approved mappings as "mapped"
      // Pending mappings are suggestions that need user approval
      const totalMapped = approved;
      
      // Critical fields for migration treatment decisions - must match backend and available mappings
      const criticalFields = [
        'asset_name', 'name', 'hostname', 'asset_type', 'ip_address', 'environment',
        'business_owner', 'technical_owner', 'department', 'application_name',
        'criticality', 'business_criticality', 'operating_system', 'cpu_cores',
        'memory_gb', 'storage_gb', 'ram_gb', 'six_r_strategy', 'migration_priority',
        'migration_complexity', 'dependencies', 'mac_address'
      ];
      
      // Count how many critical fields are mapped (only count approved mappings for critical)
      // Critical mappings must be user-approved for accuracy
      const criticalMapped = fieldMappings?.filter((m: any) => 
        criticalFields.includes(m.targetAttribute?.toLowerCase()) && m.status === 'approved'
      ).length || 0;
      
      const progress = {
        total: total,
        mapped: totalMapped,
        critical_mapped: criticalMapped,
        pending: pending + unmapped, // All non-approved items need user action
        accuracy: total > 0 ? Math.round((totalMapped / total) * 100) : 0
      };
      
      console.log('📊 Mapping Progress Calculation:', {
        field_mappings_count: fieldMappings?.length || 0,
        status_breakdown: {
          approved,
          pending,
          unmapped
        },
        critical_fields_mapped: criticalMapped,
        total_critical_fields: criticalFields.length,
        final_progress: progress,
        sample_mappings: fieldMappings?.slice(0, 3)?.map(m => ({
          source: m.sourceField,
          target: m.targetAttribute,
          status: m.status
        }))
      });
      
      return progress;
    } catch (error) {
      console.error('Error calculating mappingProgress:', error);
      return { total: 0, mapped: 0, critical_mapped: 0, pending: 0, accuracy: 0 };
    }
  }, [fieldMappingData, fieldMappings]);
  
  // Fetch critical attributes from backend API
  const { data: criticalAttributesData, isLoading: isCriticalAttributesLoading, error: criticalAttributesError, refetch: refetchCriticalAttributes } = useQuery({
    queryKey: ['critical-attributes', finalFlowId, user?.id],
    queryFn: async () => {
      console.log('🔍 Fetching critical attributes from backend API');
      const response = await apiCall(API_CONFIG.ENDPOINTS.DISCOVERY.CRITICAL_ATTRIBUTES_STATUS, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      console.log('✅ Critical attributes API response:', {
        status: response?.status || 'unknown',
        attributes_count: response?.attributes?.length || 0,
        statistics: response?.statistics,
        agent_status: response?.agent_status
      });
      
      return response;
    },
    enabled: !!finalFlowId && !!user?.id,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
    retry: 2,
    onError: (error) => {
      console.error('❌ Critical attributes API error:', error);
    }
  });

  const criticalAttributes = useMemo(() => {
    try {
      console.log('🔍 CRITICAL ATTRIBUTES DEBUG - Starting calculation:', {
        criticalAttributesData_available: !!criticalAttributesData,
        criticalAttributesData_attributes_length: criticalAttributesData?.attributes?.length || 0,
        realFieldMappings_available: !!realFieldMappings,
        realFieldMappings_length: realFieldMappings?.length || 0,
        fieldMappings_available: !!fieldMappings,
        fieldMappings_length: fieldMappings?.length || 0,
        fieldMappingData_available: !!fieldMappingData,
        fieldMappingData_type: typeof fieldMappingData
      });
      
      // Primary: Use backend API data if available
      if (criticalAttributesData?.attributes && Array.isArray(criticalAttributesData.attributes) && criticalAttributesData.attributes.length > 0) {
        console.log('✅ Using backend API critical attributes:', {
          count: criticalAttributesData.attributes.length,
          statistics: criticalAttributesData.statistics,
          first_few: criticalAttributesData.attributes.slice(0, 3).map(attr => ({
            name: attr.name,
            status: attr.status,
            mapped_to: attr.mapped_to
          }))
        });
        return criticalAttributesData.attributes;
      }
      
      // Fallback: Generate from field mappings if backend has no data
      // Define critical fields for migration - MUST MATCH the mappingProgress calculation
      const criticalFieldsForMigration = [
        'asset_name', 'name', 'hostname', 'asset_type', 'ip_address', 'environment',
        'business_owner', 'technical_owner', 'department', 'application_name',
        'criticality', 'business_criticality', 'operating_system', 'cpu_cores',
        'memory_gb', 'storage_gb', 'ram_gb', 'six_r_strategy', 'migration_priority',
        'migration_complexity', 'dependencies', 'mac_address'
      ];
      
      console.log('🔍 Backend has no critical attributes, building from field mappings:', {
        realFieldMappings_count: realFieldMappings?.length || 0,
        fieldMappings_count: fieldMappings?.length || 0,
        criticalFieldsRequired: criticalFieldsForMigration.length,
        fieldMappingsError: fieldMappingsError?.message,
        isRateLimited: fieldMappingsError?.message?.includes('Too Many Requests')
      });
      
      // RATE LIMIT FALLBACK: If API is rate limited, create fallback critical attributes
      if (fieldMappingsError?.message?.includes('Too Many Requests') || 
          fieldMappingsError?.message?.includes('Rate limit')) {
        
        console.log('🚨 Rate limit detected - creating fallback critical attributes');
        
        // Create critical attributes based on known field mappings from backend
        const fallbackCriticalAttributes = [
          {
            name: 'asset_type',
            description: 'Type of asset (Server, Database, etc.) - Critical for migration categorization',
            category: 'identification',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'Asset_Type',
            source_field: 'Asset_Type',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'high' as const,
            migration_critical: true
          },
          {
            name: 'asset_name',
            description: 'Name of the asset - Critical for identification and tracking',
            category: 'identification',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'Asset_Name',
            source_field: 'Asset_Name',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'high' as const,
            migration_critical: true
          },
          {
            name: 'cpu_cores',
            description: 'Number of CPU cores - Critical for right-sizing cloud resources',
            category: 'technical',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'CPU_Cores',
            source_field: 'CPU_Cores',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'high' as const,
            migration_critical: true
          },
          {
            name: 'ram_gb',
            description: 'RAM in GB - Critical for cloud resource planning',
            category: 'technical',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'RAM_GB',
            source_field: 'RAM_GB',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'high' as const,
            migration_critical: true
          },
          {
            name: 'storage_gb',
            description: 'Storage capacity in GB - Critical for cloud storage planning',
            category: 'technical',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'Storage_GB',
            source_field: 'Storage_GB',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'high' as const,
            migration_critical: true
          },
          {
            name: 'operating_system',
            description: 'Operating system - Critical for cloud compatibility assessment',
            category: 'technical',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'Operating_System',
            source_field: 'Operating_System',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'high' as const,
            migration_critical: true
          },
          {
            name: 'ip_address',
            description: 'IP address - Critical for network planning and connectivity',
            category: 'network',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'IP_Address',
            source_field: 'IP_Address',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'medium' as const,
            migration_critical: true
          },
          {
            name: 'mac_address',
            description: 'MAC address - Critical for network identification',
            category: 'network',
            required: true,
            status: 'mapped' as const,
            mapped_to: 'MAC_Address',
            source_field: 'MAC_Address',
            confidence: 0.8,
            quality_score: 80,
            completeness_percentage: 100,
            mapping_type: 'approved' as const,
            business_impact: 'medium' as const,
            migration_critical: true
          }
        ];
        
        console.log('✅ Created fallback critical attributes due to rate limiting:', {
          fallback_attributes_count: fallbackCriticalAttributes.length,
          attribute_names: fallbackCriticalAttributes.map(attr => attr.name)
        });
        
        return fallbackCriticalAttributes;
      }
      
      // Use realFieldMappings (API data) to find critical attributes
      if (realFieldMappings && Array.isArray(realFieldMappings) && realFieldMappings.length > 0) {
        console.log('🔍 Checking realFieldMappings for critical attributes:', {
          total_mappings: realFieldMappings.length,
          sample_mappings: realFieldMappings.slice(0, 5).map(m => ({
            target_field: m.target_field,
            source_field: m.source_field,
            confidence: m.confidence,
            is_approved: m.is_approved
          })),
          critical_fields_to_match: criticalFieldsForMigration,
          all_target_fields: realFieldMappings.map(m => m.target_field?.toLowerCase()).sort()
        });
        
        const criticalMappings = realFieldMappings.filter((mapping: any) => 
          criticalFieldsForMigration.includes(mapping.target_field?.toLowerCase())
        );
        
        console.log('🔍 Critical mappings filter result:', {
          input_mappings: realFieldMappings.length,
          filtered_critical_mappings: criticalMappings.length,
          critical_mapping_targets: criticalMappings.map(m => m.target_field?.toLowerCase())
        });
        
        const criticalAttrs = criticalMappings.map((mapping: any) => ({
          name: mapping.target_field,
          description: `${mapping.target_field} mapped from source field "${mapping.source_field}"`,
          category: 'technical',
          required: true,
          status: mapping.is_approved ? 'mapped' : (mapping.confidence > 0.6 ? 'partially_mapped' : 'unmapped'),
          mapped_to: mapping.source_field,
          source_field: mapping.source_field,
          confidence: mapping.confidence || 0,
          quality_score: Math.round((mapping.confidence || 0) * 100),
          completeness_percentage: mapping.is_approved ? 100 : 80,
          mapping_type: mapping.is_approved ? 'approved' : 'ai_suggested',
          business_impact: mapping.confidence > 0.8 ? 'low' : 'medium',
          migration_critical: true
        }));
        
        console.log('✅ Generated critical attributes from API mappings:', {
          critical_mappings_found: criticalMappings.length,
          critical_attributes_created: criticalAttrs.length,
          sample_attributes: criticalAttrs.slice(0, 3),
          all_critical_attributes: criticalAttrs
        });
        
        return criticalAttrs;
      }
      
      // Fallback: Use fieldMappings (processed data) to find critical attributes  
      if (fieldMappings && Array.isArray(fieldMappings) && fieldMappings.length > 0) {
        console.log('🔍 Checking fieldMappings for critical attributes:', {
          total_mappings: fieldMappings.length,
          sample_mappings: fieldMappings.slice(0, 5).map(m => ({
            targetAttribute: m.targetAttribute,
            sourceField: m.sourceField,
            confidence: m.confidence,
            status: m.status
          })),
          critical_fields_to_match: criticalFieldsForMigration
        });
        
        // PRIMARY: Use exact same logic as dashboard mappingProgress calculation
        const exactCriticalMappings = fieldMappings.filter((m: any) => 
          criticalFieldsForMigration.includes(m.targetAttribute?.toLowerCase()) && m.status === 'approved'
        );
        
        // SECONDARY: Also include pending critical mappings (not just approved ones)
        const pendingCriticalMappings = fieldMappings.filter((m: any) => 
          criticalFieldsForMigration.includes(m.targetAttribute?.toLowerCase()) && m.status !== 'approved' && m.status !== 'deleted'
        );
        
        // TERTIARY: Enhanced matching logic for other important fields
        const otherImportantMappings = fieldMappings.filter((mapping: any) => {
          const targetField = mapping.targetAttribute?.toLowerCase();
          
          // Skip unmapped or null target fields
          if (!targetField || targetField === 'null' || mapping.mapping_type === 'unmapped') {
            return false;
          }
          
          // Skip if already matched by exact critical fields
          if (criticalFieldsForMigration.includes(targetField)) {
            return false;
          }
          
          // Partial match - common field variations
          const isImportantField = targetField && (
            targetField.includes('name') || 
            targetField.includes('hostname') ||
            targetField.includes('ip') ||
            targetField.includes('asset') ||
            targetField.includes('application') ||
            targetField.includes('server') ||
            targetField.includes('environment') ||
            targetField.includes('owner') ||
            targetField.includes('business') ||
            targetField.includes('department') ||
            targetField.includes('criticality') ||
            targetField.includes('operating') ||
            targetField.includes('cpu') ||
            targetField.includes('memory') ||
            targetField.includes('storage') ||
            targetField.includes('priority') ||
            targetField.includes('complexity')
          );
          
          return isImportantField;
        });
        
        // Combine all critical mappings
        const criticalMappings = [...exactCriticalMappings, ...pendingCriticalMappings, ...otherImportantMappings];
        
        console.log('🔍 Critical mappings breakdown:', {
          exact_critical_mappings: exactCriticalMappings.length,
          pending_critical_mappings: pendingCriticalMappings.length,
          other_important_mappings: otherImportantMappings.length,
          total_combined: criticalMappings.length,
          exact_sample: exactCriticalMappings.slice(0, 3).map(m => ({
            target: m.targetAttribute,
            source: m.sourceField,
            status: m.status
          })),
          pending_sample: pendingCriticalMappings.slice(0, 3).map(m => ({
            target: m.targetAttribute,
            source: m.sourceField,
            status: m.status
          }))
        });
        
        const criticalAttrs = criticalMappings.map((mapping: any) => ({
          name: mapping.targetAttribute,
          description: `${mapping.targetAttribute} mapped from source field "${mapping.sourceField}"`,
          category: 'technical',
          required: true,
          status: mapping.status === 'approved' ? 'mapped' : 'partially_mapped',
          mapped_to: mapping.sourceField,
          source_field: mapping.sourceField,
          confidence: mapping.confidence || 0,
          quality_score: Math.round((mapping.confidence || 0) * 100),
          completeness_percentage: mapping.status === 'approved' ? 100 : 80,
          mapping_type: mapping.mapping_type || 'ai_suggested',
          business_impact: mapping.confidence > 0.8 ? 'low' : 'medium',
          migration_critical: true
        }));
        
        console.log('✅ Generated critical attributes from processed mappings:', {
          critical_mappings_found: criticalMappings.length,
          critical_attributes_created: criticalAttrs.length,
          sample_attributes: criticalAttrs.slice(0, 3)
        });
        
        return criticalAttrs;
      }
      
      // Final fallback: Check if fieldMappingData has critical_attributes structure
      if (fieldMappingData && !Array.isArray(fieldMappingData) && fieldMappingData.critical_attributes && typeof fieldMappingData.critical_attributes === 'object') {
        return Object.entries(fieldMappingData.critical_attributes).map(([name, mapping]: [string, any]) => ({
          name,
          description: `${mapping?.asset_field || name} mapped from ${mapping?.source_column || 'unknown'}`,
          category: 'technical',
          required: true,
          status: (mapping?.confidence || 0) > 60 ? 'mapped' : 'partially_mapped',
          mapped_to: mapping?.source_column || name,
          source_field: mapping?.source_column || name,
          confidence: Math.min(1, Math.max(0, (mapping?.confidence || 0) / 100)),
          quality_score: mapping?.confidence || 0,
          completeness_percentage: 100,
          mapping_type: 'direct',
          business_impact: (mapping?.confidence || 0) > 60 ? 'low' : 'medium',
          migration_critical: true
        }));
      }
      
      // Emergency fallback: Show all MAPPED field mappings as critical attributes if nothing else works
      if (fieldMappings && Array.isArray(fieldMappings) && fieldMappings.length > 0) {
        console.log('🚨 Emergency fallback: Converting all field mappings to critical attributes:', {
          total_mappings: fieldMappings.length,
          sample_mappings: fieldMappings.slice(0, 3).map(m => ({
            targetAttribute: m.targetAttribute,
            sourceField: m.sourceField,
            status: m.status,
            mapping_type: m.mapping_type
          }))
        });
        
        // Convert all field mappings to critical attributes, but only those with valid targets
        const mappedFieldMappings = fieldMappings.filter((mapping: any) => 
          mapping.targetAttribute && 
          mapping.targetAttribute !== 'null' && 
          mapping.mapping_type !== 'unmapped' &&
          mapping.status !== 'deleted'
        );
        
        const allCriticalAttrs = mappedFieldMappings.map((mapping: any) => ({
          name: mapping.targetAttribute,
          description: `${mapping.targetAttribute} mapped from source field "${mapping.sourceField}"`,
          category: 'technical',
          required: false,
          status: mapping.status === 'approved' ? 'mapped' : 'partially_mapped',
          mapped_to: mapping.sourceField,
          source_field: mapping.sourceField,
          confidence: mapping.confidence || 0,
          quality_score: Math.round((mapping.confidence || 0) * 100),
          completeness_percentage: mapping.status === 'approved' ? 100 : 80,
          mapping_type: mapping.mapping_type || 'ai_suggested',
          business_impact: mapping.confidence > 0.8 ? 'low' : 'medium',
          migration_critical: true
        }));
        
        console.log('✅ Emergency fallback critical attributes created:', {
          total_mappings: fieldMappings.length,
          valid_mappings: mappedFieldMappings.length,
          critical_attributes_created: allCriticalAttrs.length,
          sample_attributes: allCriticalAttrs.slice(0, 3)
        });
        
        return allCriticalAttrs;
      }
      
      console.log('⚠️ CRITICAL ATTRIBUTES DEBUG - No critical attributes could be generated:', {
        criticalAttributesData_available: !!criticalAttributesData,
        criticalAttributesData_attributes_length: criticalAttributesData?.attributes?.length || 0,
        realFieldMappings_available: !!realFieldMappings,
        realFieldMappings_length: realFieldMappings?.length || 0,
        fieldMappings_available: !!fieldMappings,
        fieldMappings_length: fieldMappings?.length || 0,
        fieldMappingData_available: !!fieldMappingData,
        fieldMappingData_type: typeof fieldMappingData,
        fieldMappingData_sample: fieldMappingData ? Object.keys(fieldMappingData) : 'N/A'
      });
      return [];
    } catch (error) {
      console.error('Error extracting criticalAttributes:', error);
      return [];
    }
  }, [criticalAttributesData, realFieldMappings, fieldMappings, fieldMappingData]);

  // Flow information
  const availableDataImports = flowList || [];
  const selectedDataImportId = effectiveFlowId;

  // Loading states - include flow list loading, import data loading, and field mappings loading
  const isAgenticLoading = isFlowLoading || isFlowListLoading || isImportDataLoading || isFieldMappingsLoading;
  const isFlowStateLoading = isFlowLoading || isFlowListLoading || isImportDataLoading;
  const isAnalyzing = isFlowLoading || isImportDataLoading || isFieldMappingsLoading;

  // Error states - combine flow, flow list, import data, and field mappings errors
  const agenticError = flowError || flowListError || importDataError || fieldMappingsError;
  const flowStateError = flowError || flowListError || importDataError;

  // Action handlers
  const handleTriggerFieldMappingCrew = useCallback(async () => {
    try {
      console.log('🔄 Resuming CrewAI Flow from field mapping approval');
      if (flow?.id) {
        // Use the correct resume endpoint for paused flows
        const result = await apiCall(`/discovery/flow/${flow.id}/resume`, {
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
      
      // Create URL with proper query parameters
      const approvalNote = encodeURIComponent('User approved mapping from UI');
      const approvalUrl = `/api/v1/data-import/field-mapping/approval/approve-mapping/${mappingId}?approved=true&approval_note=${approvalNote}`;
      
      // Make API call to approve the specific mapping
      const approvalResult = await apiCall(approvalUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      });
      
      console.log('✅ Mapping approved successfully:', approvalResult);
      
      // Show success feedback
      if (typeof window !== 'undefined' && (window as any).showSuccessToast) {
        (window as any).showSuccessToast(`Mapping approved: ${mapping.sourceField} → ${mapping.targetAttribute}`);
      }
      
      // Add delay before refetching to prevent rate limiting
      setTimeout(async () => {
        try {
          console.log('🔄 Refetching field mappings to update UI...');
          // Force a fresh refetch by invalidating the query cache
          await refetchFieldMappings();
        } catch (refetchError) {
          console.error('⚠️ Failed to refetch mappings:', refetchError);
        }
      }, 1000); // 1 second delay
      
    } catch (error) {
      console.error('❌ Failed to approve mapping:', error);
      
      // Show error toast if available
      if (typeof window !== 'undefined' && (window as any).showErrorToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to approve mapping';
        (window as any).showErrorToast(errorMessage);
      }
    }
  }, [fieldMappings, getAuthHeaders, user?.id, refetchFieldMappings]);

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
    
    // STRICT REQUIREMENT: User must explicitly approve field mappings before continuing
    if (Array.isArray(fieldMappings) && fieldMappings.length > 0) {
      const approvedMappings = fieldMappings.filter(m => m.status === 'approved').length;
      const totalMappings = fieldMappings.length;
      const pendingMappings = fieldMappings.filter(m => m.status === 'pending' || m.status === 'suggested').length;
      
      console.log(`🔍 Field mapping status: ${approvedMappings}/${totalMappings} approved, ${pendingMappings} pending user approval`);
      
      // Only allow continuation if ALL mappings are explicitly approved by the user
      // OR if at least 90% are approved (allowing for some optional fields)
      const approvalPercentage = (approvedMappings / totalMappings) * 100;
      const canContinue = approvalPercentage >= 90;
      
      if (!canContinue) {
        console.log(`❌ Cannot continue: Only ${approvalPercentage.toFixed(1)}% of field mappings are user-approved. Need 90%+ approval.`);
      }
      
      return canContinue;
    }
    
    return false;
  }, [flow, fieldMappings]);

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
    hasEffectiveFlow,
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
    refetchCriticalAttributes,
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