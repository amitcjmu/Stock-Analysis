# Code Review Comments Repository

**Testing References (review before adding tests)**
- [docs/testing/testing-strategy.md](../testing/testing-strategy.md)
- [docs/testing/QA_GUIDE.md](../testing/QA_GUIDE.md)
- [docs/testing/README.md](../testing/README.md)
- [docs/testing/Discovery-Flow-UnitTest-Coverage.md](../testing/Discovery-Flow-UnitTest-Coverage.md)
- [docs/testing/CrewAIAgents-UnitTest-Coverage.md](../testing/CrewAIAgents-UnitTest-Coverage.md)

> **Purpose:** Central repository of common review feedback to maintain code quality standards.  
> **Usage:** Reference this before creating PRs to avoid common pitfalls.  
> **Update:** Team members should add new patterns as they encounter them in reviews.

---

## 📋 How to Use This Document

**Before Creating a PR:**
- Review relevant sections based on your changes
- Self-check against common issues
- Fix proactively before review

**After Receiving Review Comments:**
- If the comment represents a new pattern, add it here
- Include only the **issue summary**, not specific solutions
- Keep it concise and searchable

---

## Import Strategy

### ❌ Local Imports Inside Functions
**Issue:** Imports placed inside function bodies instead of module top  
**Why:** Performance overhead on every function call, harder to track dependencies, violates project import strategy  
**Example:** `from app.services.x import Y` inside a loop or function  
**Check:** Ensure all imports are at module level (lines 1-30) unless absolutely necessary for circular dependency resolution

**Reference:** PR #581 - operations.py lines 252-255, 325-328

---

## Transaction Management & Database

### ❌ Creating New Sessions Inside Transactions
**Issue:** Creating new `AsyncSessionLocal()` inside a method that's part of a larger transaction  
**Why:** Breaks atomic transaction boundaries, can cause orphaned data on failure, race conditions possible  
**Example:** Method creates new `async with AsyncSessionLocal() as db:` when session already exists  
**Check:** Reuse existing session/transaction context from caller

**Reference:** PR #581 - executor.py line 442-516

### ❌ N+1 Query Pattern
**Issue:** Looping through items and making individual database queries for each  
**Why:** Severe performance impact - 100 items = 200+ queries instead of 2 batch queries  
**Example:** `for item in items: await db.query(...).where(id == item.id)`  
**Check:** 
- Collect all IDs upfront: `ids = [item.id for item in items]`
- Use batch query with IN clause or joins
- Build lookup dictionary for loop usage

**Reference:** PR #581 - operations.py lines 245-298

---

## Error Handling

### ❌ Missing Error Handling for External Calls
**Issue:** No try-catch around calls to external services, helpers, or database operations that can fail  
**Why:** Unhandled exceptions break entire flow, no graceful degradation  
**Example:** Calling helper method without try-catch  
**Check:** 
- Wrap external calls in try-except
- Provide sensible fallback values
- Log warnings with context
- Don't fail silently - always log

**Reference:** PR #581 - operations.py lines 249-275

### ❌ Exposing Internal Error Details to End Users
**Issue:** Error messages include raw exception strings (`str(exc)`) that expose internal system details  
**Why:** Security risk - internal stack traces, file paths, database errors visible to users; Poor UX - technical jargon confuses users  
**Example:** `phase_data={"error": str(exc)}` or `detail=str(exc)` in HTTP responses  
**Check:**
- Sanitize error messages before exposing to users
- Map internal exceptions to user-friendly messages
- Log full details internally (with `exc_info=True`)
- Return generic messages to users: `"An error occurred processing your request. Please contact support."`
- Include actionable context: `"File validation failed. Please check that all required fields are present."`

**Sanitization Pattern:**
```python
# ❌ BAD: Exposes internal details
await update_flow_status(
    flow_id=flow_id,
    status="failed",
    phase_data={"error": str(exc)},  # Exposes file paths, DB errors
)

# ✅ GOOD: Sanitized user message
error_message = self._sanitize_error(exc)  # Maps to user-friendly message
logger.error("Processing failed", exc_info=True)  # Full details in logs
await update_flow_status(
    flow_id=flow_id,
    status="failed",
    phase_data={"error": error_message},  # Safe user message
)
```

