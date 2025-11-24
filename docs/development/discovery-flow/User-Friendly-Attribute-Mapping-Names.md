# User-Friendly Attribute Mapping Names

This note captures how the Discovery attribute-mapping experience shows user-friendly field names for both CMDB imports and application-dependency imports.

## Backend Source of Friendly Names (PR #956)

| Component | Purpose | File / Reference |
| --- | --- | --- |
| Asset model column metadata | PR #956 added `Column.info` entries (`display_name`, `short_hint`, `category`) to the CMDB fields so we always have friendly labels co-located with the schema. | `backend/app/models/asset/*.py` |
| Target field handler | `/api/v1/data-import/available-target-fields` introspects `migration.assets` using that metadata. It also appends the dependency columns from `asset_dependencies` so the response already contains user-friendly names for both CMDB and application-dependency flows. | `backend/app/api/v1/endpoints/data_import/handlers/field_handler.py` |
| Knowledge bases | Processors/agents can reference `field_mapping_patterns.json` when they need canonical names for learning or validation. | `backend/app/knowledge_bases/field_mapping_patterns.json` |

## Frontend Consumers

| Component | Role | File |
| --- | --- | --- |
| FieldOptionsContext | Fetches `/data-import/available-target-fields` once after login and caches the CMDB-friendly list globally so classic CMDB flows render the proper labels. | `src/contexts/FieldOptionsContext/provider.tsx` |
| `useTargetFields` hook | When the Attribute Mapping page is tied to a specific flow, this hook calls the same endpoint with `flow_id`. If the backend response says `import_category === 'app_discovery'`, the hook returns that limited field list; otherwise it falls back to the global context list. | `src/hooks/discovery/attribute-mapping/useTargetFields.ts` |
| Mapping UI | `FieldMappingsTab`, `CriticalAttributesTab`, `ThreeColumnFieldMapper`, etc., render whichever list they receive so they automatically switch between CMDB and dependency fields. | `src/components/discovery/attribute-mapping/*` |

## Import-Type Behavior

1. **CMDB imports**
   - `FieldOptionsContext` supplies the friendly CMDB schema.
   - The flow-specific hook returns `null`, so the UI stays on the CMDB list.
2. **Application-dependency imports**
   - `useTargetFields` calls `/data-import/available-target-fields?flow_id=...`.
   - Backend already includes the dependency columns (e.g., `dependency_type`, `relationship_nature`, `direction`, `port`, `protocol_name`, `conn_count`, `first_seen`, `last_seen`).
   - The hook sees `import_category = 'app_discovery'` and returns that limited list so the dropdowns only show dependency-relevant fields.

## Extension Points

- If we want the backend to enforce per-import filtering, the handler already has access to the flow/import records; we can trim the list before returning it instead of relying on the hook.
- When new CMDB fields are added, update the column metadata on the `Asset` model—both the API and UI pick up the friendly labels automatically.
