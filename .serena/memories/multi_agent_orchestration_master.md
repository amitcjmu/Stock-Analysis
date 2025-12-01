# Multi-Agent Orchestration Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 12 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Parallel Execution**: Backend + Frontend agents CAN run simultaneously
> 2. **Sequential Dependencies**: QA → SRE → DevSecOps → QA for validation chain
> 3. **Triage First**: 57% of bugs don't need fixes (already resolved/invalid)
> 4. **Agent Instructions**: Always include CLAUDE.md + agent_instructions.md reads
> 5. **Batch PRs**: Multiple bug fixes → single PR with individual commits

---

## Table of Contents

1. [Overview](#overview)
2. [Execution Patterns](#execution-patterns)
3. [Bug Fix Workflow](#bug-fix-workflow)
4. [Agent Capabilities](#agent-capabilities)
5. [GitHub Integration](#github-integration)
6. [Anti-Patterns](#anti-patterns)
7. [Code Templates](#code-templates)
8. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Patterns for orchestrating multiple Claude Code subagents (qa-playwright-tester, python-crewai-fastapi-expert, sre-precommit-enforcer, etc.) for complex features and bug fixing workflows.

### When to Reference
- Implementing multi-file features (backend + frontend)
- Orchestrating parallel agent execution
- Setting up bug fix automation pipelines
- Optimizing agent efficiency

### Key Subagents
- `python-crewai-fastapi-expert`: Backend implementation
- `nextjs-ui-architect`: Frontend implementation
- `qa-playwright-tester`: E2E testing and validation
- `sre-precommit-enforcer`: Code quality enforcement
- `devsecops-linting-engineer`: Security and compliance
- `issue-triage-coordinator`: Bug investigation

---

## Execution Patterns

### Pattern 1: Parallel Agent Execution

**When to use**: Backend and frontend changes that don't depend on each other.

```typescript
// Single message with multiple Task invocations
<invoke name="Task">
  <parameter name="subagent_type">python-crewai-fastapi-expert</parameter>
  <parameter name="description">Implement backend API</parameter>
  <parameter name="prompt">Create API endpoints for feature X...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">nextjs-ui-architect</parameter>
  <parameter name="description">Implement frontend UI</parameter>
  <parameter name="prompt">Create React components for feature X...</parameter>
</invoke>
```

**Results**:
- Sequential: ~6-8 hours
- Parallel: ~2-3 hours
- Time saved: 50-60%

**When NOT to parallelize**:
- Changes touch same files (merge conflicts)
- One fix depends on another
- Shared database schema changes

---

### Pattern 2: Sequential Agent Chain

**When to use**: Validation requires previous work completion.

```
issue-triage-coordinator → Root cause analysis
         ↓
python-crewai-fastapi-expert → Implementation
         ↓
qa-playwright-tester → E2E verification
         ↓
sre-precommit-enforcer → Commit handling
```

**Critical rule**: Each agent's output becomes input for next agent.

---

### Pattern 3: QA Validation Loop

**Standard validation pipeline**:

```
QA Reproduction → SRE Fix → DevSecOps Validate → QA Approve
       ↑                                              ↓
       └────────── NEEDS_REVISION ←─────────────────────┘
```

**Agent responsibilities**:
1. QA: Reproduce bug, capture evidence
2. SRE: Implement fix
3. DevSecOps: Validate code quality
4. QA: Final approval

---

## Bug Fix Workflow

### Pattern 4: Triage Before Fixing (Critical)

**Finding**: 57% of bugs don't need new code.

```bash
# Check if issue already fixed
gh issue view <number> --json body,comments,labels

# Look for fix indicators
grep -i "fixed\|resolved\|merged" comments

# Verify in codebase
git log --grep="issue #<number>" --oneline
```

**Skip conditions**:
- Already fixed in prior commits
- Invalid/empty template
- Cannot reproduce locally
- Working as designed (check Serena memories)

---

### Pattern 5: QA Agent Reproduction Protocol

**CRITICAL**: Always reproduce before coding.

```typescript
Task: qa-playwright-tester
Prompt: "
  CRITICAL REPRODUCTION REQUIREMENTS:
  1. LOCAL DOCKER REPRODUCTION: Navigate to URL, capture screenshots
  2. DATABASE VERIFICATION: Check actual data state
  3. ROOT CAUSE ANALYSIS: Identify exact code causing issue
  4. FIX REQUIREMENTS: List specific changes needed
  5. SKIP CONDITIONS: When to mark as 'Cannot Reproduce'

  Return:
  - REPRODUCTION_STATUS: SUCCESS/FAILED/PARTIAL
  - LOCAL_BUG_EXISTS: YES/NO
  - ROOT_CAUSE: [file paths + line numbers]
  - FIX_RECOMMENDATIONS: [specific code changes]
"
```

---

### Pattern 6: Batch Commits, Single PR

**Problem**: One PR per bug creates noise.

```bash
# Create timestamped feature branch
BRANCH="fix/bug-batch-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BRANCH"

# Fix multiple bugs, commit individually
git add <files_for_bug_927>
git commit -m "fix: Bug #927 description"

git add <files_for_bugs_875_876>
git commit -m "fix: Bugs #875, #876 description"

# Single PR covering all fixes
git push -u origin "$BRANCH"
gh pr create --title "fix: Bug batch - Nov 2025"
```

---

## Agent Capabilities

### Agent Prompt Template

```markdown
IMPORTANT: First read these files:
1. /docs/analysis/Notes/coding-agent-guide.md
2. /.claude/agent_instructions.md

After completing your task, provide a detailed summary following
the template in agent_instructions.md, not just "Done".
Include: what was requested, what was accomplished, technical details,
and verification steps.
```

### Agent Specializations

| Agent | Specialty | Files Created/Modified |
|-------|-----------|----------------------|
| python-crewai-fastapi-expert | Backend | Services, endpoints, migrations |
| nextjs-ui-architect | Frontend | Components, hooks, API methods |
| qa-playwright-tester | Testing | Finds bugs, validates fixes |
| sre-precommit-enforcer | Quality | Runs checks, fixes violations |
| devsecops-linting-engineer | Security | Code quality, compliance |

---

## GitHub Integration

### Pattern 7: Automatic Project Tagging

**For each bug issue created**:

```bash
# 1. Assign and set milestone
gh issue edit $ISSUE_NUMBER --add-assignee CryptoYogiLLC
gh issue edit $ISSUE_NUMBER --milestone "Collection Flow Ready"

# 2. Add to project
gh project item-add 2 --owner CryptoYogiLLC --url "https://github/.../issues/$ISSUE_NUMBER"

# 3. Tag project fields via GraphQL
gh api graphql -f query='
mutation {
  team: updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_..."
    itemId: "'$ITEM_ID'"
    fieldId: "PVTSSF_..."
    value: { singleSelectOptionId: "..." }
  }) { projectV2Item { id } }
}'
```

### Priority Mapping

| Severity Label | Priority |
|---------------|----------|
| critical/high | P0 |
| medium | P1 |
| low | P2 |

### Issue Update Pattern

```bash
gh issue comment <number> --body "
## ✅ Issue Fixed

### Resolution Summary
[One-line what was fixed]

### Root Cause
[File:line where problem was]

### Changes Made
[Bullet list of files + what changed]

### Validation
- ✅ [What was tested]
- ✅ [Pass criteria]

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"

gh issue edit <number> --add-label "fixed-pending-review"
```

---

## Anti-Patterns

### Don't: Fix First, Validate Later

```
❌ WRONG: Bug title → Implement fix → Hope it works
✅ RIGHT: QA reproduction → SRE fix → DevSecOps validate → QA approve
```

### Don't: Create PR Per Bug

```
❌ WRONG: 7 bugs = 7 PRs (too much noise)
✅ RIGHT: 7 bugs = 1 PR with 7 commits
```

### Don't: Assume Bug Based on Title

```
❌ WRONG: "Field missing" → Add field
✅ RIGHT: Check Serena memories → Reproduce → Analyze → Fix
```

### Don't: Skip Pre-Commit Checks

```
❌ WRONG: git commit --no-verify
✅ RIGHT: Let formatters run → Add changes → Re-commit
```

### Don't: Overlap Agent Scopes

```
❌ WRONG: Both agents modify same file
✅ RIGHT: Clear scope boundaries per agent
```

---

## Code Templates

### Template 1: Parallel Investigation

```typescript
// Triage 3 issues simultaneously
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator</parameter>
  <parameter name="description">Triage issue A</parameter>
  <parameter name="prompt">Investigate...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator</parameter>
  <parameter name="description">Triage issue B</parameter>
  <parameter name="prompt">Investigate...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator</parameter>
  <parameter name="description">Triage issue C</parameter>
  <parameter name="prompt">Investigate...</parameter>
</invoke>
```

### Template 2: Feature Implementation Pipeline

```
1. Backend + Frontend (parallel)
   python-crewai-fastapi-expert + nextjs-ui-architect

2. QA Testing (sequential)
   qa-playwright-tester

3. Code Quality (sequential)
   sre-precommit-enforcer → devsecops-linting-engineer
```

### Template 3: Pre-Commit Delegation

```typescript
<invoke name="Task">
  <parameter name="subagent_type">sre-precommit-enforcer</parameter>
  <parameter name="description">Handle pre-commit violations</parameter>
  <parameter name="prompt">
## Task: Resolve Pre-Commit Violations

**Context**: Commit blocked by:
1. File length violation: file.py (683 lines > 400 limit)
2. Black formatting (auto-fixed)

**Options**:
- A: Exclude oversized file from this commit
- B: Modularize file if trivial
- C: Use SKIP if violations unrelated to changes

**Commit Message**: [Provided message]
  </parameter>
</invoke>
```

---

## Metrics (Example Session)

**Bug Batch Session**:
- Issues Processed: 7 (3 fixed, 4 closed)
- Agent Executions: 12
- Agent Failures: 0
- Validation Pass Rate: 100%

**Time Allocation**:
- Triage: 30% (saved 4 unnecessary implementations)
- Implementation: 30%
- Validation: 30%
- Documentation: 10%

**Key Insight**: Triage efficiency prevents 57% wasted effort.

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `multi-agent-orchestration-patterns` | 2025-11 | Core patterns |
| `automated_bug_fix_multi_agent_workflow_2025_11` | 2025-11 | Bug fix pipeline |
| `multi-agent-orchestration-parallel-execution-pattern-2025-11` | 2025-11 | Parallel execution |
| `multi-agent-qa-testing-with-auto-github-tagging` | 2025-11 | GitHub integration |
| `multi_agent_bug_fixing_orchestration` | 2025-11 | Bug orchestration |
| `multi_agent_orchestration` | 2025-10 | General orchestration |
| `multi_agent_orchestration_patterns` | 2025-10 | Pattern overview |
| `multi_agent_workflow_patterns` | 2025-10 | Workflow patterns |
| `automated_bug_fix_workflow_multi_agent` | 2025-11 | Automation |
| `agent_orchestration_best_practices` | 2025-10 | Best practices |
| `agent_orchestration_patterns` | 2025-10 | Agent patterns |
| `agent_coordination_patterns_batch4` | 2025-10 | Coordination |

**Archive Location**: `.serena/archive/multi_agent/`

---

## Search Keywords

multi_agent, orchestration, parallel, sequential, qa_agent, bug_fix, triage, github, automation
