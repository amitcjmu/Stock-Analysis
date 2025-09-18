## Database and Model Consolidation Plan — DiscoveryFlow, MasterFlow FK, AssessmentFlow
## Revised Implementation Plan — DiscoveryFlow Consolidation, Master FK Correction, Assessment Progress

Owner: Coding Assistant
Date: 2025-09-18

This plan consolidates DiscoveryFlow schema and code in a single PR, based on measured reference counts and your directives:
canonical columns →
  - field_mapping_completed,
  - asset_inventory_completed,
  - dependency_analysis_completed,
  - tech_debt_assessment_completed.
It also corrects the discovery master FK to CFSE.flow_id and aligns AssessmentFlow progress to integer.

---

## 0) Outcomes (single PR, zero ambiguity)

- Canonical DiscoveryFlow phase flags are the NEW names listed above; legacy flags removed from model and DB.
- All backend/frontend references updated to canonical names with exact file/line edits below.
- FK fixed: `discovery_flows.master_flow_id` → `crewai_flow_state_extensions.flow_id` via safe column-swap with NOT VALID/VALIDATE.
- AssessmentFlow `progress` is integer across model and API.
- Boolean comparisons fixed where touched (`is True` → `== True`).
- Audit queries included; no phased compatibility layer retained.

---

## 1) Canonicalization decisions (data-driven)

- field_mapping_completed beats attribute_mapping_completed (35 > 23 total refs)
- asset_inventory_completed beats inventory_completed (32 > 17)
- dependency_analysis_completed beats dependencies_completed (24 > 14)
- tech_debt_assessment_completed beats tech_debt_completed (15 ≈ 16; directive: keep NEW)

Legacy columns to drop: attribute_mapping_completed, inventory_completed, dependencies_completed, tech_debt_completed.

---

## 2) Model edits

Files:
- `backend/app/models/discovery_flow.py`
  - Ensure only canonical columns exist:
    - Keep Boolean, not-null, default False:
      - field_mapping_completed
      - asset_inventory_completed
      - dependency_analysis_completed
      - tech_debt_assessment_completed
  - Update methods to use canonical names:
    - calculate_progress, update_progress, get_current_phase, get_next_phase, is_complete, to_dict (phases map keys)

- `backend/app/models/crewai_flow_state_extensions.py`
  - Add fields present in DB (no DB changes):
    - collection_flow_id: UUID, FK("collection_flows.id"), nullable=True
    - automation_tier: String(20), nullable=True
    - collection_quality_score: Float, nullable=True
    - data_collection_metadata: JSONB, server_default '{}'

- `backend/app/models/assessment_flow/core_models.py`
  - Change `progress = Column(Integer, default=0, nullable=False)`

Lint: fix any imports (Float, JSONB, text) as needed.

---

## 3) Exact code refactors (new ← legacy)

Replace attribute_mapping_completed → field_mapping_completed at:
- backend/app/api/v1/endpoints/unified_discovery/field_mapping_handlers.py:130, 399
- backend/app/services/flow_orchestration/field_mapping_logic.py:372, 387
- backend/app/services/crewai_flows/flow_state_utils.py:70
- backend/app/api/v1/endpoints/unified_discovery/health_handlers.py:97
- backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:101, 105
- backend/app/services/discovery/phase_transition_service.py:106
- backend/app/services/discovery/field_mapping_helpers.py:36
- backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py:338
- backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:57, 218, 231, 257
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:89
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:45, 155
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:47, 63
- backend/app/services/discovery/flow_status/data_helpers.py:137
- backend/app/services/crewai_flows/flow_state_bridge.py:203
- backend/app/models/discovery_flow.py:59, 150, 171, 192, 209, 265
- backend/app/core/auto_seed_demo_data.py:98, 111
- Frontend:
  - src/hooks/discovery/useDiscoveryFlowAutoDetection.ts (2 spots total for pair)
  - src/hooks/useUnifiedDiscoveryFlow.ts (pair occurrences)
  - src/types/discovery.ts (pair occurrence)

