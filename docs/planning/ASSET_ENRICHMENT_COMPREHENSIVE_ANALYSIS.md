# Asset Type Analysis: Comprehensive Enrichment and Assessment Pathways

**Date**: January 2025  
**Analyst**: CC (Claude Code)  
**Purpose**: Complete analysis of asset types, enrichment tables, data flow, and assessment requirements

---

## Executive Summary

This comprehensive analysis examines how different asset types (applications, servers, databases, network devices) are stored, enriched, and prepared for 6R assessment across the discovery, collection, and assessment phases.

**Key Findings**:
1. ✅ **Unified Asset Architecture**: All asset types converge into single `assets` table
2. ⚠️ **Staging Table Orphans**: Bulk import tables have NO automated migration to `assets`
3. ✅ **Canonical Applications**: Robust deduplication with vector embeddings
4. ⚠️ **Missing Enrichment Pipelines**: No automated pathway from staging → enriched assets
5. ✅ **22 Critical Attributes Defined**: Clear requirements for 6R analysis readiness

---

## 1. Asset Type Models and Database Tables

### 1.1 Universal Asset Table

**`migration.assets`** - Single source of truth for ALL asset types  
- 78 columns covering infrastructure, application, business, and assessment data
- Supports: `server`, `database`, `application`, `device`, `network_device`
- Multi-tenant: `client_account_id` + `engagement_id`
- Flow tracking: Links to discovery, assessment, planning, execution flows

**Core Fields by Category**:
```
Identity: name, asset_type, hostname, ip_address, fqdn
Infrastructure: operating_system, cpu_cores, memory_gb, storage_gb
Application: application_name, technology_stack, business_criticality  
Assessment: assessment_readiness, assessment_readiness_score, sixr_ready
6R Strategy: six_r_strategy, migration_priority, migration_complexity
Quality: completeness_score, quality_score, confidence_score
Enrichment: custom_attributes, technical_details (JSON)
```

### 1.2 Bulk Import Staging Tables (ORPHANED)

These tables serve as **staging areas ONLY** - NO automatic migration to `assets`:

**`migration.applications`**: name, business_criticality, description, technology_stack  
**`migration.servers`**: name, hostname, ip_address, os, cpu_cores, memory_gb, storage_gb  
**`migration.databases`**: name, database_type, version, size_gb, criticality  
**`migration.devices`**: name, device_type, manufacturer, model, serial_number, location

⚠️ **Critical Issue**: These tables have NO foreign key to `assets` table

### 1.3 Canonical Applications (Master Registry)

**`migration.canonical_applications`** - Application identity deduplication  
- Name normalization and SHA-256 hashing for exact match
- Vector embeddings (384D) for fuzzy similarity matching
- Usage tracking and confidence scoring
- Relationships to `application_name_variants` and `collection_flow_applications`

---

## 2. Enrichment Data Tables

### 2.1 Universal Enrichment (All Asset Types)

**`collected_data_inventory`**
- Raw collected data from discovery/collection flows
- Platform, collection_method, raw_data, normalized_data (JSONB)
- Quality scoring and validation status

**`collection_data_gaps`**
- Missing/incomplete data identified during collection
- Two-phase: Programmatic scan + AI enhancement
- Fields: asset_id, gap_type, field_name, impact_on_sixr, priority
- AI: confidence_score, ai_suggestions

**`collection_questionnaire_response`**
- User responses to fill data gaps
- Links to gap_id, asset_id
- Response validation and confidence tracking

**`asset_dependencies`**
- Maps relationships between assets
- Enriches `assets.dependencies` JSON field

**`asset_field_conflicts`**
- Resolves conflicts from multiple sources
- Multi-source import conflict resolution

### 2.2 Application-Specific

**`collection_flow_applications`**
- Links collection flows to applications
- Maps to `canonical_applications` (deduplication)
- Tracks gap_analysis_result, collection_status

**`application_name_variants`**
- Alternative names for canonical applications
- Match method and confidence tracking

**`application_components`**
- Architecture component tracking

### 2.3 Infrastructure Enrichment

**`asset_resilience`** - HA, backup, DR configuration  
**`asset_vulnerabilities`** - Security vulnerability tracking  
**`asset_compliance_flags`** - Compliance and regulatory status  
**`asset_licenses`** - Software licensing information

---

## 3. Data Flow Through Flows

### 3.1 Discovery Flow → Asset Creation

```
CMDB Import / Azure Migrate
  ↓
collected_data_inventory (raw data)
  ↓
Attribute Mapping (Field Mapper Agent)
  ↓
Data Cleansing (normalize, validate, deduplicate)
  ↓
INSERT INTO migration.assets
  - Sets discovery_flow_id
  - Sets source_phase = 'discovery'
  - Sets assessment_readiness = 'not_ready'
  ↓
Dependency Analysis → asset_dependencies
```

### 3.2 Collection Flow → Asset Enrichment (7 Phases)

```
Phase 1: Asset Selection
  → User selects from discovery
  → Creates collection_flow_applications
  → Links to canonical_applications

Phase 2: Gap Analysis (Two-Phase AI)
  → Programmatic Scan: Compare vs 22 critical attributes
  → INSERT INTO collection_data_gaps
  → AI Enhancement: Add confidence_score, ai_suggestions

Phase 3: Questionnaire Generation
  → AI generates adaptive forms based on gaps

Phase 4: Manual Collection
  → User fills questionnaires
  → INSERT INTO collection_questionnaire_response

Phase 5: Data Validation
  → Validate responses, update quality_score

Phase 6: Finalization/Synthesis
  → UPDATE migration.assets SET <enriched_fields>
  → completeness_score, quality_score calculated
  → assessment_readiness = 'ready' (if criteria met)
  → UPDATE collection_data_gaps: resolution_status = 'resolved'

Phase 7: Completion
  → assessment_ready = true
  → apps_ready_for_assessment count set
```

