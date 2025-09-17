# Multi-Agent Workflow Patterns

## Successful Agent Orchestration Pattern
**Problem**: Complex modularization requiring multiple specialized agents
**Solution**: Sequential agent chain with validation
**Workflow**:
```
1. python-crewai-fastapi-expert → Modularize
2. code-review-analyzer → Validate 
3. python-crewai-fastapi-expert → Fix issues
4. qa-playwright-tester → Test functionality
5. Pre-commit hooks → Final validation
```

## Agent Task Instructions Template
**Critical**: Always include in agent prompts
```
IMPORTANT: First read these files:
1. /docs/analysis/Notes/coding-agent-guide.md
2. /.claude/agent_instructions.md

After completing your task, provide a detailed summary following 
the template in agent_instructions.md, not just "Done".
Include: what was requested, what was accomplished, technical 
details, and verification steps.
```

## QA Agent Docker Fix Pattern
**Problem**: Backend startup blocked by migration errors
**Solution**: Pre-create alembic_version table
```sql
-- Fix migration name length issue
CREATE TABLE IF NOT EXISTS migration.alembic_version (
    version_num VARCHAR(100) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
```

## Git Workflow for Modularization
```bash
# Stage deletion of original file
git add removed_file.py

# Stage new modularized directory
git add new_directory/

# Commit with comprehensive message
git commit -m "fix: [Description]

Changes:
- Removed original file (X lines)
- Created modular structure
- Maintained backward compatibility

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```