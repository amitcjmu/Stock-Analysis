# Asset-Agnostic Data Collection Remedial Plan

## Executive Summary

This plan addresses the critical gap where the Data Integration page shows only dummy demo data and the collection flow requires selecting an application first. We will transform the system to accept ANY asset type (servers, databases, devices, applications) and detect real conflicts when the same field has different values from different sources.

## Current State Issues

### 1. Data Integration Page
- **Problem**: Shows hardcoded dummy data instead of real conflicts
- **Impact**: Users cannot resolve actual data conflicts
- **Evidence**: Static mock data in `/src/pages/assessment/collection-gaps/data-integration.tsx`

### 2. Application-First Requirement
- **Problem**: Collection flow forces application selection first
- **Impact**: Cannot collect data for infrastructure assets without applications
- **Evidence**: Application selection required in adaptive forms flow

### 3. No Real Conflict Detection
- **Problem**: No backend mechanism to detect field-level conflicts
- **Impact**: Conflicting data from multiple sources goes undetected
- **Evidence**: No conflict detection service or database tables

### 4. Fixed Asset Schema
- **Problem**: Cannot handle dynamic/unknown asset types
- **Impact**: New asset types require code changes
- **Evidence**: Fixed Asset model with predefined fields

## Proposed Solution Architecture

### Phase 1: Database Foundation (Week 1)

#### 1.1 EAV Schema Implementation
```sql
-- Core tables for asset-agnostic data storage
CREATE TABLE asset_type_definitions (
    id UUID PRIMARY KEY,
    type_name VARCHAR(255),
    json_schema JSONB,
    client_account_id INTEGER,
    engagement_id INTEGER
);

CREATE TABLE asset_field_values (
    id UUID PRIMARY KEY,
    asset_id UUID REFERENCES assets(id),
    field_name VARCHAR(255),
    field_value TEXT,
    source_system VARCHAR(255),
    confidence_score FLOAT,
    collected_at TIMESTAMP,
    identity_vector vector(768)  -- pgvector for similarity
);

CREATE TABLE asset_field_conflicts (
    id UUID PRIMARY KEY,
    asset_id UUID,
    field_name VARCHAR(255),
    conflicting_values JSONB,
    resolution_status VARCHAR(50),
    resolved_value TEXT,
    resolved_by UUID
);
```

#### 1.2 Migration Strategy
- Create migration `074_add_asset_agnostic_eav_schema.py`
- Preserve existing Asset model for backward compatibility
- Add foreign key relationships to link EAV with existing assets
- Create indexes for performance (asset_id, field_name composite)

#### 1.3 Confidence Scoring System
```python
confidence_score = (
    source_reliability_weight * 0.4 +
    data_freshness_weight * 0.3 +
    validation_status_weight * 0.2 +
    historical_accuracy * 0.1
)
```

### Phase 2: Backend Services (Week 1-2)

#### 2.1 Conflict Detection Service
```python
class ConflictDetectionService:
    async def detect_conflicts(self, asset_id: str) -> List[FieldConflict]:
        # Query all field values for asset
        # Group by field_name
        # Identify fields with multiple distinct values
        # Calculate confidence scores
        # Return conflict list

    async def auto_resolve(self, conflict: FieldConflict) -> Optional[str]:
        # Apply resolution rules
        # Consider confidence thresholds
        # Return winning value or None for manual review
```

#### 2.2 Asset Collection API Endpoints
```python
# New endpoints to implement
POST /api/v1/collection/assets/start  # Start collection for any asset
GET /api/v1/collection/assets/{asset_id}/conflicts  # Get real conflicts
POST /api/v1/collection/assets/{asset_id}/conflicts/resolve  # Resolve conflict
GET /api/v1/collection/assets/{asset_id}/schema  # Get dynamic schema
POST /api/v1/collection/assets/bulk-import  # Import multiple assets
```

#### 2.3 Data Source Integration
- Enhance CSV upload processing to populate EAV tables
- CMDB connector to sync field values with provenance
- Manual form submissions tracked with source metadata
- API integrations with confidence scoring

### Phase 3: CrewAI Agent Enhancement (Week 2)

#### 3.1 New Agent Types
```python
# Schema Discovery Agent
class SchemaDiscoveryAgent:
    """Analyzes asset data to discover dynamic schema"""

# Conflict Detection Agent
class ConflictDetectorAgent:
    """Identifies field-level conflicts across sources"""

# Conflict Resolution Agent
class ConflictResolverAgent:
    """Suggests automated resolutions based on patterns"""

# Relationship Discovery Agent
class RelationshipDiscovererAgent:
    """Detects implicit relationships between assets"""

# Similarity Analyzer Agent
class SimilarityAnalyzerAgent:
    """Uses pgvector to find duplicate/similar assets"""
```

