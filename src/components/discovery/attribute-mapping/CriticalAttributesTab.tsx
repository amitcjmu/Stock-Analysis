import React, { useMemo } from 'react';
import { Target, AlertTriangle } from 'lucide-react';
import ThreeColumnFieldMapper from './FieldMappingsTab/components/ThreeColumnFieldMapper/ThreeColumnFieldMapper';
import type { FieldMapping } from '../../../types/api/discovery/field-mapping-types';
import { useTargetFields } from '../../../hooks/discovery/attribute-mapping/useTargetFields';

interface CriticalAttributesTabProps {
  fieldMappings?: FieldMapping[];
  onMappingAction?: (mappingId: string, action: 'approve' | 'reject', rejectionReason?: string) => void;
  onMappingChange?: (mappingId: string, newTarget: string) => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  isAnalyzing?: boolean;
  flowId?: string | null;
  importCategory?: string;
}

const CriticalAttributesTab: React.FC<CriticalAttributesTabProps> = ({
  fieldMappings = [],
  onMappingAction,
  onMappingChange,
  onRefresh,
  isLoading = false,
  isAnalyzing = false,
  flowId,
  importCategory,
}) => {
  const {
    fields: availableFields,
  } = useTargetFields({ flowId, importCategory });
  // Define critical field names based on business requirements
  const criticalFieldNames = useMemo(() => new Set([
    // Core Identity Fields
    'asset_name', 'asset_type', 'asset_id', 'hostname', 'fqdn', 'name',
    // Network Fields
    'ip_address', 'mac_address', 'dns_name', 'subnet', 'vlan',
    // System Fields
    'operating_system', 'os_version', 'cpu_cores', 'memory_gb', 'storage_gb', 'architecture',
    // Location Fields
    'datacenter', 'region', 'environment', 'availability_zone', 'rack_location',
    // Business Fields
    'business_owner', 'business_unit', 'department', 'cost_center', 'technical_owner',
    // Migration Fields
    'criticality', 'business_criticality', 'migration_priority', 'migration_complexity',
    'migration_wave', 'six_r_strategy', 'migration_status',
    // Application Fields
    'application_name', 'technology_stack',
    // Performance Fields
    'cpu_utilization_percent', 'memory_utilization_percent', 'disk_iops', 'network_throughput_mbps',
    // Financial Fields
    'current_monthly_cost', 'estimated_cloud_cost'
  ]), []);

  // Filter field mappings to only include critical attributes
  const criticalFieldMappings = useMemo(() => {
    const safeFieldMappings = Array.isArray(fieldMappings) ? fieldMappings : [];

    const filtered = safeFieldMappings.filter(mapping => {
      // Support both snake_case (API format) and camelCase (legacy format)
      const targetField = (mapping.target_field || (mapping as any).targetAttribute || (mapping as any).targetField)?.toLowerCase();
      const sourceField = (mapping.source_field || (mapping as any).sourceField)?.toLowerCase();

      // Include if target field is critical, or if source field name suggests it might be critical
      return targetField && criticalFieldNames.has(targetField) ||
             sourceField && criticalFieldNames.has(sourceField);
    });

    // Normalize field mappings to ensure they have the correct structure for ThreeColumnFieldMapper
    return filtered.map((mapping, index) => {
      // Ensure the mapping has all required properties in snake_case format
      const sourceField = (mapping as any).source_field || (mapping as any).sourceField || '';
      const targetField = (mapping as any).target_field || (mapping as any).targetAttribute || (mapping as any).targetField || null;
      
      // Generate unique ID: use existing id, or create from fields, or use index as fallback
      const generateId = () => {
        if (mapping.id) {
          return mapping.id;
        }
        if (sourceField && targetField) {
          return `${sourceField}_${targetField}`;
        }
        if (sourceField) {
          return `${sourceField}_${index}`;
        }
        // Final fallback: use index to ensure uniqueness
        return `mapping_${index}`;
      };

      const normalized: any = {
        ...mapping,
        id: generateId(),
        source_field: sourceField,
        target_field: targetField,
        status: (mapping as any).status || 'pending',
        mapping_type: (mapping as any).mapping_type || (mapping as any).mappingType || 'auto',
        confidence_score: (mapping as any).confidence_score || (mapping as any).confidence || 0.5
      };
      return normalized;
    });
  }, [fieldMappings, criticalFieldNames]);

  // Filter available fields to only include critical ones
  const criticalAvailableFields = useMemo(() => {
    const safeAvailableFields = Array.isArray(availableFields) ? availableFields : [];

    return safeAvailableFields.filter(field => {
      const fieldName = field.name?.toLowerCase();
      return fieldName && criticalFieldNames.has(fieldName);
    });
  }, [availableFields, criticalFieldNames]);


  if (isAnalyzing) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Analyzing critical attributes...</p>
          <p className="text-sm text-gray-500 mt-2">
            AI agents are identifying migration-critical fields
          </p>
        </div>
      </div>
    );
  }

  if (criticalFieldMappings.length === 0) {
    return (
      <div className="text-center py-12">
        <Target className="h-16 w-16 mx-auto mb-4 text-gray-400" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Critical Attributes Found</h3>
        <p className="text-gray-600 mb-4">
          No field mappings match the critical attribute criteria yet.
        </p>
        <p className="text-sm text-gray-500">
          Complete field mappings in the Field Mappings tab to see critical attributes here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 p-4 rounded-lg border border-red-200">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-6 w-6 text-red-600" />
          <div>
            <h3 className="text-lg font-semibold text-red-900">Critical Attributes</h3>
            <p className="text-sm text-red-700">
              These attributes are essential for migration planning and must be mapped accurately.
              {criticalFieldMappings.length > 0 && (
                <span className="ml-2 font-medium">
                  {criticalFieldMappings.length} critical field{criticalFieldMappings.length !== 1 ? 's' : ''} identified
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Use the same ThreeColumnFieldMapper component with filtered data */}
      <ThreeColumnFieldMapper
        fieldMappings={criticalFieldMappings}
        availableFields={criticalAvailableFields}
        onMappingAction={onMappingAction}
        onMappingChange={onMappingChange}
        onRefresh={onRefresh}
      />

      {/* Footer Info */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <div className="flex items-start space-x-3">
          <Target className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900">Why These Fields Are Critical</h4>
            <p className="text-sm text-blue-700 mt-1">
              Critical attributes include identity fields (hostname, IP address), system specifications
              (CPU, memory, OS), business context (owner, environment, criticality), and migration planning
              fields (6R strategy, wave, priority). These fields are essential for accurate migration
              planning and cloud sizing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CriticalAttributesTab;
