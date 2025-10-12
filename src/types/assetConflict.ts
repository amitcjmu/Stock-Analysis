/**
 * Asset Conflict Resolution Types
 *
 * Types for handling duplicate asset detection and user-driven conflict resolution
 * during discovery flow CSV imports.
 *
 * CC: Matches backend schemas from app/schemas/asset_conflict.py
 */

/**
 * Asset data for comparison - partial snapshot with mergeable fields only
 * Aligns with DEFAULT_ALLOWED_MERGE_FIELDS from backend deduplication.py
 */
export interface AssetConflictData {
  // Core identification (display only, not mergeable)
  id?: string;
  name?: string;
  hostname?: string;
  asset_type?: string;

  // Technical specs (mergeable)
  operating_system?: string;
  os_version?: string;
  cpu_cores?: number;
  memory_gb?: number;
  storage_gb?: number;

  // Network info (mergeable)
  ip_address?: string;
  fqdn?: string;
  mac_address?: string;

  // Infrastructure (mergeable)
  environment?: string;
  location?: string;
  datacenter?: string;
  rack_location?: string;
  availability_zone?: string;

  // Business info (mergeable)
  business_owner?: string;
  technical_owner?: string;
  department?: string;
  application_name?: string;
  technology_stack?: string;
  criticality?: string;
  business_criticality?: string;

  // Migration planning (mergeable)
  six_r_strategy?: string;
  migration_priority?: number;
  migration_complexity?: number;
  migration_wave?: number;

  // Metadata (mergeable)
  description?: string;
  custom_attributes?: Record<string, unknown>;

  // Performance metrics (mergeable)
  cpu_utilization_percent?: number;
  memory_utilization_percent?: number;
  disk_iops?: number;
  network_throughput_mbps?: number;
  current_monthly_cost?: number;
  estimated_cloud_cost?: number;

  // Timestamps (display only)
  created_at?: string;
  updated_at?: string;
}

/**
 * Conflict types based on unique constraint violations
 */
export type ConflictType = 'hostname' | 'ip_address' | 'name';

/**
 * Full conflict detail with side-by-side comparison
 * Matches AssetConflictDetail from backend schemas
 */
export interface AssetConflict {
  conflict_id: string; // UUID
  conflict_type: ConflictType;
  conflict_key: string; // The value that caused the conflict
  existing_asset: AssetConflictData;
  new_asset: AssetConflictData;
}

/**
 * Resolution action types
 */
export type ResolutionAction = 'keep_existing' | 'replace_with_new' | 'merge';

/**
 * Field source selection for merge action
 */
export type FieldSource = 'existing' | 'new';

/**
 * Merge field selections for "merge" action
 * Key = field name, Value = which source to use
 */
export type MergeFieldSelections = Record<string, FieldSource>;

/**
 * Single conflict resolution request
 * Matches AssetConflictResolutionRequest from backend schemas
 */
export interface ConflictResolution {
  conflict_id: string; // UUID
  resolution_action: ResolutionAction;
  merge_field_selections?: MergeFieldSelections; // Required if action is "merge"
}

/**
 * Bulk resolution request payload
 * Matches BulkConflictResolutionRequest from backend schemas
 */
export interface BulkConflictResolutionRequest {
  resolutions: ConflictResolution[];
}

/**
 * Resolution response from backend
 * Matches ConflictResolutionResponse from backend schemas
 */
export interface ConflictResolutionResponse {
  resolved_count: number;
  total_requested: number;
  errors?: string[];
}

/**
 * List of mergeable field names - aligns with DEFAULT_ALLOWED_MERGE_FIELDS from backend
 * Fields NOT in this list cannot be merged (immutable identifiers, tenant context)
 */
export const MERGEABLE_FIELDS = [
  // Technical specs
  'operating_system',
  'os_version',
  'cpu_cores',
  'memory_gb',
  'storage_gb',
  // Network info
  'ip_address',
  'fqdn',
  'mac_address',
  // Infrastructure
  'environment',
  'location',
  'datacenter',
  'rack_location',
  'availability_zone',
  // Business info
  'business_owner',
  'technical_owner',
  'department',
  'application_name',
  'technology_stack',
  'criticality',
  'business_criticality',
  // Migration planning
  'six_r_strategy',
  'migration_priority',
  'migration_complexity',
  'migration_wave',
  // Metadata
  'description',
  'custom_attributes',
  // Performance metrics
  'cpu_utilization_percent',
  'memory_utilization_percent',
  'disk_iops',
  'network_throughput_mbps',
  'current_monthly_cost',
  'estimated_cloud_cost',
] as const;

/**
 * Never merge these fields - immutable identifiers and tenant context
 */
export const NEVER_MERGE_FIELDS = [
  'id',
  'client_account_id',
  'engagement_id',
  'flow_id',
  'master_flow_id',
  'discovery_flow_id',
  'assessment_flow_id',
  'planning_flow_id',
  'execution_flow_id',
  'raw_import_records_id',
  'created_at',
  'created_by',
  'name',
  'asset_name',
  'hostname', // Part of unique constraint - never merge
] as const;

/**
 * Helper to get display-friendly field labels
 */
export const FIELD_LABELS: Record<string, string> = {
  operating_system: 'Operating System',
  os_version: 'OS Version',
  cpu_cores: 'CPU Cores',
  memory_gb: 'Memory (GB)',
  storage_gb: 'Storage (GB)',
  ip_address: 'IP Address',
  fqdn: 'FQDN',
  mac_address: 'MAC Address',
  environment: 'Environment',
  location: 'Location',
  datacenter: 'Datacenter',
  rack_location: 'Rack Location',
  availability_zone: 'Availability Zone',
  business_owner: 'Business Owner',
  technical_owner: 'Technical Owner',
  department: 'Department',
  application_name: 'Application Name',
  technology_stack: 'Technology Stack',
  criticality: 'Criticality',
  business_criticality: 'Business Criticality',
  six_r_strategy: '6R Strategy',
  migration_priority: 'Migration Priority',
  migration_complexity: 'Migration Complexity',
  migration_wave: 'Migration Wave',
  description: 'Description',
  cpu_utilization_percent: 'CPU Utilization %',
  memory_utilization_percent: 'Memory Utilization %',
  disk_iops: 'Disk IOPS',
  network_throughput_mbps: 'Network Throughput (Mbps)',
  current_monthly_cost: 'Current Monthly Cost',
  estimated_cloud_cost: 'Estimated Cloud Cost',
};
