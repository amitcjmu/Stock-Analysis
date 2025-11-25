# Cursor AI Agent PR Workflow - Git Push & Code Review Process

> **Purpose:** This guide defines the standard workflow for Cursor AI agents when pushing code and managing PRs.
> **Scope:** Git push process, code review checks, testing, and repository document updates.
> **Note:** This is specific to Cursor AI agents (coding assistants), not CrewAI agents or other system agents.

## 📊 Simple Workflow Overview

### 🔵 Step 1: Before Pushing Code

```
1. Code Review Check
   ↓
2. Sync with Main
   ↓
3. Push Code ✓
```

### 🟢 Step 2: Before PR Review

```
1. Run Tests
   ↓
2. Update PR Description
   ↓
3. Request Review ✓
```

### 🟡 Step 3: After PR Comments

```
1. Address Comments
   ↓
2. Update Repository Docs (if pattern found)
   ↓
3. Next Push (cycle continues)
```

---

### Quick Reference

**When you say "Push Code":**
- ✅ Code review check → Sync with main → Push

**When you say "Ready for Review":**
- ✅ Run tests → Update PR → Request review

**After PR comments:**
- ✅ Fix issues → Update docs → Next push

---

## ⚠️ MANDATORY WORKFLOW FOR CURSOR AI AGENTS

### 1. Sync Main Before Push (MANDATORY)

**BEFORE ANY `git push` operation, ALWAYS sync the branch with latest `origin/main` first.**

This is part of the standard process and prevents merge conflicts in PRs. This requirement applies to ALL code pushes, regardless of user prompt phrasing.

### 2. Update Repository Documents (MANDATORY)

**WHEN ADDRESSING PR REVIEW COMMENTS, ALWAYS update repository documents if comments represent generalizable patterns.**

This ensures repository documents stay current and continuously improve. Update code review or testing repositories with new patterns as they're discovered.

### 3. Run Tests Before PR Review (REQUIRED)

**BEFORE REQUESTING MANUAL PR REVIEW, ALWAYS explicitly prompt to run tests.**

This ensures code quality before review and is typically done toward the end of PR when code is ready for review.

## Required Implementation

### Standard Process (MANDATORY)

When user requests to push code:

1. **Review code against common patterns (RECOMMENDED):**
   ```bash
   ./scripts/pre-commit-code-review-check.sh
   ```
   - Checks changed files against patterns in code review repository
   - Helps catch common issues before PR review
   - Reference: `docs/code-reviews/review-comments-repository.md`

2. **ALWAYS run sync script:**
   ```bash
   ./scripts/sync-with-main.sh
   ```

3. **Handle conflicts if they occur:**
   - Resolve conflicts in affected files
   - Stage resolved files: `git add <files>`
   - Continue rebase: `git rebase --continue`
   - Re-run sync to verify: `./scripts/sync-with-main.sh`

4. **Only after successful sync, then push:**
   ```bash
   git push origin <branch-name>
   ```

**Or use combined command:**
```bash
./scripts/sync-with-main.sh --push
```

## Never Skip This Step

- ❌ **NEVER** do `git push` without syncing first
- ❌ **NEVER** skip even if user says "just push"
- ❌ **NEVER** assume branch is up to date
- ✅ **ALWAYS** verify with sync script first

## User Prompts (No Special Keywords Needed)

### When User Says "Push Code":
**You automatically:**
1. ✅ Review code against common patterns (`pre-commit-code-review-check.sh`)
2. ✅ Reference code review repository for patterns
3. ✅ Check if branch is behind main
4. ✅ Run `./scripts/sync-with-main.sh` if needed
5. ✅ Handle any conflicts
6. ✅ Verify sync succeeded
7. ✅ Then push

**After addressing PR review comments:**
8. ✅ **Update repository documents** if comment represents a pattern
9. ✅ Add pattern to code review or testing repository
10. ✅ Include PR reference in pattern documentation
11. ✅ Verify documents are updated before next push

### When User Says "Ready for Review" or "PR Ready":
**You MUST explicitly prompt to run tests:**
1. ✅ **Prompt**: "Before PR review, should I run tests? Run `./scripts/run-pr-tests.sh`"
2. ✅ Run tests if user confirms: `./scripts/run-pr-tests.sh`
3. ✅ Reference testing repository: `docs/testing/testing-strategy.md`, `docs/testing/QA_GUIDE.md`
4. ✅ Review test results and report pass/fail status
5. ✅ Update PR description with test results if requested

### When Addressing PR Review Comments:
**You MUST update repository documents:**
1. ✅ **Identify patterns**: Check if comment represents a generalizable pattern
2. ✅ **Determine repository**: Code review vs testing repository
3. ✅ **Add pattern**: Update appropriate repository document with proper format
4. ✅ **Include reference**: Add PR # to pattern documentation
5. ✅ **Verify update**: Check that document is updated before next push

**This ensures repository documents stay current and improve continuously.**

### Explicit Test Prompting:

**ALWAYS explicitly prompt when:**
- User says "ready for review" or "pr ready"
- User asks to update PR description
- Toward the end of PR when code is complete
- Before requesting manual code review

