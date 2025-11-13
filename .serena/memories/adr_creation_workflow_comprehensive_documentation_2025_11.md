# ADR Creation Workflow - Comprehensive Documentation Pattern

**Date**: November 7, 2025
**Context**: Created ADR-034 for asset-centric questionnaire deduplication (PR #969)

---

## Workflow Pattern: From PR to ADR

### Step 1: Gather PR Context
```bash
# Fetch PR details including files changed
gh pr view <PR_NUMBER> --json title,body,files

# Get specific file paths from PR
gh pr view <PR_NUMBER> --json files --jq '.files[] | select(.path | contains("<keyword>")) | .path'
```

### Step 2: Read Reference ADRs
Always read 2-3 recent ADRs to understand:
- Current documentation style and tone
- Section structure and depth
- Code example formatting
- How consequences are framed

**Key Files**:
- `docs/adr/README.md` - Index and reading order
- Recent ADRs (028, 030, 032, 033) - Style reference

### Step 3: Validate Code Reality
**CRITICAL**: ADR must reflect actual implementation, not assumed design.

```bash
# Read actual implementation files
Read backend/app/api/v1/endpoints/<module>/<file>.py
Read backend/alembic/versions/<migration>.py
Read backend/app/models/<module>/<model>.py

# Verify code snippets match reality
grep -r "get_existing_questionnaire_for_asset" backend/
```

**Anti-Pattern**: Writing ADR based only on PR description
**Correct Pattern**: Read code → Extract patterns → Document what exists

### Step 4: Structure ADR Content

```markdown
# ADR-XXX: [Title]

## Status
[Accepted|Proposed] (YYYY-MM-DD)

Implemented in: PR #XXX

Related: [Other ADRs]

## Context

### Problem Statement
- Concrete problem with business impact
- Current state before changes
- Why existing approach failed

### Current State Before PR #XXX
```code showing old pattern```

## Decision

**Core Principle**: One-sentence architectural shift

### Architectural Shift
```
❌ OLD: [Describe with diagram]
✅ NEW: [Describe with diagram]
```

### Database Schema Changes
```sql
-- Actual migration SQL
```

### Implementation Details
```python
# Actual code from codebase (verified)
```

## Implementation

### Rollout Strategy
- Phase 1: Non-breaking changes
- Phase 2: Enable feature
- Phase 3: Cleanup

### Files Changed
- Exact file paths with line counts

## Consequences

### Positive
1. Specific benefit with metric
2. Another benefit with evidence

### Negative / Trade-offs
1. Honest drawback
2. Mitigation strategy

## Testing
```bash
# Actual test commands
```

## Future Enhancements
1. Specific enhancement idea
2. Another enhancement

## References
- PR #XXX
- Migration XXX
- Related ADRs
- Serena memories

## Key Patterns Established
### Pattern Name
```code
# Reusable pattern template
```

**When to Use**: Specific use case

## Success Metrics
1. ✅ Measurable outcome
2. ✅ Another metric
```

### Step 5: Update ADR README

**Two updates required**:

1. **Index Table** (top of README):
```markdown
| [ADR-XXX](XXX-title.md) | Title | Accepted | YYYY-MM-DD |
```

2. **Reading Order** (middle of README):
```markdown
XX. **ADR-XXX** - Title - Brief description
```

**Placement**: After related ADRs, before unrelated ones

### Step 6: Commit with Detailed Message

```bash
git add docs/adr/XXX-title.md docs/adr/README.md

git commit -m "$(cat <<'EOF'
docs: Add ADR-XXX for [feature name]

Add comprehensive Architecture Decision Record documenting [change].

Key architectural change:
- [Bullet point]
- [Bullet point]

Database changes (Migration XXX):
- [Change 1]
- [Change 2]

Benefits:
- [Benefit 1 with metric]
- [Benefit 2 with metric]

Updated ADR README with:
- Added ADR-XXX to index table
- Added to reading order after ADR-YYY

Related: PR #XXX, Migration XXX, ADR-YYY

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push origin main
```

## Critical Validation Checklist

Before finalizing ADR:

- [ ] Read actual implementation code (not just PR description)
- [ ] Verify code snippets compile/run
- [ ] Check database migration matches schema description
- [ ] Confirm file paths and line numbers are accurate
- [ ] Test commands are executable
- [ ] SQL examples are idempotent (IF EXISTS checks)
- [ ] Multi-tenant scoping rationale documented
- [ ] Business impact quantified (time/cost savings)
- [ ] Negative consequences honestly stated
- [ ] Future enhancements are actionable
- [ ] README index and reading order updated

## Common Pitfalls

### ❌ Writing ADR from PR description alone
**Problem**: PR description may be incomplete or outdated
**Solution**: Always read implementation code first

### ❌ Overly technical without business context
**Problem**: ADR explains "how" but not "why"
**Solution**: Start with problem statement and business impact

### ❌ Code snippets that don't match reality
**Problem**: Future readers try to copy non-existent code
**Solution**: Copy-paste actual code, verify with grep

### ❌ Ignoring multi-tenant implications
**Problem**: Missing security considerations
**Solution**: Explicitly document tenant scoping decisions

### ❌ Missing rollout strategy
**Problem**: Unclear how to deploy safely
**Solution**: Document phases, feature flags, monitoring

## ADR Quality Metrics

**Length**: 800-1200 lines for major architectural changes
**Code/Text Ratio**: ~30% code examples, 70% explanation
**Sections**: All template sections populated
**Readability**: Diagrams for architectural shifts
**Actionability**: Specific file paths and test commands

## Integration with Serena Memories

**Pattern**: ADR documents architecture, memory documents implementation patterns

**ADR Scope**:
- Why decision was made
- What alternatives were considered
- Long-term consequences

**Memory Scope**:
- How to implement the pattern
- Common errors and fixes
- Reusable code snippets

**Reference Pattern**:
```markdown
## References
- Serena Memory: `pattern_name_2025_11.md`
```

## When to Create ADR vs Update Existing

**Create New ADR**:
- Introduces new architectural pattern
- Changes core system behavior
- Adds new database tables/major schema change
- Replaces existing approach (supersedes ADR)

**Update Existing ADR**:
- Fixes bugs in existing architecture
- Optimizes performance without changing approach
- Adds examples to existing pattern

## Success Story: ADR-034

**Input**: PR #969 with 5 bug fixes and asset-centric deduplication
**Challenge**: Separate core architectural change from bug fixes
**Solution**: Focus ADR on deduplication, mention fixes as "additional"

**Validation Steps**:
1. Read migration 128 SQL → Verified partial unique constraint
2. Read deduplication.py → Verified get-or-create pattern
3. Read commands.py → Verified integration at creation point
4. Read model.py → Verified asset_id FK and nullable collection_flow_id

**Result**: 1,050-line comprehensive ADR reflecting actual implementation

## Files
- ADR: `docs/adr/034-asset-centric-questionnaire-deduplication.md`
- README: `docs/adr/README.md` (lines 41, 105)
- Commit: `1657feb23`
