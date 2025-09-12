import { useMemo, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '../../../contexts/AuthContext';
import { apiCall } from '../../../config/api';
import { apiClient } from '../../../lib/api/apiClient';
import { useWebSocket } from '../../useWebSocket';
import { isCacheFeatureEnabled } from '@/constants/features';
import type { FormFieldValue } from '@/types/shared/form-types';
import type {
  FieldMappingsResponse,
  FieldMappingItem,
  FieldMapping,
  FieldMappingsResult as StandardFieldMappingsResult,
  FieldMappingType,
  FieldMappingStatus
} from '@/types/api/discovery/field-mapping-types';
import {
  transformToFrontendResponse,
  isFieldMappingsResponse,
  isValidConfidenceScore
} from '@/types/api/discovery/field-mapping-types';

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

// Use standardized FieldMapping interface from types
// (removed duplicate interface definition to avoid conflicts)

export interface FieldMappingsResult {
  fieldMappings: FieldMapping[];
  realFieldMappings: RawFieldMapping[];
  isFieldMappingsLoading: boolean;
  fieldMappingsError: Error | null;
  refetchFieldMappings: () => Promise<RawFieldMapping[]>;

  // Enhanced type safety fields
  backendResponse?: FieldMappingsResponse;
  validationErrors?: string[];
  transformationApplied?: boolean;
}

/**
 * Hook for field mappings data fetching and management
 * Handles both API field mappings and flow state fallbacks
 */
// Debug logging flag - disable in production
const DEBUG_LOGS = process.env.NODE_ENV !== 'production' || process.env.NEXT_PUBLIC_DEBUG_LOGS === 'true';

// Debug logging helper
const debugLog = (...args: unknown[]) => {
  if (DEBUG_LOGS) {
    console.log(...args);
  }
};

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
        debugLog('🔍 Fetching field mappings using flow ID:', effectiveFlowId);
        try {
          const response = await apiCall(`/api/v1/unified-discovery/flows/${effectiveFlowId}/field-mappings`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              ...getAuthHeaders()
            }
          });

          // Validate response using type guard
          if (isFieldMappingsResponse(response)) {
            debugLog('✅ Fetched valid field mappings from unified discovery:', {
              flow_id: response.flow_id,
              count: response.count,
              success: response.success
            });

            // Use proper transformation utility for type safety
            const frontendResult = transformToFrontendResponse(response);

            // Convert to legacy format for backward compatibility
            const legacyMappings = frontendResult.field_mappings.map(mapping => ({
              id: mapping.id,
              // Include both camelCase and snake_case for compatibility
              sourceField: mapping.source_field,
              source_field: mapping.source_field,
              targetAttribute: mapping.target_field,
              target_field: mapping.target_field,
              target_attribute: mapping.target_field,
              confidence: mapping.confidence_score,
              is_approved: mapping.status === 'approved',
              status: mapping.status,
              mapping_type: mapping.mapping_type,
              transformation_rule: mapping.transformation,
              validation_rule: mapping.validation_rules,
              // Legacy fields for compatibility
              sample_values: mapping.sample_values || [],
              ai_reasoning: mapping.ai_reasoning || '',
              is_user_defined: mapping.is_user_defined || false,
              user_feedback: mapping.user_feedback,
              validation_method: mapping.validation_method || 'semantic_analysis',
              is_validated: mapping.is_validated || false
            }));

            debugLog('✅ Transformed unified discovery mappings with type safety:', {
              original_count: response.count,
              transformed_count: legacyMappings.length,
              validation_applied: true,
              sample_transformed: legacyMappings.slice(0, 2)
            });

            return legacyMappings;
          } else if (response?.field_mappings) {
            // Fallback for invalid response structure
            console.warn('⚠️ Received invalid field mappings response structure, using fallback processing');

            const transformedMappings = response.field_mappings.map((m: unknown) => {
              const mapping = m as Record<string, unknown>;
              const confidenceScore = isValidConfidenceScore(mapping.confidence_score) ? mapping.confidence_score : 0.5;

              return {
                id: mapping.id || `${mapping.source_field}_${mapping.target_field || 'unmapped'}`,
                sourceField: mapping.source_field,
                source_field: mapping.source_field,
                targetAttribute: mapping.target_field,
                target_field: mapping.target_field,
                target_attribute: mapping.target_field,
                confidence: confidenceScore,
                is_approved: mapping.status === 'approved',
                status: mapping.status || (mapping.target_field ? 'pending' : 'unmapped'),
                mapping_type: mapping.mapping_type || 'auto',
                transformation_rule: mapping.transformation,
                validation_rule: mapping.validation_rules,
                sample_values: [],
                ai_reasoning: '',
                is_user_defined: false,
                user_feedback: null,
                validation_method: 'semantic_analysis',
                is_validated: false
              };
            });

            return transformedMappings;
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

      debugLog('🔍 Fetching field mappings for import ID:', importId);

      try {
        // Use new API client if custom cache is disabled, otherwise use legacy
        const mappings = isCacheFeatureEnabled('DISABLE_CUSTOM_CACHE')
          ? await apiClient.get(`/data-import/field-mappings/imports/${importId}/mappings`)
          : await apiCall(`/api/v1/data-import/field-mappings/imports/${importId}/mappings`, {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
              }
            });

        debugLog('✅ Fetched field mappings from API:', {
          import_id: importId,
          mappings_count: Array.isArray(mappings) ? mappings.length : 'not an array',
          mappings_sample: Array.isArray(mappings) ? mappings.slice(0, 2) : mappings
        });

        // No filtering - show all fields from backend

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

          debugLog('📊 Raw import data retrieved:', {
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

            debugLog('✅ Raw import data retrieved:', {
              actual_csv_fields: actualCsvFields,
              field_count: actualCsvFields.length
            });
          }

          // If we have raw data, ensure all CSV fields are represented as mappings
          if (rawImportData?.sample_record || rawImportData?.raw_data) {
            const sampleRecord = rawImportData.sample_record || rawImportData.raw_data;
            const allCsvFields = Object.keys(sampleRecord);
            const mappedFieldNames = (mappings || []).map(m => m.source_field);

            // Log unmapped fields but don't create placeholder mappings
            const missingFields = allCsvFields.filter(field => !mappedFieldNames.includes(field));

            if (missingFields.length > 0) {
              console.warn(`⚠️ Found ${missingFields.length} unmapped CSV fields - backend should handle these:`, missingFields);
              // Don't create placeholder mappings - let the backend be the single source of truth
            }
          }
        } catch (rawDataError) {
          console.warn('⚠️ Could not fetch raw import data:', rawDataError);
        }

        // Return all mappings without filtering
        if (Array.isArray(mappings) && mappings.length > 0) {
          console.log('✅ Returning all field mappings from API:', {
            count: mappings.length,
            sample_mappings: mappings.slice(0, 3)
          });
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

    // Use the API field mappings data without any filtering
    if (realFieldMappings && Array.isArray(realFieldMappings)) {
      console.log('🔍 [DEBUG] Using all field mappings from API:', {
        count: realFieldMappings.length
      });

      const mappedData = realFieldMappings.map((mapping, index) => {
        // Enhanced type validation for each mapping
        const sourceField = String(mapping.sourceField || mapping.source_field || 'Unknown Field');
        const targetField = mapping.targetAttribute || mapping.target_field || mapping.target_attribute;
        const isUnmapped = targetField === 'UNMAPPED' || targetField === null || targetField === undefined;

        // Validate confidence score using type guard
        const confidenceScore = isValidConfidenceScore(mapping.confidence)
          ? mapping.confidence
          : 0.5;

        // Validate mapping type
        const mappingType = mapping.mapping_type as FieldMappingType ||
          (isUnmapped ? 'auto' : 'auto');

        // Validate status
        const validStatuses: FieldMappingStatus[] = ['suggested', 'approved', 'rejected', 'pending', 'unmapped'];
        let finalStatus: FieldMappingStatus = 'pending';

        if (mapping.status && validStatuses.includes(mapping.status as FieldMappingStatus)) {
          finalStatus = mapping.status as FieldMappingStatus;
        } else if (isUnmapped) {
          finalStatus = 'unmapped';
        } else if (mapping.is_approved === true) {
          finalStatus = 'approved';
        }

        const transformedMapping: FieldMapping = {
          id: mapping.id || `mapping_${index}_${sourceField}_${targetField || 'unmapped'}`,
          source_field: sourceField,
          target_field: isUnmapped ? null : (targetField || null),
          confidence_score: confidenceScore,
          mapping_type: mappingType,
          transformation: mapping.transformation_rule || null,
          validation_rules: mapping.validation_rule || null,
          status: finalStatus,
          sample_values: mapping.sample_values || [],
          ai_reasoning: mapping.ai_reasoning || (isUnmapped
            ? `Field "${sourceField}" needs mapping assignment`
            : `AI suggested mapping to ${targetField}`),
          is_user_defined: mapping.is_user_defined || false,
          user_feedback: mapping.user_feedback || null,
          validation_method: mapping.validation_method || 'semantic_analysis',
          is_validated: mapping.is_validated || mapping.is_approved === true,
          metadata: {
            legacyMapping: true,
            originalData: mapping
          }
        };

        return transformedMapping;
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
              id: uuidv4(), // Generate proper UUID
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
          id: uuidv4(), // Generate proper UUID
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
    // Use the same cache key that the query uses (flow ID takes precedence)
    const cacheKey = effectiveFlowId || importData?.import_metadata?.import_id;
    if (!cacheKey) return;

    // WebSocket cache invalidation (if enabled)
    let unsubscribeWebSocket: (() => void) | null = null;

    if (isCacheFeatureEnabled('ENABLE_WEBSOCKET_CACHE') && subscribe) {
      console.log('🔗 Setting up WebSocket cache invalidation for field mappings:', cacheKey);

      unsubscribeWebSocket = subscribe('field_mappings_updated', (event) => {
        console.log('🔄 WebSocket cache invalidation event received:', event);

        // Check if the event is for this specific flow/import
        if (event.entity_id === cacheKey ||
            event.metadata?.import_id === cacheKey ||
            event.metadata?.flow_id === cacheKey) {
          console.log('🔄 Invalidating field mappings cache for:', cacheKey);

          queryClient.invalidateQueries({
            queryKey: ['field-mappings', cacheKey],
            exact: true
          });
        }
      });
    }

    // Legacy cache invalidation function for bulk operations
    const invalidateFieldMappings = async () => {
      console.log('🔄 Manual invalidation of field mappings cache for:', cacheKey);
      await queryClient.invalidateQueries({
        queryKey: ['field-mappings', cacheKey],
        exact: true
      });
      // Also trigger a refetch to ensure fresh data
      await refetchFieldMappings();
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
  }, [effectiveFlowId, importData?.import_metadata?.import_id, queryClient, subscribe, refetchFieldMappings]);

  return {
    fieldMappings,
    realFieldMappings: realFieldMappings || [],
    isFieldMappingsLoading,
    fieldMappingsError,
    refetchFieldMappings,

    // Enhanced type safety information
    backendResponse: undefined, // Could be populated with validated response
    validationErrors: [], // Could track validation issues
    transformationApplied: !!fieldMappings.length // Indicates if transformations were applied
  };
};
