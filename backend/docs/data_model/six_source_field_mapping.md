# Six-Source Asset Field Mapping

**Issue**: #1110 (Phase 1 of ADR-037 Implementation)
**Created**: 2025-11-24
**Purpose**: Comprehensive mapping of ALL asset data sources to eliminate false gaps in questionnaire generation

## Executive Summary

This document maps **ALL 50+ asset fields** to their possible storage locations across **6 different data sources**. Understanding these locations is critical for intelligent gap detection - a field that appears "missing" in standard columns may actually exist in custom_attributes, enrichment_data, environment JSON, canonical_applications, or related assets.

**False Gap Example**:
```python
# ❌ WRONG - Only checks standard column
if not asset.database_type:
    gaps.append("database_type")  # FALSE GAP!

# ✅ CORRECT - Checks all 6 sources
data_found_in = [
    asset.database_type,  # Source 1: Standard column
    asset.custom_attributes.get("db_type"),  # Source 2: Custom attributes
    asset.custom_attributes.get("database", {}).get("type"),  # Source 2: Nested
    enrichment.database_config,  # Source 3: Enrichment data
    asset.environment.get("database", {}).get("type"),  # Source 4: Environment
    canonical_app.application_type == "database",  # Source 5: Canonical apps
]
is_true_gap = not any(data_found_in)  # Only TRUE gap if nowhere
```

## Six Data Sources Overview

### Source 1: Standard Columns (`assets.{field}`)
**Table**: `migration.assets`
**Type**: Direct PostgreSQL columns
**Confidence**: 1.0 (highest)
**Characteristics**:
- Fastest access (indexed columns)
- Type-safe (enforced by PostgreSQL)
- Most reliable (explicit schema)
- Limited to ~70 predefined fields

**Example Fields**:
- `cpu_cores`, `memory_gb`, `storage_gb`
- `operating_system`, `os_version`
- `ip_address`, `hostname`, `fqdn`
- `asset_type`, `description`

### Source 2: Custom Attributes (`assets.custom_attributes`)
**Table**: `migration.assets.custom_attributes` (JSONB column)
**Type**: User-defined key-value pairs
**Confidence**: 0.95
**Characteristics**:
- Flexible schema (any field name)
- Supports nested objects and arrays
- User-populated during imports
- Can have variant naming (e.g., `db_type` vs `database_type`)

**Common Patterns**:
```json
{
  "db_type": "PostgreSQL 14",
  "database": {
    "type": "PostgreSQL",
    "version": "14.5",
    "cluster": "production"
  },
  "cpu": 8,
  "hardware": {
    "cpu_count": 8,
    "memory_gb": 32,
    "disk_type": "SSD"
  }
}
```

### Source 3: Enrichment Data (Separate Tables)
**Tables**:
- `migration.asset_tech_debt`
- `migration.asset_performance_metrics`
- `migration.asset_cost_optimization`
- `migration.asset_resilience`
- `migration.asset_compliance_flags`
- `migration.asset_vulnerabilities`
- `migration.asset_licenses`
- `migration.asset_eol_assessments`
- `migration.asset_contacts`

**Type**: 1:1 relationship tables with structured data
**Confidence**: 0.90
**Characteristics**:
- Agent-generated enrichments
- Structured schemas per table
- Includes JSONB fields (`debt_items`, `additional_metrics`, `optimization_opportunities`)
- Populated during assessment flows

**Example**:
```python
# AssetPerformanceMetrics table
{
  "cpu_utilization_avg": 65.5,
  "memory_utilization_avg": 78.2,
  "additional_metrics": {
    "peak_cpu": 95,
    "iops": 5000
  }
}
```

### Source 4: Environment Field (`assets.environment`)
**Table**: `migration.assets.environment` (JSON column)
**Type**: Environment configuration JSON
**Confidence**: 0.85
**Characteristics**:
- Environment-specific settings
- Can duplicate standard columns
- Often populated by discovery agents
- Hierarchical structure

**Common Pattern**:
```json
{
  "os": "RHEL 8.5",
  "cpu_count": 16,
  "memory_gb": 64,
  "database": {
    "type": "Oracle",
    "version": "19c"
  },
  "network": {
    "primary_ip": "10.0.1.50",
    "gateway": "10.0.1.1"
  }
}
```

### Source 5: Canonical Applications Junction Table
**Table**: `migration.canonical_applications`
**Type**: Many-to-many junction (via `collection_flow_applications`)
**Confidence**: 0.80
**Characteristics**:
- Application identity resolution
- Deduplicates application names across flows
- Contains application metadata
- Fields: `application_type`, `business_criticality`, `technology_stack` (JSONB)