**Reference:** PR #1046 - Qodo review comments on error detail exposure

### ❌ Generic Error Messages Without Context
**Issue:** Error messages lack actionable context, making debugging difficult for users  
**Why:** Users can't resolve issues without understanding what went wrong  
**Example:** `"An error occurred"` or `"Failed to read file"` without context  
**Check:**
- Include operation context: `"Failed to validate uploaded file"`
- Include affected resource: `"Record at row 5 missing required field 'server_name'"`
- Include troubleshooting steps: `"Please check file format and try again"`
- Balance detail with security (don't expose internal details)

**Reference:** PR #1046 - Qodo review on generic failure paths; PR #1091 - CSV parsing error handling

---

## Type Safety & Code Quality

### ❌ Using SimpleNamespace or Dict Instead of Proper Types
**Issue:** Bypassing type system with `SimpleNamespace` or plain dicts for structured data  
**Why:** No type checking, no IDE autocomplete, harder to maintain, runtime errors  
**Example:** `result = SimpleNamespace(field1=..., field2=...)`  
**Check:** Use `@dataclass` or proper class definitions for structured data

**Reference:** PR #581 - flow_processing_converters.py lines 74-80

### ❌ Field Naming Convention Violation (camelCase vs snake_case)
**Issue:** Frontend using camelCase for API fields when backend returns snake_case  
**Why:** Field name mismatches cause data loss, silent failures, recurring bugs  
**Example:** `cleansingStats` vs `cleansing_stats`, `totalRows` vs `total_rows`  
**Check:** Frontend SHOULD use snake_case fields to match backend for all NEW code; Check interface definitions match backend schemas

**Reference:** PR #1091 - Qodo bot BLOCKING review on field naming convention

### ❌ Missing Enum Values
**Issue:** Code references enum value that doesn't exist in enum definition  
**Why:** Runtime AttributeError, flow breaks silently  
**Example:** `if action == PhaseAction.COMPLETE:` but `COMPLETE` not defined in enum  
**Check:** When checking enum values, verify they exist in enum definition; When adding enum checks, ensure corresponding value exists

**Reference:** PR #1107 - PhaseAction enum missing COMPLETE value

### ❌ Magic Numbers
**Issue:** Hardcoded numbers in calculations without context (e.g., `/ 6`, `* 100`, `10`)  
**Why:** Unclear meaning, hard to update if value changes, poor maintainability  
**Example:** `progress = round((completed / 6) * 100, 1)` or `parseCsvFileForDiscovery(file, 10)`  
**Check:** 
- Define named constants at module level
- Use descriptive names: `TOTAL_DISCOVERY_PHASES = 6`, `DISCOVERY_SAMPLE_ROWS = 10`
- Add comments explaining the constant
- Replace ALL hardcoded numbers, even in function calls

**Reference:** PR #581 - operations.py lines 303, 388; PR #1091 - useCMDBImport.ts line 88

---

## API & Interface Changes

### ❌ Breaking Function Signatures Without Verification
**Issue:** Changing function parameters without checking all callers  
**Why:** Runtime errors in unchecked call sites, breaks existing code  
**Example:** Adding required parameter to widely-used function  
**Check:** 
- Search codebase: `grep -r "function_name(" backend/`
- Verify all call sites updated
- Consider backward compatibility (optional params, defaults)

**Reference:** PR #581 - flow_processing_converters.py line 145

---

## Documentation & Tracking

### ❌ Missing Documentation for Significant Fixes
**Issue:** Bug fixes or architecture changes committed without documentation  
**Why:** Lost context over time, hard to debug similar issues later, knowledge not shared  
**Example:** Complex bug fix without explanation of root cause  
**Check:** 
- Create `docs/fixes/*.md` for significant fixes
- Include: root cause, solution, testing approach
- Reference bug numbers in code comments

**Reference:** PR #581 - backend/docs/fixes/DISCOVERY_FLOW_STATUS_FIXES.md

### ❌ Inconsistent Logging
**Issue:** Some code paths log extensively, others have no logging at all  
**Why:** Hard to debug in production, inconsistent observability  
**Example:** Error handling without logging the error context  
**Check:**
- Add context to log messages (IDs, counts, etc.)
- Use consistent emoji prefixes for visual scanning
- Log at appropriate levels (info, warning, error)

**Reference:** PR #581 - operations.py logging consistency

### ❌ Missing Audit Logs for Critical Operations
**Issue:** Critical operations (file uploads, data imports, exports) don't emit structured audit log entries  
**Why:** Security compliance requires audit trails for sensitive operations; No traceability for security incidents; Regulatory violations (SOC2, GDPR audit requirements)  
**Example:** Upload endpoint performs file upload, category routing, background processing without audit logging  
**Check:**
- Use `AuditLoggingService` for critical operations (data imports, exports, uploads)
- Include user ID, action, outcome, metadata in audit logs
- Log both success and failure cases
- Store audit logs in database, not just application logs

**Audit Logging Pattern:**
```python
from app.services.collection_flow.audit_logging.logger import AuditLoggingService
from app.services.collection_flow.audit_logging.base import AuditEventType, AuditSeverity

# ❌ BAD: No audit logging
@router.post("/upload")
async def upload_data_import(...):
    # Process upload...
    return {"success": True}

# ✅ GOOD: Structured audit logging
@router.post("/upload")
async def upload_data_import(..., db: AsyncSession, context: RequestContext):
    audit_service = AuditLoggingService(db, context)
    try:
        # Process upload...
        await audit_service.log_user_action(
            flow_id=master_flow_id,
            action="data_import_upload",
            details={
                "filename": file.filename,
                "file_size": len(file_bytes),
                "import_category": normalized_category,
                "record_count": len(records),
                "status": "success",
            },
        )
        return {"success": True}
    except Exception as exc:
        await audit_service.log_security_event(
            event_type=AuditEventType.FLOW_FAILED,
            description="Data import upload failed",
            flow_id=master_flow_id,
            details={
                "filename": file.filename,
                "import_category": normalized_category,
                "error_type": type(exc).__name__,
                "status": "failed",
            },
        )
        raise
```

**When to Audit Log:**
- File uploads/downloads
- Data imports/exports
- User authentication/authorization
- Configuration changes
- Data deletion
- Security-sensitive operations

**Reference:** PR #1046 - Qodo review comments on missing audit logs; `data_cleansing/audit_utils.py` for example implementation

### ❌ Logging Sensitive Data
**Issue:** Logs include raw user data, file contents, or sensitive identifiers that could expose PII or confidential information  
**Why:** Log files may be accessible to multiple team members or external services; Compliance violations (GDPR, HIPAA); Security breach risk  
**Example:** `logger.error("Failed to parse file: %s", file_contents)` or `logger.info("Processing user data: %s", raw_records[:10])`  
**Check:**
- Never log raw file contents or user data
- Redact PII before logging (IPs, emails, IDs)
- Use summaries: `"Processing 150 records"` not `"Processing: {raw_records}"`
- Log metadata only: filenames, counts, status codes
- Use structured logging with sanitization

**Sanitization Pattern:**
```python
# ❌ BAD: Logs sensitive data
logger.info(f"Processing records: {raw_records[:5]}")
logger.error(f"Validation failed for: {user_input}")

# ✅ GOOD: Logs metadata only
logger.info(f"Processing {len(raw_records)} records from {filename}")
logger.error("Validation failed", extra={
    "record_count": len(raw_records),
    "error_type": "missing_required_fields",
    # No raw data
})
```

**Reference:** PR #1046 - Qodo review comments on log content risk

---

## Architecture & Design

### ❌ Violating Single Responsibility Principle
**Issue:** Functions or methods trying to do too many things at once  
**Why:** Hard to test, hard to maintain, tight coupling  
**Example:** Method that queries DB, processes data, AND sends notifications  
**Check:** Each function should have one clear purpose

### ❌ Not Following Established Patterns
**Issue:** Implementing similar functionality differently than existing code  
**Why:** Inconsistency, confusion, harder for team to understand  
**Example:** New endpoint not following same structure as others  
**Check:** Review similar existing code before implementing new features

---

## Testing

### ❌ No Tests for Critical Bug Fixes
**Issue:** Fixing bugs without adding tests to prevent regression  
**Why:** Bug can resurface, no verification of fix  
**Example:** Complex logic fix without unit test  
**Check:** Add test cases that would have caught the original bug

### ❌ Not Testing Error Paths
**Issue:** Tests only cover happy path, not error scenarios  
**Why:** Production errors not caught, poor error handling goes unnoticed  
**Example:** Test doesn't verify behavior when API call fails  
**Check:** Test both success and failure scenarios

### ❌ Missing E2E Tests for New Workflows
**Issue:** New features/workflows only have unit tests, missing end-to-end user journey tests  
**Why:** Unit tests verify individual functions, but don't validate complete user workflows; Common review comment - reviewers expect E2E coverage for new features  
**Example:** Added new import type (app-discovery) with backend logic and frontend UI, but no E2E test covering the complete workflow  
**Check:**
- For new workflows/features, create E2E tests in `tests/e2e/` directory
- Test complete user journey: login → upload → processing → results
- Focus on workflow completion, not specific field values
- Follow existing E2E test patterns (see `tests/e2e/discovery/` for examples)
- Verify UI interactions and navigation work correctly

**E2E Test Pattern:**
```typescript
// ✅ GOOD: Complete workflow E2E test
test('should complete app-discovery import workflow', async ({ page }) => {
  await page.goto('/discovery/cmdb-import');
  // Upload file, verify attribute mapping, verify completion
  // Focus on workflow, not specific field values
  await expect(page.locator('[data-testid="import-complete"]')).toBeVisible();
});
```

**Reference:** PR #1046 - Multi-Type Data Import Feature (common review comment pattern)

---

## Performance Considerations

### ❌ Not Considering Scale
**Issue:** Code works for 10 items but breaks at 1000 items  
**Why:** Performance problems in production, timeout issues  
**Example:** Loading all records into memory without pagination  
**Check:** 
- Consider pagination for large datasets
- Use streaming where appropriate
- Think about N+1 queries

---

## Alembic Database Migrations

### ❌ Creating Migrations Without Checking Latest Migration in Branch
**Issue:** Creating new migration files that reference migrations that don't exist in current branch  
**Why:** Alembic fails with `KeyError: 'revision_id'` - backend won't start, deployment blocked  
**Example:** Creating migration 146 that references `145_create_help_documents_table` when migration 145 only exists in main branch, not in feature branch  
**Check - MANDATORY before creating ANY migration:**

**1. Check Latest Migration in Current Branch:**
```bash
# Find the latest numbered migration in YOUR branch
ls -1 backend/alembic/versions/*.py | xargs -I {} basename {} | grep -E "^[0-9]{3}_" | sort -V | tail -1

# Check what it references
grep "down_revision" backend/alembic/versions/144_*.py
```

**2. Merge Latest Main Branch FIRST:**
```bash
# ALWAYS merge main before creating migrations
git fetch origin main
git merge origin/main
# Resolve any conflicts
# Verify migration files from main are present
```

**3. Verify Migration Chain:**
```bash
# After merging main, check what the latest migration is
ls -1 backend/alembic/versions/*.py | xargs -I {} basename {} | grep -E "^[0-9]{3}_" | sort -V | tail -1

# Your new migration MUST reference this as down_revision
```

**4. Follow Migration Naming Standards:**
```bash
# Check existing migration naming pattern
ls -1 backend/alembic/versions/*.py | tail -5

# Pattern: {number}_{descriptive_name}.py
# Example: 146_add_additional_cmdb_fields_to_assets.py
# NOT: 146_add_serial_number_architecture_type_asset_status.py (too specific)
```

**5. Verify Migration File in Container:**
```bash
# After creating migration, rebuild backend
docker-compose -f config/docker/docker-compose.yml build backend

# Verify migration file exists in container
docker-compose -f config/docker/docker-compose.yml exec backend ls -la /app/alembic/versions/146*.py

# If file doesn't exist, container needs rebuild
```

**6. Test Backend Startup:**
```bash
# ALWAYS test backend starts after creating migration
docker-compose -f config/docker/docker-compose.yml restart backend

# Check logs for migration errors
docker-compose -f config/docker/docker-compose.yml logs backend | grep -i "migration\|alembic\|error"

# Verify backend is running
docker-compose -f config/docker/docker-compose.yml ps backend
```

**7. Verify Migration Applied:**
```bash
# Check database version
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U postgres -d migration_db -c "SELECT version_num FROM migration.alembic_version;"

# Verify new columns/objects exist
docker-compose -f config/docker/docker-compose.yml exec postgres psql -U postgres -d migration_db -c "\d migration.assets" | grep "new_column_name"
```

**Migration Creation Checklist:**
1. ✅ Merged latest main branch (`git merge origin/main`)
2. ✅ Identified latest migration in branch (`ls -1 backend/alembic/versions/*.py | sort -V | tail -1`)
3. ✅ Created migration with correct number (next sequential number)
4. ✅ Set `down_revision` to latest migration from step 2
5. ✅ Followed naming pattern (e.g., `146_add_additional_cmdb_fields_to_assets.py`)
6. ✅ Rebuilt backend container (`docker-compose build backend`)
7. ✅ Verified migration file exists in container
8. ✅ Tested backend startup (`docker-compose restart backend`)
9. ✅ Verified no migration errors in logs
10. ✅ Verified migration applied in database
11. ✅ Verified new database objects exist (columns, tables, indexes)

**Common Mistakes:**
- ❌ Creating migration before merging main → References non-existent migration
- ❌ Using wrong migration number → Conflicts with existing migrations
- ❌ Not rebuilding container → Migration file not in container, Alembic can't find it
- ❌ Not testing startup → Migration errors discovered in deployment
- ❌ Wrong `down_revision` → Breaks migration chain

**Real World Example:**
- Created migration 146 referencing `145_create_help_documents_table`
- Migration 145 only existed in main branch, not in feature branch
- Backend failed to start with `KeyError: '145_create_help_documents_table'`
- Fixed by: Merging main branch first, then updating migration 146 to reference correct down_revision

**Reference:** Migration 146 creation (Dec 2025) - Backend startup failure due to missing migration reference

### ❌ Not Following Alembic Migration Numbering Standards
**Issue:** Migration file names don't follow project standards, causing confusion and potential conflicts  
**Why:** Inconsistent naming makes it hard to track migration order, can cause merge conflicts  
**Example:** Using overly specific names like `146_add_serial_number_architecture_type_asset_status.py` instead of descriptive category name  
**Check:**
- Use descriptive category names: `146_add_additional_cmdb_fields_to_assets.py`
- Not field-by-field names: `146_add_serial_number_architecture_type_asset_status.py`
- Follow existing patterns in `backend/alembic/versions/` directory
- Check similar migrations for naming conventions

**Reference:** Migration 146 naming correction (Dec 2025)

### ❌ Not Testing Migration Before Committing
**Issue:** Committing migration files without verifying backend builds and starts correctly  
**Why:** Migration errors discovered in deployment, blocking releases  
**Check:**
- **ALWAYS** rebuild backend after creating migration
- **ALWAYS** restart backend and verify it starts
- **ALWAYS** check logs for migration errors
- **ALWAYS** verify migration applied in database
- **NEVER** commit migrations without build verification

**Reference:** Migration 146 - Backend startup failure (Dec 2025)

## Git & Version Control

### ❌ Not Pulling Latest Before Push
**Issue:** Pushing without merging latest changes from main  
**Why:** Merge conflicts, broken builds, integration issues  
**Check:** 
- `git fetch origin main`
- `git merge origin/main`
- Resolve conflicts completely
- Test after merge
- **For migrations: Merge main FIRST, then create migration**

### ❌ Unclear Commit Messages
**Issue:** Vague commit messages like "fix bug" or "update code"  
**Why:** Hard to understand what changed and why  
**Example:** "fix"  
**Check:** 
- Use conventional commits: `fix:`, `feat:`, `refactor:`
- Include bug/issue numbers
- Explain WHAT and WHY, not HOW

---

## Refactoring & Code Splitting

### ❌ Losing Functionality During Refactoring/Code Splitting
**Issue:** When splitting large files into modules or refactoring code structure, critical parameters, fields, or logic get accidentally dropped  
**Why:** Causes data loss, silent failures, broken features that worked before refactoring  
**Example:** Splitting `asset_service.py` into `deduplication/orchestration.py` and forgetting to copy 22 CMDB field parameters  
**Check - MANDATORY for ANY refactoring:**

**1. Line Count Verification:**
```bash
# Before refactoring
wc -l backend/app/services/asset_service/base.py

# After refactoring (sum of all new files)
wc -l backend/app/services/asset_service/deduplication/*.py | tail -1
# Total lines should be approximately equal (±10% for imports/headers)
```

**2. Parameter/Field Integrity Check:**
```bash
# Count critical field occurrences BEFORE refactoring
grep -c "business_unit" backend/app/services/asset_service/base.py

# Count critical field occurrences AFTER refactoring (all new files)
grep -c "business_unit" backend/app/services/asset_service/deduplication/*.py

# Numbers MUST match! Repeat for ALL critical fields.
```

**3. Function Signature Preservation:**
```bash
# Extract old function signature
grep -A 50 "def create_asset" backend/app/services/asset_service/base.py > /tmp/old_sig.txt

# Extract new function signature
grep -A 50 "def create_asset" backend/app/services/asset_service/deduplication/orchestration.py > /tmp/new_sig.txt

# Manually compare - every parameter must be present
```

**4. Behavioral Equivalence Test:**
- Before refactoring: Run existing tests and note results
- After refactoring: Tests must produce identical results
- Add integration test that exercises the refactored code path

**Cursor-Specific Verification Commands:**

Use Cursor's `codebase_search` to find ALL references:
```
Query: "Where is create_asset method called with business_unit parameter?"
Target: [] (search everywhere)
```

Use `grep` to count occurrences:
```bash
# Find all CMDB fields in old code
grep -o "business_unit\|vendor\|application_type\|lifecycle\|hosting_model" backend/app/services/asset_service/base.py | wc -l

# Find all CMDB fields in new code
grep -o "business_unit\|vendor\|application_type\|lifecycle\|hosting_model" backend/app/services/asset_service/deduplication/*.py | wc -l
```

**Git-Based Verification:**
```bash
# Compare what was removed vs what was added
git diff HEAD~1 backend/app/services/asset_service/base.py | grep "^-.*=" | wc -l  # Removed lines
git diff HEAD~1 backend/app/services/asset_service/deduplication/ | grep "^+.*=" | wc -l  # Added lines
# Should be approximately equal
```

**Real World Example of Violation:**
- PR #884 added 22 CMDB fields to `base.py:create_asset()` 
- Commit d327e56ae (Qodo Bot refactoring) moved code to `orchestration.py:create_new_asset()`
- **FORGOT to copy all 22 CMDB field parameters** → Data loss for weeks
- A simple `grep -c "business_unit"` before/after would have caught this immediately

**Reference:** PR #884 → Commit d327e56ae refactoring bug (Nov 2025)

---

## Cursor AI Assistant Best Practices

### ❌ Not Using Cursor Tools for Refactoring Verification
**Issue:** Relying on manual inspection instead of using Cursor's built-in tools to verify refactoring completeness  
**Why:** Human eyes miss things, especially in large refactorings with 500+ lines moved  
**Check - Use these Cursor tools EVERY TIME:**

**Tool 1: `codebase_search` - For Understanding Context**
```
Query: "How does AssetService.create_asset handle CMDB fields?"
Target: ["backend/app/services/asset_service"]
```
Use before AND after refactoring to verify same behavior.

**Tool 2: `grep` - For Counting Occurrences**
```bash
# Count critical patterns
grep -c "business_unit" backend/app/services/asset_service/base.py
grep -c "\.get\(\"" backend/app/services/asset_service/base.py  # Count field extractions
```

**Tool 3: `read_file` - For Comparing Implementations**
```
# Read old implementation
read_file("backend/app/services/asset_service/base.py", offset=100, limit=150)

# Read new implementation  
read_file("backend/app/services/asset_service/deduplication/orchestration.py", offset=150, limit=200)

# Manually compare side-by-side
```

**Tool 4: `run_terminal_cmd` - For Automated Verification**
```bash
# Create verification script
diff <(grep "business_unit\|vendor\|lifecycle" old_file.py | sort) \
     <(grep "business_unit\|vendor\|lifecycle" new_file.py | sort)
# Empty output = all fields present
```

**Cursor Memory System:**
- Cursor stores memories of coding patterns and decisions
- When refactoring, explicitly tell Cursor: "Remember this refactoring must preserve all 22 CMDB fields"
- Ask Cursor to verify: "Did I copy all fields from old implementation to new?"

**Pre-Refactoring Checklist (Tell Cursor):**
```
"Before I start this refactoring:
1. List all functions being moved
2. List all parameters in each function signature
3. List all fields being passed to repository/database calls
4. Store these counts - we'll verify after refactoring"
```

**Post-Refactoring Checklist (Ask Cursor):**
```
"After refactoring, verify:
1. Compare function signatures - all parameters present?
2. Compare field counts - use grep to verify
3. Compare line counts - total preserved?
4. Run tests - same results?"
```

**Reference:** Refactoring failures in commits d327e56ae, 96e79d34f (Nov 2025)

---

## 🔄 Review Checklist Template

Use this before submitting PRs:

- [ ] All imports at module top (no local imports in functions)
- [ ] Reusing existing database sessions (no new session creation mid-transaction)
- [ ] Error handling with try-catch and fallbacks
- [ ] Error messages sanitized (no `str(exc)` exposed to users)
- [ ] Error messages include actionable context
- [ ] Audit logging added for critical operations (uploads, imports, exports)
- [ ] Sensitive data not logged (no raw file contents, PII, user data)
- [ ] No magic numbers - using named constants
- [ ] Type safety - using dataclasses not SimpleNamespace
- [ ] All function signature changes verified across codebase
- [ ] Documentation created for significant fixes
- [ ] Consistent logging throughout
- [ ] Tests added for bug fixes
- [ ] Pulled and merged latest from main
- [ ] **For migrations: Merged main FIRST, then created migration**
- [ ] **For migrations: Verified latest migration in branch before creating new one**
- [ ] **For migrations: Tested backend builds and starts correctly**
- [ ] **For migrations: Verified migration file exists in container**
- [ ] **For migrations: Verified migration applied in database**
- [ ] Pre-commit checks passing
- [ ] Manual verification completed
- [ ] **Refactoring integrity verified (line counts, field counts, signature preservation)**
- [ ] **Used Cursor tools (grep, codebase_search) to verify completeness**
- [ ] **E2E tests added for new workflows/features (not just unit tests)**

---

## 📝 Contributing to This Document

**When to Add:**
- Reviewer asks for a change that represents a broader pattern
- You notice the same comment appearing in multiple PRs
- Architecture decision affects how code should be written

**How to Add:**
1. Create section with clear ❌ header
2. Include: **Issue**, **Why**, **Example**, **Check**
3. Reference the PR where it was identified
4. Keep it concise - this is a quick reference, not a tutorial

**What NOT to Add:**
- One-off specific bugs
- Complete solutions (only the pattern/issue)
- Personal preferences (only team-agreed standards)

---

**Last Updated:** December 5, 2025  
**Initial Contributors:** Ram, CryptoYogiLLC  
**Source PRs:** #581 - Discovery Flow Status Fixes, #1046 - Qodo Review Compliance, #1091 - Data Cleansing Feature, #1107 - Data Cleansing Bug Fixes, #1046 - Multi-Type Data Import Feature, Migration 146 - Alembic Migration Issues (Dec 2025)

---

## 📚 Related Resources

- [CLAUDE.md](../../CLAUDE.md) - Full development guidelines
- [Architecture Decision Records](../adr/) - Major architectural decisions
- [Code Reviews Archive](../code-reviews/) - Past review summaries

