import React from 'react'
import type { ReactNode } from 'react';
import { createContext, useContext, useState } from 'react'

// Types
interface TargetField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  category: string;
  is_custom?: boolean;
}

interface FieldOptionsContextType {
  availableFields: TargetField[];
  isLoading: boolean;
  error: string | null;
  refetchFields: () => Promise<void>;
  lastUpdated: Date | null;
}

const FieldOptionsContext = createContext<FieldOptionsContextType | undefined>(undefined);

// Complete asset fields list based on backend Asset model
// This eliminates the need for API calls on every app start
const ASSET_TARGET_FIELDS: TargetField[] = [
  // Identity fields (Critical for migration)
  { name: 'name', type: 'string', required: true, description: 'Asset name', category: 'identification' },
  { name: 'asset_name', type: 'string', required: false, description: 'Asset display name', category: 'identification' },
  { name: 'hostname', type: 'string', required: false, description: 'Network hostname', category: 'identification' },
  { name: 'fqdn', type: 'string', required: false, description: 'Fully qualified domain name', category: 'identification' },
  { name: 'asset_type', type: 'string', required: true, description: 'Type of asset (server, database, application, etc.)', category: 'identification' },
  { name: 'description', type: 'string', required: false, description: 'Asset description', category: 'identification' },

  // Network fields (Critical for migration)
  { name: 'ip_address', type: 'string', required: false, description: 'IP address (supports IPv6)', category: 'network' },
  { name: 'mac_address', type: 'string', required: false, description: 'MAC address', category: 'network' },

  // Location and Environment fields (Critical for migration)
  { name: 'environment', type: 'string', required: false, description: 'Environment (prod, dev, test)', category: 'environment' },
  { name: 'location', type: 'string', required: false, description: 'Physical location', category: 'environment' },
  { name: 'datacenter', type: 'string', required: false, description: 'Data center', category: 'environment' },
  { name: 'rack_location', type: 'string', required: false, description: 'Rack location', category: 'environment' },
  { name: 'availability_zone', type: 'string', required: false, description: 'Availability zone', category: 'environment' },

  // Technical specifications (from Azure Migrate)
  { name: 'operating_system', type: 'string', required: false, description: 'Operating system', category: 'technical' },
  { name: 'os_version', type: 'string', required: false, description: 'OS version', category: 'technical' },
  { name: 'cpu_cores', type: 'number', required: false, description: 'Number of CPU cores', category: 'technical' },
  { name: 'memory_gb', type: 'number', required: false, description: 'Memory in GB', category: 'technical' },
  { name: 'storage_gb', type: 'number', required: false, description: 'Storage in GB', category: 'technical' },

  // Business information (Critical for migration)
  { name: 'business_owner', type: 'string', required: false, description: 'Business owner', category: 'business' },
  { name: 'technical_owner', type: 'string', required: false, description: 'Technical owner', category: 'business' },
  { name: 'department', type: 'string', required: false, description: 'Department', category: 'business' },
  { name: 'application_name', type: 'string', required: false, description: 'Application name', category: 'application' },
  { name: 'technology_stack', type: 'string', required: false, description: 'Technology stack', category: 'application' },
  { name: 'criticality', type: 'string', required: false, description: 'Business criticality (low, medium, high, critical)', category: 'business' },
  { name: 'business_criticality', type: 'string', required: false, description: 'Business criticality level', category: 'business' },
  { name: 'custom_attributes', type: 'string', required: false, description: 'Custom attributes captured during import', category: 'business' },

  // Migration assessment (Critical for migration)
  { name: 'six_r_strategy', type: 'string', required: false, description: '6R migration strategy', category: 'migration' },
  { name: 'mapping_status', type: 'string', required: false, description: 'Mapping status (pending, in_progress, completed)', category: 'migration' },
  { name: 'migration_priority', type: 'number', required: false, description: 'Migration priority (1-10 scale)', category: 'migration' },
  { name: 'migration_complexity', type: 'string', required: false, description: 'Migration complexity (low, medium, high)', category: 'migration' },
  { name: 'migration_wave', type: 'number', required: false, description: 'Migration wave number', category: 'migration' },
  { name: 'sixr_ready', type: 'string', required: false, description: '6R readiness status', category: 'migration' },

  // Status and ownership
  { name: 'status', type: 'string', required: false, description: 'Operational status', category: 'status' },
  { name: 'migration_status', type: 'string', required: false, description: 'Migration status', category: 'status' },

  // Dependencies and relationships (Critical for migration)
  { name: 'dependencies', type: 'string', required: false, description: 'List of dependent asset IDs or names', category: 'dependencies' },
  { name: 'related_assets', type: 'string', required: false, description: 'Related CI items', category: 'dependencies' },

  // Discovery metadata
  { name: 'discovery_method', type: 'string', required: false, description: 'Discovery method (network_scan, agent, manual, import)', category: 'discovery' },
  { name: 'discovery_source', type: 'string', required: false, description: 'Tool or system that discovered the asset', category: 'discovery' },
  { name: 'discovery_timestamp', type: 'string', required: false, description: 'Discovery timestamp', category: 'discovery' },

  // Performance and utilization (from Azure Migrate)
  { name: 'cpu_utilization_percent', type: 'number', required: false, description: 'CPU utilization percentage', category: 'performance' },
  { name: 'memory_utilization_percent', type: 'number', required: false, description: 'Memory utilization percentage', category: 'performance' },
  { name: 'disk_iops', type: 'number', required: false, description: 'Disk IOPS', category: 'performance' },
  { name: 'network_throughput_mbps', type: 'number', required: false, description: 'Network throughput in Mbps', category: 'performance' },

  // Data quality metrics
  { name: 'completeness_score', type: 'number', required: false, description: 'Data completeness score', category: 'ai_insights' },
  { name: 'quality_score', type: 'number', required: false, description: 'Data quality score', category: 'ai_insights' },

  // Cost information
  { name: 'current_monthly_cost', type: 'number', required: false, description: 'Current monthly cost', category: 'cost' },
  { name: 'estimated_cloud_cost', type: 'number', required: false, description: 'Estimated cloud cost', category: 'cost' },

  // Import and processing metadata
  { name: 'source_filename', type: 'string', required: false, description: 'Source filename', category: 'metadata' },
  { name: 'raw_data', type: 'string', required: false, description: 'Original imported data', category: 'metadata' },
  { name: 'field_mappings_used', type: 'string', required: false, description: 'Field mappings applied during import', category: 'metadata' },

  // Multi-tenant and flow tracking (typically not user-mapped)
  { name: 'client_account_id', type: 'string', required: false, description: 'Client account ID', category: 'system' },
  { name: 'engagement_id', type: 'string', required: false, description: 'Engagement ID', category: 'system' },
  { name: 'flow_id', type: 'string', required: false, description: 'Discovery flow ID', category: 'system' },
  { name: 'master_flow_id', type: 'string', required: false, description: 'Master flow ID', category: 'system' },
  { name: 'source_phase', type: 'string', required: false, description: 'Source phase', category: 'system' },
  { name: 'current_phase', type: 'string', required: false, description: 'Current phase', category: 'system' },
  { name: 'phase_context', type: 'string', required: false, description: 'Phase context', category: 'system' },

  // Audit fields (typically not user-mapped)
  { name: 'created_at', type: 'string', required: false, description: 'Creation timestamp', category: 'system' },
  { name: 'updated_at', type: 'string', required: false, description: 'Update timestamp', category: 'system' },
  { name: 'imported_by', type: 'string', required: false, description: 'User who imported the asset', category: 'system' },
  { name: 'imported_at', type: 'string', required: false, description: 'Import timestamp', category: 'system' },
  { name: 'created_by', type: 'string', required: false, description: 'User who created the asset', category: 'system' },
  { name: 'updated_by', type: 'string', required: false, description: 'User who last updated the asset', category: 'system' }
];

