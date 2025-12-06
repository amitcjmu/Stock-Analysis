# Three-Level Compliance Validation (Issue #1243)

## Overview
Implementation of a three-level technology compliance validation system for cloud migration assessment. This replaces the previous deterministic validation with an intelligent CrewAI agent-based approach.

## Three Levels
1. **OS Compliance (Level 1)**: Validates operating system versions against engagement standards
   - Examples: RHEL 9.x, Windows Server 2022, Ubuntu 22.04
   - Checks: EOL dates, supported versions, vendor support status

2. **Application Compliance (Level 2)**: Validates COTS applications against vendor EOL
   - Examples: Oracle Database 19c, SQL Server 2019
   - Checks: License compliance, vendor support, security patches

3. **Component Compliance (Level 3)**: Validates technical components
   - Categories: Databases, runtimes, frameworks
   - Examples: PostgreSQL 16, Java 21, Node.js 20, Spring Boot 3.x

## Architecture

### DB-First, RAG-Augment Caching Strategy
1. **Query catalog first** (Level 1 - EOL Catalog Lookup)
   - Check VendorProductsCatalog → ProductVersionsCatalog → LifecycleMilestones
   - Fast lookup for known technologies

2. **RAG fallback** (Level 2 - RAG EOL Enrichment)
   - Query endoflife.date API or embedded knowledge base
   - For technologies not in catalog

3. **Cache results** (Level 3 - Asset Product Linker)
   - Persist RAG findings back to catalog for future lookups
   - Link assets to product versions via AssetProductLinks

### Key Files Created/Modified

#### Tools (new)
- `backend/app/services/persistent_agents/tools/__init__.py`
- `backend/app/services/persistent_agents/tools/eol_catalog_lookup_tool.py`
- `backend/app/services/persistent_agents/tools/rag_eol_enrichment_tool.py`
- `backend/app/services/persistent_agents/tools/asset_product_linker_tool.py`

#### Configuration (modified)
- `backend/app/services/persistent_agents/agent_tool_config.py` - Added tool factories and compliance_validator agent config
- `backend/app/services/persistent_agents/agent_pool_constants.py` - Added compliance_validator agent definition

#### Executor (modified)
- `backend/app/services/flow_orchestration/execution_engine_crew_assessment/architecture_minimums_executor.py`
  - Now uses TenantScopedAgentPool to get compliance_validator agent
  - Contains THREE_LEVEL_COMPLIANCE_PROMPT template
  - Falls back to deterministic validation if agent unavailable

#### API Schema (modified)
- `backend/app/api/v1/master_flows/assessment/info_endpoints/compliance_queries.py`
  - Added: CheckedItem, LevelComplianceResult, ThreeLevelComplianceResult models
  - Updated ComplianceValidationResponse with by_level and checked_items fields

#### Migration (new)
- `backend/alembic/versions/151_seed_eol_catalog_data_issue_1243.py`
  - Seeds VendorProductsCatalog, ProductVersionsCatalog, LifecycleMilestones
  - Includes data for: RHEL, Oracle Linux, Windows Server, AIX, z/OS, Ubuntu
  - Databases: Oracle Database, SQL Server, PostgreSQL, MySQL, MongoDB, Db2
  - Runtimes: Java, OpenJDK, .NET, Node.js, Python
  - Frameworks: Spring Boot, Spring Framework, Angular, React

## Technology Normalization
The eol_catalog_lookup_tool.py contains TECHNOLOGY_ALIASES mapping for normalizing technology names:
- "Linux Red Hat" → "rhel"
- "Windows Server" → "windows-server"
- "Oracle Database" → "oracle-database"

## Response Schema
The compliance validation response now includes:
```json
{
  "by_level": {
    "os_compliance": {
      "level_name": "os",
      "is_compliant": true,
      "checked_count": 5,
      "passed_count": 4,
      "failed_count": 1,
      "checked_items": [...],
      "issues": [...]
    },
    "application_compliance": {...},
    "component_compliance": {...}
  },
  "checked_items": [
    {
      "technology": "RHEL",
      "version": "9",
      "eol_status": "active",
      "eol_date": "2032-05-31",
      "source": "catalog",
      "is_compliant": true
    }
  ]
}
```

## IMPORTANT: Existing Tables Used (NO NEW TABLES)
- VendorProductsCatalog - Global product catalog
- ProductVersionsCatalog - Product versions
- LifecycleMilestones - EOL dates and support dates
- AssetProductLinks - Asset to product version mapping
- AssetEOLAssessment - (if needed for caching results)

## Agent Configuration
The compliance_validator agent is configured in agent_pool_constants.py with:
- tools: eol_catalog_lookup, rag_eol_enrichment, asset_product_linker
- llm: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 (via DeepInfra)
- temperature: 0.1 (low for consistency)
