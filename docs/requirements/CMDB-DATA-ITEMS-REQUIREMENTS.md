# CMDB Data Items Requirements

**Document Purpose:** Define CMDB data item mapping to database tables and columns for demo dataset creation.

**Status:** Draft  
**Date:** 2025-10-28  
**Related:** Issue #753 - Create Realistic Demo Dataset

---

## 1. Existing Field Mapping

This section maps CMDB data items to their corresponding database tables and columns in the migration platform.

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `name` | `Assets` | `name` | Do we need name and Asset name |
| `asset_name` | `Assets` | `asset_name` | Yes |
| `hostname` | `Assets` | `hostname` | Yes |
| `asset_type` | `Assets` | `asset_type` | Yes |
| `description` | `Assets` | `description` | Yes |
| `ip_address` | `Assets` | `ip_address` | Yes |
| `fqdn` | `Assets` | `fqdn` | Yes |
| `mac_address` | `Assets` | `mac_address` | Yes |
| `environment` | `Assets` | `environment` | Yes |
| `location` | `Assets` | `location` | Yes |
| `datacenter` | `Assets` | `datacenter` | Yes |
| `rack_location` | `Assets` | `rack_location` | Yes |
| `availability_zone` | `Assets` | `availability_zone` | Yes |
| `operating_system` | `Assets` | `operating_system` | Yes |
| `os_version` | `Assets` | `os_version` | Yes |
| `cpu_cores` | `Assets` | `cpu_cores` | Yes |
| `memory_gb` | `Assets` | `memory_gb` | Yes |
| `storage_gb` | `Assets` | `storage_gb` | Yes |
| `business_owner` | `Assets` | `business_owner` | Yes |
| `technical_owner` | `Assets` | `technical_owner` | Yes |
| `department` | `Assets` | `department` | Yes |
| `application_name` | `Assets` | `application_name` | Yes |
| `technology_stack` | `Assets` | `technology_stack` | Yes |
| `criticality` | `Assets` | `criticality` | Do we need criticality and business criticality? |
| `business_criticality` | `Assets` | `business_criticality` | Yes |
| `custom_attributes` | `Assets` | `custom_attributes` | Yes |
| `six_r_strategy` | `Assets` | `six_r_strategy` | Yes |
| `mapping_status` | `Assets` | `mapping_status` | Yes |
| `migration_priority` | `Assets` | `migration_priority` | Yes |
| `migration_complexity` | `Assets` | `migration_complexity` | Yes |
| `migration_wave` | `Assets` | `migration_wave` | Yes |
| `sixr_ready` | `Assets` | `sixr_ready` | Yes |
| `status` | `Assets` | `status` | Yes |
| `migration_status` | `Assets` | `migration_status` | Yes |
| `dependencies` | `Assets` | `dependencies` | Yes |
| `related_assets` | `Assets` | `related_assets` | No, Internal Field |
| `discovery_method` | `Assets` | `discovery_method` | No, Internal Field |
| `discovery_source` | `Assets` | `discovery_source` | Yes |
| `discovery_timestamp` | `Assets` | `discovery_timestamp` | No, Internal Field |
| `cpu_utilization_percent` | `Assets` | `cpu_utilization_percent` | Yes |
| `memory_utilization_percent` | `Assets` | `memory_utilization_percent` | Yes |
| `disk_iops` | `Assets` | `disk_iops` | Yes |
| `network_throughput_mbps` | `Assets` | `network_throughput_mbps` | Yes |
| `completeness_score` | `Assets` | `completeness_score` | No, Internal Field |
| `quality_score` | `Assets` | `quality_score` | No, Internal Field |
| `current_monthly_cost` | `Assets` | `current_monthly_cost` | Yes |
| `estimated_cloud_cost` | `Assets` | `estimated_cloud_cost` | Yes |
| `imported_by` | `Assets` | `imported_by` | No, Internal Field |
| `imported_at` | `Assets` | `imported_at` | No, Internal Field |
| `source_filename` | `Assets` | `source_filename` | No, Internal Field |
| `raw_data` | `Assets` | `raw_data` | No, Internal Field |
| `field_mappings_used` | `Assets` | `field_mappings_used` | Do we need this? |
| `raw_import_records_id` | `Assets` | `raw_import_records_id` | No, Internal Field |
| `created_at` | `Assets` | `created_at` | No, Internal Field |
| `updated_at` | `Assets` | `updated_at` | No, Internal Field |
| `created_by` | `Assets` | `created_by` | No, Internal Field |
| `updated_by` | `Assets` | `updated_by` | No, Internal Field |
| `discovery_status` | `Assets` | `discovery_status` | No, Internal Field |
| `discovery_completed_at` | `Assets` | `discovery_completed_at` | No, Internal Field |
| `assessment_readiness` | `Assets` | `assessment_readiness` | No, Internal Field |
| `assessment_readiness_score` | `Assets` | `assessment_readiness_score` | No, Internal Field |
| `assessment_blockers` | `Assets` | `assessment_blockers` | No, Internal Field |
| `assessment_recommendations` | `Assets` | `assessment_recommendations` | No, Internal Field |
| `confidence_score` | `Assets` | `confidence_score` | No, Internal Field |
| `technical_details` | `Assets` | `technical_details` | Yes |
| `discovered_at` | `Assets` | `discovered_at` | No, Internal Field |

