# Agent Orchestration Best Practices [2025-01-18]

## Insight 1: Multi-Agent Task Distribution
**Problem**: Complex tasks require coordinated agent work
**Solution**: Use specialized agents concurrently for different aspects
**Example Session**:
```python
# Modularization + Security + Linting in parallel
agents_used = [
    "python-crewai-fastapi-expert",  # Modularization
    "sre-precommit-enforcer",        # Pre-commit compliance
    "devsecops-linting-engineer"     # Security fixes
]
```
**Result**: 3 agents completed all PR fixes systematically

## Insight 2: Agent Instruction Template
**Problem**: Agents need consistent instructions
**Solution**: Always include required reading and summary format
**Template**:
```
IMPORTANT: First read these files:
1. /docs/analysis/Notes/coding-agent-guide.md
2. /.claude/agent_instructions.md

[Specific task details]

After completing, provide detailed summary following template in agent_instructions.md.
Include: what was requested, accomplished, technical details, verification steps.
```
**Usage**: Every agent invocation

## Insight 3: Pre-commit Fix Priority
**Problem**: Multiple pre-commit failures block commits
**Fix Order**:
1. Security issues (bandit, secrets)
2. File length violations (>400 lines)
3. Unused imports (flake8 F401)
4. Formatting (black)
5. Type checking (mypy)
**Usage**: Address in this order for efficiency

## Insight 4: Agent Selection Criteria
**Problem**: Choosing wrong agent for task
**Quick Reference**:
- File modularization → python-crewai-fastapi-expert
- Pre-commit failures → sre-precommit-enforcer
- Security/linting → devsecops-linting-engineer
- Issue investigation → issue-triage-coordinator
- UI/frontend → nextjs-ui-architect
- Database/pgvector → pgvector-data-architect
**Usage**: Match task type to specialized agent