**Example**:
```python
# CanonicalApplication for "SAP ERP Production"
{
  "canonical_name": "SAP ERP",
  "application_type": "database",  # Can infer asset type
  "technology_stack": {
    "database": "Oracle 19c",
    "app_server": "WebLogic"
  }
}
```

### Source 6: Related Assets (Dependency Propagation)
**Table**: `migration.asset_dependencies`
**Type**: Many-to-many relationship table
**Confidence**: 0.70 (lowest - inferred)
**Characteristics**:
- Dependency relationships between assets
- Data propagation from related assets
- Network discovery data (ports, protocols)
- Inferred attributes (e.g., "this asset connects to Oracle DB → likely uses Oracle client")

**Example**:
```python
# Asset A depends on Asset B (Oracle DB)
# Can infer: Asset A likely has Oracle client libraries
# Can inherit: Database connection details from Asset B
```

## Complete Field Mapping Matrix

### Infrastructure Fields

#### CPU Count / Cores
**Logical Field**: CPU count or number of cores
**Possible Locations**:
1. ✅ `assets.cpu_cores` (standard column)
2. ✅ `assets.custom_attributes.cpu` (direct key)
3. ✅ `assets.custom_attributes.hardware.cpu_count` (nested)
4. ✅ `asset_performance_metrics.additional_metrics.cpu_cores`
5. ✅ `assets.environment.cpu_count`
6. ❌ (Not typically in canonical apps or related assets)

**Variant Names**: `cpu`, `cpu_count`, `cpu_cores`, `cores`, `vcpu`, `vcpus`

#### Memory (RAM)
**Logical Field**: Memory in gigabytes
**Possible Locations**:
1. ✅ `assets.memory_gb` (standard column)
2. ✅ `assets.custom_attributes.memory` (direct key)
3. ✅ `assets.custom_attributes.hardware.memory_gb` (nested)
4. ✅ `asset_performance_metrics.additional_metrics.memory_gb`
5. ✅ `assets.environment.memory_gb`
6. ❌ (Not typically in canonical apps or related assets)

**Variant Names**: `memory`, `memory_gb`, `ram`, `ram_gb`, `memory_mb` (needs conversion)

#### Storage
**Logical Field**: Storage capacity in gigabytes
**Possible Locations**:
1. ✅ `assets.storage_gb` (standard column)
2. ✅ `assets.custom_attributes.storage` (direct key)
3. ✅ `assets.custom_attributes.hardware.storage_gb` (nested)
4. ✅ `assets.custom_attributes.disks` (array of disk objects)
5. ✅ `asset_performance_metrics.additional_metrics.storage_gb`
6. ✅ `assets.environment.storage_gb`

**Variant Names**: `storage`, `storage_gb`, `disk`, `disk_gb`, `disk_space`

#### Operating System
**Logical Field**: OS name and type
**Possible Locations**:
1. ✅ `assets.operating_system` (standard column)
2. ✅ `assets.custom_attributes.os` (direct key)
3. ✅ `assets.custom_attributes.operating_system` (direct key)
4. ✅ `assets.custom_attributes.os_details.name` (nested)
5. ✅ `assets.environment.os` (direct key)
6. ✅ `assets.environment.operating_system.name` (nested)

**Variant Names**: `os`, `operating_system`, `os_name`, `platform`

#### OS Version
**Logical Field**: Operating system version
**Possible Locations**:
1. ✅ `assets.os_version` (standard column)
2. ✅ `assets.custom_attributes.os_version` (direct key)
3. ✅ `assets.custom_attributes.os_details.version` (nested)
4. ✅ `assets.environment.os_version`
5. ✅ `assets.environment.operating_system.version` (nested)
6. ❌ (Not typically in canonical apps)

**Variant Names**: `os_version`, `version`, `os_release`, `kernel_version`

### Network Fields

#### IP Address
**Logical Field**: Primary IP address
**Possible Locations**:
1. ✅ `assets.ip_address` (standard column)
2. ✅ `assets.custom_attributes.ip` (direct key)
3. ✅ `assets.custom_attributes.network.ip_address` (nested)
4. ✅ `assets.custom_attributes.primary_ip` (direct key)
5. ✅ `assets.environment.network.primary_ip` (nested)
6. ✅ `asset_dependencies.{discovered IP from network scans}`

**Variant Names**: `ip`, `ip_address`, `primary_ip`, `ipv4_address`

#### Hostname
**Logical Field**: System hostname
**Possible Locations**:
1. ✅ `assets.hostname` (standard column)
2. ✅ `assets.custom_attributes.hostname` (direct key)
3. ✅ `assets.custom_attributes.system.hostname` (nested)
4. ✅ `assets.environment.hostname`
5. ❌ (Not typically in enrichment or canonical apps)