#### 3.2 Agent Workflow Changes
```python
# Modified collection flow phases
ASSET_AGNOSTIC_PHASES = [
    "ASSET_IDENTIFICATION",     # Any asset type
    "SCHEMA_DISCOVERY",          # Dynamic field detection
    "DATA_COLLECTION",           # Multi-source gathering
    "CONFLICT_DETECTION",        # Real conflict identification
    "CONFLICT_RESOLUTION",       # Automated + manual resolution
    "RELATIONSHIP_DISCOVERY",    # Find dependencies
    "CANONICAL_MAPPING"          # Map to applications
]
```

#### 3.3 EAV-Aware Tools
```python
# New tools for agents
class EAVFieldValueTool:
    """Read/write field values in EAV structure"""

class ConflictDetectionTool:
    """Detect conflicts for specific asset"""

class SimilaritySearchTool:
    """Find similar assets using pgvector"""
```

### Phase 4: Frontend UI Transformation (Week 2-3)

#### 4.1 Asset Entry Point Component
```typescript
// New asset selector component
interface AssetSelectorProps {
    onSelectAsset: (asset: Asset) => void;
    allowedTypes: AssetType[];  // Any type allowed
}

// Universal asset search
const UniversalAssetSearch: React.FC = () => {
    // Search across all asset types
    // Display type badges (server, DB, app, device)
    // Allow bulk CSV import
};
```

#### 4.2 Real Conflict Resolution UI
```typescript
// Replace dummy data with real conflicts
interface ConflictResolverProps {
    asset_id: string;
    conflicts: FieldConflict[];
    onResolve: (resolution: ConflictResolution) => void;
}

const RealConflictResolver: React.FC<ConflictResolverProps> = () => {
    // Fetch real conflicts from backend
    // Show confidence scores and sources
    // Allow manual override
    // Track resolution history
};
```

#### 4.3 Progressive Data Collection
```typescript
// Dynamic form based on discovered schema
const DynamicAssetForm: React.FC<{assetId: string}> = () => {
    const { data: schema } = useQuery(['asset-schema', assetId]);
    const { data: values } = useQuery(['asset-values', assetId]);

    // Generate form fields dynamically
    // Show completeness percentage
    // Highlight missing required fields
};
```

#### 4.4 User Journey Redesign
```
1. START → Select/Import ANY Asset
2. DISCOVER → Agent analyzes asset schema
3. COLLECT → Gather from multiple sources
4. DETECT → Show real conflicts
5. RESOLVE → User resolves conflicts
6. ENRICH → Progressive data collection
7. MAP → Connect to canonical apps
```

## Implementation Timeline

### Week 1: Database & Backend Foundation
- **Day 1-2**: Create and run EAV schema migration
- **Day 3-4**: Implement ConflictDetectionService
- **Day 5**: Create new API endpoints

### Week 2: Agent & Service Integration
- **Day 1-2**: Implement new agent types
- **Day 3-4**: Create EAV-aware tools
- **Day 5**: Test agent workflows

### Week 3: Frontend Transformation
- **Day 1-2**: Build AssetSelector component
- **Day 3-4**: Replace dummy data with real conflicts
- **Day 5**: Test end-to-end flow

### Week 4: Testing & Refinement
- **Day 1-2**: Integration testing
- **Day 3-4**: Performance optimization
- **Day 5**: Documentation & deployment

## Success Criteria

1. **Asset Agnostic**: Can start collection with ANY asset type
2. **Real Conflicts**: Data Integration shows actual field conflicts
3. **Confidence Scoring**: Multi-factor confidence displayed
4. **Progressive Collection**: Dynamic schema discovery works
5. **Relationship Detection**: Asset dependencies identified
6. **Performance**: Conflict detection < 2 seconds for 100 fields
7. **User Experience**: Clear conflict resolution workflow

## Risk Mitigation

### Technical Risks
- **EAV Performance**: Mitigate with proper indexing and caching
- **pgvector Scaling**: Use IVFFlat indexes for large datasets
- **Schema Evolution**: Version schemas with migration support

### Business Risks
- **User Adoption**: Provide training on new workflow
- **Data Quality**: Implement validation rules and audit trails
- **Backward Compatibility**: Maintain existing flows during transition

## Rollback Strategy

If issues arise:
1. Keep existing Asset model functional
2. Feature flag for new asset-agnostic flow
3. Gradual migration with parallel runs
4. Complete rollback via feature toggle

## Monitoring & Metrics

Track:
- Conflict detection accuracy
- Resolution time per conflict
- Data completeness percentage
- User satisfaction scores
- System performance metrics

## Approval Checklist

- [ ] Database migration reviewed
- [ ] API endpoint design approved
- [ ] Agent architecture validated
- [ ] UI mockups approved
- [ ] Performance requirements met
- [ ] Security review completed
- [ ] Testing strategy defined

---

**Next Steps**: Review this plan and provide feedback for refinement before implementation begins.