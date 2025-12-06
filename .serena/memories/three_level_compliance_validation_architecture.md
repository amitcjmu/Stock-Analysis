# Three-Level Compliance Validation Architecture

## Overview

The compliance validation system validates technology compliance at three distinct levels, using **existing infrastructure** from the VendorProductsCatalog system. This design ensures NO NEW TABLES are needed and follows the DB-first, RAG-augment caching strategy.

## The Three Levels

### Level 1: Operating System Compliance
Validates that the underlying OS version meets engagement minimum requirements.

| Aspect | Implementation |
|--------|---------------|
| **Data Source** | `Asset.operating_system` + `Asset.os_version` |
| **Standards** | `EngagementArchitectureStandard` where `requirement_type = 'operating_system'` |
| **EOL Lookup** | `VendorProductsCatalog` → `ProductVersionsCatalog` → `LifecycleMilestones` |
| **Result Storage** | `AssetEOLAssessment` with `technology_component = 'os:rhel:9.6'` |
| **Linkage** | `AssetProductLinks` connecting asset to catalog version entry |

### Level 2: Application Compliance (COTS)
Validates COTS application versions against vendor support/EOL dates.

| Aspect | Implementation |
|--------|---------------|
| **Data Source** | `Asset.application_type = 'cots'`, `Asset.vendor`, collection data |
| **Standards** | Vendor product EOL dates from catalog |
| **Result Storage** | `AssetEOLAssessment` with `technology_component = 'app:sap:s4hana:2023'` |
| **Tech Debt** | Non-compliant → Creates `AssetTechDebt` entry |

### Level 3: Component Compliance
Validates individual technology components (databases, runtimes, frameworks, libraries).

| Aspect | Implementation |
|--------|---------------|
| **Data Source** | `Asset.technology_stack`, `Asset.database_type/version`, collection responses |
| **Standards** | `EngagementArchitectureStandard` per component type |
| **Result Storage** | Multiple `AssetEOLAssessment` entries per asset |
| **Security** | Links to `AssetVulnerabilities` for CVE data |

## Existing Infrastructure (NO NEW TABLES!)

### Table Reference

| Table | Purpose | File Location |
|-------|---------|---------------|
| `VendorProductsCatalog` | Global vendor/product catalog | `vendor_products_catalog.py:17` |
| `ProductVersionsCatalog` | Version entries per product | `vendor_products_catalog.py:54` |
| `LifecycleMilestones` | EOL/support dates with provenance | `vendor_products_catalog.py:103` |
| `TenantVendorProducts` | Tenant-specific overrides | `vendor_products_catalog.py:159` |
| `AssetProductLinks` | Asset → Version links with confidence | `vendor_products_catalog.py:203` |
| `AssetEOLAssessment` | Per-asset EOL findings | `asset/specialized.py:17` |
| `EngagementArchitectureStandard` | Minimum requirements per engagement | `assessment_flow/core_models.py:231` |
| `AssetTechDebt` | Tech debt scoring | `asset_enrichments.py` |

## Data Flow

```
Asset.operating_system/os_version ──┐
Asset.application_type/vendor ──────┤
Asset.technology_stack ─────────────┼──► Compliance Validator Agent
Asset.database_type/version ────────┤         │
                                    │         ▼
EngagementArchitectureStandard ─────┘    VendorProductsCatalog
                                              │
                                              ▼
                                    ProductVersionsCatalog
                                              │
                                              ▼
                                    LifecycleMilestones
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                            AssetEOLAssessment  AssetProductLinks  AssetTechDebt
```

## Agent Tools

1. **eol_catalog_lookup** - Query existing catalog tables first
2. **rag_eol_enrichment** - Fetch from endoflife.date API on cache miss, then cache
3. **asset_product_linker** - Create AssetProductLinks entries

## Key Design Principles

1. **DB-First Strategy**: Always query VendorProductsCatalog before using RAG
2. **Cache-on-RAG**: Any RAG results are immediately cached to catalog tables
3. **Provenance Tracking**: LifecycleMilestones.source tracks data origin
4. **Multi-Tenant Isolation**: All queries scoped by client_account_id + engagement_id
5. **No New Tables**: Reuse existing infrastructure entirely

## Technology Component Naming Convention

Format: `{level}:{product}:{version}`

Examples:
- `os:rhel:9.6` - OS level, Red Hat Enterprise Linux 9.6
- `app:sap:s4hana:2023` - Application level, SAP S/4HANA 2023
- `db:oracle:19c` - Component level, Oracle Database 19c
- `runtime:java:17` - Component level, Java 17

## Related Issues

- #1243 - Agent-Based Architecture Minimums Compliance Validation (Three-Level)
- #1245 - Architecture Minimums Enrichment
- #1246 - EOL Data Seeding

## Related ADRs

- ADR-015: Persistent Multi-Tenant Agent Architecture
- ADR-024: TenantMemoryManager Architecture
- ADR-039: Architecture Minimums Phase