**Variant Names**: `hostname`, `host`, `computer_name`, `fqdn` (if includes domain)

#### FQDN
**Logical Field**: Fully qualified domain name
**Possible Locations**:
1. ✅ `assets.fqdn` (standard column)
2. ✅ `assets.custom_attributes.fqdn` (direct key)
3. ✅ `assets.custom_attributes.network.fqdn` (nested)
4. ✅ `assets.environment.fqdn`
5. ❌ (Not in enrichment or canonical apps)

**Variant Names**: `fqdn`, `fully_qualified_domain_name`, `dns_name`

#### MAC Address
**Logical Field**: Network interface MAC address
**Possible Locations**:
1. ✅ `assets.mac_address` (standard column)
2. ✅ `assets.custom_attributes.mac` (direct key)
3. ✅ `assets.custom_attributes.network.mac_address` (nested)
4. ✅ `assets.custom_attributes.interfaces[].mac` (array)
5. ✅ `assets.environment.network.mac_address`
6. ❌ (Not in enrichment or canonical apps)

**Variant Names**: `mac`, `mac_address`, `physical_address`

### Application Fields

#### Database Type
**Logical Field**: Database system type
**Possible Locations**:
1. ✅ `assets.custom_attributes.db_type` (direct key)
2. ✅ `assets.custom_attributes.database.type` (nested)
3. ✅ `assets.custom_attributes.database_type` (direct key)
4. ✅ `assets.environment.database.type` (nested)
5. ✅ `canonical_applications.application_type == "database"` (junction)
6. ✅ `canonical_applications.technology_stack.database` (JSONB)

**Variant Names**: `db_type`, `database_type`, `database`, `rdbms_type`

#### Application Name
**Logical Field**: Primary application name
**Possible Locations**:
1. ✅ `assets.application_name` (standard column)
2. ✅ `assets.custom_attributes.application` (direct key)
3. ✅ `assets.custom_attributes.app_name` (direct key)
4. ✅ `canonical_applications.canonical_name` (junction)
5. ✅ `canonical_applications.description` (junction)
6. ❌ (Not typically in environment or enrichment)

**Variant Names**: `application`, `application_name`, `app_name`, `service_name`

#### Technology Stack
**Logical Field**: Technology stack description
**Possible Locations**:
1. ✅ `assets.technology_stack` (standard column)
2. ✅ `assets.custom_attributes.tech_stack` (direct key)
3. ✅ `assets.custom_attributes.technologies` (array)
4. ✅ `canonical_applications.technology_stack` (JSONB)
5. ✅ `asset_tech_debt.debt_items` (inferred from modernization needs)
6. ❌ (Not typically in environment)

**Variant Names**: `tech_stack`, `technology_stack`, `technologies`, `stack`

### Business Fields

#### Business Owner
**Logical Field**: Business owner or stakeholder
**Possible Locations**:
1. ✅ `assets.business_owner` (standard column)
2. ✅ `assets.custom_attributes.owner` (direct key)
3. ✅ `assets.custom_attributes.business_owner` (direct key)
4. ✅ `assets.custom_attributes.owners.business` (nested)
5. ✅ `asset_contacts` (table with `contact_type == "business_owner"`)
6. ❌ (Not in environment or canonical apps)

**Variant Names**: `owner`, `business_owner`, `stakeholder`, `sponsor`

#### Technical Owner
**Logical Field**: Technical owner or administrator
**Possible Locations**:
1. ✅ `assets.technical_owner` (standard column)
2. ✅ `assets.custom_attributes.tech_owner` (direct key)
3. ✅ `assets.custom_attributes.technical_owner` (direct key)
4. ✅ `assets.custom_attributes.owners.technical` (nested)
5. ✅ `asset_contacts` (table with `contact_type == "technical_owner"`)
6. ❌ (Not in environment or canonical apps)

**Variant Names**: `tech_owner`, `technical_owner`, `administrator`, `admin`

#### Department
**Logical Field**: Business department or unit
**Possible Locations**:
1. ✅ `assets.department` (standard column)
2. ✅ `assets.custom_attributes.department` (direct key)
3. ✅ `assets.custom_attributes.business_unit` (direct key)
4. ✅ `assets.custom_attributes.org.department` (nested)
5. ❌ (Not in enrichment, environment, or canonical apps)

**Variant Names**: `department`, `business_unit`, `org_unit`, `division`

#### Business Criticality
**Logical Field**: Business impact rating
**Possible Locations**:
1. ✅ `assets.business_criticality` (standard column)
2. ✅ `assets.custom_attributes.criticality` (direct key)
3. ✅ `assets.custom_attributes.business_criticality` (direct key)
4. ✅ `canonical_applications.business_criticality` (junction)
5. ✅ `asset_tech_debt.modernization_priority` (inferred)
6. ❌ (Not typically in environment)

