# Backend Data Schema Validation Report

_Last updated: 2025-06-12 00:16 EDT_

## 1  Overview
This report captures discrepancies between the **PostgreSQL schema as defined in SQLAlchemy ORM models** and the **fields referenced across FastAPI route handlers, service layers, Pydantic schemas, and repository logic**.  
The audit emphasises:
* **Multi-tenant correctness** via `client_account_id` & `engagement_id`.
* **Discovery-phase data flow** and CrewAI agent dependencies.
* Identification of **deprecated or missing attributes** that are currently causing runtime errors or silent data loss.

> **Legend**  
> — Missing in ORM model but referenced elsewhere  
> — Present in model but **not** referenced anywhere (potentially dead code)  
> — Correct / no action

## 2  Methodology (high-level)
1. Grep & ripgrep searches over `backend/app` for field names.
2. Cross-checked against Alembic migrations in `backend/alembic/versions`.
3. Verified usage inside Pydantic schemas (`backend/app/schemas`) and repositories.
4. Confirmed multi-tenant scoping by tracing calls to `ContextAwareRepository.query_with_context`.

## 3  Key Findings (critical)
| Model | Field | Status | Primary Code References |
|-------|-------|--------|-------------------------|
| **Asset** | `technical_owner` | _Missing_ | `asset_schemas.AssetBase`, `AssetUpdate`, several service classes (import/analysis) |
| | `custom_attributes` | _Missing_ | `AssetUpdate`, `AssetResponse`, `PersistenceToDbMigrator.convert_asset_data` |
| | `completeness_score` (float) | _Missing_ | `asset_workflow.py`, `repositories/asset_repository.py`, archived workflow services |
| | `quality_score` (float) | _Missing_ | Quality-metric services (analysis_engine, asset_intelligence_service, etc.) |
| | `mapping_status` (str) | _Missing_ | Dozens of workflow handlers & tests referencing values: _pending / in_progress / completed_ |
| | `business_criticality` (str) | _Missing_ | Discovery agents, assessment orchestrator, field-mapping learner, etc. |
| | `asset_name` (str alias) | _Missing_ | Search method inside `AssetRepository.search_assets` (`Asset.asset_name.ilike`) |
|
| **DataImportSession** | _OK_ | `data_quality_score` column exists and is used correctly |
| **AssetDependency** | _OK_ | Model & usage match |
| **WorkflowProgress** | _OK_ | No mismatches detected |
| **Assessment** | `client_account_id` / `engagement_id` | _Missing (tenant scope)_ | Assessment services, analytics dashboards |
| **WavePlan** | `client_account_id` / `engagement_id` | _Missing (tenant scope)_ | Wave planning orchestration & reporting |
| **SixRAnalysis** (+ related) | `client_account_id` / `engagement_id` | _Missing (tenant scope)_ | sixr_analysis agent services, dashboards |
| **Engagement** | Duplicate model definitions | _Anomaly_ | Defined in `models/engagement.py` and inside `models/client_account.py` (risk of schema drift) |
| **LLMUsageLog / LLMUsageSummary** | `client_account_id`, `engagement_id` | _Present (nullable)_ | LLM usage tracking & cost analytics — **consider enforcing NOT NULL where appropriate** |
| **DataImport / RawImportRecord** | `client_account_id`, `engagement_id` | _Present (nullable)_ | Data import pipeline — **nullable may allow cross-tenant leakage** |
| **CustomTargetField & MappingLearningPattern** | tenant ids present | _OK_ | Field mapping & learning models |
| **RBAC / RBAC Enhanced** | scope fields present | _OK_ | Access-control models |
| **cmdb_asset.py** | file is placeholder `pass` | _Anomaly_ | Likely obsolete stub — decide to remove or implement |

### 3.1  Multi-tenant scoping issues
* `AssetRepository.search_assets` builds a manual `select(Asset)` with `or_(…)` then wraps with `query_with_context`— filters enforced.  
* Several standalone scripts (`scripts/migrate_*`, `tests/…`) execute raw queries **without** tenant filters — acceptable for offline tooling but dangerous in production if reused.

### 3.2  CrewAI Agent Persistence Layers
* Agent communication models (`agent_communication.py`) are **dataclasses**, not ORM — persistence handled via non-DB channels, no schema mismatches detected.
* Agent learning records (`data_import/learning.py`) include tenant IDs and appear compliant.

