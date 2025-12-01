# Serena Memory Consolidation Plan v2.0

**Created**: 2025-11-30
**Revised**: 2025-11-30 (based on docs-curator review)
**Status**: READY FOR PILOT EXECUTION

## Executive Summary

| Metric | Current | Target | Reduction |
|--------|---------|--------|-----------|
| Total Memories | **336** | ~50 | 85% |
| Naming Convention | Mixed | Underscores only | Standardized |
| Structure | Ad-hoc | Templated | Consistent |

---

## Verified Memory Counts by Category

| Category | Actual Count | Action |
|----------|-------------|--------|
| Collection Flow | 35 | Consolidate → `collection_flow_patterns_master` |
| Qodo/PR Review | 27 | Consolidate → `pr_review_patterns_master` |
| Questionnaire | 18 | Consolidate → `questionnaire_patterns_master` |
| Discovery Flow | 16 | Consolidate → `discovery_flow_patterns_master` |
| Playwright/E2E | 16 | Consolidate → `e2e_testing_patterns_master` |
| Database/Alembic | 16 | Consolidate → `database_patterns_master` |
| Modularization | 16 | Consolidate → `modularization_patterns_master` |
| Docker/Deploy | 15 | Consolidate → `docker_deployment_patterns_master` |
| Assessment Flow | 14 | Consolidate → `assessment_flow_patterns_master` |
| Multi-Agent | 12 | Consolidate → `multi_agent_orchestration_master` |
| Security | 12 | Consolidate → `security_patterns_master` |
| LLM/JSON | 11 | Consolidate → `llm_json_patterns_master` |
| Pre-commit/Lint | 5 | Consolidate → `precommit_patterns_master` |
| **Critical (Keep)** | ~20 | KEEP AS-IS |
| **Uncategorized** | ~100 | Review individually |

---

## Naming Convention: UNDERSCORES ONLY

**Standard Format**: `{component}_{type}_master`

| Old (Mixed) | New (Standardized) |
|-------------|-------------------|
| `collection-flow-patterns-master` | `collection_flow_patterns_master` |
| `e2e-testing-patterns-master` | `e2e_testing_patterns_master` |
| `pr-review-patterns-master` | `pr_review_patterns_master` |

**Rationale**: Matches existing critical memories (`mfo_two_table_flow_id_pattern_critical`, `api_request_patterns_422_errors`)

---

## Phase 1: Pilot Consolidation (Collection Flow)

Execute ONE category first to validate approach.

### 1.1 Files to Consolidate

```bash
# Verified list (35 files):
collection_assessment_transition_fixes.md
collection_flow_alternate_entry_fixes_2025_27.md
collection_flow_architecture_issues_2025_10.md
collection_flow_child_service_migration_pattern_2025_10.md
collection_flow_comprehensive_fixes_2025_09_30.md
collection_flow_diagnostic_fixes_2025_09.md
collection_flow_error_handling_cancelled_flows_2025_10.md
collection_flow_fixes_2025_09.md
collection_flow_phase_status_fixes_2025_10.md
collection_flow_qodo_fixes_2025_10_01.md
collection_flow_resume_errors_fix_2025_23.md
collection_flow_status_filter_exclusion_pattern_2025_11.md
collection_gap_analysis_comprehensive_implementation_2025_24.md
collection_gap_analysis_lean_refactor_2025_10.md
collection_gaps_phase2_implementation.md
collection_gaps_qodo_bot_fixes_2025_21.md
collection_questionnaire_empty_sections_fix_2025_30.md
collection_questionnaire_generation_fix_complete_2025_30.md
collection_questionnaire_generation_fix.md
collection_questionnaire_id_fixes_2025_29.md
collection-assessment-transition-fk-fix.md
collection-flow-id-resolver-fix.md
collection-flow-mfo-registration-fix.md
collection-flow-qa-bug-fix-workflow-682-692.md
collection-flow-questionnaire-lifecycle-state-machine-2025-11.md
# Plus ~10 more with partial matches
```

### 1.2 Consolidation Process

1. **Read all source memories**
2. **Extract unique insights** (deduplicate)
3. **Organize by sub-topic** using template
4. **Create `collection_flow_patterns_master.md`**
5. **Archive source files** to `.serena/archive/collection/`
6. **Update references** in CLAUDE.md and agent_config.json
7. **Validate** with acceptance criteria

### 1.3 Pilot Success Criteria

- [ ] Single master file < 500 lines
- [ ] All unique patterns preserved
- [ ] No broken references in CLAUDE.md
- [ ] Agent can find collection patterns via search
- [ ] Chronological ordering preserved for bug fixes