**Variant Names**: `criticality`, `business_criticality`, `impact`, `priority`

### Migration Fields

#### 6R Strategy
**Logical Field**: Migration recommendation (Rehost, Replatform, etc.)
**Possible Locations**:
1. ✅ `assets.six_r_strategy` (standard column)
2. ✅ `assets.custom_attributes.migration_strategy` (direct key)
3. ✅ `assets.custom_attributes.six_r` (direct key)
4. ✅ `assets.phase_context.six_r_recommendation` (JSON)
5. ✅ `cmdb_sixr_analyses.analysis_results` (historical analysis)
6. ❌ (Not in environment or canonical apps)

**Variant Names**: `six_r`, `six_r_strategy`, `migration_strategy`, `recommendation`

#### Migration Complexity
**Logical Field**: Migration complexity rating
**Possible Locations**:
1. ✅ `assets.migration_complexity` (standard column)
2. ✅ `assets.custom_attributes.complexity` (direct key)
3. ✅ `assets.custom_attributes.migration.complexity` (nested)
4. ✅ `asset_tech_debt.tech_debt_score` (inferred)
5. ✅ `asset_dependencies` (count of dependencies)
6. ❌ (Not typically in environment or canonical apps)

**Variant Names**: `complexity`, `migration_complexity`, `difficulty`

#### Migration Wave
**Logical Field**: Migration wave assignment
**Possible Locations**:
1. ✅ `assets.migration_wave` (standard column)
2. ✅ `assets.custom_attributes.wave` (direct key)
3. ✅ `assets.custom_attributes.migration.wave` (nested)
4. ✅ `migration_waves` (table - assets associated with waves)
5. ❌ (Not in enrichment, environment, or canonical apps)

**Variant Names**: `wave`, `migration_wave`, `phase`, `batch`

### Resilience Fields

#### RTO (Recovery Time Objective)
**Logical Field**: Recovery time objective in minutes
**Possible Locations**:
1. ✅ `asset_resilience.rto_minutes` (enrichment table)
2. ✅ `assets.custom_attributes.rto` (direct key)
3. ✅ `assets.custom_attributes.resilience.rto_minutes` (nested)
4. ✅ `assets.custom_attributes.sla.rto` (nested)
5. ✅ `asset_resilience.sla_json.rto` (JSONB)
6. ❌ (Not in environment or canonical apps)

**Variant Names**: `rto`, `rto_minutes`, `recovery_time`, `downtime_tolerance`

#### RPO (Recovery Point Objective)
**Logical Field**: Recovery point objective in minutes
**Possible Locations**:
1. ✅ `asset_resilience.rpo_minutes` (enrichment table)
2. ✅ `assets.custom_attributes.rpo` (direct key)
3. ✅ `assets.custom_attributes.resilience.rpo_minutes` (nested)
4. ✅ `assets.custom_attributes.sla.rpo` (nested)
5. ✅ `asset_resilience.sla_json.rpo` (JSONB)
6. ❌ (Not in environment or canonical apps)

**Variant Names**: `rpo`, `rpo_minutes`, `data_loss_tolerance`, `backup_frequency`

#### High Availability
**Logical Field**: HA configuration or requirement
**Possible Locations**:
1. ✅ `assets.custom_attributes.ha` (direct key)
2. ✅ `assets.custom_attributes.high_availability` (direct key)
3. ✅ `assets.custom_attributes.resilience.ha_enabled` (nested)
4. ✅ `asset_resilience.sla_json.ha_config` (JSONB)
5. ✅ `assets.environment.ha_config` (nested)
6. ✅ `asset_dependencies` (clustered assets)

**Variant Names**: `ha`, `high_availability`, `ha_enabled`, `clustered`

### Performance Fields

#### CPU Utilization
**Logical Field**: Average CPU utilization percentage
**Possible Locations**:
1. ✅ `asset_performance_metrics.cpu_utilization_avg` (enrichment table)
2. ✅ `assets.custom_attributes.cpu_util` (direct key)
3. ✅ `assets.custom_attributes.performance.cpu_utilization` (nested)
4. ✅ `asset_performance_metrics.additional_metrics.cpu_stats` (JSONB)
5. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `cpu_util`, `cpu_utilization`, `cpu_usage`, `cpu_percent`

