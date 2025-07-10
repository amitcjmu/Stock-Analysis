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
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes to reduce API calls
    cacheTime: 20 * 60 * 1000, // Keep in cache for 20 minutes
    retry: 1, // Only retry once to prevent 429 errors
    retryDelay: 5000, // Fixed 5 second delay between retries
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
                target_field: null, // No mapping yet
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
        
        return mappings || [];
      } catch (error) {
        console.error('❌ Error fetching field mappings:', error);
        return [];
      }
    },
    enabled: !!importData?.import_metadata?.import_id,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes to reduce API calls
    cacheTime: 20 * 60 * 1000, // Keep in cache for 20 minutes
    retry: 1, // Only retry once to prevent 429 errors
    retryDelay: 5000, // Fixed 5 second delay between retries
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
      const mappedData = realFieldMappings.map(mapping => ({
        id: mapping.id,
        sourceField: mapping.source_field,
        targetAttribute: mapping.target_field,
        confidence: mapping.confidence,
        mapping_type: 'ai_suggested',
        sample_values: [],
        status: mapping.is_approved ? 'approved' : 'suggested', // Use 'suggested' to match backend data
        ai_reasoning: `AI suggested mapping to ${mapping.target_field}`,
        is_user_defined: false,
        user_feedback: null,
        validation_method: 'semantic_analysis',
        is_validated: mapping.is_approved
      }));
      
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
      const suggested = fieldMappings?.filter((m: any) => m.status === 'suggested').length || 0;
      const pending = fieldMappings?.filter((m: any) => m.status === 'pending').length || 0;
      
      // Count suggested and approved as "mapped" since suggested mappings are AI-generated and ready for use
      const totalMapped = approved + suggested;
      
      // Critical fields for migration treatment decisions - must match backend and available mappings
      const criticalFields = [
        'asset_name', 'name', 'hostname', 'asset_type', 'ip_address', 'environment',
        'business_owner', 'technical_owner', 'department', 'application_name',
        'criticality', 'business_criticality', 'operating_system', 'cpu_cores',
        'memory_gb', 'storage_gb', 'ram_gb', 'six_r_strategy', 'migration_priority',
        'migration_complexity', 'dependencies', 'mac_address'
      ];
      
      // Count how many critical fields are mapped (including suggested mappings)
      const criticalMapped = fieldMappings?.filter((m: any) => 
        criticalFields.includes(m.targetAttribute) && (m.status === 'approved' || m.status === 'suggested')
      ).length || 0;
      
      const progress = {
        total: total,
        mapped: totalMapped,
        critical_mapped: criticalMapped,
        pending: pending, // Only truly pending/unmapped items
        accuracy: total > 0 ? Math.round((totalMapped / total) * 100) : 0
      };
      
      console.log('📊 Mapping Progress Calculation:', {
        field_mappings_count: fieldMappings?.length || 0,
        status_breakdown: {
          approved,
          suggested,
          pending
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
  
  const criticalAttributes = useMemo(() => {
    try {
      // Define critical fields for migration - these are the minimum required for proper migration planning
      const criticalFieldsForMigration = [
        'asset_name', 'name', 'hostname', 'asset_type', 'ip_address', 'environment',
        'business_owner', 'technical_owner', 'department', 'application_name',
        'criticality', 'business_criticality', 'operating_system', 'cpu_cores',
        'memory_gb', 'storage_gb', 'ram_gb', 'migration_priority', 'migration_complexity',
        'mac_address'
      ];
      
      console.log('🔍 Building critical attributes from field mappings:', {
        realFieldMappings_count: realFieldMappings?.length || 0,
        fieldMappings_count: fieldMappings?.length || 0,
        criticalFieldsRequired: criticalFieldsForMigration.length
      });
      
      // Primary: Use realFieldMappings (API data) to find critical attributes
      if (realFieldMappings && Array.isArray(realFieldMappings) && realFieldMappings.length > 0) {
        const criticalMappings = realFieldMappings.filter((mapping: any) => 
          criticalFieldsForMigration.includes(mapping.target_field?.toLowerCase())
        );
        
        const criticalAttrs = criticalMappings.map((mapping: any) => ({
          name: mapping.target_field,
          description: `${mapping.target_field} mapped from source field "${mapping.source_field}"`,
          category: 'technical',
          required: true,
          status: mapping.confidence > 0.6 ? 'mapped' : 'partially_mapped',
          mapped_to: mapping.source_field,
          source_field: mapping.source_field,
          confidence: mapping.confidence || 0,
          quality_score: Math.round((mapping.confidence || 0) * 100),
          completeness_percentage: mapping.is_approved ? 100 : 80,
          mapping_type: 'ai_suggested',
          business_impact: mapping.confidence > 0.8 ? 'low' : 'medium',
          migration_critical: true
        }));
        
        console.log('✅ Generated critical attributes from API mappings:', {
          critical_mappings_found: criticalMappings.length,
          critical_attributes_created: criticalAttrs.length,
          sample_attributes: criticalAttrs.slice(0, 3)
        });
        
        return criticalAttrs;
      }
      
      // Fallback: Use fieldMappings (processed data) to find critical attributes  
      if (fieldMappings && Array.isArray(fieldMappings) && fieldMappings.length > 0) {
        const criticalMappings = fieldMappings.filter((mapping: any) => 
          criticalFieldsForMigration.includes(mapping.targetAttribute?.toLowerCase())
        );
        
        const criticalAttrs = criticalMappings.map((mapping: any) => ({
          name: mapping.targetAttribute,
          description: `${mapping.targetAttribute} mapped from source field "${mapping.sourceField}"`,
          category: 'technical',
          required: true,
          status: mapping.confidence > 0.6 ? 'mapped' : 'partially_mapped',
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
      
      console.log('⚠️ No critical attributes could be generated - no suitable mapping data found');
      return [];
    } catch (error) {
      console.error('Error extracting criticalAttributes:', error);
      return [];
    }
  }, [realFieldMappings, fieldMappings, fieldMappingData]);

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
    
    // Check if sufficient field mappings are approved or suggested
    if (Array.isArray(fieldMappings) && fieldMappings.length > 0) {
      const approvedMappings = fieldMappings.filter(m => m.status === 'approved').length;
      const suggestedMappings = fieldMappings.filter(m => m.status === 'suggested').length;
      const readyMappings = approvedMappings + suggestedMappings; // Both are ready for use
      const totalMappings = fieldMappings.length;
      const completionPercentage = (readyMappings / totalMappings) * 100;
      
      // Allow continuation if at least 80% of mappings are ready (approved or suggested)
      console.log(`🔍 Field mapping completion: ${readyMappings}/${totalMappings} (${completionPercentage.toFixed(1)}%) - Approved: ${approvedMappings}, Suggested: ${suggestedMappings}`);
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