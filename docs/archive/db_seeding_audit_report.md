# Database Table Population & Seeding Audit  
_Date: 2025-06-11_

---

## 1. Table Population Status (schema = `migration`)

| Table | Row Count | Status |
|-------|-----------|--------|
| assets | 6 | ✅ Populated |
| asset_embeddings | 6 | ✅ Populated |
| asset_tags | 1 | ✅ Populated |
| client_accounts | 1 | ✅ Populated |
| engagements | 1 | ✅ Populated |
| migration_waves | 3 | ✅ Populated |
| tags | 21 | ✅ Populated |
| users | 3 | ✅ Populated |
| user_account_associations | 2 | ✅ Populated |
| user_roles | 6 | ✅ Populated |
| alembic_version | 1 | ✅ System meta |
| **All remaining 33 tables** | 0 | ❌ _Empty_ |

<details>
<summary>Empty table list</summary>

```
access_audit_log
asset_dependencies
assessments
client_access
cmdb_sixr_analyses
custom_target_fields
data_imports
data_import_sessions
data_quality_issues
engagement_access
enhanced_access_audit_log
enhanced_user_profiles
feedback
feedback_summaries
import_field_mappings
import_processing_steps
llm_model_pricing
llm_usage_logs
llm_usage_summary
mapping_learning_patterns
migration_logs
migrations
raw_import_records
role_permissions
sixr_analyses
sixr_iterations
sixr_parameters
sixr_question_responses
sixr_questions
sixr_recommendations
soft_deleted_items
workflow_progress
wave_plans
```
</details>

---

## 2. Existing Seeding Mechanisms & Coverage

| Script / Migration | Location | Tables Populated |
|--------------------|----------|------------------|
| `init_db.py` | `backend/app/scripts/` | client_accounts, users, user_account_associations, engagements, tags, assets, migration_waves, asset_embeddings, asset_tags |
| `508e8589c9d0_add_missing_seed_data_for_roles_and_.py` | `backend/alembic/versions` | user_roles, user_profiles |
| `e3c32f125929_add_seed_data_for_user_roles.py` | `backend/alembic/versions` | user_roles (template roles), users (system user) |

**Coverage:** 11/44 tables currently receive seed data (~25%).

---

## 3. Gap Analysis & Recommended Seed Scripts

The following tables have no seed data and are prime candidates for scripted population to support local development, automated testing, and demo environments.

| Table | Recommendation |
|-------|---------------|
| sixr_questions / sixr_parameters | Create `seed_sixr_questions.py` to insert master question catalogue & scoring parameters. |
| sixr_analyses / sixr_iterations / sixr_question_responses / sixr_recommendations | Extend above script or create `seed_sixr_analysis_demo.py` to generate a sample analysis with one iteration and mock responses. |
| wave_plans | `seed_wave_plans.py` – generate a baseline migration wave plan linked to existing engagement. |
| migration_logs / workflow_progress | `seed_migration_workflow.py` – insert example log entries & progress checkpoints for demo waves. |
| data_quality_issues | `seed_data_quality_issues.py` – add sample issues tied to assets for cleansing workflow validation. |
| client_access / engagement_access | `seed_access_matrices.py` – grant demo users/viewers appropriate scoped access. |
| role_permissions | Include default permission matrix – either merge into `init_db.py` or create dedicated Alembic revision. |
| import_field_mappings / import_processing_steps / import_* / mapping_learning_patterns | `seed_import_pipeline.py` – mock an import session with steps & learned mappings. |
| llm_model_pricing / llm_usage_logs / llm_usage_summary | `seed_llm_usage.py` – add baseline cost/usage rows for analytics. |
| feedback / feedback_summaries | `seed_feedback.py` – example feedback linked to assets & six-R analysis. |
| assessments | `seed_assessments.py` – create placeholder assessments for assets. |
| asset_dependencies | Enhance `init_db.py` to add cross-asset dependency relationships. |
| soft_deleted_items | Optional: insert a sample soft-deleted asset to exercise restoration workflows. |
| enhanced_*_audit_log & access_audit_log | `seed_audit_logs.py` – back-fill a few audit events. |

