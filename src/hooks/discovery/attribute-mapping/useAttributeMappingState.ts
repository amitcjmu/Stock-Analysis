import { useEffect, useMemo } from 'react';
import { FieldMapping } from './useFieldMappings';

export interface MappingProgress {
  total: number;
  mapped: number;
  critical_mapped: number;
  pending: number;
  accuracy: number;
}

export interface AttributeMappingStateResult {
  mappingProgress: MappingProgress;
  agenticData: { attributes: unknown[] };
  crewAnalysis: unknown[];
  isAgenticLoading: boolean;
  isFlowStateLoading: boolean;
  isAnalyzing: boolean;
  agenticError: unknown;
  flowStateError: unknown;
  availableDataImports: unknown[];
  selectedDataImportId: string | null;
  hasActiveFlow: boolean;
  currentPhase: string;
  flowProgress: number;
  agentClarifications: unknown[];
  isClarificationsLoading: boolean;
  clarificationsError: unknown;
}

/**
 * Hook for centralized attribute mapping state management
 * Handles progress tracking, loading states, and error handling
 */
export const useAttributeMappingState = (
  fieldMappings: FieldMapping[],
  realFieldMappings: unknown[],
  fieldMappingData: any,
  flow: any,
  flowList: unknown[],
  effectiveFlowId: string | null,
  isFlowLoading: boolean,
  isFlowListLoading: boolean,
  isImportDataLoading: boolean,
  isFieldMappingsLoading: boolean,
  flowError: any,
  flowListError: any,
  importDataError: any,
  fieldMappingsError: any
): AttributeMappingStateResult => {

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
      const approved = fieldMappings?.filter((m: unknown) => m.status === 'approved').length || 0;
      const pending = fieldMappings?.filter((m: unknown) => m.status === 'pending').length || 0;
      const unmapped = fieldMappings?.filter((m: unknown) => m.status === 'unmapped').length || 0;
      
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
      const criticalMapped = fieldMappings?.filter((m: unknown) => 
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

  // Agent clarifications (placeholder)
  const agentClarifications = [];
  const isClarificationsLoading = false;
  const clarificationsError = null;

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
  }, [flow, fieldMappings, realFieldMappings, agenticData, fieldMappingData]);

  return {
    mappingProgress,
    agenticData,
    crewAnalysis,
    isAgenticLoading,
    isFlowStateLoading,
    isAnalyzing,
    agenticError,
    flowStateError,
    availableDataImports,
    selectedDataImportId,
    hasActiveFlow: !!flow,
    currentPhase: flow?.next_phase,
    flowProgress: flow?.progress_percentage || 0,
    agentClarifications,
    isClarificationsLoading,
    clarificationsError
  };
};