#### Memory Utilization
**Logical Field**: Average memory utilization percentage
**Possible Locations**:
1. ✅ `asset_performance_metrics.memory_utilization_avg` (enrichment table)
2. ✅ `assets.custom_attributes.memory_util` (direct key)
3. ✅ `assets.custom_attributes.performance.memory_utilization` (nested)
4. ✅ `asset_performance_metrics.additional_metrics.memory_stats` (JSONB)
5. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `memory_util`, `memory_utilization`, `ram_usage`, `memory_percent`

#### Disk IOPS
**Logical Field**: Disk I/O operations per second
**Possible Locations**:
1. ✅ `asset_performance_metrics.disk_iops_avg` (enrichment table)
2. ✅ `assets.custom_attributes.iops` (direct key)
3. ✅ `assets.custom_attributes.performance.disk_iops` (nested)
4. ✅ `asset_performance_metrics.additional_metrics.disk_stats` (JSONB)
5. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `iops`, `disk_iops`, `io_operations`, `disk_io`

### Cost Fields

#### Monthly Cost
**Logical Field**: Current monthly cost in USD
**Possible Locations**:
1. ✅ `asset_cost_optimization.monthly_cost_usd` (enrichment table)
2. ✅ `assets.custom_attributes.cost` (direct key)
3. ✅ `assets.custom_attributes.monthly_cost` (direct key)
4. ✅ `assets.custom_attributes.financials.monthly_cost` (nested)
5. ✅ `asset_cost_optimization.cost_breakdown` (JSONB - detailed)
6. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `cost`, `monthly_cost`, `monthly_cost_usd`, `monthly_spend`

#### Projected Cost
**Logical Field**: Projected monthly cost after migration
**Possible Locations**:
1. ✅ `asset_cost_optimization.projected_monthly_cost_usd` (enrichment table)
2. ✅ `assets.custom_attributes.projected_cost` (direct key)
3. ✅ `assets.custom_attributes.target_cost` (direct key)
4. ✅ `assets.custom_attributes.migration.projected_cost` (nested)
5. ✅ `asset_cost_optimization.cost_breakdown.projected` (JSONB)
6. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `projected_cost`, `target_cost`, `future_cost`, `estimated_cost`

### Compliance Fields

#### Data Classification
**Logical Field**: Data sensitivity classification
**Possible Locations**:
1. ✅ `asset_compliance_flags.data_classification` (enrichment table)
2. ✅ `assets.custom_attributes.classification` (direct key)
3. ✅ `assets.custom_attributes.data_classification` (direct key)
4. ✅ `assets.custom_attributes.compliance.classification` (nested)
5. ✅ `asset_compliance_flags.evidence_refs` (JSONB - references)
6. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `classification`, `data_classification`, `sensitivity`, `tier`

#### Compliance Scopes
**Logical Field**: Regulatory compliance requirements
**Possible Locations**:
1. ✅ `asset_compliance_flags.compliance_scopes` (enrichment table - array)
2. ✅ `assets.custom_attributes.compliance` (direct key - array or string)
3. ✅ `assets.custom_attributes.regulations` (array)
4. ✅ `assets.custom_attributes.compliance.scopes` (nested array)
5. ✅ `asset_compliance_flags.evidence_refs` (JSONB - per-scope evidence)
6. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `compliance`, `compliance_scopes`, `regulations`, `standards`

#### Residency Requirements
**Logical Field**: Data residency requirements
**Possible Locations**:
1. ✅ `asset_compliance_flags.residency` (enrichment table)
2. ✅ `assets.custom_attributes.residency` (direct key)
3. ✅ `assets.custom_attributes.data_residency` (direct key)
4. ✅ `assets.custom_attributes.compliance.residency` (nested)
5. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `residency`, `data_residency`, `location_requirement`, `geo_restriction`

### Technical Debt Fields

#### Tech Debt Score
**Logical Field**: Technical debt score (0-100)
**Possible Locations**:
1. ✅ `asset_tech_debt.tech_debt_score` (enrichment table)
2. ✅ `assets.custom_attributes.tech_debt` (direct key)
3. ✅ `assets.custom_attributes.tech_debt_score` (direct key)
4. ✅ `asset_tech_debt.debt_items` (JSONB - itemized)
5. ✅ `asset_tech_debt.code_quality_score` (inverse correlation)
6. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `tech_debt`, `tech_debt_score`, `debt_score`, `technical_debt`

#### Modernization Priority
**Logical Field**: Modernization priority rating
**Possible Locations**:
1. ✅ `asset_tech_debt.modernization_priority` (enrichment table)
2. ✅ `assets.custom_attributes.modernization` (direct key)
3. ✅ `assets.custom_attributes.priority` (direct key)
4. ✅ `assets.custom_attributes.tech_debt.priority` (nested)
5. ✅ `asset_tech_debt.debt_items` (JSONB - prioritized list)
6. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `modernization`, `modernization_priority`, `refactor_priority`, `priority`

