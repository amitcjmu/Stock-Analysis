# PR-Agent / Qodo Merge Workflow

## Overview

PR-Agent (Qodo Merge) is installed and ready to use. It provides AI-powered code reviews for **pull requests**, not pre-commit hooks.

## How It Works

### Pre-Commit (Current Setup)
- ✅ **Pattern-based code review** runs automatically before commits
- ✅ Checks for common issues (hardcoded heuristics, multi-tenant filters, etc.)
- ✅ Fast and lightweight

### Pull Requests (PR-Agent)
- 🤖 **Full AI code review** runs automatically when you create a PR
- 🤖 Provides intelligent suggestions and improvements
- 🤖 Detects bugs, security issues, and code quality problems

## Setup for PR Reviews

### Option 1: GitHub App (Recommended)

1. **Install PR-Agent GitHub App:**
   - Visit: https://github.com/apps/qodo-merge
   - Click "Install" and select your repositories
   - Configure permissions

2. **Automatic Reviews:**
   - PR-Agent automatically reviews every PR
   - Comments appear on your PR with suggestions
   - Use commands like `/review`, `/improve`, `/describe`

### Option 2: Manual PR Review

If you want to manually trigger a review:

```bash
# Review a PR
pr-agent --pr-url=https://github.com/owner/repo/pull/123 review

# Improve code
pr-agent --pr-url=https://github.com/owner/repo/pull/123 improve

# Describe PR
pr-agent --pr-url=https://github.com/owner/repo/pull/123 describe
```

## Current Status

✅ **PR-Agent Installed**: `pr-agent` is installed and available  
✅ **Pre-Commit Hook**: Pattern-based review runs before commits  
✅ **Ready for PR Reviews**: Install GitHub App for automatic PR reviews

## Workflow

1. **Make changes** and commit (pattern-based review runs)
2. **Push to branch** and create PR
3. **PR-Agent automatically reviews** the PR (if GitHub App installed)
4. **Review suggestions** and address them
5. **Merge** when ready

## Configuration

PR-Agent uses `configuration.toml` for settings. You can customize:
- Review depth and thoroughness
- Which files to focus on
- Review style and tone
- Custom instructions

See [PR-Agent Documentation](https://github.com/Codium-ai/pr-agent) for full configuration options.

## Benefits

- **Pre-Commit**: Fast pattern checks catch issues early
- **PR Reviews**: Comprehensive AI review catches complex issues
- **Best of Both**: Quick feedback + thorough analysis

## Next Steps

1. **Install GitHub App** for automatic PR reviews:
   - https://github.com/apps/qodo-merge

2. **Create a PR** to see PR-Agent in action

3. **Customize** PR-Agent settings if needed (see documentation)

