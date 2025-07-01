/**
 * Field Compatibility Types for API v3
 * Handles backward compatibility for field name changes during database consolidation
 */

// Field mapping configurations
export interface FieldMapping {
  oldField: string;
  newField: string;
  valueTransform?: (value: any) => any;
  deprecated?: boolean;
}

// Field mappings for backward compatibility
export const FIELD_MAPPINGS: FieldMapping[] = [
  // DataImport field renames
  { oldField: 'source_filename', newField: 'filename' },
  { oldField: 'file_size_bytes', newField: 'file_size' },
  { oldField: 'file_type', newField: 'mime_type' },
  
  // Asset field renames
  { oldField: 'name', newField: 'asset_name' },
  { oldField: 'type', newField: 'asset_type' },
  { oldField: 'cpu_count', newField: 'cpu_cores' },
  { 
    oldField: 'memory_mb', 
    newField: 'memory_gb',
    valueTransform: (mb: number) => mb / 1024
  },
  { 
    oldField: 'storage_mb', 
    newField: 'storage_gb',
    valueTransform: (mb: number) => mb / 1024
  },
  
  // DiscoveryFlow field renames
  { oldField: 'flow_status', newField: 'status' },
  { oldField: 'phase', newField: 'current_phase' },
  { oldField: 'user_id', newField: 'created_by_user_id' },
  
  // Deprecated fields
  { oldField: 'is_mock', newField: '', deprecated: true },
  { oldField: 'legacy_field', newField: '', deprecated: true }
];

// Response types that include both old and new fields for compatibility
export interface BackwardCompatibleResponse<T> {
  data: T;
  _legacy?: Record<string, any>;
}

// Import response with backward compatibility
export interface DataImportCompatibleResponse {
  // New fields
  import_id: string;
  name: string;
  description?: string;
  source_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  
  // Multi-tenant context
  client_account_id: string;
  engagement_id: string;
  user_id?: string;
  
  // Data statistics
  total_records: number;
  valid_records: number;
  invalid_records: number;
  processed_records: number;
  
  // Quality metrics
  data_quality_score: number;
  validation_errors: Record<string, any>[];
  validation_warnings: Record<string, any>[];
  
  // Field analysis
  field_analysis: Record<string, any>;
  suggested_mappings: Record<string, string>;
  
  // Metadata with consolidated fields
  metadata: {
    filename: string;
    file_size: number;
    mime_type: string;
    source_system?: string;
    // Legacy field names for compatibility
    source_filename?: string;
    file_size_bytes?: number;
    file_type?: string;
  };
  
  // Associated flow
  flow_id?: string;
}

// Asset response with backward compatibility
export interface AssetCompatibleResponse {
  // New fields
  id: string;
  asset_name: string;
  asset_type: string;
  ip_address?: string;
  operating_system?: string;
  environment?: string;
  location?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;
  
  // Legacy fields for compatibility
  name?: string;
  type?: string;
  cpu_count?: number;
  memory_mb?: number;
  storage_mb?: number;
  
  // Multi-tenant context
  client_account_id: string;
  engagement_id: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

// Field mapping info response
export interface FieldMappingInfo {
  field_mappings: Record<string, string>;
  reverse_mappings: Record<string, string>;
  deprecated_fields: string[];
  unit_conversions: Record<string, string>;
}

// Utility type to add legacy fields to any response
export type WithLegacyFields<T> = T & {
  _legacy?: Record<string, any>;
};

// Helper function type definitions
export interface FieldCompatibilityHelpers {
  applyRequestCompatibility: (data: Record<string, any>) => Record<string, any>;
  applyResponseCompatibility: (data: Record<string, any>, includeLegacy?: boolean) => Record<string, any>;
  getFieldMappingInfo: () => FieldMappingInfo;
}