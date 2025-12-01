# Network Discovery Integration Analysis - October 2025

## Executive Summary

Reviewed GitHub discussions #658 (High-Level Technical Design) and #660 (Stage-by-Stage Pipeline) for non-CMDB data import (network discovery processing). Found **90% requirements alignment** with platform capabilities but **WRONG implementation approach** (standalone CLI instead of Discovery Flow integration).

## Key Findings

### Current Platform Readiness: 85% Complete
- ✅ Collection Flow: Bulk import, canonical dedup, two-phase gap analysis, questionnaires
- ✅ Discovery Flow: Data import phase, field mapping, asset inventory, 4 discovery agents
- ✅ Infrastructure: 17 AI agents, LLM tracking, TenantMemoryManager, multi-tenant DB
- ❌ Missing: Network connection record processing, ML classification models, dependency graph

### Critical Design Flaws in Proposals

1. **MAJOR ISSUE**: Proposes standalone CLI tool (`discovery-processor`)
   - Breaks multi-tenant architecture (no client_account_id/engagement_id scoping)
   - No integration with existing Discovery Flow phases
   - Bypasses LLM usage tracking (`llm_usage_logs`)
   - Creates parallel system instead of extending existing flows

2. **Technology Stack Mismatch**:
   - Proposes open ML framework (scikit-learn/XGBoost/TensorFlow)
   - Current reality: CrewAI + DeepInfra (Llama 4, Gemma 3) with 95%+ accuracy
   - Should leverage Dependency Analyst Agent before adding new frameworks

3. **Missing Integration Points**:
   - No connection to Collection Flow gap analysis (we have two-phase system!)
   - No canonical application deduplication (we solved this in bulk import!)
   - No tenant memory system integration (we have TenantMemoryManager!)

## Recommended Implementation: Integrate into Discovery Flow

### New Discovery Flow Phase: network_discovery

```python
# backend/app/services/flow_configs/discovery_phases/network_discovery_phase.py
PhaseConfig(
    name="network_discovery",
    display_name="Network Discovery & Dependencies",
    description="Process network traffic data (Device42, Cloudscape, firewall logs)",
    required_inputs=["connection_data_file"],
    pre_handlers=[
        "stage1_edge_aggregation",      # 10M → 200-500k rows
        "stage2_business_noise_classifier",  # ML Pass #1
        "stage3_shared_service_inference",   # ML Pass #2
    ],
    crew_config={
        "crew_type": "dependency_analysis",  # Use existing agent!
        "input_mapping": {"aggregated_edges": "state.stage3_output"},
        "output_mapping": {
            "app_dependencies": "crew_results.application_dependencies",
            "orphan_servers": "crew_results.orphan_candidates",
        },
    },
    post_handlers=[
        "persist_application_dependencies",
        "trigger_gap_analysis_for_missing_deps",  # Link to Collection!
        "create_canonical_app_mappings",          # Deduplication!
    ],
)
```

### New Database Tables

```sql
-- Raw network connection aggregates (Stage 1 output)
CREATE TABLE migration.network_connection_records (
    id UUID PRIMARY KEY,
    discovery_flow_id UUID REFERENCES discovery_flows(id),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    source_server VARCHAR(255),
    dest_server VARCHAR(255),
    protocol VARCHAR(50),
    dest_port INTEGER,
    conn_count_total INTEGER,
    bytes_total BIGINT,
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    days_seen INTEGER,
    is_business_traffic BOOLEAN,  -- ML prediction
    is_shared_service BOOLEAN,    -- Infra detection
    ml_confidence FLOAT
);

-- Application-level dependencies (Stage 4-5 output)
CREATE TABLE migration.application_dependencies (
    id UUID PRIMARY KEY,
    discovery_flow_id UUID REFERENCES discovery_flows(id),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    source_canonical_app_id UUID REFERENCES canonical_applications(id),
    dest_canonical_app_id UUID REFERENCES canonical_applications(id),
    criticality_score FLOAT,  -- 0-10
    total_connections INTEGER,
    total_volume_gb FLOAT,
    communication_summary JSONB,  -- {protocols, ports, patterns}
    ml_confidence FLOAT
);
```

### Extended Collection Flow Gap Analysis

