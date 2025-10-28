# Runtime Data in Git: Anti-Pattern and Cleanup

## Problem: Runtime-Generated Files Tracked in Version Control

**Symptom**: `backend/data/agent_insights.json` grew to 1.1MB (32K lines) with 105 commits modifying it. Caused merge conflicts and bloated repository.

**Root Cause**: Files were added to Git BEFORE `.gitignore` rules existed. Once tracked, gitignore doesn't automatically untrack files.

## Runtime Data Files to Exclude

```bash
# Agent persistence (environment-specific)
backend/data/agent_insights.json          # Agent learnings (1.1MB)
backend/data/agent_memory.json            # CrewAI memory (9.4MB)
backend/data/agent_questions.json         # Pending questions (78KB)
backend/data/agent_context.json           # Cross-page context
backend/data/agent_learning_experiences.json
backend/data/field_mappings.json          # Cached mappings
```

**Why Exclude**:
1. Environment-specific (flow IDs, tenant IDs)
2. Generated during runtime, not configuration
3. Each environment has different agent activity
4. Causes merge conflicts between developers
5. Bloats Git history with non-code changes

## Solution: Remove from Tracking (Keep Locally)

```bash
# Stop tracking files but keep them locally
git rm --cached backend/data/agent_insights.json
git rm --cached backend/data/agent_memory.json
git rm --cached backend/data/agent_questions.json
git rm --cached backend/data/agent_context.json
git rm --cached backend/data/agent_learning_experiences.json
git rm --cached backend/data/field_mappings.json

# Verify gitignore covers them
git check-ignore -v backend/data/agent_insights.json
# Should output: .gitignore:XX:backend/data/**

# Commit removal
git commit -m "chore: Remove runtime agent data from version control"
```

## Gitignore Pattern

```gitignore
# Data artifacts (keep structure, ignore contents)
backend/data/**
!backend/data/.gitkeep
!backend/data/README.md  # Document the directory
```

## Documentation Template

Create `backend/data/README.md`:

```markdown
# Runtime Data Directory

Auto-generated files (DO NOT commit to Git):
- `agent_insights.json` - Agent learnings
- `agent_memory.json` - CrewAI memory state
- `agent_questions.json` - Pending questions

## Production Deployment
Mount as persistent volume:
```yaml
services:
  backend:
    volumes:
      - agent_data:/app/backend/data
```

## Cleanup
```bash
# Fresh start (local dev)
rm backend/data/*.json
```

## Detection Pattern

```bash
# Find runtime data accidentally committed
git log --oneline --all -- backend/data/*.json | wc -l
# If > 10 commits, likely runtime data

# Check file size
ls -lh backend/data/*.json
# If > 1MB, definitely runtime data
```

## Usage

Apply this pattern when:
- Files in `data/`, `cache/`, `tmp/`, `logs/` directories
- Files growing with usage (not commits adding features)
- Multiple commits modifying same file without code changes
- File content is JSON/pickle with UUIDs, timestamps, flow IDs