### Application Components

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `component_name` | `application_components` | `component_name` | Yes |
| `component_type` | `application_components` | `component_type` | Yes |
| `component_config` | `application_components` | `component_config` | Yes |

### Application Name Variants

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `canonical_application_id` | `application_name_variants` | `canonical_application_id` | No, Internal Field |
| `variant_name` | `application_name_variants` | `variant_name` | No, Internal Field |
| `normalized_variant` | `application_name_variants` | `normalized_variant` | No, Internal Field |
| `variant_hash` | `application_name_variants` | `variant_hash` | No, Internal Field |
| `client_account_id` | `application_name_variants` | `client_account_id` | No, Internal Field |
| `engagement_id` | `application_name_variants` | `engagement_id` | No, Internal Field |
| `variant_embedding` | `application_name_variants` | `variant_embedding` | No, Internal Field |
| `similarity_score` | `application_name_variants` | `similarity_score` | No, Internal Field |
| `match_method` | `application_name_variants` | `match_method` | No, Internal Field |
| `match_confidence` | `application_name_variants` | `match_confidence` | No, Internal Field |
| `usage_count` | `application_name_variants` | `usage_count` | No, Internal Field |
| `first_seen_at` | `application_name_variants` | `first_seen_at` | No, Internal Field |
| `last_used_at` | `application_name_variants` | `last_used_at` | No, Internal Field |
| `created_at` | `application_name_variants` | `created_at` | No, Internal Field |
| `updated_at` | `application_name_variants` | `updated_at` | No, Internal Field |

### Asset Compliance Flags

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `asset_id` | `asset_compliance_flags` | `asset_id` | No, Internal Field |
| `compliance_scopes` | `asset_compliance_flags` | `compliance_scopes` | No, Internal Field |
| `data_classification` | `asset_compliance_flags` | `data_classification` | No, Internal Field |
| `residency` | `asset_compliance_flags` | `residency` | No, Internal Field |
| `evidence_refs` | `asset_compliance_flags` | `evidence_refs` | No, Internal Field |
| `created_at` | `asset_compliance_flags` | `created_at` | No, Internal Field |
| `updated_at` | `asset_compliance_flags` | `updated_at` | No, Internal Field |

### Asset Custom Attributes

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `asset_custom_attributes` | `id` | No, Internal Field |
| `client_account_id` | `asset_custom_attributes` | `client_account_id` | No, Internal Field |
| `engagement_id` | `asset_custom_attributes` | `engagement_id` | No, Internal Field |
| `asset_id` | `asset_custom_attributes` | `asset_id` | No, Internal Field |
| `asset_type` | `asset_custom_attributes` | `asset_type` | No, Internal Field |
| `attributes` | `asset_custom_attributes` | `attributes` | No, Internal Field |
| `source` | `asset_custom_attributes` | `source` | No, Internal Field |
| `import_batch_id` | `asset_custom_attributes` | `import_batch_id` | No, Internal Field |
| `import_timestamp` | `asset_custom_attributes` | `import_timestamp` | No, Internal Field |
| `pattern_detected` | `asset_custom_attributes` | `pattern_detected` | No, Internal Field |
| `suggested_standard_field` | `asset_custom_attributes` | `suggested_standard_field` | No, Internal Field |
| `created_at` | `asset_custom_attributes` | `created_at` | No, Internal Field |
| `updated_at` | `asset_custom_attributes` | `updated_at` | No, Internal Field |

