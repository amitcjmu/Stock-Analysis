# Quick Start: Next Bug Fix Session

## TL;DR - What to Do

Run this command to start the next bug fix session:

```bash
# Read the full prompt
cat NEXT_SESSION_BUG_FIX_PROMPT.md

# Or just start with:
/fix-bugs execute
```

---

## What's Already Fixed (PR #669)

✅ Bug #668 - Collection → Assessment Transition (P0) - **FULLY FIXED**
✅ Bug #670 - Data Structure Mismatch (P1) - **FULLY FIXED**
⏳ Bug #666 - Fallback Strategy (P0) - **Phase 1 Complete** (Phase 2 needed)

**PR #669**: https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/pull/669

---

## What Needs to Be Fixed Next

### Priority Order

1. **Bug #666 Phase 2** (P0) - Enable real CrewAI agent execution
   - Wire `TenantScopedAgentPool` at 8-10 endpoint files
   - Address Qodo Bot security concerns (fail-fast validation)
   - Verify real LLM calls appear in `/finops/llm-costs`

2. **Bug #664** (P0) - Display completed analysis results
   - Frontend shows "not analyzed" even after analysis completes
   - Root cause: Polling disabled or data refresh issue

3. **Bug #663** (P1) - Progress tab blank content
   - Progress tab shows nothing during analysis
   - Need fallback UI or re-enable polling

4. **Bug #665** (P1) - Polling disabled without notification
   - No auto-refresh and no manual refresh button
   - Add HTTP polling or manual refresh option

5. **Bug #667** (P2) - SQL cartesian product warning
   - Missing JOIN condition in 6R analysis query
   - Performance issue when database scales

---

## Quick Commands

### Start Bug Fixing
```bash
# Option 1: Use automated workflow
/fix-bugs execute

# Option 2: Manual approach
git checkout -b fix/remaining-qa-bugs-batch-2
# Then use issue-triage-coordinator agent for each bug
```

### After Fixes
```bash
# Commit
git add -A
SKIP=check-file-length git commit -m "fix: Remaining QA bugs - See NEXT_SESSION_BUG_FIX_PROMPT.md"

# Create PR
git push -u origin fix/remaining-qa-bugs-batch-2
gh pr create --title "fix: Remaining QA Bugs - Assessment Flow Enhancements (Batch 2)" --label "bug"

# Update issues
for issue in 666 664 663 665 667; do
  gh issue comment $issue --body "Fixed in PR #<NUMBER>"
  gh issue edit $issue --add-label "fixed-pending-review"
done
```

---

## Key Context

- **All bugs discovered**: 2025-10-21 during comprehensive QA testing
- **QA Test Report**: `QA_TEST_REPORT_COLLECTION_FLOW_E2E.md`
- **Environment**: Docker (localhost:8081 frontend, localhost:8000 backend)
- **Multi-agent pipeline**: QA → SRE → DevSecOps → QA Validation

---

## Success Criteria

- ✅ All 5 bugs fixed and validated
- ✅ PR created with comprehensive commit message
- ✅ All issues labeled "fixed-pending-review"
- ✅ Pre-commit checks pass
- ✅ No breaking changes

---

**For full details, see**: `NEXT_SESSION_BUG_FIX_PROMPT.md`
