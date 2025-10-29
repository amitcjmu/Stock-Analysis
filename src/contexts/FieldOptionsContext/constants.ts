/**
 * Field Options Constants
 * Static data for asset target fields
 */

import type { TargetField } from './types';

// Complete asset fields list based on backend Asset model
// This eliminates the need for API calls on every app start
export const ASSET_TARGET_FIELDS: TargetField[] = [
  // Identity fields(Critical for migration): any { name: 'name', type: 'string', required: true, description: 'Asset name', category: 'identification' },
  { name: 'asset_name', type: 'string', required: false, description: 'Asset display name', category: 'identification' },
  { name: 'hostname', type: 'string', required: false, description: 'Network hostname', category: 'identification' },
  { name: 'fqdn', type: 'string', required: false, description: 'Fully qualified domain name', category: 'identification' },
  { name: 'asset_type', type: 'string', required: true, description: 'Type of asset (server, database, application, etc.)', category: 'identification' },
  { name: 'description', type: 'string', required: false, description: 'Asset description', category: 'identification' },

  // Network fields(Critical for migration): any { name: 'ip_address', type: 'string', required: false, description: 'IP address (supports IPv6)', category: 'network' },
  { name: 'mac_address', type: 'string', required: false, description: 'MAC address', category: 'network' },

  // Location and Environment fields(Critical for migration): any { name: 'environment', type: 'string', required: false, description: 'Environment (prod, dev, test)', category: 'environment' },
  { name: 'location', type: 'string', required: false, description: 'Physical location', category: 'environment' },
  { name: 'datacenter', type: 'string', required: false, description: 'Data center', category: 'environment' },
  { name: 'rack_location', type: 'string', required: false, description: 'Rack location', category: 'environment' },
  { name: 'availability_zone', type: 'string', required: false, description: 'Availability zone', category: 'environment' },
  { name: 'security_zone', type: 'string', required: false, description: 'Security zone classification (DMZ, trusted, restricted, etc.)', category: 'security' },

  // Technical specifications(from Azure Migrate): any { name: 'operating_system', type: 'string', required: false, description: 'Operating system name and version (e.g., Windows Server 2019, RHEL 8)', category: 'technical' },
  { name: 'os_version', type: 'string', required: false, description: 'OS version', category: 'technical' },
  { name: 'cpu_cores', type: 'number', required: false, description: 'Number of CPU cores', category: 'technical' },
  { name: 'memory_gb', type: 'number', required: false, description: 'Memory in GB', category: 'technical' },
  { name: 'storage_gb', type: 'number', required: false, description: 'Total storage in GB', category: 'technical' },
  { name: 'storage_used_gb', type: 'number', required: false, description: 'Used storage in GB', category: 'technical' },
  { name: 'storage_free_gb', type: 'number', required: false, description: 'Free storage space in GB', category: 'technical' },
  { name: 'lifecycle', type: 'string', required: false, description: 'Asset lifecycle: Retire, Replace, Retain, Invest', category: 'technical' },
  { name: 'hosting_model', type: 'string', required: false, description: 'Hosting model: OnPremises, Cloud, Hybrid, Colo, Managed', category: 'technical' },
  { name: 'server_role', type: 'string', required: false, description: 'Server role: Web, App, Database, Citrix, FileServer, DomainController', category: 'technical' },
  { name: 'tshirt_size', type: 'string', required: false, description: 'T-shirt sizing: XS, S, M, L, XL, XXL', category: 'technical' },
  { name: 'backup_policy', type: 'string', required: false, description: 'Backup policy and schedule', category: 'technical' },
  { name: 'database_type', type: 'string', required: false, description: 'Database type (MySQL, PostgreSQL, Oracle, etc.)', category: 'database' },
  { name: 'database_version', type: 'string', required: false, description: 'Database version', category: 'database' },
  { name: 'database_size_gb', type: 'number', required: false, description: 'Database size in GB', category: 'database' },

  // Business information(Critical for migration): any { name: 'business_owner', type: 'string', required: false, description: 'Business owner', category: 'business' },
  { name: 'technical_owner', type: 'string', required: false, description: 'Technical owner', category: 'business' },
  { name: 'department', type: 'string', required: false, description: 'Department', category: 'business' },
  { name: 'business_unit', type: 'string', required: false, description: 'Business unit or division', category: 'business' },
  { name: 'vendor', type: 'string', required: false, description: 'Vendor or manufacturer', category: 'business' },
  { name: 'risk_level', type: 'string', required: false, description: 'Migration risk level: Low, Medium, High, Critical', category: 'business' },
  { name: 'application_name', type: 'string', required: false, description: 'Application name', category: 'application' },
  { name: 'application_type', type: 'string', required: false, description: 'Application type: COTS, Custom, Custom-COTS, SaaS, Others', category: 'application' },
  { name: 'technology_stack', type: 'string', required: false, description: 'Technology stack', category: 'application' },
  { name: 'criticality', type: 'string', required: false, description: 'Business criticality (low, medium, high, critical)', category: 'business' },
  { name: 'business_criticality', type: 'string', required: false, description: 'Business criticality level', category: 'business' },
  { name: 'custom_attributes', type: 'string', required: false, description: 'Custom attributes captured during import', category: 'business' },

  // Migration assessment(Critical for migration): any { name: 'six_r_strategy', type: 'string', required: false, description: '6R migration strategy', category: 'migration' },
  { name: 'mapping_status', type: 'string', required: false, description: 'Mapping status (pending, in_progress, completed)', category: 'migration' },
  { name: 'migration_priority', type: 'number', required: false, description: 'Migration priority (1-10 scale)', category: 'migration' },
  { name: 'migration_complexity', type: 'string', required: false, description: 'Migration complexity (low, medium, high)', category: 'migration' },
  { name: 'migration_wave', type: 'number', required: false, description: 'Migration wave number', category: 'migration' },
  { name: 'sixr_ready', type: 'string', required: false, description: '6R readiness status', category: 'migration' },
  { name: 'has_saas_replacement', type: 'boolean', required: false, description: 'Has SaaS replacement available', category: 'migration' },
  { name: 'proposed_treatmentplan_rationale', type: 'string', required: false, description: 'Treatment plan rationale and justification', category: 'migration' },
  { name: 'tech_debt_flags', type: 'string', required: false, description: 'Technical debt flags and indicators', category: 'migration' },
  { name: 'assessment_readiness', type: 'string', required: false, description: 'Cloud/migration readiness assessment status', category: 'assessment' },
  { name: 'assessment_readiness_score', type: 'number', required: false, description: 'Cloud/migration readiness score', category: 'assessment' },
  { name: 'assessment_blockers', type: 'string', required: false, description: 'Assessment blockers and issues', category: 'assessment' },
  { name: 'assessment_recommendations', type: 'string', required: false, description: 'Assessment recommendations', category: 'assessment' },

  // Status and ownership
  { name: 'status', type: 'string', required: false, description: 'Operational status', category: 'status' },
  { name: 'migration_status', type: 'string', required: false, description: 'Migration status', category: 'status' },

  // Dependencies and relationships(Critical for migration): any { name: 'dependencies', type: 'string', required: false, description: 'List of dependent asset IDs or names', category: 'dependencies' },
  { name: 'related_assets', type: 'string', required: false, description: 'Related CI items', category: 'dependencies' },

  // Discovery metadata
  { name: 'discovery_method', type: 'string', required: false, description: 'Discovery method (network_scan, agent, manual, import)', category: 'discovery' },
  { name: 'discovery_source', type: 'string', required: false, description: 'Tool or system that discovered the asset', category: 'discovery' },
  { name: 'discovery_timestamp', type: 'string', required: false, description: 'Discovery timestamp', category: 'discovery' },
  { name: 'discovery_status', type: 'string', required: false, description: 'Discovery process status', category: 'discovery' },
  { name: 'discovered_at', type: 'string', required: false, description: 'When the asset was discovered', category: 'discovery' },
  { name: 'discovery_completed_at', type: 'string', required: false, description: 'When discovery completed', category: 'discovery' },

  // Performance and utilization(from Azure Migrate): any { name: 'cpu_utilization_percent', type: 'number', required: false, description: 'CPU utilization percentage', category: 'performance' },
  { name: 'cpu_utilization_percent_max', type: 'number', required: false, description: 'Maximum CPU utilization percentage', category: 'performance' },
  { name: 'memory_utilization_percent', type: 'number', required: false, description: 'Memory utilization percentage', category: 'performance' },
  { name: 'memory_utilization_percent_max', type: 'number', required: false, description: 'Maximum memory utilization percentage', category: 'performance' },
  { name: 'disk_iops', type: 'number', required: false, description: 'Disk IOPS', category: 'performance' },
  { name: 'network_throughput_mbps', type: 'number', required: false, description: 'Network throughput in Mbps', category: 'performance' },

  // Data quality metrics
  { name: 'completeness_score', type: 'number', required: false, description: 'Data completeness score', category: 'ai_insights' },
  { name: 'quality_score', type: 'number', required: false, description: 'Data quality score', category: 'ai_insights' },
  { name: 'confidence_score', type: 'number', required: false, description: 'AI confidence score', category: 'ai_insights' },
  { name: 'complexity_score', type: 'number', required: false, description: 'Migration complexity score', category: 'ai_insights' },

  // Security and Compliance
  { name: 'pii_flag', type: 'boolean', required: false, description: 'Contains personally identifiable information (PII)', category: 'security' },
  { name: 'application_data_classification', type: 'string', required: false, description: 'Data classification level (public, internal, confidential, restricted)', category: 'security' },

  // Cost information
  { name: 'current_monthly_cost', type: 'number', required: false, description: 'Current monthly cost', category: 'cost' },
  { name: 'estimated_cloud_cost', type: 'number', required: false, description: 'Estimated cloud cost', category: 'cost' },
  { name: 'annual_cost_estimate', type: 'number', required: false, description: 'Annual cost estimate', category: 'cost' },

  // Additional CMDB metadata
  { name: 'asset_tags', type: 'string', required: false, description: 'Asset tags for categorization and search', category: 'metadata' },
  { name: 'technical_details', type: 'string', required: false, description: 'Additional technical details and specifications', category: 'metadata' },

  // Asset Resilience (Related Table)
  { name: 'rto_minutes', type: 'number', required: false, description: 'Recovery Time Objective in minutes (Resilience)', category: 'resilience' },
  { name: 'rpo_minutes', type: 'number', required: false, description: 'Recovery Point Objective in minutes (Resilience)', category: 'resilience' },
  { name: 'sla_json', type: 'string', required: false, description: 'SLA details and targets (Resilience)', category: 'resilience' },

  // Asset Contacts (Related Table)
  { name: 'contact_type', type: 'string', required: false, description: 'Contact role type - business_owner, technical_owner (Contacts)', category: 'contacts' },
  { name: 'contact_email', type: 'string', required: false, description: 'Contact email address (Contacts)', category: 'contacts' },
  { name: 'contact_name', type: 'string', required: false, description: 'Contact person name (Contacts)', category: 'contacts' },
  { name: 'contact_phone', type: 'string', required: false, description: 'Contact phone number (Contacts)', category: 'contacts' },

  // Asset EOL Assessments (Related Table)
  { name: 'technology_component', type: 'string', required: false, description: 'Technology component name (EOL)', category: 'eol_assessment' },
  { name: 'eol_date', type: 'string', required: false, description: 'End-of-life date (EOL)', category: 'eol_assessment' },
  { name: 'eol_risk_level', type: 'string', required: false, description: 'EOL risk level - low, medium, high, critical (EOL)', category: 'eol_assessment' },
  { name: 'eol_assessment_notes', type: 'string', required: false, description: 'Assessment notes and details (EOL)', category: 'eol_assessment' },
  { name: 'eol_remediation_options', type: 'string', required: false, description: 'Remediation options (EOL)', category: 'eol_assessment' }
];