### Asset Dependencies

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `asset_dependencies` | `id` | No, Internal Field |
| `asset_id` | `asset_dependencies` | `asset_id` | Yes |
| `depends_on_asset_id` | `asset_dependencies` | `depends_on_asset_id` | Yes |
| `dependency_type` | `asset_dependencies` | `dependency_type` | Yes |
| `description` | `asset_dependencies` | `description` | Yes |
| `created_at` | `asset_dependencies` | `created_at` | No, Internal Field |
| `updated_at` | `asset_dependencies` | `updated_at` | No, Internal Field |
| `relationship_nature` | `asset_dependencies` | `relationship_nature` | Yes |
| `direction` | `asset_dependencies` | `direction` | Yes |
| `criticality` | `asset_dependencies` | `criticality` | Yes |
| `dataflow_type` | `asset_dependencies` | `dataflow_type` | Yes |

### Asset Licenses

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `asset_licenses` | `id` | No, Internal Field |
| `asset_id` | `asset_licenses` | `asset_id` | No, Internal Field |
| `license_type` | `asset_licenses` | `license_type` | Yes |
| `renewal_date` | `asset_licenses` | `renewal_date` | Yes |
| `contract_reference` | `asset_licenses` | `contract_reference` | Yes |
| `support_tier` | `asset_licenses` | `support_tier` | Yes |
| `created_at` | `asset_licenses` | `created_at` | No, Internal Field |
| `updated_at` | `asset_licenses` | `updated_at` | No, Internal Field |

### Asset Product Links

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `asset_product_links` | `id` | No, Internal Field |
| `asset_id` | `asset_product_links` | `asset_id` | No, Internal Field |
| `catalog_version_id` | `asset_product_links` | `catalog_version_id` | No, Internal Field |
| `tenant_version_id` | `asset_product_links` | `tenant_version_id` | Yes |
| `confidence_score` | `asset_product_links` | `confidence_score` | No, Internal Field |
| `matched_by` | `asset_product_links` | `matched_by` | No, Internal Field |
| `created_at` | `asset_product_links` | `created_at` | No, Internal Field |
| `updated_at` | `asset_product_links` | `updated_at` | No, Internal Field |

### Asset Resilience

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `asset_resilience` | `id` | No, Internal Field |
| `asset_id` | `asset_resilience` | `asset_id` | No, Internal Field |
| `rto_minutes` | `asset_resilience` | `rto_minutes` | Yes |
| `rpo_minutes` | `asset_resilience` | `rpo_minutes` | Yes |
| `sla_json` | `asset_resilience` | `sla_json` | Yes |
| `created_at` | `asset_resilience` | `created_at` | No, Internal Field |
| `updated_at` | `asset_resilience` | `updated_at` | No, Internal Field |

### Asset Vulnerabilities

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `asset_vulnerabilities` | `id` | No, Internal Field |
| `asset_id` | `asset_vulnerabilities` | `asset_id` | No, Internal Field |
| `cve_id` | `asset_vulnerabilities` | `cve_id` | No, Internal Field |
| `severity` | `asset_vulnerabilities` | `severity` | Yes |
| `detected_at` | `asset_vulnerabilities` | `detected_at` | No, Internal Field |
| `source` | `asset_vulnerabilities` | `source` | Yes |
| `details` | `asset_vulnerabilities` | `details` | Yes |
| `created_at` | `asset_vulnerabilities` | `created_at` | No, Internal Field |
| `updated_at` | `asset_vulnerabilities` | `updated_at` | No, Internal Field |

