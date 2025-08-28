# Multi-Agent Orchestration Patterns

## Effective Agent Usage Strategy

### Agent Selection Criteria
```python
# Choose agents based on domain expertise:
devsecops-linting-engineer: Code quality, linting, security analysis
sre-precommit-enforcer: Pre-commit failures, systematic fixes
python-crewai-fastapi-expert: Backend implementation, API design
nextjs-ui-architect: Frontend components, React patterns
qa-playwright-tester: E2E testing, UI validation
pgvector-data-architect: Database schema, vector operations
```

### Orchestration Pattern
```python
# 1. Discovery Phase - Use DevSecOps agent
Task: "Analyze the codebase to understand current implementation"
Output: Detailed analysis of existing patterns, issues, gaps

# 2. Implementation Phase - Use domain experts
Task: "Implement [specific feature] following discovered patterns"
Output: Working code with proper integration

# 3. Testing Phase - Use QA agent
Task: "Test the implementation with real scenarios"
Output: Test results, screenshots, validation report

# 4. Cleanup Phase - Use SRE agent
Task: "Fix all pre-commit failures systematically"
Output: Clean, committable code
```

### Parallel Agent Execution
```python
# Run multiple agents concurrently for independent tasks:
agents = [
    Task("Analyze backend", "devsecops-linting-engineer"),
    Task("Check frontend", "nextjs-ui-architect"),
    Task("Review database", "pgvector-data-architect")
]
# Results synthesized after parallel execution
```

### Agent Communication Pattern
```python
# Pass context between agents:
discovery_result = await devsecops_agent.analyze()
implementation_spec = {
    "findings": discovery_result.issues,
    "patterns": discovery_result.patterns,
    "requirements": user_requirements
}
implementation = await python_expert.implement(implementation_spec)
```

### Success Metrics
- Discovery agents find root causes, not symptoms
- Implementation agents follow existing patterns
- Testing agents provide concrete evidence
- Cleanup agents fix without shortcuts

## Real Example: Field Mapping Intelligence
1. DevSecOps discovered placeholder returning 0.5 confidence
2. SRE implemented real IntelligentMappingEngine
3. Python expert created learning service
4. NextJS architect built UI components
5. QA validated with Playwright
6. SRE fixed all pre-commit issues

## Common Pitfalls Avoided
- Don't use agents for simple tasks (use direct tools)
- Don't skip discovery phase
- Don't ignore agent findings
- Always validate with QA agent
- Always cleanup with SRE agent
