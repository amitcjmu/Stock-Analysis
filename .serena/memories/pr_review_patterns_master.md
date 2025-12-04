# PR Review & Qodo Bot Patterns Master

**Last Updated**: 2025-12-03
**Version**: 1.1
**Consolidates**: 25+ memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Qodo Bot Credibility**: Anti-pattern warnings are usually correct (e.g., `window.location.reload()`)
> 2. **Multi-Tenant Security**: ALWAYS pass tenant context through background tasks
> 3. **Three-Tier Logging**: DEBUG (dev), INFO/ERROR (prod-safe), Database (user-facing)
> 4. **Atomic Commits**: One commit per Qodo suggestion with clear traceability
> 5. **Verify Before Criticizing**: Search codebase (grep) before flagging patterns as "wrong"

---

## Table of Contents

1. [Overview](#overview)
2. [Qodo Bot Response Patterns](#qodo-bot-response-patterns)
3. [Security Patterns](#security-patterns)
4. [Data Quality Patterns](#data-quality-patterns)
5. [Code Quality Patterns](#code-quality-patterns)
6. [PR Workflow Patterns](#pr-workflow-patterns)
7. [Anti-Patterns](#anti-patterns)
8. [Code Templates](#code-templates)
9. [Troubleshooting](#troubleshooting)
10. [Related Documentation](#related-documentation)
11. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Patterns for handling PR reviews, Qodo Bot feedback, security review integration, and code review best practices. Includes lessons learned from bugs caused by dismissed bot warnings.

### When to Reference
- Responding to Qodo Bot code review comments
- Fixing PR review feedback
- Implementing security suggestions
- Handling multi-tenant context in background tasks
- Creating atomic commits for review fixes

### Key Files in Codebase
- `backend/app/api/v1/endpoints/*/` (most review targets)
- `src/hooks/*/` (frontend review targets)
- `.pre-commit-config.yaml` (pre-commit hooks)

---

## Qodo Bot Response Patterns

### Pattern 1: Qodo Bot Credibility Assessment

**Critical Learning**: When Qodo Bot warns about anti-patterns, it's usually RIGHT.

**Bug #1102 Incident**:
- Qodo warned about `window.location.reload()` anti-pattern
- Previous agent dismissed: "User tested it, works fine"
- Result: Infinite reload loop bug

**Decision Framework**:

| Category | Credibility | Action |
|----------|-------------|--------|
| Security vulnerabilities | Very High | Fix immediately |
| Anti-patterns (reload, N+1, etc.) | High | Fix unless strong justification |
| Architectural suggestions | Medium | Evaluate against project patterns |
| Code style | Low | Follow project conventions |

**Red Flags Bot is Probably Right**:
1. Industry-standard anti-pattern (reload in SPA, SELECT *, plaintext passwords)
2. Bot provides specific alternative, not just "don't do X"
3. "User confirms works" but bot warns about pattern (may hide future bug)

**Source**: Consolidated from `qodo-bot-code-review-credibility-pattern-2025-11`

---

### Pattern 2: Importance Score Prioritization

**Scale Interpretation**:
- **7-10/10**: Critical (security, architecture) → Fix immediately
- **4-6/10**: Important (clarity, redundancy) → Batch if time-limited
- **1-3/10**: Style preferences → Consider project conventions

**Example Response**:
```markdown
## ✅ ALL Review Items Addressed

### Priority 7+/10 ✅
1. **ESLint disable proliferation** (7/10)
   - Removed 11 eslint-disable comments
   - Added setState to dependency arrays

### Priority 4-6/10 ✅
1. **Redundant Array.isArray** (4/10)
   - Removed type guard after type narrowing
```

**Source**: Consolidated from `qodo_bot_code_review_resolution_patterns_2025_10`

---

### Pattern 3: Batched Qodo Bot Fix Workflow (NEW - Dec 2025)

**When to use**: PR has 15+ Qodo suggestions that span multiple files and categories.

**Workflow**:
1. **Batch 1**: Fix critical security and high-importance (7+/10) items first
2. **Commit Batch 1**: Run pre-commit, commit, push
3. **Batch 2**: Fix medium-importance (4-6/10) items
4. **Commit Batch 2**: Run pre-commit, commit, push
5. **Defer to Issue**: Create GitHub enhancement issue for architectural changes requiring separate PRs

**Example (from Issue #1227 - ADR-038 Data Validation)**:
```bash
# Batch 1: 11 high-priority suggestions
git commit -m "fix(data-cleansing): address Qodo Bot security and code quality findings"

# Batch 2: 5 medium-priority suggestions
git commit -m "fix(data-validation): address Qodo Bot medium-priority improvements"

# Deferred: Async profiling, streaming → GitHub Issue #1227
```

**What to Defer**:
- Performance optimizations requiring architectural changes
- Streaming responses requiring frontend/backend coordination
- New service layer abstractions

**Source**: Session learning from ADR-038 intelligent data validation PR (Dec 2025)

---

### Pattern 4: Verify Before Criticizing

**Problem**: Flagging unfamiliar patterns as "wrong" without verification.

**Solution**: Search codebase before criticizing:
```bash
# Before flagging "double commit"
grep -r "await db.commit()" backend/app/api/v1/endpoints --include="*.py" | wc -l
# Result: 112 instances → This IS the pattern!

# Before flagging "test data violation"
# Check how data is filtered - may be intentional
```

**Decision Matrix**:
- **Flag as Issue**: Violates ADR, breaks functionality, inconsistent with 90%+ codebase
- **Accept as Pattern**: Consistent with codebase, has valid reason, defense-in-depth

**Source**: Consolidated from `pr_review_challenging_assumptions`

---

## Security Patterns

### Pattern 5: Multi-Tenant Context in Background Tasks (CRITICAL)

**Problem**: Background tasks querying database without tenant scoping = security vulnerability.

**Qodo Bot Detection**: Importance 9/10 - "Background tasks query tables WITHOUT tenant scoping"

**Solution**:
```python
# Step 1: Pass tenant context from API endpoint
background_tasks.add_task(
    service.run_analysis,
    analysis.id,
    parameters.dict(),
    context.client_account_id,  # SECURITY: Pass tenant context
    context.engagement_id,       # SECURITY: Pass tenant context
)

# Step 2: Update service method signature
async def run_analysis(
    self,
    analysis_id: int,
    parameters: Dict[str, Any],
    client_account_id: Optional[int] = None,
    engagement_id: Optional[int] = None,
):
    pass

# Step 3: Add tenant scoping to ALL queries
query = select(Analysis).where(Analysis.id == analysis_id)
if client_account_id is not None:
    query = query.where(Analysis.client_account_id == client_account_id)
if engagement_id is not None:
    query = query.where(Analysis.engagement_id == engagement_id)

# Step 4: Fail securely (don't reveal cross-tenant data)
if not analysis:
    logger.error(f"Analysis {analysis_id} not found for tenant")
    return  # Silent fail - don't reveal if ID exists in another tenant
```

**Verification Checklist**:
- [ ] Background task accepts client_account_id and engagement_id
- [ ] All SELECT queries include tenant scoping
- [ ] Query failures logged with tenant context
- [ ] No error messages reveal cross-tenant data

**Source**: Consolidated from `qodo-bot-multi-tenant-security-pattern`

---

### Pattern 6: Three-Tier Logging Strategy

**Purpose**: Prevent sensitive information exposure in logs.

**Tiers**:

| Tier | Level | Audience | Content |
|------|-------|----------|---------|
| 1 | DEBUG | Developers (dev only) | Everything - exceptions, SQL, tokens |
| 2 | INFO/ERROR | Production monitoring | Generic status, exception types only |
| 3 | Database | End users, support | User-facing errors only |

**Implementation**:
```python
except Exception as e:
    # Tier 1: DEBUG (full details)
    logger.debug(f"Failed for flow {flow_id}: {e}", exc_info=True)

    # Tier 2: ERROR (generic only)
    logger.error(f"Failed for flow {flow_id} (type: {type(e).__name__})")

    # Tier 3: Database (user-facing)
    error_msg = f"Operation failed: {type(e).__name__}"
    await update_status(id, "failed", error_message=error_msg, db=db)
```

**Frontend**:
```typescript
// Development only logging
if (import.meta.env.DEV) {
  console.log('🔄 Refreshing auth token...');
}
```

**What Goes Where**:
- **DEBUG**: Stack traces, field names, asset names, SQL, tokens
- **INFO/ERROR**: Counts, aggregates, generic status, exception types
- **Database**: Generic errors only, NO technical details

**Source**: Consolidated from `qodo_security_logging_three_tier_pattern_2025_11`

---

### Pattern 7: Sensitive Field Redaction in Data Previews (NEW - Dec 2025)

**Problem**: Data profiling/preview endpoints may expose sensitive field values.

**Qodo Bot Detection**: Importance 8/10 - "Sensitive fields exposed in preview data"

**Solution**:
```python
# In data profiling/preview code
SENSITIVE_KEYWORDS = ["password", "secret", "token", "key", "ssn", "credit", "cvv", "pin"]

def get_preview_value(field_name: str, value: Any) -> str:
    """Redact sensitive fields in preview data."""
    if any(sensitive in field_name.lower() for sensitive in SENSITIVE_KEYWORDS):
        return "[REDACTED - sensitive field]"

    # Normal value processing
    if value is None:
        return ""
    return str(value)[:100]  # Truncate long values
```

**Files typically affected**:
- `backend/app/services/crewai_flows/handlers/phase_executors/data_import_validation/data_profiler.py`
- Any data preview/sample extraction endpoints

**Verification Checklist**:
- [ ] Field name checked against sensitive keywords (case-insensitive)
- [ ] Redaction applied BEFORE any logging or response building
- [ ] Redaction message doesn't reveal what the value contained

**Source**: Session learning from Qodo Bot review on ADR-038 data validation PR (Dec 2025)

---

## Data Quality Patterns

### Pattern 8: Falsy Value Handling (NEW - Dec 2025)

**Problem**: Python treats `0`, empty string `""`, and `False` as falsy, causing valid data to be filtered out.

**Wrong**:
```python
# Filters out valid 0 values!
if value:
    valid_values.append(value)
```

**Correct**:
```python
# Explicitly check for None and empty string, allow 0
if value is not None and value != "":
    valid_values.append(value)

# For length checks
if value is not None and str(value).strip():
    # Has actual content
```

**Common scenarios**:
- Data profiling sample extraction
- Field completeness calculations
- Data validation statistics

**Source**: Session learning from Qodo Bot review (Dec 2025)

---

### Pattern 9: Case-Insensitive Field Matching (NEW - Dec 2025)

**Problem**: Field names from different sources may have inconsistent casing (e.g., `IP_Address` vs `ip_address`).

**Wrong**:
```python
# Fails to match 'IP_Address' with 'ip_address'
decisions_by_field = {field: decision for field, decision in decisions.items()}
result = decisions_by_field.get(field_name)  # None if case mismatch
```

**Correct**:
```python
# Build case-insensitive lookup
decisions_by_field = {field.lower(): decision for field, decision in decisions.items()}

# Query with normalized key
result = decisions_by_field.get(field_name.lower())
```

**When to use**:
- Field mapping between systems
- Validation decision lookups
- Data cleansing field matching

**Source**: Session learning from ADR-038 data validation implementation (Dec 2025)

---

### Pattern 10: Field-Based vs Cell-Based Compliance Scoring

**Problem**: Compliance scores calculated per cell inflate counts; should be per unique field.

**Wrong**:
```python
# Counts every cell, inflating totals
compliant_cells = sum(1 for row in data for cell in row if is_compliant(cell))
total_cells = len(data) * len(fields)
compliance_score = compliant_cells / total_cells
```

**Correct**:
```python
# Count per field, not per cell
fields_checked = set()
compliant_fields = set()

for field in unique_fields:
    if field not in fields_checked:
        fields_checked.add(field)
        if is_field_compliant(field, data):
            compliant_fields.add(field)

compliance_score = len(compliant_fields) / len(fields_checked) if fields_checked else 0.0
```

**Source**: Session learning from Qodo Bot review on data profiler (Dec 2025)

---

## Code Quality Patterns

### Pattern 11: Transaction Atomicity

**Problem**: Nested commits breaking transaction atomicity.

**Wrong**:
```python
async def update_flow_status(self, flow_id, new_status):
    async with self.db.begin():
        await self._update_master_flow(...)  # Contains commit()
        await self._update_child_flow(...)   # Contains commit()
    # Transaction broken - partial updates possible
```

**Correct**:
```python
async def update_flow_status_atomically(self, flow_id, new_status):
    async with self.db.begin():
        await self._update_master_flow_in_transaction(...)  # flush() only
        await self._update_child_flow_in_transaction(...)   # flush() only
    # Single commit - all or nothing

async def _update_master_flow_in_transaction(self, ...):
    """Internal method - flushes but does NOT commit"""
    master_flow.status = new_status
    await self.db.flush()  # Make visible to transaction, don't commit
```

**Rule**: Internal methods use `flush()`, outer method owns `commit()`.

**Source**: Consolidated from `qodo_bot_pr_fixes_transaction_session_patterns_2025_10_02`

---

### Pattern 12: ESLint Disable Cleanup

**Problem**: Multiple `eslint-disable-next-line` comments cluttering code.

**Wrong**:
```typescript
const handleChange = useCallback((value) => {
  setState((prev) => ({...prev, value}));
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```

**Correct**:
```typescript
const handleChange = useCallback((value) => {
  setState((prev) => ({...prev, value}));
}, [setState]);  // React guarantees setState stability - no perf impact
```

**Key Insight**: Disable comments are code smell - fix root cause instead.

**Source**: Consolidated from `qodo_bot_code_review_resolution_patterns_2025_10`

---

### Pattern 13: Data Corruption Prevention - Field Order

**Problem**: Inconsistent field order causing row data misalignment.

**Wrong**:
```python
for record in records:
    source_fields = list(record.raw_data.keys())  # Order may vary!
    sample_rows.append(list(record.raw_data.values()))
# Result: ["name", "ip"] → ["Alice", "10.0.0.1"]
#         ["ip", "name"] → ["10.0.0.2", "Bob"]  # CORRUPTED!
```

**Correct**:
```python
source_fields = []
for idx, record in enumerate(records):
    if idx == 0:
        source_fields = list(record.raw_data.keys())  # Establish order
    ordered_values = [record.raw_data.get(field) for field in source_fields]
    sample_rows.append(ordered_values)
```

**Source**: Consolidated from `qodo_bot_pr_fixes_transaction_session_patterns_2025_10_02`

---

### Pattern 14: Stable React Keys for Dynamic Lists

**Problem**: Using array index as React key causes unnecessary re-renders and state bugs.

**Wrong**:
```typescript
{issues.map((issue, index) => (
  <IssueCard key={index} issue={issue} />  // ❌ Index changes on filter/sort
))}
```

**Correct**:
```typescript
{issues.map((issue) => {
  // Create stable key from content
  const issueKey = `${issue.type}-${issue.field}-${issue.issue.replace(/\s/g, '-')}`;
  return <IssueCard key={issueKey} issue={issue} />;
})}
```

**Source**: Session learning from Qodo Bot review (Dec 2025)

---

## PR Workflow Patterns

### Pattern 15: Atomic Commits per Suggestion

**Commit Strategy**:
```bash
# Commit 1: Low-impact fix first (4/10)
git commit -m "refactor: Remove redundant Array.isArray check

Per Qodo Bot review (Importance 4/10): Type system guarantees array.

Changes:
- src/hooks/useApplicationData.ts: Remove redundant check

Addresses: [PR comment URL]"

# Commit 2: High-impact fix second (7/10)
git commit -m "refactor: Replace eslint-disable with proper dependencies

Per Qodo Bot review (Importance 7/10): Include setState in deps."
```

**Benefits**: Easy to review, easy to revert, clear traceability.

**Source**: Consolidated from `qodo_bot_code_review_resolution_patterns_2025_10`

---

### Pattern 16: Fix ALL Feedback in Same PR

**Principle**: Never defer to "follow-up PR" - reviewers expect complete resolution.

**Response Template**:
```markdown
## ✅ ALL Review Items Addressed

### Must-Fix Items ✅
1. **Issue**: [Description]
   **Fixed**: [What was done]
   **File**: [path/to/file.py]

### High-Priority Items ✅
1. **TypeScript Type Safety** ✅
   - Removed ALL 'any' casts
   - Exported proper interfaces

Ready for final review and merge! 🚀
```

**Source**: Consolidated from `pr_review_handling_patterns`

---

### Pattern 17: Update Existing PR, Don't Create New

**Wrong**:
```bash
git checkout -b fix/qodo-bot-suggestions  # ❌ New branch
```

**Correct**:
```bash
git checkout fix/original-branch  # ✅ Stay on original
git add -A && git commit -m "fix: Apply Qodo Bot suggestions"
git push origin fix/original-branch
```

**Source**: Consolidated from `pr_review_handling_patterns`

---

### Pattern 18: GitHub Enhancement Issue for Deferred Work (NEW - Dec 2025)

**When to use**: Qodo suggestions require architectural changes that don't fit current PR scope.

**Issue Template**:
```markdown
## Enhancement: [Title]

### Background
This enhancement was identified during PR review for [PR link].

### Deferred Items
1. **Async Profiling** (Qodo suggestion X/10)
   - Current: Synchronous data profiling
   - Proposed: `run_in_executor()` for CPU-bound tasks
   - Impact: Better response times for large datasets

2. **Streaming Responses** (Qodo suggestion Y/10)
   - Current: Full response returned at once
   - Proposed: `StreamingResponse` for large payloads
   - Impact: Reduced memory pressure

### Implementation Notes
- Requires coordination between frontend and backend
- Consider pagination as alternative to streaming
- Performance benchmarks needed first

### Related
- PR: [link]
- ADR: [if applicable]
```

**Example**: Issue #1227 created for ADR-038 async profiling and streaming deferred work.

**Source**: Session learning from ADR-038 intelligent data validation PR (Dec 2025)

---

## Anti-Patterns

### Don't: Dismiss Anti-Pattern Warnings Based on "Works"

**Why it's bad**: "Working" hides technical debt that manifests as bugs later.

**Example**: Bug #1102 - `window.location.reload()` "worked" but caused infinite loop.

**Right approach**: Research the pattern, provide technical justification if disagreeing.

---

### Don't: Use `window.location.reload()` in React

**Why it's bad**: Destroys React state, causes reload loops, hides state bugs.

**Wrong**:
```typescript
window.location.reload();  // ❌ Nuclear option
```

**Right**:
```typescript
// Proper state management
queryClient.invalidateQueries(['questionnaire']);
// OR: Navigation with remount
navigate(location.pathname, { replace: true, state: { key: Date.now() } });
```

---

### Don't: Expose Sensitive Data in Logs

**Why it's bad**: SQL injection attack vectors, schema exposure, PII leaks.

**Wrong**:
```python
logger.error(f"Database error: {str(e)}")  # Exposes SQL
```

**Right**:
```python
logger.debug(f"Database error: {str(e)}", exc_info=True)  # Tier 1
logger.error(f"Database error (type: {type(e).__name__})")  # Tier 2
```

---

### Don't: Query Without Tenant Scoping in Background Tasks

**Why it's bad**: Cross-tenant data access via ID guessing.

**Wrong**:
```python
query = select(Analysis).where(Analysis.id == analysis_id)
```

**Right**:
```python
query = select(Analysis).where(
    Analysis.id == analysis_id,
    Analysis.client_account_id == client_account_id,
    Analysis.engagement_id == engagement_id,
)
```

---

### Don't: Allow Critical Issues to be Bypassed (NEW - Dec 2025)

**Why it's bad**: Data validation workflows should enforce resolution of critical issues.

**Wrong**:
```python
# Frontend disabled button but backend didn't check
@router.post("/complete")
async def complete_validation(flow_id: str):
    # Completes even if critical issues exist
    return {"success": True}
```

**Right**:
```python
@router.post("/complete")
async def complete_validation(flow_id: str, db: AsyncSession):
    # Check for unresolved critical issues
    violations = await check_critical_issues(flow_id, db)
    if violations:
        raise HTTPException(
            status_code=400,
            detail="Cannot complete validation. Critical issues found that require user decisions.",
        )
    return {"success": True}
```

**Source**: Session learning from Qodo Bot security review (Dec 2025)

---

## Code Templates

### Template 1: Qodo Bot Disagreement Response

When disagreeing with Qodo bot, use this template:

```markdown
## Response to Qodo Bot

**Bot's Claim**: [Anti-pattern X exists]
**Bot's Evidence**: [Code references]
**Bot's Recommendation**: [Fix Y]

**My Analysis**:
1. **Context**: [Specific architectural pattern we use]
2. **Why bot may be wrong**: [Technical reasoning]
3. **Why our approach is correct**: [Concrete benefits]
4. **Trade-offs considered**: [What we're accepting]

**If I'm wrong**: [Consequences, how we'd detect, mitigation plan]
```

---

### Template 2: PR Review Fix Commit

```bash
git commit -m "$(cat <<'EOF'
refactor: [One-line summary]

Per Qodo Bot review (Importance X/10): [Qodo's explanation]

Changes:
- [File path]: [Specific change]
- [File path]: [Specific change]

[Additional context about why fix is safe/correct]

Addresses: [GitHub PR comment URL]
EOF
)"
```

---

### Template 3: Security-Safe Error Handler

```python
async def handle_operation(self, id: int, client_account_id: int, engagement_id: int):
    try:
        # Operation
        pass
    except Exception as e:
        # Tier 1: DEBUG (full details for dev)
        logger.debug(f"Operation failed: {e}", exc_info=True)

        # Tier 2: ERROR (production-safe)
        logger.error(
            f"Operation failed for id={id}, tenant=({client_account_id}, {engagement_id}), "
            f"type={type(e).__name__}"
        )

        # Tier 3: Database (user-facing)
        await self.update_status(id, "failed", f"Operation failed: {type(e).__name__}")

        raise  # Re-raise for caller to handle
```

---

### Template 4: Sensitive Field Redaction (NEW - Dec 2025)

```python
SENSITIVE_KEYWORDS = ["password", "secret", "token", "key", "ssn", "credit", "cvv", "pin"]

def redact_sensitive_preview(field_name: str, value: Any) -> str:
    """Safely preview field values, redacting sensitive data."""
    if any(sensitive in field_name.lower() for sensitive in SENSITIVE_KEYWORDS):
        return "[REDACTED - sensitive field]"

    if value is None:
        return ""

    str_value = str(value)
    return str_value[:100] if len(str_value) > 100 else str_value
```

---

## Troubleshooting

### Issue: Qodo Bot flags pattern used 100+ times in codebase

**Solution**: Verify before criticizing
```bash
grep -r "pattern" backend/ --include="*.py" | wc -l
```
If widely used, it's the project pattern. Accept it.

---

### Issue: Pre-commit blocks on Qodo fix commits

**Solution**: Run pre-commit, fix issues, then commit
```bash
pre-commit run --all-files
# Fix any issues
git add -A
git commit -m "fix: Apply Qodo suggestions"
```

---

### Issue: Which Qodo suggestions to prioritize?

**Solution**: Use importance score
- 7+/10: Fix immediately
- 4-6/10: Batch if time permits
- 1-3/10: Consider if aligns with project conventions

---

### Issue: Qodo suggests architectural changes that don't fit PR scope

**Solution**: Create GitHub enhancement issue
1. Fix what can be fixed in current PR
2. Create enhancement issue for architectural work
3. Reference issue in PR comment explaining deferral

---

## Related Documentation

| Resource | Location | Purpose |
|----------|----------|---------|
| Security Best Practices | `.serena/memories/security_best_practices.md` | General security |
| Pre-commit Patterns | `.serena/memories/precommit_troubleshooting_2025_01.md` | Pre-commit hooks |
| Coding Agent Guide | `/docs/analysis/Notes/coding-agent-guide.md` | Implementation patterns |

---

## Consolidated Sources

This master memory consolidates the following original memories:

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `qodo_bot_feedback_patterns` | 2025-10 | Common issues and solutions |
| `qodo_bot_code_review_resolution_patterns_2025_10` | 2025-10 | ESLint, type guards, atomic commits |
| `qodo-bot-multi-tenant-security-pattern` | 2025-10 | Tenant context in background tasks |
| `pr_review_handling_patterns` | 2025-10 | Complete review resolution |
| `qodo_security_logging_three_tier_pattern_2025_11` | 2025-11 | Three-tier logging |
| `qodo_bot_pr_fixes_transaction_session_patterns_2025_10_02` | 2025-10 | Transaction atomicity |
| `qodo-bot-code-review-credibility-pattern-2025-11` | 2025-11 | Credibility assessment |
| `pr_review_challenging_assumptions` | 2025-10 | Verify before criticizing |
| `qodo_bot_feedback_resolution_patterns` | 2025-10 | Patching, signatures |
| `qodo_bot_performance_optimization_patterns_2025_11` | 2025-11 | Performance |
| `qodo_bot_multi_tenant_security_fixes_2025_10` | 2025-10 | Security fixes |
| `qodo_bot_race_condition_memory_leak_fixes` | 2025-10 | Race conditions |
| `qodo_bot_pr_review_handling` | 2025-10 | PR review handling |
| `qodo-bot-pr-review-and-issue-tracking-patterns-2025-11` | 2025-11 | Issue tracking |
| `qodo-compliance-verification-methodology-2025-11` | 2025-11 | Compliance |
| `qodo-security-review-integration-pattern-2025-11` | 2025-11 | Security integration |
| `pr_review_and_precommit_compliance_patterns` | 2025-10 | Pre-commit compliance |
| `pr_review_without_local_branch_changes_2025_10` | 2025-10 | Review without local changes |
| `pr-review-multi-fix-workflow-and-ag-grid-patterns-2025-11` | 2025-11 | Multi-fix workflow |
| `pr_review_patterns_collection_assessment_2025_01` | 2025-01 | Collection/assessment reviews |
| `pr_review_patterns_collection_status_remediation_completed` | 2025-10 | Status remediation |
| `adr_028_compliance_qodo_sql_safety_2025_10` | 2025-10 | SQL safety |
| `dependency-analysis-qodo-optimization-patterns-2025-01` | 2025-01 | Optimization |
| `modularization_cleanup_and_pr_review_2025_16` | 2025-10 | Modularization review |
| `pr_recovery_and_qodo_feedback_workflow_2025_11` | 2025-11 | Recovery workflow |
| Session learning ADR-038 | 2025-12 | Batched fixes, sensitive field redaction, falsy values |

**Archive Location**: `.serena/archive/qodo_pr_review/`

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-30 | Initial consolidation of 25 memories | Claude Code |
| 2025-12-03 | Added patterns 3, 7-10, 14, 18 from ADR-038 session | Claude Code |

---

## Search Keywords

qodo, pr_review, code_review, security, multi_tenant, logging, transaction, atomicity, credibility, anti_pattern, background_task, tenant_scoping, sensitive_field, redaction, falsy_value, case_insensitive, batched_fixes