---

## Phase 2: Full Consolidation (After Pilot Success)

Execute remaining categories using validated approach.

### 2.1 Category Priority Order

1. **Qodo/PR Review** (27 files) - High overlap
2. **Questionnaire** (18 files) - Related to Collection
3. **Discovery Flow** (16 files) - Similar to Collection
4. **Playwright/E2E** (16 files) - Testing patterns
5. **Database/Alembic** (16 files) - Technical patterns
6. **Modularization** (16 files) - Code patterns
7. **Docker/Deploy** (15 files) - DevOps patterns
8. **Assessment Flow** (14 files) - Flow patterns
9. **Multi-Agent** (12 files) - Orchestration
10. **Security** (12 files) - Critical patterns
11. **LLM/JSON** (11 files) - Parsing patterns
12. **Pre-commit** (5 files) - Quick consolidation

### 2.2 Per-Category Checklist

```markdown
## Category: {name}

### Pre-Consolidation
- [ ] List all files: `ls -1 | grep -i "{keyword}"`
- [ ] Verify count matches plan
- [ ] Identify critical files to preserve references

### Consolidation
- [ ] Create master file using template
- [ ] Extract unique patterns from each source
- [ ] De-duplicate overlapping content
- [ ] Add chronological references for bug fixes
- [ ] Add "See Also" cross-references

### Post-Consolidation
- [ ] Move sources to archive: `mkdir -p archive/{category} && mv {files} archive/{category}/`
- [ ] Update CLAUDE.md if any sources referenced
- [ ] Update agent_config.json keywords
- [ ] Run validation script

### Validation
- [ ] Master file exists and is well-structured
- [ ] No broken grep references
- [ ] Agent search returns master file
```

---

## Phase 3: Keep As-Is (Critical Memories)

These memories are actively referenced and MUST NOT be consolidated:

| Memory | Reason |
|--------|--------|
| `mfo_two_table_flow_id_pattern_critical` | Referenced in CLAUDE.md, critical pattern |
| `architectural_patterns` | Core reference document |
| `api_request_patterns_422_errors` | Common bug pattern, CLAUDE.md |
| `common_bug_fixes_and_solutions` | Quick reference |
| `project_overview` | Project context |
| `agent-serena-memory-integration-pattern` | This integration |
| `issue-triage-coordinator-agent-investigation-protocol` | Agent config |
| `adr024_crewai_memory_disabled_2025_10_02` | ADR reference |
| `anti_hallucination_system_implementation` | Agent behavior |
| `gap-analyzer-vs-intelligent-gap-scanner-architecture-2025-11` | Recent architecture |
| `canonical-application-architecture-critical-findings` | Critical architecture |
| `bug_investigation_cannot_reproduce_workflow_2025_10` | Investigation workflow |
| `verification_fields_pattern_data_quality_2025_11` | Data quality |
| `automated_bug_fix_workflow` | Workflow reference |
| `automated_bug_fix_workflow_multi_agent` | Workflow reference |

---

## Phase 4: Archive Strategy

### 4.1 Archive Criteria (ALL must be true)

1. **Superseded**: Content fully covered in consolidated master file
2. **Not Critical**: NOT in Phase 3 "Keep As-Is" list
3. **No Active References**: Zero matches in:
   - CLAUDE.md
   - agent_config.json
   - /docs/adr/*.md

### 4.2 Archive Structure

```
.serena/
├── memories/           # Active memories (~50 after consolidation)
│   ├── collection_flow_patterns_master.md
│   ├── discovery_flow_patterns_master.md
│   └── ... (consolidated + critical)
├── archive/            # Archived memories (~286)
│   ├── collection/     # Original collection flow files
│   ├── discovery/      # Original discovery flow files
│   ├── qodo/           # Original qodo/pr review files
│   └── ...
├── MEMORY_INDEX.md     # Index of all active memories
└── ARCHIVE_INDEX.md    # Index of archived memories with dates
```

### 4.3 Archive Verification Script

```bash
#!/bin/bash
# verify_archive.sh

echo "=== Archive Verification ==="

# Check no broken references
for mem in $(ls .serena/archive/*/*.md 2>/dev/null | xargs -n1 basename | sed 's/.md//'); do
    if grep -q "$mem" CLAUDE.md .claude/agent_config.json 2>/dev/null; then
        echo "WARNING: $mem still referenced!"
    fi
done

