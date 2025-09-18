# Multi-Agent Orchestration Patterns - 2025-09-18

## Insight 1: Parallel Agent Deployment for Complex Tasks
**Problem**: Need to coordinate multiple specialized agents for comprehensive fixes
**Solution**: Deploy agents in parallel when tasks are independent
```python
# Parallel deployment pattern
agents = [
    ("python-crewai-fastapi-expert", backend_fixes),
    ("nextjs-ui-architect", frontend_fixes),
    ("pgvector-data-architect", database_migrations)
]
# Execute simultaneously, gather results, then proceed
```
**Usage**: When fixes span multiple layers (backend/frontend/database)

## Insight 2: Agent Task Delegation with Strict Instructions
**Problem**: Agents improvising beyond plan scope causing issues
**Critical Instructions**:
```markdown
IMPORTANT: First read these files:
1. /docs/analysis/code-review/revised_schema_consolidation_plan.md
2. /docs/analysis/Notes/coding-agent-guide.md

CRITICAL: STICK TO THE PLAN. Do NOT improvise or add features not in the plan.

[Specific task details with exact line numbers and file paths]
```
**Usage**: Prevent agent hallucination and scope creep

## Insight 3: Issue Triage Before Implementation
**Problem**: Unknown scope of required changes
**Solution**: Deploy issue-triage-coordinator first
```
1. Analyze current state
2. Identify all inconsistencies
3. Catalog files needing changes
4. Create implementation plan
5. Then deploy specialized agents
```
**Usage**: For comprehensive fixes across large codebases

## Insight 4: QA Validation with Playwright
**Problem**: Need to verify fixes work end-to-end
**Solution**: Deploy qa-playwright-tester after implementation
- Test specific changed functionality
- Check for console errors
- Verify API responses use new field names
- Smoke test critical paths
**Usage**: Post-implementation validation

## Insight 5: Pre-commit Enforcement Pattern
**Problem**: Code quality issues blocking commits
**Solution**: Deploy sre-precommit-enforcer to fix:
- Boolean comparisons (`is True` vs `== True`)
- Unused imports
- Type annotations
- Formatting issues
**Note**: Some agents handle this automatically, verify after