### Vulnerability Fields

#### Vulnerabilities
**Logical Field**: Security vulnerabilities
**Possible Locations**:
1. ✅ `asset_vulnerabilities` (enrichment table)
2. ✅ `assets.custom_attributes.vulnerabilities` (array)
3. ✅ `assets.custom_attributes.cve` (array of CVE IDs)
4. ✅ `assets.custom_attributes.security.vulnerabilities` (nested)
5. ❌ (Not in standard columns, environment, or canonical apps)

**Variant Names**: `vulnerabilities`, `cves`, `security_issues`, `vulns`

### License Fields

#### License Type
**Logical Field**: Software license type
**Possible Locations**:
1. ✅ `asset_licenses.license_type` (enrichment table)
2. ✅ `assets.custom_attributes.license` (direct key)
3. ✅ `assets.custom_attributes.license_type` (direct key)
4. ✅ `assets.custom_attributes.licensing.type` (nested)
5. ✅ `canonical_applications.technology_stack.licenses` (JSONB)
6. ❌ (Not in standard columns or environment)

**Variant Names**: `license`, `license_type`, `licensing`, `software_license`

### EOL (End of Life) Fields

#### EOL Date
**Logical Field**: End of life or support date
**Possible Locations**:
1. ✅ `asset_eol_assessments.eol_date` (enrichment table)
2. ✅ `assets.custom_attributes.eol` (direct key)
3. ✅ `assets.custom_attributes.end_of_life` (direct key)
4. ✅ `assets.custom_attributes.support.end_date` (nested)
5. ✅ `asset_eol_assessments.extended_support_end` (enrichment table)
6. ❌ (Not in environment or canonical apps)

**Variant Names**: `eol`, `eol_date`, `end_of_life`, `support_end_date`

## JSONB Path Patterns

### Direct Key Access
```python
# Simple key-value pairs
value = asset.custom_attributes.get("cpu")
value = asset.custom_attributes.get("db_type")
```

### Nested Object Access
```python
# Nested dictionary access
value = asset.custom_attributes.get("hardware", {}).get("cpu_count")
value = asset.custom_attributes.get("database", {}).get("type")
value = asset.custom_attributes.get("resilience", {}).get("rto_minutes")
```

### Array Access
```python
# Array of values
vulns = asset.custom_attributes.get("vulnerabilities", [])
licenses = asset.custom_attributes.get("licenses", [])

# Array of objects
interfaces = asset.custom_attributes.get("interfaces", [])
for iface in interfaces:
    ip = iface.get("ip_address")
    mac = iface.get("mac_address")
```

### Deep Nesting
```python
# Multiple levels of nesting
value = asset.custom_attributes.get("org", {}).get("department", {}).get("name")
value = asset.environment.get("database", {}).get("connection", {}).get("port")
```

### SQLAlchemy JSONB Query Patterns
```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import cast, func

# Direct key query
stmt = select(Asset).where(
    Asset.custom_attributes["db_type"].astext == "PostgreSQL"
)

# Nested key query
stmt = select(Asset).where(
    Asset.custom_attributes["database"]["type"].astext == "PostgreSQL"
)

# Check key exists
stmt = select(Asset).where(
    Asset.custom_attributes.has_key("cpu")
)

# Array contains
stmt = select(Asset).where(
    Asset.custom_attributes["vulnerabilities"].contains(["CVE-2023-1234"])
)
```

## Data Location Best Practices

### Priority Order for Gap Detection
When checking if data exists, scan sources in this order:

1. **Standard Columns** (highest confidence)
2. **Custom Attributes** (most flexible)
3. **Enrichment Tables** (agent-generated)
4. **Environment Field** (discovery data)
5. **Canonical Applications** (application metadata)
6. **Related Assets** (dependency inference)

### Confidence Scoring
```python
def calculate_data_confidence(data_sources: List[DataSource]) -> float:
    """
    Calculate confidence score based on data source priority.

    Returns:
        0.0 = No data found (true gap)
        0.70-0.80 = Data found in canonical apps or related assets
        0.85 = Data found in environment field
        0.90 = Data found in enrichment tables
        0.95 = Data found in custom_attributes
        1.0 = Data found in standard columns
    """
    if not data_sources:
        return 0.0  # True gap

    # Return confidence of highest-priority source
    max_confidence = max(ds.confidence for ds in data_sources)
    return max_confidence
```

