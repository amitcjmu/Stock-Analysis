# Master Flow Orchestrator Schema Documentation

## Overview

The Master Flow Orchestrator uses the `crewai_flow_state_extensions` table as the central coordination point for all flow types in the migration platform. This document describes the schema enhancements made to support unified flow management.

## Schema Changes

### New Columns Added

#### 1. `phase_transitions` (JSONB)
- **Purpose**: Tracks the complete history of phase transitions for audit and debugging
- **Structure**: Array of transition objects
- **Example**:
```json
[
  {
    "phase": "data_import",
    "status": "completed",
    "timestamp": "2025-01-05T10:30:00Z",
    "duration_ms": 45000,
    "metadata": {"records_processed": 1500}
  },
  {
    "phase": "field_mapping",
    "status": "active",
    "timestamp": "2025-01-05T10:31:00Z"
  }
]
```

#### 2. `error_history` (JSONB)
- **Purpose**: Maintains history of errors and recovery attempts
- **Structure**: Array of error objects
- **Example**:
```json
[
  {
    "timestamp": "2025-01-05T10:45:00Z",
    "phase": "data_cleansing",
    "error": "Data validation failed",
    "details": {
      "error_code": "VALIDATION_001",
      "affected_records": 25,
      "stack_trace": "..."
    },
    "recovery_attempted": true,
    "recovery_successful": false
  }
]
```

#### 3. `retry_count` (INTEGER)
- **Purpose**: Tracks retry attempts for the current phase
- **Default**: 0
- **Constraints**: Must be >= 0
- **Usage**: Incremented on each retry, reset when moving to new phase

#### 4. `parent_flow_id` (UUID)
- **Purpose**: Enables hierarchical flow relationships
- **Foreign Key**: References `crewai_flow_state_extensions.flow_id`
- **Nullable**: Yes (root flows have no parent)
- **Example Use Cases**:
  - Discovery flow spawning multiple assessment flows
  - Planning flow creating execution sub-flows

#### 5. `child_flow_ids` (JSONB)
- **Purpose**: List of child flow IDs for quick traversal
- **Structure**: Array of UUID strings
- **Example**:
```json
[
  "550e8400-e29b-41d4-a716-446655440001",
  "550e8400-e29b-41d4-a716-446655440002"
]
```

#### 6. `flow_metadata` (JSONB)
- **Purpose**: Extensible metadata storage for flow-specific data
- **Structure**: Object with arbitrary key-value pairs
- **Example**:
```json
{
  "source": "api_v1",
  "triggered_by": "scheduled_job",
  "priority": "high",
  "tags": ["critical", "customer_xyz"],
  "custom_fields": {
    "department": "finance",
    "compliance_required": true
  }
}
```

### New Indexes

#### 1. `idx_crewai_flow_state_flow_type_status`
- **Columns**: `flow_type`, `flow_status`
- **Purpose**: Optimize queries filtering by flow type and status
- **Example Query**:
```sql
SELECT * FROM crewai_flow_state_extensions 
WHERE flow_type = 'discovery' AND flow_status = 'active';
```

#### 2. `idx_crewai_flow_state_client_status`
- **Columns**: `client_account_id`, `flow_status`
- **Purpose**: Optimize multi-tenant queries
- **Example Query**:
```sql
SELECT * FROM crewai_flow_state_extensions 
WHERE client_account_id = ? AND flow_status IN ('active', 'processing');
```

#### 3. `idx_crewai_flow_state_created_desc`
- **Columns**: `created_at DESC`
- **Purpose**: Optimize queries for recent flows
- **Example Query**:
```sql
SELECT * FROM crewai_flow_state_extensions 
ORDER BY created_at DESC LIMIT 10;
```

### New Constraints

#### 1. `chk_valid_flow_type`
- **Type**: CHECK constraint
- **Rule**: `flow_type IN ('discovery', 'assessment', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission')`
- **Purpose**: Ensure only valid flow types are stored

