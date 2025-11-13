# Issue Triage Coordinator Agent Investigation Protocol

## When to Use
Use `issue-triage-coordinator` agent for comprehensive bug analysis requiring multiple investigation steps and potential coordination with other specialized agents.

## Agent Capabilities

1. **Root Cause Analysis**
   - Traces code execution paths
   - Checks database state
   - Reviews backend logs
   - Analyzes frontend behavior

2. **Multi-Hypothesis Testing**
   - Forms multiple hypotheses with confidence levels
   - Tests each systematically
   - Updates confidence based on evidence

3. **Agent Coordination**
   - Delegates to specialized agents when needed:
     - `python-crewai-fastapi-expert` for backend fixes
     - `nextjs-ui-architect` for frontend fixes
     - `devsecops-linting-engineer` for code quality

## Investigation Pattern

```typescript
// Agent follows this structure
{
  "hypotheses": [
    {
      "description": "JSONB serialization bug",
      "confidence": 40,
      "evidence": ["Model uses JSONB type", "Query returns data"],
      "result": "REJECTED - Code is correct"
    },
    {
      "description": "Background task interrupted by reload",
      "confidence": 95,
      "evidence": ["Logs show reload", "Questionnaire exists", "Phase not updated"],
      "result": "CONFIRMED - This is the root cause"
    }
  ]
}
```

## Example Usage

```bash
# Launch agent with comprehensive task
Task: issue-triage-coordinator
Prompt: "
Triage and fix issue #677: Questionnaire display shows 0/0 fields

IMPORTANT: First read:
1. /docs/analysis/Notes/coding-agent-guide.md
2. /.claude/agent_instructions.md

Your tasks:
1. Investigate root cause (check DB, logs, code)
2. Form and test hypotheses
3. Coordinate fix implementation
4. Verify solution works
5. Update GitHub issue with findings
"
```

## Anti-Hallucination Protocol

Agent uses evidence-based reasoning:

1. **Check Database State**
```bash
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT * FROM table WHERE condition;"
```

2. **Verify Code Paths**
```bash
# Use Grep/Read tools to examine actual code
# Never assume behavior without verification
```

3. **Test Hypotheses**
```bash
# For each hypothesis:
# - Collect supporting/contradicting evidence
# - Update confidence level
# - Mark as CONFIRMED/REJECTED
```

4. **Avoid Premature Conclusions**
```text
❌ BAD: "The bug is X" (without evidence)
✅ GOOD: "Hypothesis: Bug is X. Testing with evidence Y..."
```

## Investigation Output Format

```markdown
## Root Cause Analysis

### Evidence Collected
- Database: Questionnaire exists with 31 questions
- Backend logs: Task started but interrupted
- Frontend: Received empty array
- Code review: Phase transition logic exists but unreachable

### Hypotheses Tested
1. ❌ JSONB serialization (40% → REJECTED)
2. ✅ Background task interruption (95% → CONFIRMED)

### Root Cause
Background task killed by server reload before phase transition executed.

### Proposed Solution
Add defensive phase transition in query endpoint as fallback.
```

## Coordination Pattern

When agent needs specialized help:

```python
# Agent delegates to specialist
if backend_fix_needed:
    coordinate_with("python-crewai-fastapi-expert", {
        "task": "Add phase transition to queries.py",
        "file": "backend/app/api/v1/.../queries.py",
        "requirements": ["Defensive check", "Proper error handling"]
    })
```

## Success Criteria

Agent must deliver:
1. ✅ Clear root cause with evidence
2. ✅ Fix implementation (direct or coordinated)
3. ✅ Testing verification
4. ✅ Comprehensive summary for issue update

## Key Learnings

- **Evidence Over Assumptions**: Always verify with logs/DB/code
- **Multiple Hypotheses**: Form several, test systematically
- **Incremental Discovery**: Build understanding step-by-step
- **Coordinate When Needed**: Use specialist agents for implementation
- **Document Thoroughly**: Capture findings for future reference
