# Qodo Compliance Verification Methodology

## Purpose
Systematic workflow for verifying Qodo bot compliance issues across multiple PR review iterations when developer claims fixes are complete.

## Context
When PR has multiple commits addressing Qodo feedback, need systematic method to:
1. Extract ALL compliance issues from initial review
2. Track which issues were addressed in subsequent commits
3. Verify fixes by examining actual code changes
4. Provide clear merge recommendation with outstanding items

## The Systematic Workflow

### Step 1: Fetch Chronological Qodo Reviews
```bash
# Get all Qodo bot comments on PR (chronologically)
gh api repos/OWNER/REPO/issues/comments \
  --jq '.[] | select(.user.login == "qodo-merge-pro[bot]") | {created_at: .created_at, body: .body}'

# Or get reviews by date range
gh api repos/OWNER/REPO/issues/comments \
  --jq '.[] | select(.user.login == "qodo-merge-pro[bot]" and .created_at >= "2025-11-14" and .created_at < "2025-11-15")'
```

**Why chronological**: Shows progression of fixes across review iterations

### Step 2: Extract Compliance Issues Systematically

Parse Qodo review into structured format:

**Security Compliance** (typically 3-7 issues):
- Issue name
- Severity (⚪ Requires Verification, 🟡 Warning, 🔴 Critical)
- Code location (`file.py:line-range`)
- Specific concern (what's wrong)
- Status (Fixed / Mitigated / Outstanding)

**Custom Compliance** (typically 3-5 issues):
- Same structure as security compliance
- Often covers: audit logging, error handling, input validation

**Example from PR #1046:**
```
Security Compliance (5 issues):
1. Unbounded file parsing (upload_handler.py:78-85)
2. Sensitive data exposure - App Discovery (app_discovery_processor.py:33-44)
3. Sensitive data exposure - Infrastructure (infrastructure_processor.py:32-45)
4. Sensitive data exposure - Sensitive Data (sensitive_data_processor.py:32-45)
5. Information disclosure (upload_handler.py:63-71)

Custom Compliance (5 issues):
1. Missing audit logs (upload_handler.py - no audit logging)
2. Generic failure path (import_processor_runner.py:162-169)
3. Error detail exposure (import_processor_runner.py - raw exceptions)
4. Log content risk (processors logging sensitive data)
5. Limited input validation (no file size/record count limits)
```

### Step 3: Check Actual Code Changes

For EACH compliance issue, verify fix in PR diff:

```bash
# Get full PR diff
gh pr diff PR_NUMBER --patch

# Search for specific file changes
gh pr diff PR_NUMBER --patch | grep -A 50 "^diff --git a/path/to/file.py"

# Check for specific patterns (e.g., file size validation)
gh pr diff PR_NUMBER | grep -B 5 -A 10 "MAX_UPLOAD_SIZE"
```

**Verification checklist per issue:**
- [ ] Code location matches Qodo's reference
- [ ] Fix addresses root cause (not just symptom)
- [ ] Fix follows best practices (not just silencing Qodo)
- [ ] Alternative mitigations documented if direct fix not feasible

### Step 4: Categorize Resolution Status

For each issue, assign status:

**✅ FIXED**: Direct fix implemented
- Example: Added `MAX_UPLOAD_SIZE_MB = 100` with pre-read validation
- Evidence: Code change visible in diff at exact location

**✅ MITIGATED**: Alternative approach with justification
- Example: Still sends 2-record preview to LLM, but added tenant context tracking
- Justification: Preview is minimal and necessary; audit logging provides oversight

**⚪ OUTSTANDING**: Not addressed, needs fix or clarification
- Create enhancement issue if non-blocking
- Flag as blocker if critical

### Step 5: Build Compliance Matrix

Create table showing before/after for each issue:

```markdown
| Issue | Qodo Concern | Status | Evidence |
|-------|-------------|---------|----------|
| Unbounded parsing | No file size limit | ✅ FIXED | upload_handler.py:44-56 - Added 100MB limit |
| Sensitive data (App) | Raw preview to LLM | ✅ MITIGATED | Added tenant context tracking (audit trail) |
| Audit logs | No structured logging | ✅ FIXED | upload_handler.py:147-182 - AccessAuditLog entries |
```

### Step 6: Provide Merge Recommendation

**Format:**
```markdown
## Verdict: [APPROVE / REQUEST CHANGES / COMMENT]

### Compliance Status: [X/Y issues resolved]

**ADDRESSED (X issues):**
- Issue 1 description [✅ FIXED / ✅ MITIGATED]
- Issue 2 description [✅ FIXED / ✅ MITIGATED]

**OUTSTANDING (Y issues):**
- Issue 3 description [⚪ BLOCKER / ⚪ ENHANCEMENT]
  - Recommendation: [Create issue #XXX / Fix before merge]

### Risk Assessment: [LOW / MEDIUM / HIGH]
- Critical issues: X resolved, Y outstanding
- Security concerns: [summary]
- Non-blocking enhancements: [count]
```

## Common Patterns in Fixes

### 1. Input Validation
**Qodo**: "Unbounded file parsing"
**Fix Evidence**: Look for limits, validation checks
```python
MAX_UPLOAD_SIZE_MB = 100
MAX_JSON_DEPTH = 100
MAX_RECORDS = 100000

if file_size > MAX_UPLOAD_SIZE_BYTES:
    raise HTTPException(status_code=413, detail="File too large")
```

### 2. Error Sanitization
**Qodo**: "Information disclosure" or "Error detail exposure"
**Fix Evidence**: Look for sanitization functions
```python
def _sanitize_error_message(exc: Exception, category: str) -> str:
    """Map exception types to user-friendly messages without internal details"""
    exc_type = type(exc).__name__
    if exc_type == "ValidationError":
        return f"Data validation failed for {category}. Check format."
    # Never expose raw exception message
```

### 3. Audit Logging
**Qodo**: "Missing audit logs"
**Fix Evidence**: Look for AccessAuditLog or structured logging
```python
audit_log = AccessAuditLog(
    user_id=context.user_id,
    action_type="data_import_upload",
    resource_id=str(data_import_id),
    result="success",
    details={"record_count": len(records)}
)
db.add(audit_log)
```

### 4. Sensitive Data Handling
**Qodo**: "Sensitive data exposure"
**Fix Evidence**: Look for masking, limited previews, or explicit justification
```python
# Mitigation approach (if masking not feasible):
# - Limit preview to 2 records (minimal exposure)
# - Add tenant context tracking (audit trail)
# - Document why preview is necessary for validation
```

## When to Accept Mitigations vs Require Direct Fixes

### Accept Mitigation:
- Direct fix would break functionality
- Alternative provides equivalent protection
- Mitigation is documented with justification
- Risk is low and observable (audit logs)

**Example**: Sending 2-record preview to LLM for validation
- **Mitigation**: Tenant context tracking + audit logging
- **Justification**: Preview necessary for schema validation; exposure minimal

### Require Direct Fix:
- Security vulnerability exploitable
- Fix is straightforward and available
- No justification for alternative approach
- High risk or compliance requirement

**Example**: Missing file size validation
- **Fix Required**: Add MAX_UPLOAD_SIZE check
- **Reason**: DoS vulnerability, trivial to fix

## Tools and Commands

```bash
# Fetch Qodo reviews chronologically
gh api repos/$OWNER/$REPO/issues/comments \
  --jq '.[] | select(.user.login == "qodo-merge-pro[bot]") | {created_at: .created_at, body: .body[0:1000]}'

# Get PR diff for verification
gh pr diff PR_NUMBER --patch > pr_changes.patch

# Search for specific patterns in diff
grep -A 20 "MAX_UPLOAD_SIZE" pr_changes.patch
grep -A 20 "AccessAuditLog" pr_changes.patch
grep -A 20 "sanitize" pr_changes.patch

# Check CI status
gh pr checks PR_NUMBER

# Create enhancement issues for non-blocking items
gh issue create --title "Enhancement: ..." --body "..." --label "enhancement,security"
```

## Session Example: PR #1046

**Context**: Multi-type data import with 65 files, Qodo flagged 10 compliance issues

**Workflow Applied:**
1. Fetched 3 Qodo reviews (Nov 14, 17, 21)
2. Extracted 5 security + 5 custom compliance issues from Nov 14
3. Verified each issue against PR diff
4. Found 8/10 fixed, 2/10 mitigated (non-blocking)
5. Created issues #1122, #1123 for enhancements
6. Verdict: **APPROVE** - All critical issues resolved

**Outcome**: Clear audit trail of compliance verification, user confidence in merge safety

## Value
- **Systematic**: No compliance issues missed
- **Evidence-based**: Verification via actual code changes
- **Transparent**: Clear status for each issue
- **Actionable**: Outstanding items tracked with issue numbers