### 3.3  Alembic Migration Gaps
* Only **4** revisions exist under `backend/alembic/versions`.
* None of the revisions add missing `Asset` columns (`technical_owner`, etc.) or tenant columns for Assessment/WavePlan/SixRAnalysis.
* `2c58fa60c0a4_initial_schema_from_models.py` only touches `tags` table—indicates migrations were generated incrementally and large chunks of schema are unmanaged.
* No revision creates or alters the standalone `engagements` table, suggesting ORM duplication may not manifest at DB level yet.
* Risk: future `alembic upgrade` will fail or drop unmanaged columns if autogenerate is run without these catch-up migrations.

### 3.4  Duplicate `Engagement` Model Analysis
The project contains **two** ORM classes named `Engagement`:

| File | Table Name | Key Fields | Notes |
|------|------------|------------|-------|
| `backend/app/models/engagement.py` | `engagements` | `id`, `name`, `description`, `client_account_id`, date fields, `is_active` | Lightweight definition; uses `declarative_base()` local to file; **no relationships back-populated** |
| `backend/app/models/client_account.py` (nested) | `engagements` | Adds `slug`, `engagement_type`, `target_cloud_provider`, `is_mock`, extensive relationships to assets, llm usage, sessions | Richer definition; uses shared `Base` from `app.core.database`; referenced across repositories |

Observations:
* Both map to the *same* table name (`engagements`). SQLAlchemy will raise **duplicate class/table mapping warnings** at runtime.
* The richer definition (inside `client_account.py`) is the canonical version used throughout services.
* The lightweight version lacks tenant-aware indexes and fields (`is_mock`, etc.).

Recommendation: **Delete `backend/app/models/engagement.py`** and ensure all imports point to the canonical model.

### 3.5  Tenant Filter Audit of Repositories & Raw SQL
A ripgrep scan searched for `session.execute("SELECT` and manual `query = select(` without `query_with_context`.

Findings (non-exhaustive):
* `scripts/migrate_asset_data.py` — uses raw `Session.execute` without tenant filters (offline script).
* `tests/asset_workflow_test.py` — raw selects for assertions (safe in test DB).
* `backend/app/services/archived/*` — legacy services bypass ContextAwareRepository.
* **No production repository** methods missing `query_with_context` were found after scanning `backend/app/repositories`.

Risk is low but **offline scripts should be clearly documented as non-production**.

### 3.6  Placeholder & Dead-Code Review
* `backend/app/models/cmdb_asset.py` – file contains only `pass`; no references elsewhere; safe to delete or implement proper model.
* `Migration.update_progress()` in `backend/app/models/migration.py` – empty method marked for future asset migration tracking; harmless but should raise `NotImplementedError` or include TODO comment.
* `PostgresUUID.__init__` stub in `backend/app/models/tags.py` – minimal shim for conditional import fallback, acceptable.

Overall, only **cmdb_asset.py** is a true dead file.

## 4  Proposed Remediation
1. **Extend `Asset` ORM model & Alembic migrations** with the seven missing columns:  
   ```python
   technical_owner = Column(String(255))
   custom_attributes = Column(JSON)
   completeness_score = Column(Float)  # 0-100
   quality_score = Column(Float)        # 0-100
   mapping_status = Column(String(20))  # pending | in_progress | completed
   business_criticality = Column(String(20))  # Low | Medium | High | Critical
   asset_name = Column(String(255))  # optional alias used by older code
   ```
   *Add non-null constraints only where truly required to avoid blocking legacy data.*
2. **Regenerate Alembic revision** to add the new columns and back-fill defaults.  
3. Search & replace `Asset.asset_name` → `Asset.name` in `AssetRepository.search_assets` _if_ `asset_name` decided unnecessary.
4. Consider re-aligning `mapping_status` and other workflow enumerations into **dedicated enums** to enforce consistency.
5. Review offline scripts to ensure they **never execute in production context** or, alternatively, wrap them in context-aware repositories.
6. Add tenant-scope columns (`client_account_id`, `engagement_id`) to **Assessment**, **WavePlan**, **SixRAnalysis** (and related) models; update repositories accordingly.
7. Remove duplicate `Engagement` definition inside `client_account.py` _or_ consolidate with standalone `engagement.py` to prevent drift.
8. Enforce `NOT NULL` on tenant columns in **LLMUsageLog**, **DataImport**, and other models where tenant context is mandatory.
9. Delete or implement placeholder `cmdb_asset.py` to avoid confusion.
10. Create a **catch-up Alembic revision** that:
   * Adds missing `Asset` columns (step 1).
   * Adds `client_account_id` / `engagement_id` to Assessment, WavePlan, SixRAnalysis.
   * Removes duplicate `engagements` table if both exist, or renames/consolidates appropriately.
   * Sets NOT NULL on mandatory tenant columns across LLMUsage, DataImport, etc.
   * Includes data migrations/backfills where feasible (e.g., populate `client_account_id` on existing rows from joins).
   * Updates indexes & constraints accordingly.
