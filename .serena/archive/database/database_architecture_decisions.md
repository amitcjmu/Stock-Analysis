# Database Architecture Decisions

## Insight 1: JSON Fields Before EAV
**Problem**: Need dynamic asset attributes without full EAV complexity
**Solution**: Use existing JSON fields first, defer EAV migration
**Code**:
```python
# Asset model has these JSON fields
custom_attributes = Column(JSON)      # For dynamic attributes
technical_details = Column(JSON)      # For technical metadata

# Use for conflict detection
if asset.custom_attributes:
    for field, value in asset.custom_attributes.items():
        sources[field].append({
            "value": value,
            "source": "custom_attributes",
            "confidence": 0.7
        })
```
**Usage**: Start with JSON fields for flexibility, migrate to EAV when scale requires

## Insight 2: Tenant ID Types
**Problem**: Confusion about client_account_id and engagement_id types
**Solution**: Always use UUID for tenant IDs in migration schema
**Code**:
```python
# CORRECT - UUIDs for tenant scoping
client_account_id = Column(
    UUID(as_uuid=True),
    ForeignKey("migration.client_accounts.id"),
    nullable=False
)
engagement_id = Column(
    UUID(as_uuid=True),
    ForeignKey("migration.engagements.id"),
    nullable=False
)
```
**Usage**: All new tables in migration schema must use UUID tenant IDs

## Insight 3: Modular Gap Analysis Tools
**Problem**: Assumption that single GapAnalysisTool needed
**Reality**: 8 specialized tools already exist and are superior
**Tools**:
```
- AttributeMapperTool
- CompletenessAnalyzerTool
- QualityScorerTool
- GapIdentifierTool
- ImpactCalculatorTool
- EffortEstimatorTool
- PriorityRankerTool
- CollectionPlannerTool
```
**Usage**: Enhance existing modular tools instead of creating monolithic tool
