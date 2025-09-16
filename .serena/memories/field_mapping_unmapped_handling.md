# Field Mapping UNMAPPED Handling

## Problem
Field mapping was blindly mapping source fields to target fields with same names, creating invalid mappings to non-existent Asset model columns like "server_name", "azure_readiness", etc.

## Root Cause
Mapping logic didn't validate target fields against actual Asset model schema before creating mappings.

## Solution Implementation

### 1. Updated Field Mapping Logic
**File**: `backend/app/api/v1/endpoints/unified_discovery/flow_initialization_handlers.py`

```python
def _find_field_mapping(source_field: str, common_mappings: Dict[str, Tuple[str, float]]) -> Tuple[str, float]:
    """Find best field mapping, mark as UNMAPPED if no valid target exists."""
    # Check if source field has a known mapping
    if source_field in common_mappings:
        return common_mappings[source_field]

    # If no match found, mark as UNMAPPED instead of creating invalid mapping
    return "UNMAPPED", 0.0

# Apply only valid Asset model field mappings
VALID_ASSET_FIELDS = {
    "hostname", "ip_address", "asset_type", "operating_system",
    "cpu_cores", "memory_gb", "storage_gb", "network_interfaces",
    "applications", "dependencies", "criticality_score", "location"
}

def _create_asset_field_mappings(source_fields: List[str]) -> List[FieldMappingCreate]:
    mappings = []
    for field in source_fields:
        target_field, confidence = _find_field_mapping(field, COMMON_FIELD_MAPPINGS)

        # Only create mappings for valid Asset fields or mark as UNMAPPED
        if target_field not in VALID_ASSET_FIELDS and target_field != "UNMAPPED":
            target_field = "UNMAPPED"
            confidence = 0.0

        mappings.append(FieldMappingCreate(
            source_field=field,
            target_field=target_field,
            confidence_score=confidence,
            field_type=FieldMappingType.INFERRED
        ))
    return mappings
```

### 2. Display UNMAPPED Fields for Manual Mapping
**File**: `backend/app/api/v1/endpoints/unified_discovery/field_mapping_handlers.py`

```python
def _create_field_mapping_item(mapping) -> Optional[FieldMappingItem]:
    """Create FieldMappingItem, showing UNMAPPED fields for manual mapping."""
    target_field = mapping.target_field
    confidence_score = getattr(mapping, "confidence_score", 0.5)

    # For UNMAPPED fields, show empty target to indicate they need mapping
    if target_field == "UNMAPPED":
        target_field = ""  # Show empty target for unmapped fields
        confidence_score = 0.0  # Zero confidence for unmapped

    return FieldMappingItem(
        id=str(mapping.id),
        source_field=mapping.source_field,
        target_field=target_field,  # Empty for UNMAPPED
        confidence_score=confidence_score,
        status=getattr(mapping, "status", "suggested"),
        # ... other fields
    )
```

## Key Principles

### 1. Schema Validation
Always validate target fields against actual model schema:
```python
# Get valid fields from SQLAlchemy model
VALID_FIELDS = {col.name for col in Asset.__table__.columns}
```

### 2. UNMAPPED Strategy
- Mark invalid mappings as "UNMAPPED" instead of filtering them out
- Show UNMAPPED fields with empty target for manual user selection
- Preserve all source fields for user review

### 3. User Experience
- Show confidence scores (0.0 for UNMAPPED)
- Allow manual mapping of UNMAPPED fields
- Preserve field mapping context for user decisions

## Usage Pattern
Apply this pattern when mapping between any source schema and target model:

1. Define valid target fields from model schema
2. Attempt automatic mapping with confidence scores
3. Mark unmappable fields as "UNMAPPED"
4. Display UNMAPPED fields for manual user mapping
5. Never create invalid database field references
