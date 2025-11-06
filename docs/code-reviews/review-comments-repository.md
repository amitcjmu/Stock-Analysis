# Code Review Comments Repository

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

---

## Type Safety & Code Quality

### ❌ Using SimpleNamespace or Dict Instead of Proper Types
**Issue:** Bypassing type system with `SimpleNamespace` or plain dicts for structured data  
**Why:** No type checking, no IDE autocomplete, harder to maintain, runtime errors  
**Example:** `result = SimpleNamespace(field1=..., field2=...)`  
**Check:** Use `@dataclass` or proper class definitions for structured data

**Reference:** PR #581 - flow_processing_converters.py lines 74-80

### ❌ Magic Numbers
**Issue:** Hardcoded numbers in calculations without context (e.g., `/ 6`, `* 100`)  
**Why:** Unclear meaning, hard to update if value changes, poor maintainability  
**Example:** `progress = round((completed / 6) * 100, 1)`  
**Check:** 
- Define named constants at module level
- Use descriptive names: `TOTAL_DISCOVERY_PHASES = 6`
- Add comments explaining the constant

**Reference:** PR #581 - operations.py lines 303, 388

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

## Git & Version Control

### ❌ Not Pulling Latest Before Push
**Issue:** Pushing without merging latest changes from main  
**Why:** Merge conflicts, broken builds, integration issues  
**Check:** 
- `git fetch origin main`
- `git merge origin/main`
- Resolve conflicts completely
- Test after merge

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
- [ ] No magic numbers - using named constants
- [ ] Type safety - using dataclasses not SimpleNamespace
- [ ] All function signature changes verified across codebase
- [ ] Documentation created for significant fixes
- [ ] Consistent logging throughout
- [ ] Tests added for bug fixes
- [ ] Pulled and merged latest from main
- [ ] Pre-commit checks passing
- [ ] Manual verification completed
- [ ] **Refactoring integrity verified (line counts, field counts, signature preservation)**
- [ ] **Used Cursor tools (grep, codebase_search) to verify completeness**

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

**Last Updated:** October 14, 2025  
**Initial Contributors:** Ram, CryptoYogiLLC  
**Source PR:** #581 - Discovery Flow Status Fixes

---

## 📚 Related Resources

- [CLAUDE.md](../../CLAUDE.md) - Full development guidelines
- [Architecture Decision Records](../adr/) - Major architectural decisions
- [Code Reviews Archive](../code-reviews/) - Past review summaries

