# Discovery Flow Remediation Plan

## Executive Summary

This document outlines the plan to enhance the current Discovery Flow implementation to achieve the advanced capabilities described in the Discovery Flow Design Document. The current implementation already has strong foundations with multi-source support, automatic field mapping, and CrewAI agents.

### Current State Summary (Corrected Analysis)
- **Architecture**: CrewAI Flow implemented with multiple data source support
- **Capabilities**: 4 data source types, automatic field mapping with AI, security validation
- **Strengths**: Multi-source imports, intelligent mapping, proper agent implementation

### Target State Summary
- **Architecture**: Enhanced with continuous refinement and conflict resolution
- **Key Enhancements**: Pattern learning persistence, multi-source reconciliation, dependency depth control
- **Timeline**: 6-8 weeks for enhancements

## Gap Analysis (Accurate Assessment)

### 1. Data Ingestion - Current vs Target

| Current State | Target State | Gap |
|--------------|--------------|-----|
| 4 source categories supported | 5+ specialized handlers (CloudAmize, etc.) | Add specific tool integrations |
| Sequential imports only | Continuous refinement of same assets | Implement update vs create logic |
| Security validation exists | Enhanced malware scanning | Add ClamAV integration |
| Source stored but not tracked | Authoritative source scoring | Add reliability tracking |
| New flow required each time | Iterative enhancement model | Enable flow continuation |

### 2. Field Mapping Intelligence - Current vs Target

| Current State | Target State | Gap |
|--------------|--------------|-----|
| Auto-mapping with confidence scores | Pattern learning persistence | Add mapping_patterns table |
| Intelligent matching implemented | Global/local pattern repository | Store learned patterns |
| In-memory pattern matching | Reusable mapping templates | Create template system |
| Single-use learning | Cross-engagement learning | Enable pattern sharing |

### 3. Conflict Resolution - Missing Capabilities

| Current State | Target State | Gap |
|--------------|--------------|-----|
| Sequential imports only | Multi-source reconciliation | Build conflict detection |
| No conflict handling | Confidence-based resolution | Create resolution engine |
| Single source of truth | Authoritative source model | Implement source hierarchy |
| No anomaly detection | Proactive alerts | Add anomaly detection |

### 4. Asset Management Enhancements Needed

| Current State | Target State | Gap |
|--------------|--------------|-----|
| Assets in flow state | Persistent assets table | Create asset lifecycle |
| Fixed types (server/app/device) | Extensible asset types | Add custom types |
| Basic classification | Component relationships | Add component mapping |
| Binary readiness flag | Graduated scoring | Implement readiness algorithm |

### 5. Dependency Discovery Enhancements

| Current State | Target State | Gap |
|--------------|--------------|-----|
| Single-level discovery | Configurable depth (1-3) | Add iterative analysis |
| Basic relationships | Typed dependencies | Implement 4 types |
| No characteristics | Coupling/criticality | Add metrics |
| In-flow storage only | Persistent dependencies | Create dependencies table |

### 6. Continuous Refinement - New Capability

| Current State | Target State | Gap |
|--------------|--------------|-----|
| New flow each import | Asset update model | Implement refinement |
| No history tracking | Source lineage | Add data provenance |
| Replace on import | Merge strategies | Build merge logic |
| No raw preservation | Raw data archive | Create raw storage |

## Enhancement Phases

### Phase 1: Continuous Refinement Foundation (Week 1-2)
**Goal**: Enable iterative asset enhancement instead of replacement

#### Week 1: Database Schema for Refinement
- [ ] Create assets table separate from flow state
- [ ] Add data_sources table with reliability scoring
- [ ] Implement raw_data_records for preservation
- [ ] Design asset version tracking
- [ ] Add source attribution per attribute

#### Week 2: Flow Modification
- [ ] Modify flow to check existing assets
- [ ] Implement merge strategies for updates
- [ ] Create conflict detection logic
- [ ] Add source lineage tracking
- [ ] Enable parallel raw data storage

### Phase 2: Pattern Learning Persistence (Week 3)
**Goal**: Store and reuse field mapping patterns

#### Week 3: Pattern Repository
- [ ] Create mapping_patterns table
- [ ] Implement pattern storage from AttributeMappingAgent
- [ ] Add template creation from successful mappings
- [ ] Enable cross-engagement pattern sharing (with opt-out)
- [ ] Build pattern confidence evolution

### Phase 3: Multi-Source Reconciliation (Week 4-5)
**Goal**: Handle conflicting data from multiple sources

#### Week 4: Conflict Detection
- [ ] Create DataReconciliationCrew
- [ ] Implement conflict identification algorithm
- [ ] Build confidence scoring for each source
- [ ] Add anomaly detection for suspicious changes
- [ ] Create conflict queue management