**Example prompt:**
```
🧪 PR Testing Required

Before requesting manual code review, tests should be run.

Should I run the PR-ready tests now?
Run: ./scripts/run-pr-tests.sh

This will:
- Run smoke + unit tests
- Verify code quality
- Generate test reports
- Reference testing repository guidelines

Reference: docs/testing/testing-strategy.md, docs/testing/QA_GUIDE.md
```

## Repository Document Updates (Continuous Improvement)

### Responsibility to Keep Documents Updated

**MANDATORY:** When addressing PR review comments, update repository documents if comments represent generalizable patterns.

### When to Update Code Review Repository

Add to `docs/code-reviews/review-comments-repository.md` if:
- Comment represents a pattern that could apply to other code
- Same issue appears in multiple PRs
- Architecture decision affects how code should be written
- Pattern would help avoid future issues

**Format to add:**
```markdown
## [Category]

### ❌ [Pattern Name]
**Issue:** [What's wrong]
**Why:** [Why this matters]
**Example:** [Code example showing the issue]
**Check:** [How to verify the pattern]

**Reference:** PR #XXX
```

### When to Update Testing Repository

Add to `docs/testing/testing-strategy.md` or `docs/testing/QA_GUIDE.md` if:
- Comment is about testing patterns or issues
- New test pattern discovered
- Testing approach needs documentation
- Test-related feedback from reviews

### Update Process

**After addressing review comment:**
1. Identify if comment represents a pattern
2. Determine which repository it belongs to (code review vs testing)
3. Add pattern with proper format
4. Include PR reference
5. Verify document is updated

**Check status:**
```bash
./scripts/update-repository-docs.sh
```

**Fetch PR comments:**
```bash
./scripts/update-repository-docs.sh --pr <number>
```

**Manual entry:**
```bash
./scripts/update-repository-docs.sh --review
```

### Continuous Improvement

- ✅ Update documents as you address review comments (don't defer)
- ✅ Keep patterns current with latest review feedback
- ✅ Reference PRs so patterns are traceable
- ✅ Use documents with each PR code push

**This ensures repository documents are always current and improve continuously.**

## Script Location

- **Sync Script**: `scripts/sync-with-main.sh`
- **Test Script**: `scripts/run-pr-tests.sh`
- **Code Review Check**: `scripts/pre-commit-code-reviews-check.sh`
- **Repository Update**: `scripts/update-repository-docs.sh`
- **Documentation**: `scripts/README.md`
- **Features**:
  - Auto-stashes uncommitted changes
  - Rebases onto origin/main
  - Restores stashed changes
  - Provides clear status messages
  - Handles conflicts gracefully

## Why This Matters

- **Prevents merge conflicts** in PRs
- **Keeps PRs clean** (no "merge main into feature" commits)
- **Ensures code is always based on latest main**
- **Required workflow** - not optional
- **Both automation (script) AND AI awareness (memory) work together**

## Standard Process Checklist

### Before Pushing Code (Initial Commit):
- [ ] **Review code against common patterns**: `./scripts/pre-commit-code-review-check.sh`
- [ ] **Reference code review repository**: Check `docs/code-reviews/review-comments-repository.md`
- [ ] Run `./scripts/sync-with-main.sh` (or `--push` flag)
- [ ] Verify sync succeeded (exit code 0)
- [ ] Handle conflicts if any (resolve, stage, continue rebase)
- [ ] Run pre-commit checks (if needed)
- [ ] Build/verify code works
- [ ] Push code

**Steps 1-2 (code review check) help catch issues early.**
**Step 3 (sync) is MANDATORY and cannot be skipped.**

### Before PR Review (Toward End of PR):
- [ ] **Run PR-ready tests**: `./scripts/run-pr-tests.sh`
- [ ] **Reference testing repository**: Check `docs/testing/testing-strategy.md`, `docs/testing/QA_GUIDE.md`
- [ ] Review test results and fix any failures
- [ ] Update PR description with test results
- [ ] **Ready for manual code review**

**Step 1 (tests) is REQUIRED before requesting manual review.**
**This is typically done toward the end of PR when code is ready for review.**

### After Addressing PR Review Comments (Continuous Updates):
- [ ] **Review PR comments for patterns**: Check if comments represent generalizable patterns
- [ ] **Update code review repository**: Add new patterns to `docs/code-reviews/review-comments-repository.md`
- [ ] **Update testing repository**: Add new testing patterns to `docs/testing/testing-strategy.md` or `docs/testing/QA_GUIDE.md`
- [ ] **Document patterns**: Include Issue, Why, Example, Check, Reference PR #
- [ ] **Verify updates**: Run `./scripts/update-repository-docs.sh` to check status

**This ensures repository documents stay current and continuously improve.**
**Patterns should be added as they're addressed, not deferred to later.**

## Fallback (if script unavailable)

If script has issues, manually sync:
```bash
git fetch origin main
git pull origin main --rebase
# Resolve conflicts if any
git add <resolved-files>
git rebase --continue
git push origin <branch-name>
```

But **prefer the script** - it handles edge cases better.

---

**This requirement is documented in:**
- `scripts/README.md` - Usage documentation
- `docs/guidelines/DEVELOPER_WORKFLOW_GUIDE.md` - Updated workflow guide
- This file - Agent requirement reference