# Count verification
active=$(ls -1 .serena/memories/*.md | wc -l)
archived=$(find .serena/archive -name "*.md" | wc -l)
echo "Active: $active, Archived: $archived, Total: $((active + archived))"
```

---

## Phase 5: Cross-Reference with /docs

### 5.1 Identify Overlaps

| Serena Memory | /docs Equivalent | Strategy |
|---------------|------------------|----------|
| `api_request_patterns_422_errors` | `/docs/guidelines/API_REQUEST_PATTERNS.md` | Serena = summary, docs = detail |
| `architectural_patterns` | `/docs/adr/*.md` | Serena = quick ref, ADRs = decisions |
| `security_patterns_master` | `/docs/security/*.md` | Merge if exists, create if not |

### 5.2 Cross-Reference Format

Add to each master memory:
```markdown
## Related Documentation
- ADR-006: Master Flow Orchestrator → `/docs/adr/006-master-flow-orchestrator.md`
- Guidelines: API Patterns → `/docs/guidelines/API_REQUEST_PATTERNS.md`
```

Add to relevant /docs files:
```markdown
## Quick Reference
For agent-friendly summary, see: `.serena/memories/{memory_name}.md`
```

---

## Validation Strategy

### Pre-Consolidation Snapshot

```bash
# Run BEFORE any consolidation
ls -1 .serena/memories/ > .serena/PRE_CONSOLIDATION_INDEX.txt
echo "Total: $(wc -l < .serena/PRE_CONSOLIDATION_INDEX.txt) memories"
date >> .serena/PRE_CONSOLIDATION_INDEX.txt
```

### Post-Phase Validation

```bash
#!/bin/bash
# validate_consolidation.sh

echo "=== Consolidation Validation ==="

# 1. File count
echo "Active memories: $(ls -1 .serena/memories/*.md | wc -l)"
echo "Archived memories: $(find .serena/archive -name '*.md' | wc -l)"

# 2. No broken CLAUDE.md references
echo "Checking CLAUDE.md references..."
grep -oE '\`[a-z_]+\`' CLAUDE.md | tr -d '`' | while read mem; do
    if [[ -f ".serena/memories/${mem}.md" ]]; then
        echo "  ✓ $mem"
    else
        echo "  ✗ BROKEN: $mem"
    fi
done

# 3. JSON validity
echo "Validating agent_config.json..."
python3 -c "import json; json.load(open('.claude/agent_config.json'))" && echo "  ✓ Valid JSON"

# 4. Master files exist
echo "Checking master files..."
for master in collection_flow discovery_flow assessment_flow questionnaire e2e_testing database security; do
    if [[ -f ".serena/memories/${master}_patterns_master.md" ]]; then
        echo "  ✓ ${master}_patterns_master.md"
    else
        echo "  - ${master}_patterns_master.md (not yet created)"
    fi
done
```

### Acceptance Criteria

| Criteria | Target | Validation |
|----------|--------|------------|
| Active memory count | 40-60 | `ls -1 .serena/memories/*.md \| wc -l` |
| No broken refs | 0 | `validate_consolidation.sh` |
| Master files | 13 | One per category |
| Critical preserved | 15+ | Manual check |
| Agent search works | Yes | Test `mcp__serena__list_memories` |

---

## Execution Plan

### Week 1: Pilot
1. **Day 1**: Create pre-consolidation snapshot
2. **Day 2**: Execute Collection Flow pilot
3. **Day 3**: Validate and adjust approach
4. **Day 4-5**: Fix any issues, get approval

### Week 2: Full Consolidation
1. **Day 1-2**: Categories 1-4 (Qodo, Questionnaire, Discovery, Playwright)
2. **Day 3-4**: Categories 5-8 (Database, Modularization, Docker, Assessment)
3. **Day 5**: Categories 9-12 (Multi-Agent, Security, LLM, Pre-commit)

### Week 3: Cleanup
1. **Day 1**: Cross-reference with /docs
2. **Day 2**: Update all references
3. **Day 3**: Final validation
4. **Day 4-5**: Documentation and handoff

---

## Rollback Plan

If consolidation causes issues:

```bash
# Restore from archive
mv .serena/archive/collection/*.md .serena/memories/
rm .serena/memories/collection_flow_patterns_master.md

# Restore from git (if committed)
git checkout HEAD~1 -- .serena/memories/
```

---

## Approval Checklist

Before execution, confirm:
- [ ] Naming convention approved (underscores)
- [ ] Template structure approved
- [ ] Archive strategy approved
- [ ] Pilot category approved (Collection Flow)
- [ ] Timeline approved

**To approve**: Reply "Execute pilot" to begin Phase 1 (Collection Flow only).