#### Week 5: Resolution Engine
- [ ] Implement authoritative source hierarchy
- [ ] Build resolution strategies (newest, highest confidence, authoritative)
- [ ] Create UI for conflict resolution
- [ ] Add audit trail for resolutions
- [ ] Enable bulk resolution capabilities

### Phase 4: Enhanced Asset Management (Week 6)
**Goal**: Improve asset lifecycle and relationships

#### Week 6: Asset Enhancements
- [ ] Implement graduated readiness scoring (0-100%)
- [ ] Add custom asset type support
- [ ] Create component relationship mapping
- [ ] Build asset state lifecycle (discovered → validated → assessed)
- [ ] Add readiness criteria configuration

### Phase 5: Dependency Analysis Depth (Week 7-8)
**Goal**: Enable configurable dependency discovery depth

#### Week 7: Iterative Discovery
- [ ] Implement depth parameter (1-3 levels)
- [ ] Add dependency type classification (runtime, data, infrastructure, temporal)
- [ ] Create coupling strength metrics
- [ ] Build criticality assessment
- [ ] Enable manual dependency additions

#### Week 8: Testing and Polish
- [ ] End-to-end testing of refinement flow
- [ ] Performance optimization for large datasets
- [ ] Documentation updates
- [ ] User training materials
- [ ] Production rollout preparation

## Key Enhancement Areas

### 1. Continuous Refinement Model
The primary gap is the ability to iteratively enhance assets rather than creating new flows each time:
- **Current**: Each import creates a new flow
- **Enhancement**: Enable asset updates across multiple imports
- **Benefit**: Build richer asset data over time

### 2. Pattern Learning Persistence
While field mapping is intelligent, patterns aren't preserved:
- **Current**: Patterns learned per flow only
- **Enhancement**: Store patterns for reuse
- **Benefit**: Faster, more accurate mapping over time

### 3. Multi-Source Reconciliation
When importing from multiple sources sequentially:
- **Current**: Latest import overwrites
- **Enhancement**: Intelligent conflict resolution
- **Benefit**: Best data from each source

### 4. Dependency Discovery Depth
- **Current**: Single-level analysis
- **Enhancement**: Configurable 1-3 levels
- **Benefit**: Complete dependency understanding

## Implementation Approach

### Database Enhancements
```sql
-- New tables to support enhancements
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    discovery_flow_id UUID,
    asset_type VARCHAR(50),
    asset_state VARCHAR(50),
    readiness_score FLOAT,
    -- Separate from flow state for persistence
);

CREATE TABLE data_sources (
    id UUID PRIMARY KEY,
    source_type VARCHAR(50),
    reliability_score FLOAT,
    is_authoritative_for JSONB
);

CREATE TABLE mapping_patterns (
    pattern_key VARCHAR(255) UNIQUE,
    source_pattern VARCHAR(255),
    target_field VARCHAR(255),
    confidence_score FLOAT,
    usage_count INTEGER
);
```

### Continuous Refinement Logic
```python
# Enhancement to existing flow
async def initialize_discovery(self):
    # Check for existing assets
    existing_assets = await self.asset_repository.find_by_engagement(
        self.context.engagement_id
    )
    
    if existing_assets:
        self.state.mode = "refinement"
        self.state.merge_strategy = "confidence_based"
    else:
        self.state.mode = "initial"
```

## Success Metrics

### Enhancement Success Criteria
| Enhancement | Success Metric | Target |
|------------|----------------|---------|
| Continuous Refinement | Assets enhanced vs replaced | >80% |
| Pattern Persistence | Mapping reuse rate | >60% |
| Conflict Resolution | Accurate reconciliation | >90% |
| Dependency Depth | Complete dependency maps | 95% |

### Business Value
- **Time Savings**: 50% reduction in manual review
- **Data Quality**: 30% improvement in completeness
- **Pattern Reuse**: 70% of mappings automated
- **Conflict Resolution**: 90% automatic resolution

## Risk Management

### Low-Risk Approach
1. **Preserve Current Function**: All enhancements are additive
2. **Feature Flags**: Enable enhancements gradually
3. **Backward Compatible**: Existing flows continue working
4. **Incremental Rollout**: Test with pilot engagements

## Timeline: 6-8 Weeks

### Quick Wins (Weeks 1-3)
- Pattern persistence for immediate reuse
- Basic continuous refinement

### Core Enhancements (Weeks 4-6)
- Multi-source reconciliation
- Dependency depth control

### Polish (Weeks 7-8)
- Performance optimization
- User training
- Documentation

This plan enhances your already capable Discovery Flow with advanced features while maintaining stability and delivering incremental value.