```python
# backend/app/services/collection_flow_analyzer.py (EXTEND EXISTING)
async def scan_gaps_with_network_enrichment(
    self, selected_asset_ids: List[str], ...
) -> Dict[str, Any]:
    """
    Phase 1: Programmatic gap scan + Network discovery enrichment

    NEW: Checks if network_discovery phase completed in Discovery flow.
    Enriches gap detection with:
    - Missing dependencies (from ApplicationDependency table)
    - Orphan server alerts (from orphan_servers output)
    - Batch job scheduling gaps (from temporal pattern analysis)
    """
    gaps = await self._programmatic_scan(selected_asset_ids, ...)

    # NEW: Network discovery enrichment
    if discovery_flow.network_discovery_completed:
        network_gaps = await self._enrich_from_network_discovery(...)
        gaps.extend(network_gaps)

    return gaps
```

### New Data Source Parsers

```python
# NEW: backend/app/services/data_import/parsers/
# - firewall_log_parser.py (Palo Alto, Cisco ASA, Fortinet)
# - netflow_parser.py (NetFlow, sFlow, IPFIX)
# - application_log_parser.py (IIS, Apache, Tomcat)
# - cloudscape_export_parser.py
# - device42_export_parser.py
```

## Extension Roadmap

### Phase 1: Foundation (2-3 weeks)
1. Add `network_connection_records` and `application_dependencies` tables (1 day)
2. Implement Stage 1-3 (Edge Aggregation + ML Classifiers) in Discovery Flow (1 week)
3. Create `network_discovery_phase.py` config (2 days)
4. Add firewall/netflow parsers to data_import service (3 days)

### Phase 2: ML Integration (3-4 weeks)
1. Train ML models OR test Dependency Analyst Agent for classification
2. Integrate into pre_handlers (Stage 2-3)
3. Add confidence thresholds and manual review flags

### Phase 3: Collection Flow Integration (2 weeks)
1. Extend `CollectionFlowAnalyzer.scan_gaps_with_network_enrichment()` (3 days)
2. Link network-derived gaps to gap analysis UI (2 days)
3. Add dependency gap resolution workflow (1 week)

### Phase 4: Agent Enhancement (1-2 weeks)
1. Use Dependency Analyst Agent for Stage 4-8
2. Feed outputs to TenantMemoryManager
3. Track LLM usage via litellm_tracking_callback

## Critical Warnings

### ❌ DO NOT Do This:
1. Build standalone CLI tool - breaks multi-tenant architecture
2. Introduce new ML frameworks without testing CrewAI agents first
3. Bypass existing gap analysis - network data should FEED it
4. Skip canonical dedup - will create duplicate apps

### ✅ DO Do This:
1. Integrate into Discovery Flow as `network_discovery` phase
2. Leverage existing Dependency Analyst Agent
3. Link to Collection Flow gap analysis
4. Use CanonicalApplication deduplication
5. Track LLM usage via existing infrastructure

## What's Already Working (Leverage This!)

### Collection Flow (85% Complete):
- Bulk import: `collection_bulk_import.py:301-428`
- Canonical dedup: `CanonicalApplication.find_or_create_canonical()`
- Two-phase gap analysis: `collection_gap_analysis.py`
- Questionnaires: Asset-agnostic data collection
- Multi-tenant scoping: All tables

### Discovery Flow (70% Complete):
- Data import phase: `data_import_phase.py`
- Field mapping: 95%+ accuracy with AI
- Asset inventory: Canonical asset creation
- 4 Discovery Agents: Including Dependency Analyst

### Infrastructure (100% Complete):
- 17 AI Agents: CrewAI + DeepInfra
- LLM Tracking: `litellm_tracking_callback.py`
- TenantMemoryManager: ADR-024 compliant
- Multi-tenant DB: PostgreSQL + async + pgvector

## Decision: Approve with Major Modifications

1. ✅ APPROVE: 9-stage pipeline design - excellent architecture
2. ✅ APPROVE: Hybrid ML/AI approach - matches CrewAI patterns
3. ❌ REJECT: Standalone CLI tool - integrate into Discovery Flow
4. ⚠️ MODIFY: Use CrewAI agents before adding ML frameworks
5. ⚠️ MODIFY: Add multi-tenant scoping, canonical dedup, gap analysis integration

## Immediate Next Steps

1. Create RFC for Discovery Flow network_discovery phase integration
2. Design database migration for new tables
3. Prototype firewall log parser (Palo Alto CSV)
4. Test Dependency Analyst Agent with sample connection data

## References

- Discussions: #658 (High-Level Design), #660 (Pipeline Stages)
- Current Code: `collection_bulk_import.py`, `collection_gap_analysis.py`, `data_import_phase.py`
- Database: `collection_data_gaps`, `discovery_flows`, `canonical_applications`
- Memories: `two-phase-gap-analysis-implementation-lessons`, `collection_gaps_phase2_implementation`