Replace inventory_completed → asset_inventory_completed at:
- backend/app/api/v1/endpoints/flow_processing.py:338, 341, 451
- backend/app/services/crewai_flows/flow_state_utils.py:72
- backend/app/api/v1/endpoints/unified_discovery/health_handlers.py:99
- backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:111, 114
- backend/app/api/v1/endpoints/unified_discovery/asset_handlers.py:178, 185, 237
- backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:59, 222, 233, 259
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:92
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:47, 157
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:49
- backend/app/services/flow_orchestration/smart_discovery_service.py:292, 293
- backend/app/services/mfo_sync_agent.py:222
- backend/app/services/crewai_flows/flow_state_bridge.py:207
- backend/app/models/discovery_flow.py:63, 152, 173, 194, 211, 267
- backend/app/core/auto_seed_demo_data.py:100, 113
- Frontend:
  - src/services/api/discoveryFlowService.ts (pair occurrences)
  - src/hooks/useUnifiedDiscoveryFlow.ts (pair occurrence)

Replace dependencies_completed → dependency_analysis_completed at:
- backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_executors.py:386, 390, 394
- backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:116, 118
- backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:60, 224, 234, 260
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:93
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:48, 158
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:50
- backend/app/services/crewai_flows/flow_state_bridge.py:209
- backend/app/models/discovery_flow.py:66, 153, 174, 195, 212, 268
- backend/app/core/auto_seed_demo_data.py:101, 114
- Frontend:
  - src/services/api/discoveryFlowService.ts (pair occurrence)
  - src/hooks/useUnifiedDiscoveryFlow.ts (pair occurrence)

Replace tech_debt_completed → tech_debt_assessment_completed at:
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:94
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:49, 159
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:51
- backend/app/services/crewai_flows/flow_state_bridge.py:211
- backend/app/models/discovery_flow.py:69, 154, 175, 196, 213, 269
- backend/app/core/auto_seed_demo_data.py:102, 115
- Frontend:
  - src/services/api/discoveryFlowService.ts (pair occurrence)
  - src/hooks/useUnifiedDiscoveryFlow.ts (pair occurrence)

Boolean comparisons (where touched):
- backend/app/repositories/discovery_flow_repository/queries/flow_queries.py:143–148 (== True)
- backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py:47–53, 58, 99 (== True)
- backend/app/repositories/discovery_flow_repository/queries/analytics_queries.py:84 (== True)

---

## 4) Alembic migrations (2 files)

4.1) 068_correct_discovery_master_fk.py

Objective: switch FK to CFSE.flow_id with minimal lock time.

Upgrade:
- Add column `master_flow_id_new uuid` (nullable).
- Backfill in two passes:
  - Pass A: `UPDATE migration.discovery_flows df SET master_flow_id_new = cfe.flow_id FROM migration.crewai_flow_state_extensions cfe WHERE df.master_flow_id = cfe.id;`
  - Pass B: `UPDATE migration.discovery_flows df SET master_flow_id_new = cfe.flow_id FROM migration.crewai_flow_state_extensions cfe WHERE df.master_flow_id_new IS NULL AND df.flow_id = cfe.flow_id AND df.client_account_id = cfe.client_account_id AND df.engagement_id = cfe.engagement_id;`
- Create FK NOT VALID: `ALTER TABLE ... ADD CONSTRAINT fk_discovery_master_flow_flowid FOREIGN KEY (master_flow_id_new) REFERENCES migration.crewai_flow_state_extensions(flow_id) ON DELETE CASCADE NOT VALID;`
- Create index on `master_flow_id_new`.
- Validate constraint: `ALTER TABLE ... VALIDATE CONSTRAINT fk_discovery_master_flow_flowid;`
- Swap columns: drop old FK; rename `master_flow_id` → `_old`; rename `_new` → `master_flow_id`.
- Optional: drop `_old` in same migration after verification query shows full coverage (or keep to 069 for final drop).

Downgrade:
- Reverse rename; drop new FK/index; restore old FK to `id` if needed.

4.2) 069_consolidate_discovery_phase_flags.py

Objective: finalize canonical columns and remove legacy.

