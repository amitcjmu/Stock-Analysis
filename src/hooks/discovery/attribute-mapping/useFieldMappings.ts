import { useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';
import { apiClient } from '../../../lib/api/apiClient';
import { useWebSocket } from '../../useWebSocket';
import { isCacheFeatureEnabled } from '@/constants/features';
import type { FormFieldValue } from '@/types/shared/form-types';

interface RawFieldMapping {
  id: string;
  source_field: string;
  target_field: string | null;
  confidence: number;
  is_approved: boolean;
  status: string;
  match_type?: string;
  transformation_rule?: string;
  validation_rule?: string;
  is_required?: boolean;
  is_placeholder?: boolean;
}

interface ImportData {
  import_metadata: {
    import_id: string;
  };
  raw_data?: Record<string, FormFieldValue>;
  sample_record?: Record<string, FormFieldValue>;
  record_count?: number;
  field_count?: number;
}

interface FieldMappingData {
  mappings?: Record<string, FieldMappingRecord>;
  attributes?: Record<string, string>;
  data?: Record<string, FormFieldValue>;
  confidence_scores?: Record<string, number>;
}

interface FieldMappingRecord {
  source_column?: string;
  asset_field?: string;
  confidence?: number;
  match_type?: string;
  pattern_matched?: string;
}

export interface FieldMapping {
  id: string;
  sourceField: string;
  targetAttribute: string | null;
  confidence: number;
  mapping_type: string;
  sample_values: FormFieldValue[];
  status: 'approved' | 'pending' | 'unmapped' | 'suggested';
  ai_reasoning: string;
  is_user_defined: boolean;
  user_feedback: string | null;
  validation_method: string;
  is_validated: boolean;
  transformation_rule?: string;
  validation_rule?: string;
  is_required?: boolean;
  is_placeholder?: boolean;
  is_fallback?: boolean;
}

export interface FieldMappingsResult {
  fieldMappings: FieldMapping[];
  realFieldMappings: RawFieldMapping[];
  isFieldMappingsLoading: boolean;
  fieldMappingsError: Error | null;
  refetchFieldMappings: () => Promise<RawFieldMapping[]>;
}

/**
 * Hook for field mappings data fetching and management
 * Handles both API field mappings and flow state fallbacks
 */
export const useFieldMappings = (
  importData: ImportData | null,
  fieldMappingData: FieldMappingData | null,
  flowId?: string | null
): FieldMappingsResult => {
  const { getAuthHeaders } = useAuth();
  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();

  // Use provided flow ID or try to extract from data
  const effectiveFlowId = flowId || fieldMappingData?.flow_id || importData?.flow_id;

  const {
    data: realFieldMappings,
    isLoading: isFieldMappingsLoading,
    error: fieldMappingsError,
    refetch: refetchFieldMappings
  } = useQuery({
    queryKey: ['field-mappings', effectiveFlowId || importData?.import_metadata?.import_id],
    queryFn: async () => {
      // Try to use flow ID first (preferred - uses MFO)
      if (effectiveFlowId) {
        console.log('🔍 Fetching field mappings using flow ID:', effectiveFlowId);
        try {
          const response = await apiCall(`/api/v1/unified-discovery/flows/${effectiveFlowId}/field-mappings`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            }
          });

          if (response?.field_mappings) {
            console.log('✅ Fetched field mappings from unified discovery:', {
              flow_id: flowId,
              count: response.field_mappings.length
            });

            // Convert unified discovery format to expected format
            return response.field_mappings.map(m => ({
              id: m.id || `${m.source_field}_${m.target_attribute}`,
              source_field: m.source_field,
              target_field: m.target_attribute,
              confidence: m.confidence,
              is_approved: m.is_approved || false,
              status: m.status || 'suggested',
              transformation_rule: m.transformation,
              validation_rule: m.validation_rules
            }));
          }
        } catch (error) {
          console.warn('Failed to fetch from unified discovery, falling back to import ID', error);
        }
      }

      // Fallback to import ID if flow ID doesn't work
      const importId = importData?.import_metadata?.import_id;
      if (!importId) {
        console.warn('⚠️ No import ID available for field mappings fetch');
        return [];
      }

      console.log('🔍 Fetching field mappings for import ID:', importId);

      try {
        // Use new API client if custom cache is disabled, otherwise use legacy
        const mappings = isCacheFeatureEnabled('DISABLE_CUSTOM_CACHE')
          ? await apiClient.get(`/data-import/field-mapping/field-mappings/imports/${importId}/mappings`)
          : await apiCall(`/api/v1/data-import/field-mapping/field-mappings/imports/${importId}/mappings`, {
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

        // CRITICAL FIX: Check for test data contamination
        if (Array.isArray(mappings) && mappings.length > 0) {
          const hasTestData = mappings.some(mapping =>
            mapping.source_field && (
              mapping.source_field.includes('Device_') ||
              mapping.source_field === 'Device_ID' ||
              mapping.source_field === 'Device_Name' ||
              mapping.source_field === 'Device_Type'
            )
          );

          if (hasTestData) {
            console.error('❌ CRITICAL ERROR: Test data detected in production field mappings!', {
              import_id: importId,
              test_fields_found: mappings.filter(m => m.source_field && m.source_field.includes('Device_')).map(m => m.source_field),
              all_source_fields: mappings.map(m => m.source_field)
            });

            // This is test data contamination - reject it and force regeneration
            throw new Error(`Test data contamination detected: Found Device_* fields in production. Import ID: ${importId}`);
          }
        }

        // Now try to get the raw import data to see all original CSV fields
        try {
          const rawImportData = isCacheFeatureEnabled('DISABLE_CUSTOM_CACHE')
            ? await apiClient.get(`/data-import/imports/${importId}`)
            : await apiCall(`/api/v1/data-import/imports/${importId}`, {
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

          // CRITICAL FIX: Validate that the raw import data matches expected field names
          if (rawImportData?.sample_record || rawImportData?.raw_data) {
            const sampleRecord = rawImportData.sample_record || rawImportData.raw_data;
            const actualCsvFields = Object.keys(sampleRecord);

            // Check for test data contamination in the raw import data
            const hasTestFieldsInRaw = actualCsvFields.some(field =>
              field.includes('Device_') || field === 'Device_ID' || field === 'Device_Name' || field === 'Device_Type'
            );

            if (hasTestFieldsInRaw) {
              console.error('❌ CRITICAL ERROR: Test data detected in raw import data!', {
                import_id: importId,
                raw_csv_fields: actualCsvFields
              });
              throw new Error(`Test data contamination in raw CSV: Found Device_* fields. Import ID: ${importId}`);
            }

            console.log('✅ Raw import data validation passed - no test data contamination detected:', {
              actual_csv_fields: actualCsvFields,
              field_count: actualCsvFields.length
            });
          }

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

              // Transform enhanced mappings to frontend format before returning
              const transformedEnhancedMappings = enhancedMappings.map((mapping: RawFieldMapping) => ({
                id: mapping.id,
                sourceField: mapping.source_field,
                targetAttribute: mapping.target_field === 'UNMAPPED' ? null : mapping.target_field,
                confidence: mapping.confidence || 0,
                mapping_type: mapping.is_approved ? 'approved' : (mapping.status === 'unmapped' ? 'unmapped' : 'ai_suggested'),
                sample_values: [],
                status: mapping.is_approved ? 'approved' : (mapping.status === 'unmapped' ? 'unmapped' : 'pending'),
                ai_reasoning: '',
                transformation_rule: mapping.transformation_rule,
                validation_rule: mapping.validation_rule,
                is_required: mapping.is_required,
                is_placeholder: mapping.is_placeholder
              }));

              console.log('✅ Transformed enhanced field mappings:', {
                enhanced_count: enhancedMappings.length,
                transformed_count: transformedEnhancedMappings.length,
                sample_transformed: transformedEnhancedMappings.slice(0, 3)
              });

              return transformedEnhancedMappings;
            }
          }
        } catch (rawDataError) {
          console.warn('⚠️ Could not fetch raw import data:', rawDataError);
        }

        // FINAL VALIDATION: Ensure no test data in final mappings
        if (Array.isArray(mappings) && mappings.length > 0) {
          const validMappings = mappings.filter(mapping => {
            const isTestData = mapping.source_field && (
              mapping.source_field.includes('Device_') ||
              mapping.source_field === 'Device_ID' ||
              mapping.source_field === 'Device_Name' ||
              mapping.source_field === 'Device_Type'
            );

            if (isTestData) {
              console.warn('⚠️ Filtering out test data mapping:', mapping.source_field);
            }

            return !isTestData;
          });

          console.log('✅ Returning validated field mappings from API:', {
            original_count: mappings.length,
            validated_count: validMappings.length,
            filtered_out: mappings.length - validMappings.length,
            sample_valid_mappings: validMappings.slice(0, 3)
          });

          return validMappings;
        }

        // Return the raw mappings directly from the API if no validation needed
        console.log('✅ Returning raw field mappings from API (no validation needed):', {
          original_count: mappings?.length || 0,
          sample_mappings: mappings?.slice(0, 3)
        });

        return mappings || [];
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
    enabled: !!(effectiveFlowId || importData?.import_metadata?.import_id),
    staleTime: isCacheFeatureEnabled('REACT_QUERY_OPTIMIZATIONS') ? 2 * 60 * 1000 : 30 * 1000, // 2 minutes with optimizations, 30 seconds legacy
    cacheTime: isCacheFeatureEnabled('REACT_QUERY_OPTIMIZATIONS') ? 5 * 60 * 1000 : 2 * 60 * 1000, // 5 minutes with optimizations, 2 minutes legacy
    retry: (failureCount, error) => {
      // Allow retries on 429 (Too Many Requests) with longer delays
      if (error && typeof error === 'object' && 'status' in error) {
        const status = (error as { status?: number }).status;
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
      if (error && typeof error === 'object' && 'status' in error && (error as { status?: number }).status === 429) {
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
      // FINAL FRONTEND VALIDATION: Filter out any test data that might have slipped through
      const productionMappings = realFieldMappings.filter(mapping => {
        const sourceField = String(mapping.sourceField || mapping.source_field || '');
        const isTestData = sourceField.includes('Device_') ||
                          sourceField === 'Device_ID' ||
                          sourceField === 'Device_Name' ||
                          sourceField === 'Device_Type';

        if (isTestData) {
          console.warn('🚫 Frontend filter: Removing test data field mapping:', sourceField);
        }

        return !isTestData;
      });

      console.log('🔍 [DEBUG] Frontend validation completed:', {
        original_count: realFieldMappings.length,
        production_count: productionMappings.length,
        filtered_test_data: realFieldMappings.length - productionMappings.length
      });

      const mappedData = productionMappings.map(mapping => {
        // Check if this is an unmapped field (handle both camelCase and snake_case)
        const targetField = mapping.targetAttribute || mapping.target_field;
        const isUnmapped = targetField === 'UNMAPPED' || targetField === null;

        // Ensure source field is always a string (handle both camelCase and snake_case)
        const sourceField = String(mapping.sourceField || mapping.source_field || 'Unknown Field');

        return {
          id: mapping.id,
          sourceField: sourceField,
          targetAttribute: isUnmapped ? null : targetField, // Show null for unmapped fields
          confidence: mapping.confidence || 0,
          mapping_type: mapping.mapping_type || (isUnmapped ? 'unmapped' : 'ai_suggested'),
          sample_values: mapping.sample_values || [],
          // IMPORTANT: Always present as 'pending' until user explicitly approves
          // Unmapped fields should show as 'unmapped' status
          status: mapping.status || (isUnmapped ? 'unmapped' : (mapping.is_approved === true ? 'approved' : 'pending')),
          ai_reasoning: mapping.ai_reasoning || (isUnmapped ? `Field "${sourceField}" needs mapping assignment` : `AI suggested mapping to ${targetField}`),
          is_user_defined: mapping.is_user_defined || false,
          user_feedback: mapping.user_feedback || null,
          validation_method: mapping.validation_method || 'semantic_analysis',
          is_validated: mapping.is_validated || mapping.is_approved === true,
          transformation_rule: mapping.transformation_rule,
          validation_rule: mapping.validation_rule,
          is_required: mapping.is_required,
          is_placeholder: mapping.is_placeholder
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

    // REMOVED FALLBACK - Always use API data to avoid field name issues
    // The fallback logic was converting field names to numeric indices
    // Dead code block - commented out to fix linting errors
    /* if (false && fieldMappingData) {
      console.log('🔍 [DEBUG] Using fallback to flow state data:', {
        fieldMappingData_structure: {
          hasMappings: fieldMappingData ? !!fieldMappingData.mappings : false,
          hasAttributes: fieldMappingData ? !!fieldMappingData.attributes : false,
          hasData: fieldMappingData ? !!fieldMappingData.data : false,
          hasConfidenceScores: fieldMappingData ? !!fieldMappingData.confidence_scores : false,
          keys: fieldMappingData ? Object.keys(fieldMappingData) : []
        }
      });

      // Case 1: Handle direct field mappings structure from backend
      if (fieldMappingData && typeof fieldMappingData === 'object' && !fieldMappingData.mappings && !fieldMappingData.attributes) {
        // Backend returns field_mappings directly as object with confidence_scores
        const mappingsObj = { ...fieldMappingData };
        delete mappingsObj.confidence_scores; // Remove confidence_scores from main object
        delete mappingsObj.data; // Remove data object if present

        console.log('🔍 [DEBUG] Processing mappingsObj:', {
          mappingsObj_type: typeof mappingsObj,
          mappingsObj_isArray: Array.isArray(mappingsObj),
          mappingsObj_keys: Object.keys(mappingsObj),
          mappingsObj_entries: Object.entries(mappingsObj).slice(0, 3),
          mappingsObj_sample: mappingsObj
        });

        const flowStateMappings = Object.entries(mappingsObj)
          .filter(([key, value]) => {
            console.log('🔍 [DEBUG] Processing entry:', { key, key_type: typeof key, value, value_type: typeof value }); // nosec - debug log for data structure analysis
            return key !== 'confidence_scores' && key !== 'data';
          })
          .map(([sourceField, targetField]: [string, string]) => {
            console.log('🔍 [DEBUG] Mapping entry:', {
              sourceField,
              sourceField_type: typeof sourceField,
              targetField,
              targetField_type: typeof targetField
            });

            // Ensure sourceField is always a string, not an array index
            const cleanSourceField = String(sourceField).trim();
            const isNumericIndex = /^\d+$/.test(cleanSourceField);

            if (isNumericIndex) {
              console.warn('⚠️ [WARNING] Detected numeric index as sourceField:', cleanSourceField);
            }

            return {
              id: crypto.randomUUID(), // Generate proper UUID
              sourceField: (cleanSourceField === 'None' || isNumericIndex) ? 'Unknown Field' : cleanSourceField,
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
            };
          });
        console.log('🔄 [DEBUG] Using direct field mappings fallback:', {
          mappings_count: flowStateMappings.length,
          sample_mappings: flowStateMappings.slice(0, 2)
        });
        return flowStateMappings;
      }

      // Handle structured mappings format
      if (fieldMappingData && fieldMappingData.mappings) {
        const mappingsObj = fieldMappingData.mappings;
        const flowStateMappings = Object.entries(mappingsObj).map(([sourceField, mapping]: [string, FieldMappingRecord]) => ({
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
    } */
    // Return empty array if no data available
    console.log('🔄 [DEBUG] No field mappings available - returning empty array');
    return [];
  }, [fieldMappingData, realFieldMappings]);

  // Set up WebSocket cache invalidation listener
  useEffect(() => {
    const importId = importData?.import_metadata?.import_id;
    if (!importId) return;

    // WebSocket cache invalidation (if enabled)
    let unsubscribeWebSocket: (() => void) | null = null;

    if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE') && subscribe) {
      console.log('🔗 Setting up WebSocket cache invalidation for field mappings:', importId);

      unsubscribeWebSocket = subscribe('field_mappings_updated', (event) => {
        console.log('🔄 WebSocket cache invalidation event received:', event);

        // Check if the event is for this specific import
        if (event.entity_id === importId || event.metadata?.import_id === importId) {
          console.log('🔄 Invalidating field mappings cache for import:', importId);

          queryClient.invalidateQueries({
            queryKey: ['field-mappings', importId],
            exact: true
          });
        }
      });
    }

    // Legacy cache invalidation function for bulk operations
    const invalidateFieldMappings = async () => {
      console.log('🔄 Manual invalidation of field mappings cache for import:', importId);
      await queryClient.invalidateQueries({
        queryKey: ['field-mappings', importId],
        exact: true
      });
    };

    // Attach to window for bulk operations to use (backward compatibility)
    interface WindowWithInvalidate extends Window {
      __invalidateFieldMappings?: () => Promise<void>;
    }
    if (typeof window !== 'undefined') {
      (window as WindowWithInvalidate).__invalidateFieldMappings = invalidateFieldMappings;
    }

    // Cleanup on unmount
    return () => {
      // Unsubscribe from WebSocket events
      if (unsubscribeWebSocket) {
        unsubscribeWebSocket();
      }

      // Clean up window function
      if (typeof window !== 'undefined') {
        delete (window as WindowWithInvalidate).__invalidateFieldMappings;
      }
    };
  }, [importData?.import_metadata?.import_id, queryClient, subscribe]);

  return {
    fieldMappings,
    realFieldMappings: realFieldMappings || [],
    isFieldMappingsLoading,
    fieldMappingsError,
    refetchFieldMappings
  };
};