### Blackout Periods

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `blackout_periods` | `id` | No, Internal Field |
| `client_account_id` | `blackout_periods` | `client_account_id` | No, Internal Field |
| `engagement_id` | `blackout_periods` | `engagement_id` | No, Internal Field |
| `scope_type` | `blackout_periods` | `scope_type` | No, Internal Field |
| `application_id` | `blackout_periods` | `application_id` | No, Internal Field |
| `asset_id` | `blackout_periods` | `asset_id` | Yes |
| `start_date` | `blackout_periods` | `start_date` | Yes |
| `end_date` | `blackout_periods` | `end_date` | Yes |
| `reason` | `blackout_periods` | `reason` | Yes |
| `created_at` | `blackout_periods` | `created_at` | Yes |
| `updated_at` | `blackout_periods` | `updated_at` | Yes |

### Lifecycle Milestones

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `lifecycle_milestones` | `id` | No, Internal Field |
| `catalog_version_id` | `lifecycle_milestones` | `catalog_version_id` | Yes |
| `tenant_version_id` | `lifecycle_milestones` | `tenant_version_id` | No, Internal Field |
| `milestone_type` | `lifecycle_milestones` | `milestone_type` | Yes |
| `milestone_date` | `lifecycle_milestones` | `milestone_date` | Yes |
| `source` | `lifecycle_milestones` | `source` | Yes |
| `provenance` | `lifecycle_milestones` | `provenance` | Yes |
| `last_checked_at` | `lifecycle_milestones` | `last_checked_at` | Yes |
| `created_at` | `lifecycle_milestones` | `created_at` | Yes |
| `updated_at` | `lifecycle_milestones` | `updated_at` | Yes |

### Maintenance Windows

| Data Item | Table | Table Columns | Is CMDB Field?/Comments |
|-----------|-------|---------------|------------------------|
| `id` | `maintenance_windows` | `id` | No, Internal Field |
| `client_account_id` | `maintenance_windows` | `client_account_id` | No, Internal Field |
| `engagement_id` | `maintenance_windows` | `engagement_id` | No, Internal Field |
| `scope_type` | `maintenance_windows` | `scope_type` | Yes |
| `application_id` | `maintenance_windows` | `application_id` | Yes |
| `asset_id` | `maintenance_windows` | `asset_id` | Yes |
| `name` | `maintenance_windows` | `name` | Yes |
| `start_time` | `maintenance_windows` | `start_time` | Yes |
| `end_time` | `maintenance_windows` | `end_time` | Yes |
| `recurring` | `maintenance_windows` | `recurring` | Yes |
| `timezone` | `maintenance_windows` | `timezone` | Yes |
| `created_at` | `maintenance_windows` | `created_at` | No, Internal Field |
| `updated_at` | `maintenance_windows` | `updated_at` | No, Internal Field |

---

## 2. CMDB Fields Summary

### Fields to Include in Demo Dataset (CMDB Fields marked "Yes"):

**Core Asset Information (Assets table):**
- Identity: `asset_name`, `hostname`, `asset_type`, `description`
- Network: `ip_address`, `fqdn`, `mac_address`
- Infrastructure: `environment`, `location`, `datacenter`, `rack_location`, `availability_zone`
- Compute: `operating_system`, `os_version`, `cpu_cores`, `memory_gb`, `storage_gb`
- Ownership: `business_owner`, `technical_owner`, `department`
- Application: `application_name`, `technology_stack`, `business_criticality`
- Migration: `six_r_strategy`, `mapping_status`, `migration_priority`, `migration_complexity`, `migration_wave`, `sixr_ready`, `status`, `migration_status`
- Operations: `dependencies`, `discovery_source`, `cpu_utilization_percent`, `memory_utilization_percent`, `disk_iops`, `network_throughput_mbps`
- Cost: `current_monthly_cost`, `estimated_cloud_cost`
- Other: `custom_attributes`, `technical_details`

**Related Tables:**
- `application_components`: component_name, component_type, component_config
- `asset_dependencies`: asset_id, depends_on_asset_id, dependency_type, description, relationship_nature, direction, criticality, dataflow_type
- `asset_licenses`: license_type, renewal_date, contract_reference, support_tier
- `asset_product_links`: tenant_version_id
- `asset_resilience`: rto_minutes, rpo_minutes, sla_json
- `asset_vulnerabilities`: severity, source, details
- `blackout_periods`: asset_id, start_date, end_date, reason, created_at, updated_at
- `lifecycle_milestones`: catalog_version_id, milestone_type, milestone_date, source, provenance, last_checked_at, created_at, updated_at
- `maintenance_windows`: scope_type, application_id, asset_id, name, start_time, end_time, recurring, timezone