Upgrade:
- Ensure canonical columns exist (Boolean NOT NULL DEFAULT false).
- Backfill canonical from legacy (precedence logic: canonical = COALESCE(canonical, legacy)).
- Audit report (temporary table or NOTICE) listing rows where canonical IS DISTINCT FROM legacy pre-update.
- Drop legacy columns: attribute_mapping_completed, inventory_completed, dependencies_completed, tech_debt_completed.
- Drop unused fields after usage check: import_session_id, flow_description (code scan found only doc/test references; safe to drop in DB).

Downgrade:
- Recreate legacy columns nullable; copy from canonical; keep canonical intact.

---

## 5) Tests and verification

- Update/confirm unit/integration tests that assert phase flags and progress types.
- Add migration test to validate FK correctness and phase flag consolidation.
- Post-migration SQL checks:
  - Counts of NULL `master_flow_id` should be zero (except truly orphaned flows).
  - Random sample verify `master_flow_id` equals CFSE.flow_id.
  - Ensure canonical flags present; legacy absent.

---

## 6) Commit and PR content

- Edits: model files, services/repos/frontend refs (listed above), tests.
- New migrations: 068, 069.
- PR description:
  - Summary of canonicalization choices (with reference counts)
  - FK correction strategy (NOT VALID/VALIDATE, swap)
  - Backfill + audit approach
  - Risk/rollback notes

---

## 7) Rollback

- Use migration downgrades. If FK causes issues, swap back using preserved `_old` or reverse constraint.

Author: Coding Assistant
Date: 2025-09-18

### Goals

- Eliminate duplicate/misaligned DiscoveryFlow phase columns by consolidating on canonical names.
- Correct the DiscoveryFlow → CrewAI master FK to reference `flow_id` (not `id`).
- Align models with actual DB (AssessmentFlow `progress` as integer; add missing CFSE fields in model).
- Reduce code sprawl and banned patterns (e.g., SQLAlchemy boolean `is True`).

### Scope (alembic 056–067 quick review)

- 056_fix_alembic_version_column_size: infra; keep.
- 060_fix_long_constraint_names: maintenance; keep.
- 061_fix_null_master_flow_ids: aligns orchestration; keep.
- 062_add_description_to_assessment_flows: adds JSONB/meta; keep.
- 063_fix_enum_case_for_pattern_type: unrelated enum fix; keep.
- 066_add_master_flow_id_to_discovery_flows: sets FK to `crewai_flow_state_extensions.id` (mismatch vs model expecting `flow_id`); replace with corrective migration.
- 067_fix_discovery_flow_columns: adds duplicate "new" phase columns; replace with consolidation migration that removes duplicates.

---

## Decisions

- DiscoveryFlow canonical flags (keep legacy names):
  - attribute_mapping_completed, inventory_completed, dependencies_completed, tech_debt_completed
  - Remove duplicates: field_mapping_completed, asset_inventory_completed, dependency_analysis_completed, tech_debt_assessment_completed

- Master FK correction:
  - `discovery_flows.master_flow_id` must reference `crewai_flow_state_extensions.flow_id` (not `id`). Backfill values accordingly.

- AssessmentFlow:
  - `progress` is integer (0–100). Update model to Integer (DB already integer per schema dump).

- CrewAIFlowStateExtensions model:
  - Add fields present in DB: collection_flow_id (UUID, FK to collection_flows.id), automation_tier (String(20)), collection_quality_score (Float), data_collection_metadata (JSONB, default {}). No DB changes needed.

- CollectionFlow enums: keep current PostgreSQL enums created by migrations (no change).

---

## Model edits (precise)

1) `backend/app/models/discovery_flow.py`

- Replace new-phase attributes with legacy names and update internal methods to reference legacy names. Ensure columns are Boolean, non-null, default False.

- Required attribute name changes:
  - field_mapping_completed → attribute_mapping_completed
  - asset_inventory_completed → inventory_completed
  - dependency_analysis_completed → dependencies_completed
  - tech_debt_assessment_completed → tech_debt_completed

- Update method bodies to use the legacy names in:
  - `calculate_progress`
  - `update_progress`
  - `get_current_phase`
  - `get_next_phase`
  - `is_complete`
  - `to_dict()` phases map

