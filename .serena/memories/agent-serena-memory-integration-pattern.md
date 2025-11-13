# Agent + Serena Memory Integration Pattern

## Problem
Agents (especially issue-triage-coordinator) can propose incorrect root causes or solutions because they don't know about recent fixes, architectural changes, or proven patterns already documented in Serena memories.

## Solution
Configure agents to CHECK SERENA MEMORIES FIRST before investigation to:
1. Learn from recent similar issues
2. Understand proven fix patterns
3. Avoid repeating past mistakes
4. Leverage architectural knowledge

## Configuration

### Enhanced Agent Config (`.claude/agent_config.json`)

```json
{
  "agent_specific_overrides": {
    "issue-triage-coordinator": {
      "require_serena_memory_check": true,
      "serena_memory_integration": {
        "enabled": true,
        "check_recent_fixes": true,
        "check_similar_issues": true,
        "list_memories_first": true,
        "relevance_keywords": [
          "issue", "bug", "fix",
          "race-condition", "timing", "phase-transition",
          "questionnaire", "collection-flow"
        ]
      },
      "prepend_text_override": "
        MANDATORY STEPS:
        0. CHECK SERENA MEMORIES FIRST:
           - Use mcp__serena__list_memories to see available learnings
           - Read relevant memories (look for issue numbers, component names)
           - Check for recent fixes to similar problems
           - Learn from past root causes before forming new hypotheses

        [... rest of investigation steps ...]
      "
    }
  }
}
```

## Agent Workflow

### Step 0: Memory Check (NEW - MANDATORY)
```typescript
// Agent starts by listing memories
const memories = await mcp__serena__list_memories();

// Filter for relevant memories based on issue keywords
// e.g., issue involves "questionnaire display" →
// read "issue-677-questionnaire-display-race-condition-fix"

// Agent learns:
// - Similar issues already solved
// - Proven fix patterns
// - Recent architectural changes
// - Banned patterns to avoid
```

### Step 1-7: Standard Investigation
Continue with evidence collection, hypothesis formation, etc., but now **informed by memory learnings**.

## Example: Issue Triage with Memory

**Without Memory Check** (old behavior):
```
Agent: "Hypothesis: JSONB serialization bug"
→ Spends 20 minutes investigating
→ Discovers it's actually a timing issue
→ Wastes time on wrong root cause
```

**With Memory Check** (new behavior):
```
Agent: Lists memories → Finds "issue-677-questionnaire-display-race-condition-fix"
Agent: Reads memory → Learns about race condition pattern
Agent: "Based on memory learning, checking for timing/phase issues first"
→ Immediately targets correct root cause
→ Proposes proven defensive fix pattern
→ 5 minutes to solution
```

## Benefits

1. **Faster Diagnosis**: Leverages past learnings
2. **Accurate Root Causes**: Avoids going off on tangents
3. **Proven Solutions**: References working fix patterns
4. **Architectural Awareness**: Knows recent changes
5. **Pattern Recognition**: Identifies similar issues quickly

## Memory Naming for Agent Discoverability

Use descriptive names with keywords agents will search for:
- `issue-[NUMBER]-[component]-[problem-type]-fix`
- Include component names: `questionnaire`, `collection-flow`, `phase-transition`
- Include problem types: `race-condition`, `timing`, `serialization`

**Good Examples**:
- `issue-677-questionnaire-display-race-condition-fix`
- `multi-agent-qa-testing-with-auto-github-tagging`
- `collection-flow-phase-transition-pattern`

**Bad Examples**:
- `bug-fix-october` (too vague)
- `temp-notes` (not searchable)
- `misc-changes` (no keywords)

## Relevance Keywords by Component

**Collection Flow**:
- `collection-flow`, `questionnaire`, `gap-analysis`, `phase-transition`

**Assessment Flow**:
- `assessment`, `6r-recommendation`, `architecture-template`, `risk-analysis`

**Discovery Flow**:
- `discovery`, `cmdb`, `dependency-mapping`, `asset-inventory`

**Infrastructure**:
- `docker`, `hot-reload`, `background-task`, `async-worker`

## Usage Pattern

When creating new agents or enhancing existing ones:

1. Add `require_serena_memory_check: true` to agent config
2. Configure `serena_memory_integration` with relevant keywords
3. Update `prepend_text_override` to include memory check step
4. Document what memories the agent should reference

## Validation

Agent should log memory usage:
```
✅ Checked Serena memories
✅ Found 2 relevant memories:
   - issue-677-questionnaire-display-race-condition-fix
   - collection-flow-phase-transition-pattern
✅ Applied learnings from memories to hypothesis formation
```

## Future Enhancements

- Auto-detect relevant memories based on issue keywords
- Memory similarity scoring (vector search)
- Memory freshness weighting (recent = higher priority)
- Cross-reference memories for related patterns
