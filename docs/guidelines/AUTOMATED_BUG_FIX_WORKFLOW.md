# Automated Bug Fix Workflow Guide

This document describes the automated bug fixing workflow used by Claude Code agents via the `/fix-bugs` command.

## Overview

The automated bug fix orchestrator systematically addresses GitHub issues labeled as 'bug' using multi-agent collaboration. The workflow includes automatic issue labeling to track fixes awaiting user verification.

## Key Features

- **Multi-Agent Pipeline**: QA (Playwright) → SRE (Pre-commit) → DevSecOps (Linting) → QA Validation
- **Batch Processing**: Up to 10 bugs fixed in a single PR
- **Automatic Labeling**: All fixed issues labeled with `fixed-pending-review`
- **Unlimited Iterations**: QA validation loop continues until bug is properly fixed
- **Production Verification**: Checks if bug still exists before fixing

## Workflow Phases

### Phase 1: Issue Discovery & Triage
```bash
gh issue list --label bug --state open
```

Agents triage issues based on:
- Already fixed indicators (comments mentioning "Fixed in PR", "Resolved", "Merged")
- In-progress markers ("Working on this", "WIP")
- Skip indicators ("Won't fix", "Duplicate", "Cannot reproduce", "By design")

### Phase 2: Create Working Branch
```bash
BRANCH_NAME="fix/bug-batch-$(date +%Y%m%d-%H%M%S)"
git checkout -b $BRANCH_NAME
```

### Phase 3: Multi-Agent Bug Fix Pipeline

For each bug:

#### Step 1: QA Agent - Reproduction & Analysis
- Navigate to production URL (if provided)
- Reproduce bug locally on http://localhost:8081
- Capture screenshots, console errors, Docker logs
- Identify root cause
- Define fix requirements and acceptance criteria

#### Step 2: SRE Agent - Implementation
- Implement fixes based on QA recommendations
- Follow existing code patterns
- Add defensive programming and logging
- Zero breaking changes policy

#### Step 3: DevSecOps Agent - Quality & Compliance
- Run all pre-commit checks
- Fix linting violations (flake8, black, mypy, ESLint)
- Security vulnerability checks
- Verify error handling

#### Step 4: QA Validation Loop (Unlimited Iterations)
- Validate bug fix on http://localhost:8081
- Run relevant test suites
- Check for regressions
- Return verdict: APPROVED or NEEDS_REVISION

If NEEDS_REVISION: Return to Step 2 with feedback
If APPROVED: Add to batch and proceed

### Phase 4: Batch Commit & PR Creation

Create single commit with all fixes:
```bash
git add -A
git commit -m "fix: Resolve multiple bug issues

Issues addressed in this batch:
- #588: Data validation page 404 error
- #590: ADR-027 test failures
- #591: Collection test timeout
..."

gh pr create --title "fix: Bug batch fixes - $(date +%Y-%m-%d)"
```

### Phase 5: Issue Updates & Automatic Labeling

**For Successfully Fixed Issues:**

```bash
# Add fix comment
gh issue comment ${ISSUE_NUMBER} --body "## ✅ Issue Fixed

### Resolution Summary
${FIX_SUMMARY}

### Root Cause
${ROOT_CAUSE}

### Changes Made
${CHANGES_LIST}

### Validation
- Bug reproduced locally: Yes
- Fix applied and tested: Yes
- Regression tests: Passed

### Pull Request
Fixed in PR: #${PR_NUMBER}"

# ✅ AUTOMATIC LABELING
gh issue edit ${ISSUE_NUMBER} --add-label "fixed-pending-review"
```

**Why Automatic Labeling?**
- Enables users to quickly identify which bugs have fixes pending verification
- Provides clear workflow: `bug` → `fixed-pending-review` → closed
- Users can filter issues: `label:fixed-pending-review` to find fixes ready for testing
- Once user verifies the fix works, they can close the issue

### Phase 6: Final Report