- Confirm FK definition remains aligned (model already references `crewai_flow_state_extensions.flow_id`).

2) `backend/app/models/crewai_flow_state_extensions.py`

- Add model fields (align to DB):
  - `collection_flow_id = Column(UUID(as_uuid=True), ForeignKey("collection_flows.id"), nullable=True)`
  - `automation_tier = Column(String(20), nullable=True)`
  - `collection_quality_score = Column(Float, nullable=True)`
  - `data_collection_metadata = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))`

3) `backend/app/models/assessment_flow/core_models.py`

- Change `progress = Column(Float, ...)` → `progress = Column(Integer, default=0, nullable=False)` (and keep the existing `valid_progress` CHECK 0–100 on DB side).

---

## Alembic migrations (new)

Create two forward migrations to replace 066 and 067 behavior without add-then-drop churn.

1) 068_correct_discovery_master_fk.py

- Purpose: Ensure `migration.discovery_flows.master_flow_id` references `migration.crewai_flow_state_extensions.flow_id` and values are backfilled correctly.

- Upgrade steps (idempotent):
  - If FK exists to `crewai_flow_state_extensions.id`, drop it.
  - Backfill mapping:
    - Case A: When `df.master_flow_id = cfe.id`, set `df.master_flow_id = cfe.flow_id` (join on `cfe.id = old_master_flow_id`).
    - Case B: When `df.master_flow_id IS NULL` and `df.flow_id = cfe.flow_id` (and tenant matches), set `df.master_flow_id = cfe.flow_id`.
  - Recreate FK: `FOREIGN KEY (master_flow_id) REFERENCES migration.crewai_flow_state_extensions(flow_id) ON DELETE CASCADE`.
  - Ensure index exists on `discovery_flows(master_flow_id)`.

- Downgrade: Drop FK to `flow_id`; (optionally) recreate FK to `id` only if strictly needed (prefer no-op downgrade to avoid reintroducing the bug).

2) 069_consolidate_discovery_phase_flags.py

- Purpose: Canonicalize to legacy phase flags and remove duplicates and unused fields.

- Upgrade steps (idempotent):
  - Ensure legacy columns exist (if missing, add Boolean NOT NULL DEFAULT false):
    - attribute_mapping_completed, inventory_completed, dependencies_completed, tech_debt_completed
  - Backfill legacy from duplicate new columns (OR semantics):
    - `attribute_mapping_completed = attribute_mapping_completed OR field_mapping_completed`
    - `inventory_completed = inventory_completed OR asset_inventory_completed`
    - `dependencies_completed = dependencies_completed OR dependency_analysis_completed`
    - `tech_debt_completed = tech_debt_completed OR tech_debt_assessment_completed`
  - Drop duplicate columns if exist:
    - field_mapping_completed, asset_inventory_completed, dependency_analysis_completed, tech_debt_assessment_completed
  - Drop unused legacy columns when confirmed not referenced:
    - import_session_id, flow_description (guarded by existence checks)
  - Normalize defaults/server_defaults to false and not-null for the legacy flags.

- Downgrade: Recreate dropped duplicate columns as nullable booleans, set them equal to the legacy flags (best-effort), and keep legacy columns.

---

## Code refactors required

1) Replace banned boolean comparisons and align attribute names

- `backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py`
  - Replace `is True` with `== True` for all SQLAlchemy booleans.
  - Align references: use `attribute_mapping_completed`, `inventory_completed`, `dependencies_completed`, `tech_debt_completed`.
  - In `phase_completed_spec`, map both "attribute_mapping" and "field_mapping" to `attribute_mapping_completed`.

- `backend/app/repositories/discovery_flow_repository/queries/analytics_queries.py`
  - Replace reads of `field_mapping_completed` with `attribute_mapping_completed`.

- `backend/app/services/discovery_flow_service/managers/summary_manager.py`
  - Replace references to new names with legacy names.

### Exact references to update (new → legacy)