### Open Questions:
1. **Do we need both `name` and `asset_name`?** (Currently both exist in Assets table)
2. **Do we need both `criticality` and `business_criticality`?** (Currently both exist in Assets table)
3. **Do we need `field_mappings_used`?** (Currently in Assets table)

---

## 3. Missing Fields Analysis

The following fields are **missing** from the current database schema and need to be added to support comprehensive CMDB data imports.

| Data Field | Table Name | Column Name | Data Type | Remarks/Comments |
|-----------|-----------|-------------|-----------|------------------|
| `virtualization_platform` | `asset` | `virtualization_platform` | `varchar` | Infra |
| `data_volume_characteristics` | `asset` | `data_volume_characteristics` | `Int` | Infra |
| `user_load_patterns` | `asset` | `user_load_patterns` | `varchar` | Application |
| `business_logic_complexity` | `asset` | `application_complexity` | `varchar(enum)` | Application |
| `configuration_complexity` | `asset` | `configuration_complexity` | `varchar(enum)` | Application |
| `change_tolerance` | `asset` | `change_tolerance` | `varchar(enum)` | Application |
| `eol_technology_assessment` | `asset_eol` | `eol_technology_assessment` | `text` | Application/Infra |
| `technical_detail` | `asset` | `technical_detail` | `JSONB` | Application |
| `business_unit` | `asset` | `business_unit` | `varchar` | Application |
| `business_owner_email` | `asset` | `business_owner_email` | `varchar` | Contact info |
| `technical_owner_email` | `asset` | `technical_owner_email` | `varchar` | Contact info |
| `lifecycle` | `asset` | `lifecycle` | `varchar(enum)` | Retire/Replace/Retain/Invest |
| `cots_or_custom` | `asset` | `application_type` | `varchar(enum)` | COTS/Custom/Custom-COTS/Other |
| `vendor` | `asset` | `vendor` | `varchar` | Vendor name |
| `has_saas_replacement` | `asset` | `has_saas_replacement` | `bool` | SaaS alternative available |
| `hosting_model` | `asset` | `hosting_model` | `varchar(enum)` | On-prem, cloud, hybrid etc |
| `primary_database_type` | `asset` | `database_type` | `varchar` | Database name |
| `primary_database_version` | `asset` | `database_version` | `varchar` | Database version |
| `db_size` | `asset` | `database_size_gb` | `Int` | Database size |
| `data_classification` | `asset` | `application_data_classification` | `varchar(enum)` | Data sensitivity level |
| `pii_flag` | `asset` | `pii_flag` | `bool` | Contains PII data |
| `cloud_readiness` | `asset` | `cloud_readiness` | `varchar(enum)` | Cloud readiness score |
| `tech_debt_flags` | `asset` | `tech_debt_flags` | `bool` | Has technical debt |
| `proposed_rationale` | `asset` | `proposed_treatmentplan_rationale` | `Text` | Treatment plan reasoning |
| `risk_level` | `asset` | `risk_level` | `varchar(enum)` | Migration risk level |
| `tshirt_size` | `asset` | `tshirt_size` | `varchar` | Complexity sizing (S/M/L/XL) |
| `annual_cost_estimate` | `asset` | `annual_cost_estimate` | `Float` | Annual operational cost |
| `clustering` | `asset` | `clustering` | `bool` | Server clustering enabled |
| `dr_support` | `asset` | `dr_support` | `bool` | Disaster recovery support |
| `rto_hours` | `asset` | `rto_hours` | `Int` | Recovery Time Objective (hours) |
| `rpo_minutes` | `asset` | `rpo_minutes` | `Int` | Recovery Point Objective (minutes) |
| `role` | `asset` | `server_role` | `varchar(enum)` | Web/DB/App/Citrix |
| `ip_secondary` | `asset` | `secondary_ips` | `Text` | Multiple secondary IPs |
| `security_zone` | `asset` | `security_zone` | `varchar` | Note: May overlap with availability_zone |
| `cpu_max_percent` | `asset` | `cpu_utilization_percent_max` | `Float8` | Peak CPU utilization |
| `memory_max_percent` | `asset` | `memory_utilization_percent_max` | `Float8` | Peak memory utilization |
| `storage_free_gb` | `asset` | `storage_free_gb` | `Float8` | Available storage |
| `backup_policy` | `asset` | `backup_policy` | `Text` | Backup policy details |
| `tags` | `asset` | `asset_tags` | `Text` | Asset tags/labels |

