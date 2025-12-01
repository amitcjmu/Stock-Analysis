# Collection Gap Analysis Comprehensive Implementation

## Insight 1: Multi-Tenant Scoping for Collection Flows
**Problem**: Collection flow queries missing tenant isolation, allowing cross-tenant data access
**Solution**: Add AND conditions with client_account_id and engagement_id to all queries
**Code**:
```python
# Before - vulnerable to cross-tenant access
flow_result = await db.execute(
    select(CollectionFlow).where(CollectionFlow.id == flow_id)
)

# After - properly scoped
flow_result = await db.execute(
    select(CollectionFlow).where(
        and_(
            CollectionFlow.id == flow_id,
            CollectionFlow.client_account_id == context.client_account_id,
            CollectionFlow.engagement_id == context.engagement_id
        )
    )
)
```
**Usage**: Apply to ALL database queries in multi-tenant systems

## Insight 2: Asset-Scoped Data Collection
**Problem**: Collected data queries returning tenant-wide data instead of asset-specific
**Solution**: Filter CollectedDataInventory by asset_id in normalized_data JSON field
**Code**:
```python
# Asset-scoped with tenant isolation
collected_query = select(CollectedDataInventory).where(
    and_(
        CollectedDataInventory.client_account_id == context.client_account_id,
        CollectedDataInventory.engagement_id == context.engagement_id,
        CollectedDataInventory.normalized_data["asset_id"].astext == str(asset.id)
    )
).order_by(desc(CollectedDataInventory.collected_at)).limit(200)
```
**Usage**: When querying JSON fields for asset-specific data

## Insight 3: Robust UUID Type Handling
**Problem**: UUID conversion failures causing 422 errors
**Solution**: Try-except blocks with proper type checking and logging
**Code**:
```python
def handle_flow_id(flow_id: Union[int, str, UUID]) -> Union[int, UUID]:
    if isinstance(flow_id, str):
        try:
            return UUID(flow_id)
        except (ValueError, TypeError):
            try:
                return int(flow_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid flow_id: {flow_id}")
    elif isinstance(flow_id, UUID):
        return flow_id
    return flow_id

# For lists of IDs
valid_ids = []
for aid in selected_asset_ids:
    try:
        if isinstance(aid, str):
            valid_ids.append(UUID(aid))
        elif isinstance(aid, UUID):
            valid_ids.append(aid)
    except (ValueError, TypeError) as e:
        logger.warning(f"Skipping invalid ID: {aid}, error: {e}")
```
**Usage**: Handle mixed UUID/string inputs from frontend

## Insight 4: Asset Model Field Mapping
**Problem**: Field names don't match actual database columns
**Solution**: Map logical names to actual columns and JSON fields
**Code**:
```python
# Direct Asset model fields
direct_fields = ["name", "asset_type", "description", "business_criticality"]
tech_fields = ["technology_stack", "environment"]  # NOT technical_stack, deployment_environment

# Access pattern
for field in direct_fields:
    value = getattr(asset, field, None)

# JSON field access
if asset.custom_attributes:
    compliance = asset.custom_attributes.get("compliance_requirements")
if asset.technical_details:
    architecture = asset.technical_details.get("architecture_pattern")
```
**Usage**: When accessing Asset model fields - check actual column names

## Insight 5: Comprehensive Gap Analysis Implementation
**Problem**: Need to analyze gaps from multiple sources (model, imports, dependencies)
**Solution**: Multi-source gap detection with severity prioritization
**Code**:
```python
async def identify_comprehensive_gaps(asset, db, context):
    gaps = []

    # 1. Asset type overlay requirements
    overlay = get_asset_type_overlay(asset.asset_type)
    for field_config in overlay["required_fields"]:
        # Check direct, technical_details, and custom_attributes

    # 2. Lost data from imports (raw vs normalized)
    for data_entry in collected_data:
        if data_entry.raw_data and data_entry.normalized_data:
            raw_keys = set(data_entry.raw_data.keys())
            normalized_keys = set(data_entry.normalized_data.keys())
            lost_fields = raw_keys - normalized_keys

    # 3. Dependencies
    deps = await db.execute(select(AssetDependency).where(...))

    # 4. 6R readiness gaps
    if not asset.custom_attributes.get("rto"):
        gaps.append({"field": "rto", "severity": "critical", ...})

    # Prioritize by severity
    gaps.sort(key=lambda x: (severity_order[x["severity"]], x["field"]))
    return gaps
```
**Usage**: Generate comprehensive questionnaires based on actual gaps

## Key Patterns
- **Always** include tenant scoping (client_account_id + engagement_id)
- **Always** wrap UUID conversions in try-except
- **Check** actual model field names vs logical names
- **Use** `.get()` for JSON field access, `getattr()` for model fields
- **Import** correct models (AssetDependency not AssetRelationship)
