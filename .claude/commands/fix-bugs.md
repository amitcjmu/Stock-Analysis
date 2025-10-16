---
allowed-tools: Bash(gh:*), Task, TodoWrite, Grep, Glob, LS, Read, Edit, MultiEdit, Write, WebSearch, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_click, mcp__playwright__browser_type, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_console_messages
description: Orchestrate multi-agent bug fixing for all GitHub issues labeled 'bug'
argument-hint: [dry-run|execute] [issue-number]
---

# Automated Bug Fix Orchestrator

I'll systematically address all GitHub issues labeled as 'bug' using multi-agent orchestration.

## Configuration
- Mode: ${1:-dry-run}
- Target: ${2:-all}
- Max Issues: 10 per run
- Single PR for all fixes
- **Auto-Label**: All fixed issues labeled with "fixed-pending-review"

## Workflow Overview
1. Fetch and triage bug issues from GitHub
2. Create feature branch for batch fixes
3. Multi-agent pipeline: QA → SRE → DevSecOps → QA Validation
4. Batch commit all fixes to single PR
5. **Update issues with fix comments and apply "fixed-pending-review" label**
6. Generate final report with PR link

## Phase 1: Issue Discovery & Triage

### Fetching Bug Issues
```bash
gh issue list --label bug --state open --json number,title,body,comments,author,createdAt,updatedAt,assignees,labels
```

### Triage Criteria
Checking each issue for:
1. **Already Fixed**: "Fixed in PR", "Resolved", "Merged"
2. **In Progress**: "Working on this", "WIP", "In progress"
3. **Needs Action**: No resolution indicators in last 48 hours
4. **Skip Indicators**: "Won't fix", "Duplicate", "Cannot reproduce", "By design"

### Priority Detection
Attempting to detect priority from:
- Issue labels (P0, P1, P2, critical, high, medium, low)
- Title keywords (CRITICAL, URGENT, BREAKING)
- Body content (data loss, security, crash)
- If not found, agents will assess based on impact

## Phase 2: Create Working Branch

```bash
# Create feature branch for this bug fix session
BRANCH_NAME="fix/bug-batch-$(date +%Y%m%d-%H%M%S)"
git checkout -b $BRANCH_NAME

# Track all issues being addressed
ISSUES_IN_BATCH=()
```

## Phase 3: Multi-Agent Bug Fix Pipeline

Processing up to 10 actionable bug issues...

### For Each Bug Issue:

#### Step 1: QA Agent - Reproduction & Analysis
```
Task: qa-playwright-tester
Prompt: "
  Analyze and reproduce GitHub issue #${ISSUE_NUMBER}:
  Title: ${ISSUE_TITLE}
  Description: ${ISSUE_BODY}
  URL mentioned: ${ISSUE_URL}

  CRITICAL: You must attempt reproduction in this order:

  1. PRODUCTION REPRODUCTION (if URL provided):
     - Navigate to ${ISSUE_URL} (e.g., https://aiforce-assess.vercel.app/)
     - Follow exact reproduction steps from issue
     - Take screenshots of the bug occurring
     - Capture console errors and network failures
     - Document: Does bug still exist in production? YES/NO

  2. LOCAL DOCKER REPRODUCTION:
     - Navigate to http://localhost:8081/
     - Follow same reproduction steps
     - Access Docker logs: docker-compose logs -f backend
     - Capture detailed error messages
     - Document: Can reproduce locally? YES/NO

  3. ROOT CAUSE ANALYSIS:
     - If reproducible, identify the root cause
     - Check relevant code files
     - Review error stack traces
     - Identify affected components

  4. FIX REQUIREMENTS:
     - Define specific code changes needed
     - List files that need modification
     - Provide acceptance criteria
     - Suggest test scenarios

  5. SKIP CONDITIONS:
     - If cannot reproduce in production: Mark as 'Cannot Reproduce - Possibly Fixed'
     - If external dependency: Mark as 'External Dependency Issue'
     - If requires major refactor: Mark as 'Requires Architecture Change'

  Return structured output:
  - REPRODUCTION_STATUS: SUCCESS/FAILED/PARTIAL
  - PRODUCTION_BUG_EXISTS: YES/NO/UNKNOWN
  - LOCAL_BUG_EXISTS: YES/NO
  - ROOT_CAUSE: [detailed explanation]
  - FIX_RECOMMENDATIONS: [specific steps]
  - ACCEPTANCE_CRITERIA: [what constitutes fixed]
"
```

