# Multi-Agent Orchestration Patterns

## Parallel Investigation and Fix Pattern

**Use Case**: Multiple unrelated issues need simultaneous investigation and fixes.

**Approach**: Launch agents in parallel, each focused on one issue.

**Example - Three Issues Triaged in Parallel**:
```typescript
// Single message with 3 parallel Task invocations
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator</parameter>
  <parameter name="description">Triage LLM tracking issue</parameter>
  <parameter name="prompt">Investigate why LLM calls aren't tracked...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator</parameter>
  <parameter name="description">Triage timestamp corruption</parameter>
  <parameter name="prompt">Investigate negative flow durations...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">issue-triage-coordinator</parameter>
  <parameter name="description">Triage agent health tables</parameter>
  <parameter name="prompt">Investigate empty dashboard tables...</parameter>
</invoke>
```

**Then - Parallel Implementation**:
```typescript
<invoke name="Task">
  <parameter name="subagent_type">python-crewai-fastapi-expert</parameter>
  <parameter name="description">Fix LLM tracking</parameter>
  <parameter name="prompt">Fix litellm callback registration...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">python-crewai-fastapi-expert</parameter>
  <parameter name="description">Fix timestamp corruption</parameter>
  <parameter name="prompt">Remove old timestamp copying...</parameter>
</invoke>
<invoke name="Task">
  <parameter name="subagent_type">python-crewai-fastapi-expert</parameter>
  <parameter name="description">Fix agent monitoring</parameter>
  <parameter name="prompt">Add monitoring startup...</parameter>
</invoke>
```

**Results**:
- Sequential: ~6-8 hours
- Parallel: ~2-3 hours
- Time saved: 60%

**When to Use**:
- Issues are truly independent (no code conflicts)
- Each requires deep investigation
- Time pressure to deliver fixes

---

## Delegating Pre-Commit Resolution

**Problem**: Pre-commit hooks block commit, need specialized handling.

**Pattern**:
```typescript
// Delegate to sre-precommit-enforcer
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

**Recommended**: [Your recommendation]
**Commit Message**: [Provided message]
  </parameter>
</invoke>
```

**Agent Responsibilities**:
- Analyze pre-commit failures
- Decide on best resolution approach
- Either fix violations or justify SKIP usage
- Complete the commit

---

## Delegating File Modularization

**Problem**: File exceeds 400-line limit but should be committed.

**Pattern**:
```typescript
<invoke name="Task">
  <parameter name="subagent_type">devsecops-linting-engineer</parameter>
  <parameter name="description">Modularize oversized file</parameter>
  <parameter name="prompt">
## Task: Modularize File for Line Limit Compliance

**File**: path/to/large_file.py (683 lines, limit: 400)

**Strategy**:
\`\`\`
large_file.py → large_file/
                 ├── __init__.py (exports)
                 ├── base.py (< 400 lines)
                 ├── commands.py (< 400 lines)
                 └── queries.py (< 400 lines)
\`\`\`

**Requirements**:
1. Each module < 400 lines
2. Preserve backward compatibility
3. Use absolute imports
4. All pre-commit checks pass
  </parameter>
</invoke>
```

**Agent Responsibilities**:
- Read and analyze file structure
- Split into logical, cohesive modules
- Maintain backward compatibility
- Verify all checks pass

---

## Agent Chain for Complex Tasks

**Pattern**: Sequential agent calls where each builds on previous work.

**Example - Issue Resolution Chain**:
```
1. issue-triage-coordinator → Root cause analysis
2. python-crewai-fastapi-expert → Implementation
3. qa-playwright-tester → End-to-end verification
4. sre-precommit-enforcer → Commit handling
```

**Key**: Each agent's output becomes input for next agent.

---

## When NOT to Use Parallel Agents

**Avoid parallelization when**:
- Changes touch same files (merge conflicts)
- One fix depends on another's completion
- Shared state modifications (database schema changes)

**Use sequential execution instead**.
