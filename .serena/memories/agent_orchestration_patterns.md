# Agent Orchestration Patterns for Complex Tasks

## Insight 1: Multi-Agent Analysis Before Implementation
**Problem**: Jumping into implementation without understanding full scope leads to rework
**Solution**: Use specialist agents to analyze different aspects before creating plan
**Code**:
```python
# Orchestration pattern
1. pgvector-data-architect → Database design
2. python-crewai-fastapi-expert → Backend architecture
3. nextjs-ui-architect → Frontend requirements
4. Synthesize findings → Create remedial plan
5. Get approval → Implement with agents
```
**Usage**: For complex architectural changes requiring cross-domain expertise

## Insight 2: QA Agent Browser Management
**Problem**: QA agent left 36+ Chrome tabs open, used curl instead of Playwright
**Solution**: Ensure proper browser lifecycle and use Playwright for UI testing
**Code**:
```bash
# Clean orphaned Chrome processes
pkill -f "playwright.*chrome"

# Proper browser cleanup in tests
await browser_close()  # Always call at end of test session
```
**Usage**: QA testing must use browser automation, not curl, to find UI issues

## Insight 3: Iterative Agent Workflow
**Problem**: Pre-commit violations and bugs when skipping validation
**Solution**: Develop → QA Test → Fix → Lint → Commit workflow
**Pattern**:
```
python-crewai-fastapi-expert → Implement
qa-playwright-tester → Validate
python-crewai-fastapi-expert → Fix issues
devsecops-linting-engineer → Ensure compliance
```
**Usage**: Never skip QA validation before linting/committing

## Insight 4: Evidence-Based Agent Decisions
**Problem**: Agents making assumptions about codebase structure
**Solution**: Always search and verify before claiming something doesn't exist
**Code**:
```python
# Search multiple ways before concluding
find_symbol("AssetModel")
search_for_pattern("class Asset")
Glob("**/asset*.py")
# Only after exhaustive search, conclude it doesn't exist
```
**Usage**: Agents must provide evidence for architectural decisions