#### Step 2: SRE Agent - Implementation
```
Task: sre-precommit-enforcer
Prompt: "
  Implement bug fix for issue #${ISSUE_NUMBER}:

  QA Analysis:
  ${QA_ANALYSIS}

  Requirements:
  1. Implement the exact fixes recommended by QA
  2. Ensure zero breaking changes
  3. Add defensive programming where appropriate
  4. Follow existing code patterns in the codebase
  5. Add logging for future debugging
  6. Update any affected documentation

  Focus areas based on QA findings:
  - Files to modify: ${FILES_TO_MODIFY}
  - Root cause to address: ${ROOT_CAUSE}

  After implementation:
  - List all files changed
  - Describe each change made
  - Note any potential side effects
"
```

#### Step 3: DevSecOps Agent - Quality & Compliance
```
Task: devsecops-linting-engineer
Prompt: "
  Validate and prepare bug fix for issue #${ISSUE_NUMBER}:

  Changes made by SRE: ${SRE_CHANGES}

  Tasks:
  1. Run all pre-commit checks
  2. Fix any linting violations (flake8, black, mypy)
  3. Ensure no security vulnerabilities introduced
  4. Check for proper error handling
  5. Verify no sensitive data exposed

  DO NOT commit yet - changes will be batched

  Return:
  - LINTING_STATUS: PASSED/FIXED/FAILED
  - SECURITY_CHECK: PASSED/CONCERNS
  - Files ready for commit
"
```

#### Step 4: QA Validation Loop (Unlimited Iterations)
```
Task: qa-playwright-tester
Prompt: "
  Validate bug fix for issue #${ISSUE_NUMBER}:

  Original issue: ${ISSUE_DESCRIPTION}
  Changes applied: ${CHANGES_SUMMARY}

  VALIDATION STEPS:

  1. LOCAL DOCKER TESTING:
     - Navigate to http://localhost:8081/
     - Execute original reproduction steps
     - Verify bug no longer occurs
     - Check for any regressions
     - Review Docker logs for new errors

  2. COMPREHENSIVE TESTING:
     - Run available tests based on affected area:
       * Backend changes: Run tests in tests/backend/
       * Frontend changes: Run tests in tests/frontend/
       * Full stack: Run tests in tests/e2e/
     - Command: docker exec migration_backend pytest tests/[relevant_path]
     - For frontend: npx playwright test tests/e2e/[relevant_test]

  3. REGRESSION CHECK:
     - Verify related functionality still works
     - Check edge cases
     - Ensure no new errors in console/logs

  Return verdict:
  - STATUS: APPROVED/NEEDS_REVISION
  - If NEEDS_REVISION:
    * Specific issues found
    * Required changes
    * Files to re-examine
  - If APPROVED:
    * Tests passed
    * Bug confirmed fixed
    * No regressions found
"
```

#### Step 5: Iteration Handler
```
If QA returns NEEDS_REVISION:
  - Return to SRE Agent (Step 2) with QA feedback
  - Continue loop until APPROVED
  - No iteration limit - fix must be complete

If QA returns APPROVED:
  - Add issue to ISSUES_IN_BATCH
  - Move to next issue
```

## Phase 4: Batch Commit & PR Creation

After all issues processed (max 10):

### Create Single Commit
```bash
# Stage all changes
git add -A

# Create comprehensive commit message
git commit -m "fix: Resolve multiple bug issues

Issues addressed in this batch:
$(for issue in ${ISSUES_IN_BATCH[@]}; do
  echo "- #$issue: ${ISSUE_TITLES[$issue]}"
done)

Detailed changes:
$(for issue in ${ISSUES_IN_BATCH[@]}; do
  echo ""
  echo "Issue #$issue:"
  echo "${FIX_SUMMARIES[$issue]}"
done)

All fixes validated through automated QA testing."
```