interface FieldOptionsProviderProps {
  children: ReactNode;
}

export const FieldOptionsProvider: React.FC<FieldOptionsProviderProps> = ({ children }) => {
  // Use hardcoded fields directly - no API calls needed
  const [availableFields] = useState<TargetField[]>(ASSET_TARGET_FIELDS);
  const [isLoading] = useState(false); // Always false since no API calls
  const [error] = useState<string | null>(null); // Always null since no API calls
  const [lastUpdated] = useState<Date | null>(new Date()); // Always current time

  console.log('✅ FieldOptionsProvider - Using hardcoded asset fields list with', ASSET_TARGET_FIELDS.length, 'fields');

  const refetchFields = async () => {
    console.log('🔄 FieldOptionsProvider - Refetch requested but using hardcoded fields');
    // No-op since we're using hardcoded fields
  };

  return (
    <FieldOptionsContext.Provider
      value={{
        availableFields,
        isLoading,
        error,
        refetchFields,
        lastUpdated
      }}
    >
      {children}
    </FieldOptionsContext.Provider>
  );
};

export const useFieldOptions = (): FieldOptionsContextType => {
  const context = useContext(FieldOptionsContext);
  if (context === undefined) {
    throw new Error('useFieldOptions must be used within a FieldOptionsProvider');
  }
  return context;
};

// Export types for use in other components
export type { TargetField };