```
Bug Fix Session Summary
══════════════════════════

Batch ID: fix/bug-batch-20251015-083144
Duration: 45 minutes

Issues Processed: 9
├── Fixed: 8
├── Skipped (Already Fixed): 1
├── Failed (Needs Manual): 0
└── In Progress (by others): 0

Successfully Fixed:
- #588: Data validation page 404 error
- #590: ADR-027 test failures
- #591: Collection test timeout
- #579: Progress % mismatch
- #561: View button inconsistency
- #582: Deduplication message not appearing
- #575: Continue flow timeout errors
- #576: Monitor flow timeout errors

Pull Request: #595
Branch: fix/bug-batch-20251015-083144

Issue Labels Applied:
- All 8 fixed issues labeled with "fixed-pending-review"
- Users can verify fixes and close issues once confirmed

Next Steps:
1. Review PR: https://github.com/.../pull/595
2. Run CI/CD pipeline
3. Merge when approved
4. Users verify fixes and close issues with "fixed-pending-review" label
```

## Safety Features

1. **Production Check First**: Verify bug still exists before fixing
2. **Local Docker Testing**: All fixes validated locally with logs access
3. **Unlimited QA Iterations**: Continue until properly fixed
4. **Batch Limit**: Maximum 10 issues per run for manageable PR review
5. **Test Discovery**: Agents determine and run relevant tests
6. **Automatic Issue Labeling**: Fixed issues labeled for user verification tracking

## Issue Label Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ GitHub Issue Created                                         │
│ Label: bug                                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ /fix-bugs Command Triggered                                  │
│ - QA reproduces bug                                          │
│ - SRE implements fix                                         │
│ - DevSecOps validates quality                                │
│ - QA confirms fix works                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ Fix Committed & PR Created                                   │
│ - Comment added to issue with fix details                    │
│ - Label AUTOMATICALLY ADDED: "fixed-pending-review"          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ PR Merged to Main                                            │
│ Labels: bug, fixed-pending-review                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ User Verifies Fix                                            │
│ - Tests in production/staging                                │
│ - Confirms bug no longer occurs                              │
│ - Closes issue if satisfied                                  │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Fix All Open Bugs (Dry Run)
```bash
/fix-bugs dry-run
```

### Fix All Open Bugs (Execute)
```bash
/fix-bugs execute
```

### Fix Specific Bug
```bash
/fix-bugs execute 588
```

### Find Issues Awaiting Verification
```bash
gh issue list --label fixed-pending-review --state open
```

## Error Handling

### Cannot Reproduce
- Skip issue with appropriate comment
- Document attempted reproduction steps
- Move to next issue
- **No label applied**

### External Dependencies
- Document dependency issue
- Skip automated fix
- Flag for manual review
- **No label applied**

### Agent Failures
- Retry once with clearer instructions
- If still fails, document and skip
- Continue with remaining issues
- **No label applied**

## For Future CC Agents

When working on the `/fix-bugs` command, ensure you:

1. ✅ Follow the complete workflow including automatic labeling
2. ✅ Apply `fixed-pending-review` label to ALL successfully fixed issues
3. ✅ Add detailed fix comment before applying label
4. ✅ Include labeling status in final report
5. ✅ Only label issues that were actually fixed and validated
6. ❌ DO NOT label issues that couldn't be reproduced
7. ❌ DO NOT label issues requiring manual intervention
8. ❌ DO NOT close issues automatically - let users verify first

## Configuration

The label `fixed-pending-review` should exist in the GitHub repository with:
- **Name**: `fixed-pending-review`
- **Description**: "Bug fixed and awaiting user verification"
- **Color**: Green (#28a745)

Check if label exists:
```bash
gh label list --search "fixed-pending-review"
```

Create label if missing:
```bash
gh label create "fixed-pending-review" \
  --description "Bug fixed and awaiting user verification" \
  --color "28a745"
```

## References

- Local command: `.claude/commands/fix-bugs.md` (gitignored)
- QA Agent: `.claude/agents/qa-playwright-tester.md`
- SRE Agent: `.claude/agents/sre-precommit-enforcer.md`
- DevSecOps Agent: `.claude/agents/devsecops-linting-engineer.md`

## Changelog

- **2025-01-15**: Added automatic `fixed-pending-review` labeling to workflow
- **2024-10-15**: Initial workflow documentation

---

**Note**: This workflow is designed to be executed by Claude Code agents. Human developers can also follow this pattern for manual bug fixes to maintain consistency.