#### 2. `chk_valid_flow_status`
- **Type**: CHECK constraint
- **Rule**: `flow_status IN ('initialized', 'active', 'processing', 'paused', 'completed', 'failed', 'cancelled')`
- **Purpose**: Ensure only valid statuses are used

#### 3. `chk_retry_count_positive`
- **Type**: CHECK constraint
- **Rule**: `retry_count >= 0`
- **Purpose**: Prevent negative retry counts

#### 4. `fk_crewai_flow_state_parent`
- **Type**: Foreign key constraint
- **Reference**: `parent_flow_id` → `crewai_flow_state_extensions.flow_id`
- **On Delete**: SET NULL
- **Purpose**: Maintain referential integrity for hierarchical flows

## Data Migration

### Discovery Flows Migration
- All existing `discovery_flows` records are migrated to the master table
- `flow_id` is preserved as the primary identifier
- Current phase and error information is converted to new format
- `master_flow_id` is set on discovery_flows table for backward compatibility

### Assessment Flows Migration
- All existing `assessment_flows` records are migrated to the master table
- New `flow_id` is generated (assessment flows didn't have one)
- Original assessment flow ID is preserved in `flow_metadata.original_id`
- Phase results and agent insights are preserved in `flow_persistence_data`

## Usage Examples

### Creating a New Flow
```python
# Master orchestrator will handle this
flow_data = {
    'flow_id': str(uuid.uuid4()),
    'client_account_id': client_id,
    'engagement_id': engagement_id,
    'user_id': user_id,
    'flow_type': 'discovery',
    'flow_name': 'Infrastructure Discovery - Production',
    'flow_status': 'initialized',
    'phase_transitions': [
        {
            'phase': 'initialization',
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }
    ]
}
```

### Querying Active Flows
```sql
-- Get all active flows for a client
SELECT flow_id, flow_type, flow_name, created_at
FROM crewai_flow_state_extensions
WHERE client_account_id = ? 
  AND flow_status IN ('active', 'processing')
ORDER BY created_at DESC;

-- Get flow hierarchy
WITH RECURSIVE flow_tree AS (
    SELECT flow_id, flow_name, parent_flow_id, 0 as level
    FROM crewai_flow_state_extensions
    WHERE parent_flow_id IS NULL AND client_account_id = ?
    
    UNION ALL
    
    SELECT c.flow_id, c.flow_name, c.parent_flow_id, p.level + 1
    FROM crewai_flow_state_extensions c
    JOIN flow_tree p ON c.parent_flow_id = p.flow_id
)
SELECT * FROM flow_tree ORDER BY level, flow_name;
```

### Updating Flow State
```python
# Add phase transition
new_transition = {
    'phase': 'asset_inventory',
    'status': 'active',
    'timestamp': datetime.utcnow().isoformat()
}
flow.phase_transitions.append(new_transition)

# Record error
error_entry = {
    'timestamp': datetime.utcnow().isoformat(),
    'phase': current_phase,
    'error': str(exception),
    'details': {'traceback': traceback.format_exc()},
    'recovery_attempted': True
}
flow.error_history.append(error_entry)
flow.retry_count += 1
```

## Performance Considerations

1. **Index Usage**: The composite indexes significantly improve query performance for common access patterns
2. **JSONB Operations**: PostgreSQL's JSONB type provides efficient storage and querying of semi-structured data
3. **Hierarchical Queries**: The parent_flow_id foreign key enables efficient recursive queries
4. **Pagination**: Use created_at DESC index for efficient pagination of recent flows

## Migration Notes

- The migration is designed to be reversible with full rollback support
- Existing data is preserved with zero data loss
- The migration handles both discovery and assessment flows
- All new columns have sensible defaults to maintain backward compatibility

## Future Enhancements

1. **Partitioning**: Consider partitioning by created_at for very large datasets
2. **Additional Indexes**: Monitor query patterns and add indexes as needed
3. **Archival Strategy**: Implement archival for completed flows older than X days
4. **Search Optimization**: Consider adding GIN indexes for JSONB full-text search