### 3.3 Assessment Flow → 6R Analysis

```
1. Migration Readiness Check
   → SELECT FROM assets WHERE assessment_readiness = 'ready'

2. Critical Attributes Assessment (22 attributes)
   → CriticalAttributesAssessor.assess_data_coverage()

3. 6R Strategy Recommendation
   → INSERT INTO sixr_analyses
   → INSERT INTO sixr_iterations
   → INSERT INTO sixr_recommendations
   
4. Asset Update
   → UPDATE assets SET six_r_strategy, migration_priority
```

---

## 4. 22 Critical Attributes for 6R Analysis

### Infrastructure (6 attributes)
1. **Application Name** (Required)
2. **Technology Stack** (Required)
3. **Operating System** (Required)
4. **CPU Cores**
5. **Memory (GB)** (Required)
6. **Storage (GB)**

### Application (8 attributes)
7. **Business Criticality** (Required)
8. **Application Type** (Required)
9. **Architecture Pattern**
10. **Dependencies/Integrations** (Required)
11. **User Base**
12. **Data Sensitivity** (Required)
13. **Compliance Requirements**
14. **SLA Requirements**

### Business (4 attributes)
15. **Business Owner** (Required)
16. **Annual Operating Cost**
17. **Business Value** (Required)
18. **Strategic Importance**

### Technical Debt (4 attributes)
19. **Code Quality/Tech Debt Score**
20. **Last Update/Version Currency** (Required)
21. **Support Status**
22. **Known Issues/Vulnerabilities** (Required)

### Readiness Scoring
- < 50% = LOW - Cannot proceed
- 50-74% = MODERATE - Manual review required
- ≥ 75% = GOOD - Ready for automated 6R analysis

---

## 5. Critical Gaps and Recommendations

### GAP 1: Bulk Import → Assets Pipeline MISSING ❌
**Issue**: CSV imports populate staging but never create `assets` records  
**Impact**: HIGH - Bulk data cannot proceed to assessment  
**Solution**: Implement automated pipeline:
```python
POST /api/v1/collection/bulk-import
  ↓ Stage in applications/servers/databases/devices tables
  ↓ Call asset creation service (NEW)
  ↓ INSERT INTO assets with source_phase='bulk_import'
  ↓ Trigger gap analysis
  ↓ Create collection_flow_applications
```

### GAP 2: No Application → Asset Linkage ❌
**Issue**: `applications` table isolated from `canonical_applications`  
**Impact**: HIGH - No deduplication for bulk imports  
**Solution**: Add `canonical_application_id` FK

### GAP 3: Assessment Blockers Not Visible ⚠️
**Issue**: `assets.assessment_blockers` not displayed in UI  
**Impact**: MEDIUM - Users don't know why assets aren't ready  
**Solution**: Add assessment readiness widget

### GAP 4: Server/Database/Device Enrichment ℹ️
**Issue**: No dedicated enrichment tables for non-app types  
**Impact**: MEDIUM - Rely on JSON fields  
**Solution**: Use JSON (flexible) or create normalized tables if needed

---

## 6. Implementation Priorities

| Priority | Recommendation | Effort | Impact |
|----------|---------------|--------|---------|
| 🔴 **P0** | Bulk Import → Assets Pipeline | Medium | Critical |
| 🔴 **P0** | Application → Canonical Linkage | Small | Critical |
| 🟡 **P1** | Assessment Blockers UI | Small | High |
| 🟡 **P1** | Unified Enrichment Service | Large | High |
| 🟢 **P2** | Asset Type Views | Medium | Medium |
| 🟢 **P3** | Auto Gap Remediation | XLarge | Low |

---

## 7. Canonical Applications Architecture

### Deduplication Workflow
```
User submits: "SAP ERP System"
  ↓
Normalize: "sap erp system"
  ↓
Hash: SHA256 → "a3f8b2..."
  ↓
Exact Match? (Fast lookup)
  ├─ Yes → Return existing + create variant
  └─ No → Fuzzy match (vector similarity)
      ├─ Match > 0.85 → Return + create variant
      └─ No match → Create new canonical
```

### Variant Tracking
Multiple names map to one canonical identity:
- "SAP-ERP-Production" → canonical "SAP ERP System"
- "sap_erp" → canonical "SAP ERP System"
- Usage count and confidence tracked per variant

---

## 8. Orphan Tables

### By Design (Intentional)
✅ `platform_adapters` - Integration credentials  
✅ `platform_credentials` - Auth secrets  
✅ `vendor_products_catalog` - Reference data  
✅ `sixr_questions` - Question library  
✅ `sixr_parameters` - Global config

### Unintentional Orphans
❌ `applications`, `servers`, `databases`, `devices` - NO tie to `assets`

---

## SQL Analysis Queries

### Count Assets by Type and Readiness
```sql
SELECT asset_type, assessment_readiness, COUNT(*) as count
FROM migration.assets
WHERE client_account_id = ? AND engagement_id = ?
GROUP BY asset_type, assessment_readiness;
```

### Find Orphaned Bulk Imports
```sql
SELECT a.id, a.name
FROM migration.applications a
LEFT JOIN migration.assets ast
  ON a.name = ast.name
  AND a.client_account_id = ast.client_account_id
WHERE ast.id IS NULL;
```

---

**Document Version**: 1.0  
**Next Review**: After bulk import pipeline implementation