### Missing Asset Dependency Fields

| Data Field | Table Name | Column Name | Data Type | Remarks/Comments |
|-----------|-----------|-------------|-----------|------------------|
| `port` | `asset_dependencies` | `port` | `Int` | Network port (verify if needed) |
| `protocol_name` | `asset_dependencies` | `protocol_name` | `varchar` | Protocol (TCP/UDP/etc.) |
| `conn_count` | `asset_dependencies` | `conn_count` | `Int` | Connection count |
| `bytes_total` | `asset_dependencies` | `bytes_total` | `Float16` | Total data transferred |
| `first_seen` | `asset_dependencies` | `first_seen` | `datetime` | First detection timestamp |
| `last_seen` | `asset_dependencies` | `last_seen` | `datetime` | Last detection timestamp |

### Missing Fields Summary by Category:

**Infrastructure Fields (Asset table):**
- Virtualization: `virtualization_platform`, `clustering`
- Performance: `data_volume_characteristics`, `cpu_max_percent`, `memory_max_percent`, `storage_free_gb`
- Network: `ip_secondary`, `security_zone`
- Disaster Recovery: `dr_support`, `rto_hours`, `rpo_minutes`, `backup_policy`
- Server: `server_role`

**Application Fields (Asset table):**
- Identity: `business_unit`, `vendor`, `cots_or_custom`
- Complexity: `business_logic_complexity`, `configuration_complexity`, `user_load_patterns`
- Database: `database_type`, `database_version`, `database_size_gb`
- Lifecycle: `lifecycle`, `eol_technology_assessment`
- Security: `application_data_classification`, `pii_flag`, `data_classification`
- Migration: `cloud_readiness`, `tech_debt_flags`, `change_tolerance`, `has_saas_replacement`, `hosting_model`, `proposed_treatmentplan_rationale`, `risk_level`, `tshirt_size`
- Cost: `annual_cost_estimate`
- Contact: `business_owner_email`, `technical_owner_email`
- Metadata: `asset_tags`, `technical_detail`

**Network Discovery Fields (Asset Dependencies table):**
- Connection metadata: `port`, `protocol_name`, `conn_count`, `bytes_total`, `first_seen`, `last_seen`

### Implementation Notes:

1. **New Table Required**: `asset_eol` for end-of-life technology assessments
2. **Enum Types**: Several fields use enums - need to define valid values:
   - `lifecycle`: Retire, Replace, Retain, Invest
   - `application_type`: COTS, Custom, Custom-COTS, Other
   - `hosting_model`: On-prem, Cloud, Hybrid
   - `server_role`: Web, DB, App, Citrix
   - Other enums: `business_logic_complexity`, `configuration_complexity`, `change_tolerance`, `application_data_classification`, `cloud_readiness`, `risk_level`

3. **Overlapping Fields**:
   - `security_zone` vs `availability_zone` - clarify usage
   - `rpo_minutes` exists in both `asset` (new) and `asset_resilience` (existing)
   - `technical_detail` (JSONB, new) vs `technical_details` (existing) - clarify

4. **Asset Dependencies Enhancement**: Network discovery fields suggest this data comes from network analysis tools (flow data, connection metrics)

---

## Notes

- **CMDB Fields (Yes)**: Should be included in demo CMDB import files
- **Internal Fields (No)**: System-generated, not part of CMDB import
- This mapping supports Issue #753 - realistic demo dataset creation
- Fields marked with questions need product clarification
- **Missing fields** in Section 3 require database schema updates before full CMDB import support