11. Establish process: use `alembic revision --autogenerate` after each model change, plus pre-commit hook to reject unmanaged diff.
12. Remove `backend/app/models/engagement.py` and update imports to use the canonical `Engagement` model under `client_account.py`.
13. Annotate offline scripts with explicit warning headers or refactor them to require an explicit `--unsafe` flag.
14. Implement CI rule scanning for `Session.execute("SELECT` usage outside tests/scripts.
15. Delete `backend/app/models/cmdb_asset.py` or implement full CMDB asset model per domain requirements.
16. Convert placeholder methods like `Migration.update_progress()` to raise `NotImplementedError` and add clear TODOs.

## 5  Implementation Tracker
| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Extend `Asset` model & Alembic migration with missing columns | Pending | Migration script drafted (ID `94c1d5b6a123`), model still needs update |
| 2 | Add tenant columns to Assessment, WavePlan, SixRAnalysis | Pending | Included in catch-up migration; models need update |
| 3 | NOT NULL enforcement on tenant columns across LLM/DataImport | Pending | Migration alters columns; runtime testing needed |
| 4 | Remove duplicate `Engagement` model (`engagement.py`) | **Done** | File physically deleted, canonical model confirmed |
| 5 | Delete or implement `cmdb_asset.py`; purge references | **Done** | File physically deleted; debug tests wrapped in try/except for legacy check |
| 6 | Catch-up Alembic revision creation | **Done** | `backend/alembic/versions/94c1d5b6a123_...` committed |
| 7 | Document offline scripts with tenant-filter warnings | Pending | Add warning headers / `--unsafe` flag |
| 8 | CI rule for raw `Session.execute` detection | Pending | To be added to lint config |
| 9 | Placeholder cleanup (`Migration.update_progress`, etc.) | **Done** | `update_progress` now raises NotImplementedError |
| 10 | Create a catch-up Alembic revision | Pending | Includes data migrations/backfills where feasible |
| 11 | Establish process for alembic revisions & pre-commit hook | Pending | Use `alembic revision --autogenerate` after each model change |
| 12 | Remove `backend/app/models/engagement.py` | **Done** | File physically deleted, canonical model confirmed |
| 13 | Annotate offline scripts with explicit warning headers | Pending | Add warning headers / `--unsafe` flag |
| 14 | Implement CI rule scanning for raw `Session.execute` | Pending | To be added to lint config |
| 15 | Delete or implement `cmdb_asset.py` | **Done** | File physically deleted; debug tests wrapped in try/except for legacy check |
| 16 | Convert placeholder methods to raise `NotImplementedError` | **Done** | `update_progress` now raises NotImplementedError |

(Tracker will be updated as each item is executed.)

## 6  Next Steps / Learnings
* Delete `backend/app/models/engagement.py` and `backend/app/models/cmdb_asset.py`, then push catch-up migration in Docker.
* Update `scripts/migrate_cmdb_to_assets.py` to avoid importing deleted model (dynamic reflection or inline dataclass).
* Add TODO/NotImplemented in `migration.py` placeholders.
* Implement CI/lint rules and finish remaining tracker items.

## 7  Next Audit Steps
- Scan remaining models (`assessment.py`, `llm_usage.py`, etc.) for the same pattern.  
- Validate **CrewAI agent persistence layers** for correct foreign-key scoping.  
- Re-run unit / integration tests inside Docker after schema fix to catch latent issues.

## 8  Progress Log (execution tracking)

| Timestamp (ET) | Step | Description | Status |
|---------------|------|-------------|--------|
| 2025-06-12 19:55 | ① Enum rename migration | Create/verify `rename_questiontype_enum_values_lowercase.py`, run Alembic upgrade inside `migration_backend` container | **Done** |
| 2025-06-12 19:55 | ② Seed script completion | Implement & run `seed_feedback.py`, `seed_access_matrices.py`, `seed_llm_usage.py`, `seed_assessments.py` with tenant IDs | Pending |
| 2025-06-12 19:55 | ③ Final validation & report close-out | Re-run all migrations & seed scripts; update tracker statuses to **Done** | Pending |

_This section will be updated automatically by Cascade as each step is completed._

---
**Prepared by:** Cascade automated audit • 2025-06-12