- Replace `field_mapping_completed` → `attribute_mapping_completed` at:
  - backend/app/api/v1/endpoints/unified_discovery/field_mapping_handlers.py:130, 399
  - backend/app/services/flow_orchestration/field_mapping_logic.py:372, 387
  - backend/app/services/crewai_flows/flow_state_utils.py:70
  - backend/app/api/v1/endpoints/unified_discovery/health_handlers.py:97
  - backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:101, 105
  - backend/app/services/discovery/phase_transition_service.py:106
  - backend/app/services/discovery/field_mapping_helpers.py:36
  - backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py:338
  - backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:57, 218, 231, 257
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:89
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:45, 155
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:47, 63
  - backend/app/services/discovery/flow_status/data_helpers.py:137
  - backend/app/services/crewai_flows/flow_state_bridge.py:203
  - backend/app/models/discovery_flow.py:59, 150, 171, 192, 209, 265
  - backend/app/core/auto_seed_demo_data.py:98, 111

- Replace `asset_inventory_completed` → `inventory_completed` at:
  - backend/app/api/v1/endpoints/flow_processing.py:338, 341, 451
  - backend/app/services/crewai_flows/flow_state_utils.py:72
  - backend/app/api/v1/endpoints/unified_discovery/health_handlers.py:99
  - backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:111, 114
  - backend/app/api/v1/endpoints/unified_discovery/asset_handlers.py:178, 185, 237
  - backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:59, 222, 233, 259
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:92
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:47, 157
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:49
  - backend/app/services/flow_orchestration/smart_discovery_service.py:292, 293
  - backend/app/services/mfo_sync_agent.py:222
  - backend/app/services/crewai_flows/flow_state_bridge.py:207
  - backend/app/models/discovery_flow.py:63, 152, 173, 194, 211, 267
  - backend/app/core/auto_seed_demo_data.py:100, 113

- Replace `dependency_analysis_completed` → `dependencies_completed` at:
  - backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_executors.py:386, 390, 394
  - backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:116, 118
  - backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:60, 224, 234, 260
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:93
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:48, 158
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:50
  - backend/app/services/crewai_flows/flow_state_bridge.py:209
  - backend/app/models/discovery_flow.py:66, 153, 174, 195, 212, 268
  - backend/app/core/auto_seed_demo_data.py:101, 114

- Replace `tech_debt_assessment_completed` → `tech_debt_completed` at:
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:94
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:49, 159
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:51
  - backend/app/services/crewai_flows/flow_state_bridge.py:211
  - backend/app/models/discovery_flow.py:69, 154, 175, 196, 213, 269
  - backend/app/core/auto_seed_demo_data.py:102, 115

### Boolean comparison fixes (replace `is True` → `== True` where applicable)

- backend/app/repositories/discovery_flow_repository/queries/flow_queries.py:143–148
- backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py:47–53, 58, 99
- backend/app/repositories/discovery_flow_repository/queries/analytics_queries.py:84
- Additional non-discovery occurrences exist (RBAC, admin, etc.); out of scope for this consolidation unless requested.

2) DiscoveryFlow model method updates (after attribute rename)

- Ensure `calculate_progress`, `get_current_phase`, `get_next_phase`, `is_complete`, and `to_dict` reference legacy names consistently.

3) AssessmentFlow model

- Change `progress` to Integer and ensure any API serializers/tests expect 0–100 integers.

4) CrewAIFlowStateExtensions model

- Add the 4 fields; no further code changes required unless explicitly referenced later.

---

## Validation checklist

- Schema
  - `\d migration.discovery_flows` shows only legacy phase flags; duplicates removed.
  - `\d migration.crewai_flow_state_extensions` contains the 4 added fields.
  - `\d migration.assessment_flows` still shows `progress integer`.
  - FK: `discovery_flows.master_flow_id` → `crewai_flow_state_extensions.flow_id` exists and valid.

- Data
  - Legacy flags correctly reflect any prior values (OR of old+new duplicates).
  - `master_flow_id` populated for all DiscoveryFlow rows that have matching CFSE.

- Runtime
  - All unit/integration tests in `tests/backend/**` pass.
  - Critical flows (discovery start/advance, summaries) execute without 500s.
  - No occurrences of banned `is True` remain in Discovery-related code paths.