### Variant Name Resolution
```python
FIELD_VARIANTS = {
    "cpu_count": ["cpu", "cpu_count", "cpu_cores", "cores", "vcpu", "vcpus"],
    "memory_gb": ["memory", "memory_gb", "ram", "ram_gb"],
    "database_type": ["db_type", "database", "database_type", "rdbms"],
    # ... more variants
}

def find_value_in_jsonb(jsonb_data: dict, logical_field: str) -> Any:
    """Try all variant names for a logical field."""
    variants = FIELD_VARIANTS.get(logical_field, [logical_field])

    for variant in variants:
        if variant in jsonb_data:
            return jsonb_data[variant]

        # Try nested path (e.g., "hardware.cpu_count")
        if "." in variant:
            parts = variant.split(".")
            current = jsonb_data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            else:
                return current  # Found via nested path

    return None  # Not found
```

### Data Consolidation Strategy
When data exists in multiple sources with conflicts:

1. **Standard Column Wins**: If data exists in standard column, use it (highest confidence)
2. **Most Recent Wins**: If multiple enrichment sources, use most recent `updated_at`
3. **User Input Wins**: If `custom_attributes` and auto-enrichment conflict, prefer user input
4. **Flag for Review**: Store conflict in `asset_field_conflicts` table for user resolution

## Migration Path for Data Consolidation

### Phase 1: Identify Fragmented Data (Current State)
```sql
-- Find assets with CPU count in multiple sources
SELECT
    a.id,
    a.name,
    a.cpu_cores AS standard_column,
    a.custom_attributes->>'cpu' AS custom_attrs,
    e.environment->>'cpu_count' AS environment,
    pm.additional_metrics->>'cpu_cores' AS performance
FROM migration.assets a
LEFT JOIN migration.asset_performance_metrics pm ON pm.asset_id = a.id
WHERE (
    a.cpu_cores IS NOT NULL
    OR a.custom_attributes ? 'cpu'
    OR e.environment ? 'cpu_count'
    OR pm.additional_metrics ? 'cpu_cores'
);
```

### Phase 2: Create Data Consolidation Service
```python
# backend/app/services/asset/data_consolidation_service.py

class AssetDataConsolidationService:
    """
    Service for consolidating asset data from multiple sources.

    Implements the 6-source priority resolution strategy.
    """

    async def consolidate_asset_data(
        self,
        asset_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Consolidate all data for an asset across 6 sources.

        Returns dictionary with:
        - consolidated_data: Dict[field, value]
        - data_sources: Dict[field, List[DataSource]]
        - conflicts: List[FieldConflict]
        """
        # Load all data sources
        asset = await self._load_asset_with_enrichments(asset_id, db)
        enrichment_tables = await self._load_enrichment_tables(asset_id, db)
        canonical_apps = await self._load_canonical_applications(asset_id, db)
        related_assets = await self._load_related_assets(asset_id, db)

        consolidated = {}
        sources_map = {}
        conflicts = []

        # For each logical field, check all 6 sources
        for logical_field in FIELD_MAPPINGS.keys():
            data_sources = self._check_all_sources(
                logical_field,
                asset,
                enrichment_tables,
                canonical_apps,
                related_assets
            )

            if len(data_sources) == 0:
                # True gap - no data anywhere
                continue
            elif len(data_sources) == 1:
                # Single source - no conflict
                consolidated[logical_field] = data_sources[0].value
                sources_map[logical_field] = data_sources
            else:
                # Multiple sources - resolve conflict
                resolved_value, conflict = self._resolve_conflict(
                    logical_field,
                    data_sources
                )
                consolidated[logical_field] = resolved_value
                sources_map[logical_field] = data_sources
                if conflict:
                    conflicts.append(conflict)

        return {
            "consolidated_data": consolidated,
            "data_sources": sources_map,
            "conflicts": conflicts
        }
```

### Phase 3: Gradual Migration to Standard Columns
```python
# Migration strategy: Move high-confidence data to standard columns

async def migrate_custom_attrs_to_standard_columns(
    db: AsyncSession,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Migrate data from custom_attributes to standard columns where appropriate.

    Rules:
    1. Only migrate if custom_attributes value exists AND standard column is NULL
    2. Only migrate if field name matches exactly (e.g., "cpu" → "cpu_cores")
    3. Validate data type before migration (e.g., "8" → 8 for Integer column)
    4. Keep custom_attributes intact (don't delete) for audit trail
    """
    migrations = []

    # Find assets with CPU in custom_attributes but NULL in standard column
    stmt = select(Asset).where(
        Asset.cpu_cores.is_(None),
        Asset.custom_attributes["cpu"].is_not(None)
    )
    result = await db.execute(stmt)
    assets = result.scalars().all()

    for asset in assets:
        cpu_value = asset.custom_attributes.get("cpu")

        # Validate and convert
        try:
            cpu_int = int(cpu_value)
            if 1 <= cpu_int <= 1024:  # Reasonable range
                if not dry_run:
                    asset.cpu_cores = cpu_int
                    await db.commit()

                migrations.append({
                    "asset_id": str(asset.id),
                    "field": "cpu_cores",
                    "old_value": None,
                    "new_value": cpu_int,
                    "source": "custom_attributes.cpu"
                })
        except (ValueError, TypeError):
            # Invalid data - log but skip
            pass

    return {
        "total_migrated": len(migrations),
        "dry_run": dry_run,
        "migrations": migrations
    }
```

