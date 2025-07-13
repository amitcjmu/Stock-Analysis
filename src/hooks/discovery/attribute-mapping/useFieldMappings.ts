import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';

export interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string | null;
  confidence: number;
  mapping_type: string;
  sample_values: any[];
  status: 'approved' | 'pending' | 'unmapped' | 'suggested';
  ai_reasoning: string;
  is_user_defined: boolean;
  user_feedback: any;
  validation_method: string;
  is_validated: boolean;
  transformation_rule?: string;
  validation_rule?: string;
  is_required?: boolean;
}

export interface FieldMappingsResult {
  fieldMappings: FieldMapping[];
  realFieldMappings: any[];
  isFieldMappingsLoading: boolean;
  fieldMappingsError: any;
  refetchFieldMappings: () => Promise<any>;
}

/**
 * Hook for field mappings data fetching and management
 * Handles both API field mappings and flow state fallbacks
 */
export const useFieldMappings = (
  importData: any,
  fieldMappingData: any
): FieldMappingsResult => {
  const { getAuthHeaders } = useAuth();

  // Get field mappings using the import ID
  const { 
    data: realFieldMappings, 
    isLoading: isFieldMappingsLoading, 
    error: fieldMappingsError, 
    refetch: refetchFieldMappings 
  } = useQuery({
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
                id: crypto.randomUUID(), // Generate proper UUID for unmapped fields
                source_field: sourceField,
                target_field: 'UNMAPPED', // Use UNMAPPED placeholder 
                confidence: 0,
                is_approved: false,
                status: 'unmapped',
                match_type: 'unmapped',
                is_placeholder: true // Mark as placeholder to prevent approval attempts
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
            id: crypto.randomUUID(), // Generate proper UUID
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
            is_validated: false,
            is_fallback: true // Mark as fallback to prevent approval attempts
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
          id: crypto.randomUUID(), // Generate proper UUID
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
          is_validated: false,
          is_fallback: true // Mark as fallback to prevent approval attempts
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

  return {
    fieldMappings,
    realFieldMappings: realFieldMappings || [],
    isFieldMappingsLoading,
    fieldMappingsError,
    refetchFieldMappings
  };
};