**Implementation Guidance**
1. Follow existing `init_db.py` pattern (async SQLAlchemy + session management) or create small Alembic "data-only" revisions for immutable reference data (e.g., master question list).
2. Use the **ContextAwareRepository** pattern to ensure `client_account_id` & `engagement_id` are included for multi-tenant isolation.
3. Mark all mock rows with `is_mock = TRUE` to allow easy purge (`--force`) similar to current logic.
4. Organise seed scripts under `backend/app/scripts/` with a clear naming convention (`seed_<domain>.py`).
5. Update the README & `DEMO_DATA_SETUP.md` to document execution (`docker exec migration_backend python app/scripts/seed_sixr_questions.py`).

---

## 4. Next Steps
1. **Prioritise reference data** (`sixr_questions`, `role_permissions`) via Alembic migrations so they are guaranteed in every environment.
2. Build remaining domain-specific seeders to achieve 100% table coverage.
3. Add CI task to run all seeders in test pipeline ensuring no table remains empty.

---

## 5. New Seed Scripts Implemented (Jun 2025)

| Script | Location | Tables Affected | Key Notes |
|--------|----------|-----------------|-----------|
| `seed_wave_plans.py` | `backend/app/scripts/` | `wave_plans` | Generates three baseline migration waves (`MOCK:` name prefix). Requires at least **one** row in `migrations` to link foreign-key. Use `--force` to purge `MOCK:` rows. |
| `seed_data_quality_issues.py` | `backend/app/scripts/` | `data_quality_issues`, `data_imports`, `raw_import_records` | Creates supporting mock `data_import` + `raw_import_record` rows if missing, then three linked quality-issue rows. Uses `reasoning` field `MOCK:` prefix for cleanup. |
| `seed_assessments.py` | `backend/app/scripts/` | `assessments` | Inserts migration-level and asset-level assessments (6R, risk & cost) with realistic scores. Needs at least one `migration` and a handful of `assets`. Cleans up via `title LIKE 'MOCK:%'`. |

---

## 6. Running Seeder Orchestration on a Fresh Docker Build

```bash
# 1. Build & start all containers
docker-compose up -d --build

# 2. Run core mock dataset (clients, users, assets, etc.)
docker exec migration_backend python app/scripts/init_db.py --force

# 3. OPTIONAL: create a placeholder migration if none exists yet
docker exec migration_backend psql -U $POSTGRES_USER -d migration_db -c "INSERT INTO migrations (id, name, status, created_at) VALUES (gen_random_uuid(), 'MOCK: Initial Migration', 'planning', NOW());"

# 4. Seed wave plans
docker exec migration_backend python app/scripts/seed_wave_plans.py --force

# 5. Seed assessments (relies on assets + migrations)
docker exec migration_backend python app/scripts/seed_assessments.py --force

# 6. Seed data-quality issues (relies on data_imports)
docker exec migration_backend python app/scripts/seed_data_quality_issues.py --force

# Repeat other seeders similarly as they are implemented
```

**Execution Order Rationale**
1. `init_db.py` lays down all core tenant context and sample assets.
2. `migrations` table must have at least one row before wave-plan & assessment seeders—use the quick SQL insert shown or implement a `seed_migrations.py` helper.
3. `wave_plans` and `assessments` depend on that migration as a foreign-key.
4. Data-quality seeder auto-creates its own prerequisite import data, so it can run any time after `init_db.py`.

Use the `--force` flag on any seeder to safely re-run and purge previously inserted `MOCK:` rows without affecting real data.

---

_This audit was generated automatically via database inspection of the running `migration_postgres` container and codebase review of existing seed scripts._