---

## Risks and mitigations

- FK correction: If any `master_flow_id` held a CFSE.id, backfill step must convert it to CFSE.flow_id before recreating the FK.
- Phase flag consolidation: Ensure no code writes to the removed columns; perform code refactor first or in the same PR before applying DB drops in production.
- AssessmentFlow progress: Verify any clients expecting float progress; adjust to integer display.

---

## Rollback plan

- Migration 068 downgrade: Drop FK to `flow_id`; optionally reintroduce FK to `id` (not recommended). Safer: leave no FK on downgrade.
- Migration 069 downgrade: Recreate duplicate columns and best-effort copy from legacy flags, keep legacy.
- Model changes are reversible with a local branch if needed; no destructive data ops aside from column drops covered by downgrades.

---

## Implementation notes (ordering)

1) Submit PR with model edits + code refactors (no DB drops yet). Ensure tests pass.
2) Add migration 068 (FK correction); run locally; validate.
3) Add migration 069 (phase flag consolidation + column drops); validate.
4) Deploy migrations with standard backup procedures.

---

## File changes summary (targets)

- Models
  - `backend/app/models/discovery_flow.py`
  - `backend/app/models/crewai_flow_state_extensions.py`
  - `backend/app/models/assessment_flow/core_models.py`

- Repositories/Services (sample, run grep to exhaustively update)
  - `backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py`
  - `backend/app/repositories/discovery_flow_repository/queries/analytics_queries.py`
  - `backend/app/repositories/discovery_flow_repository/queries/flow_queries.py`
  - `backend/app/services/discovery_flow_service/managers/summary_manager.py`
  - `backend/app/services/discovery_flow_service/**`
  - `backend/app/services/crewai_flows/**`

- Alembic (new)
  - `backend/alembic/versions/068_correct_discovery_master_fk.py`
  - `backend/alembic/versions/069_consolidate_discovery_phase_flags.py`

---

## Example code references (for context)

DiscoveryFlow model currently uses new names; we will rename to legacy equivalents and update methods accordingly:

```54:71:backend/app/models/discovery_flow.py
    # Phase completion tracking - HYBRID APPROACH
    # Boolean flags (keep for backward compatibility)
    data_import_completed = Column(Boolean, nullable=False, default=False)
    field_mapping_completed = Column(Boolean, nullable=False, default=False)  # was attribute_mapping_completed
    data_cleansing_completed = Column(Boolean, nullable=False, default=False)
    asset_inventory_completed = Column(Boolean, nullable=False, default=False)  # was inventory_completed
    dependency_analysis_completed = Column(Boolean, nullable=False, default=False)  # was dependencies_completed
    tech_debt_assessment_completed = Column(Boolean, nullable=False, default=False)  # was tech_debt_completed
```

Boolean comparison bug to fix (`is True` → `== True`):

```46:53:backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py
        return ~and_(
            DiscoveryFlow.data_import_completed is True,
            DiscoveryFlow.attribute_mapping_completed is True,
            DiscoveryFlow.data_cleansing_completed is True,
            DiscoveryFlow.inventory_completed is True,
            DiscoveryFlow.dependencies_completed is True,
            DiscoveryFlow.tech_debt_completed is True,
        )
```

FK mismatch to correct (migration created FK to `id`; model expects `flow_id`):

```72:83:backend/alembic/versions/066_add_master_flow_id_to_discovery_flows.py
        op.create_foreign_key(
            "fk_discovery_flows_master_flow",
            "discovery_flows",
            "crewai_flow_state_extensions",
            ["master_flow_id"],
            ["id"],  # should reference flow_id instead
            source_schema="migration",
            referent_schema="migration",
            ondelete="CASCADE",
        )
```

---

## Success criteria

- No duplicate DiscoveryFlow phase columns in DB; canonical legacy names only.
- Correct FK path (`master_flow_id` → CFSE.flow_id) with valid references and index.
- AssessmentFlow model matches DB types; tests pass.
- No `is True` boolean comparisons in ORM queries for Discovery domain.

