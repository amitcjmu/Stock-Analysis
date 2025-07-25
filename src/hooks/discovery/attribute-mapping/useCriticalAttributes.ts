import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../../contexts/AuthContext';
import { API_CONFIG, apiCall } from '../../../config/api';
import type { FieldMapping } from './useFieldMappings';

export interface CriticalAttribute {
  name: string;
  description: string;
  category: string;
  required: boolean;
  status: 'mapped' | 'partially_mapped' | 'unmapped';
  mapped_to: string;
  source_field: string;
  confidence: number;
  quality_score: number;
  completeness_percentage: number;
  mapping_type: 'approved' | 'ai_suggested' | 'unmapped';
  business_impact: 'high' | 'medium' | 'low';
  migration_critical: boolean;
}

export interface CriticalAttributesResult {
  criticalAttributes: CriticalAttribute[];
  isCriticalAttributesLoading: boolean;
  criticalAttributesError: unknown;
  refetchCriticalAttributes: () => Promise<unknown>;
}

/**
 * Hook for critical attributes calculation and management
 * Handles backend API data and fallback generation from field mappings
 */
export const useCriticalAttributes = (
  finalFlowId: string | null,
  realFieldMappings: unknown[],
  fieldMappings: FieldMapping[],
  fieldMappingData: unknown
): CriticalAttributesResult => {
  const { user, getAuthHeaders } = useAuth();

  // Fetch critical attributes from backend API
  const {
    data: criticalAttributesData,
    isLoading: isCriticalAttributesLoading,
    error: criticalAttributesError,
    refetch: refetchCriticalAttributes
  } = useQuery({
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
        criticalFieldsRequired: criticalFieldsForMigration.length
      });

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

        const criticalMappings = realFieldMappings.filter((mapping: { target_field?: string }) =>
          mapping.target_field && criticalFieldsForMigration.includes(mapping.target_field.toLowerCase())
        );

        console.log('🔍 Critical mappings filter result:', {
          input_mappings: realFieldMappings.length,
          filtered_critical_mappings: criticalMappings.length,
          critical_mapping_targets: criticalMappings.map(m => m.target_field?.toLowerCase())
        });

        const criticalAttrs = criticalMappings.map((mapping: {
          target_field?: string;
          source_field?: string;
          is_approved?: boolean;
          confidence?: number
        }) => ({
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
        const exactCriticalMappings = fieldMappings.filter((m: FieldMapping) =>
          m.targetAttribute && criticalFieldsForMigration.includes(m.targetAttribute.toLowerCase()) && m.status === 'approved'
        );

        // SECONDARY: Also include pending critical mappings (not just approved ones)
        const pendingCriticalMappings = fieldMappings.filter((m: FieldMapping) =>
          m.targetAttribute && criticalFieldsForMigration.includes(m.targetAttribute.toLowerCase()) && m.status !== 'approved' && m.status !== 'deleted'
        );

        // TERTIARY: Enhanced matching logic for other important fields
        const otherImportantMappings = fieldMappings.filter((mapping: FieldMapping) => {
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

        const criticalAttrs = criticalMappings.map((mapping: FieldMapping) => ({
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
        return Object.entries(fieldMappingData.critical_attributes).map(([name, mapping]: [string, {
          asset_field?: string;
          source_column?: string;
          confidence?: number;
        }]) => ({
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
        const mappedFieldMappings = fieldMappings.filter((mapping: FieldMapping) =>
          mapping.targetAttribute &&
          mapping.targetAttribute !== 'null' &&
          mapping.mapping_type !== 'unmapped' &&
          mapping.status !== 'deleted'
        );

        const allCriticalAttrs = mappedFieldMappings.map((mapping: FieldMapping) => ({
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

  return {
    criticalAttributes,
    isCriticalAttributesLoading,
    criticalAttributesError,
    refetchCriticalAttributes
  };
};