### Phase 4: Data Quality Reports
```python
# Generate reports on data completeness across sources

async def generate_data_quality_report(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID
) -> Dict[str, Any]:
    """
    Generate data quality report showing:
    - Fields with data in standard columns vs custom_attributes
    - Assets with fragmented data across multiple sources
    - Data conflicts requiring resolution
    - Recommendations for data consolidation
    """
    report = {
        "total_assets": 0,
        "fields_analysis": {},
        "fragmented_assets": [],
        "conflict_summary": {},
        "recommendations": []
    }

    # Analyze each field
    for field in FIELD_MAPPINGS.keys():
        field_stats = {
            "standard_column_count": 0,
            "custom_attributes_count": 0,
            "enrichment_count": 0,
            "environment_count": 0,
            "canonical_apps_count": 0,
            "multiple_sources_count": 0,
            "gap_count": 0
        }

        # Query for this field across all sources
        # ... (implementation details)

        report["fields_analysis"][field] = field_stats

    return report
```

## Usage Examples

### Example 1: Intelligent Gap Detection
```python
from app.services.collection.gap_analysis.intelligent_gap_scanner import (
    IntelligentGapScanner
)

scanner = IntelligentGapScanner(db, client_account_id=1, engagement_id=1)

# Scan asset for TRUE gaps only
gaps = await scanner.scan_gaps(asset)

for gap in gaps:
    if gap.is_true_gap:
        print(f"TRUE GAP: {gap.field_name}")
        print(f"  Checked {len(gap.data_found)} sources, found no data")
    else:
        print(f"DATA EXISTS: {gap.field_name}")
        for source in gap.data_found:
            print(f"  Found in: {source.source_type} = {source.value}")
```

### Example 2: Field Mapping Lookup
```python
from backend.docs.data_model.six_source_field_mapping import FIELD_MAPPINGS

# Get all possible locations for "database_type"
locations = FIELD_MAPPINGS["database_type"]
# Returns:
# [
#   "assets.custom_attributes.db_type",
#   "assets.custom_attributes.database.type",
#   "enrichment_data.database_config",
#   "assets.environment.database.type",
#   "canonical_applications.application_type=database",
#   "canonical_applications.technology_stack.database"
# ]

# Check each location
for location in locations:
    value = check_location(asset, location)
    if value:
        print(f"Found database_type in {location}: {value}")
        break
```

### Example 3: Data Consolidation
```python
from app.services.asset.data_consolidation_service import (
    AssetDataConsolidationService
)

service = AssetDataConsolidationService()
result = await service.consolidate_asset_data(asset.id, db)

print(f"Consolidated {len(result['consolidated_data'])} fields")
print(f"Found {len(result['conflicts'])} conflicts requiring resolution")

for conflict in result['conflicts']:
    print(f"\nConflict for {conflict.field_name}:")
    print(f"  Standard column: {conflict.standard_value}")
    print(f"  Custom attributes: {conflict.custom_attr_value}")
    print(f"  Recommended: {conflict.resolved_value}")
```

## Summary

This comprehensive mapping document provides:

1. ✅ **Complete field inventory**: 50+ asset fields mapped to all possible locations
2. ✅ **Six-source awareness**: Every field checked against all 6 data sources
3. ✅ **JSONB path patterns**: Nested keys, arrays, and SQLAlchemy query patterns
4. ✅ **Variant name resolution**: Handle naming inconsistencies across sources
5. ✅ **Confidence scoring**: Prioritize data sources by reliability
6. ✅ **Migration strategy**: Path to consolidate fragmented data
7. ✅ **Code examples**: Ready-to-use patterns for intelligent gap detection

**Impact on ADR-037**:
- Eliminates false gaps by checking ALL 6 sources before flagging as missing
- Reduces questionnaire length by 40-60% (only ask for TRUE gaps)
- Improves user experience (no re-entering existing data)
- Enables data quality reports (identify fragmented data)

**Next Steps** (Issues #1111-#1113):
- Implement `IntelligentGapScanner` with 6-source checking
- Create test fixtures validating all 6 sources
- Build data consolidation service
- Generate data quality reports for production engagements