### Create Pull Request
```bash
gh pr create \
  --title "fix: Bug batch fixes - $(date +%Y-%m-%d)" \
  --body "## Bug Fix Batch

This PR addresses the following bug issues:

$(for issue in ${ISSUES_IN_BATCH[@]}; do
  echo "### Issue #$issue: ${ISSUE_TITLES[$issue]}"
  echo "- **Status**: Fixed and validated"
  echo "- **Root Cause**: ${ROOT_CAUSES[$issue]}"
  echo "- **Solution**: ${SOLUTIONS[$issue]}"
  echo "- **Tests**: ${TEST_RESULTS[$issue]}"
  echo ""
done)

## Testing
- ✅ All bugs reproduced before fix
- ✅ All bugs validated as fixed
- ✅ No regressions detected
- ✅ Pre-commit checks passed

## Validation Method
Each fix was validated by:
1. Reproducing the issue locally
2. Applying the fix
3. Confirming resolution through automated testing
4. Running relevant test suites" \
  --label "bug-fix" \
  --label "automated-fix"
```

## Phase 5: Issue Updates

### For Successfully Fixed Issues
```bash
# Add comment to issue
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
- Related tests: ${TEST_RESULTS}

### Pull Request
Fixed in PR: #${PR_NUMBER}

The fix has been validated through automated testing and is ready for review."

# Apply fixed-pending-review label
gh issue edit ${ISSUE_NUMBER} --add-label "fixed-pending-review"
```

### For Issues That Couldn't Be Fixed
```bash
gh issue comment ${ISSUE_NUMBER} --body "## ⚠️ Requires Manual Intervention

### Analysis Results
${QA_ANALYSIS}

### Blocking Reason
${BLOCKING_REASON}

### Findings
${DETAILED_FINDINGS}

### Recommendation
${MANUAL_STEPS_NEEDED}

This issue requires manual review due to the complexity or external dependencies involved."
```

## Phase 6: Final Report

```
Bug Fix Session Summary
══════════════════════════

Batch ID: ${BRANCH_NAME}
Duration: ${DURATION}

Issues Processed: ${TOTAL_PROCESSED}
├── Fixed: ${FIXED_COUNT}
├── Skipped (Already Fixed): ${SKIPPED_COUNT}
├── Failed (Needs Manual): ${FAILED_COUNT}
└── In Progress (by others): ${IN_PROGRESS_COUNT}

Successfully Fixed:
${FIXED_ISSUES_LIST}

Pull Request: #${PR_NUMBER}
Branch: ${BRANCH_NAME}

Issue Labels Applied:
- All fixed issues labeled with "fixed-pending-review"
- Users can verify fixes and close issues once confirmed

Next Steps:
1. Review PR: ${PR_URL}
2. Run CI/CD pipeline
3. Merge when approved
4. Users verify fixes and close issues with "fixed-pending-review" label
```

## Safety Features

1. **Production Check First**
   - Always verify bug still exists before fixing
   - Avoid fixing already-resolved issues

2. **Local Docker Testing**
   - All fixes validated locally
   - Direct access to logs and debugging

3. **Unlimited QA Iterations**
   - Continue until properly fixed
   - No premature commits

4. **Batch Limit**
   - Maximum 10 issues per run
   - Single PR for review efficiency

5. **Test Discovery**
   - Agents determine relevant tests
   - Use available tests in /tests/

6. **Automatic Issue Labeling**
   - All fixed issues automatically labeled with "fixed-pending-review"
   - Enables users to track fixes awaiting verification
   - Label applied immediately after posting fix comment
   - Users can verify and close issues once confirmed working

## Error Handling

### Cannot Reproduce
- Skip issue with appropriate comment
- Document attempted steps
- Move to next issue

### External Dependencies
- Document dependency issue
- Skip automated fix
- Flag for manual review

### Agent Failures
- Retry once with clearer instructions
- If still fails, document and skip
- Continue with remaining issues
