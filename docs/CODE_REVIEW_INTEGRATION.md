# Code Review Integration Guide

This document describes how code review is integrated into the pre-commit workflow, including support for AI-powered code review tools.

## Overview

The code review integration runs automatically before each commit to:
- Check code against common patterns from the review repository
- Identify potential issues early in the development cycle
- Support optional AI-powered code review tools (Qodo Merge, CodeRabbit, etc.)

## Pre-Commit Integration

### Automatic Code Review Hook

The code review check runs automatically via pre-commit hooks before each commit:

```bash
# The hook runs automatically when you commit
git commit -m "Your message"
```

The hook checks:
- ✅ Pattern-based code review (hardcoded heuristics, multi-tenant filters, etc.)
- ✅ Common code quality issues
- ✅ Best practices from the review repository

### Manual Code Review Check

You can also run the code review check manually:

```bash
# Check all changed files
./scripts/pre-commit-code-review-check.sh

# Check only staged files
./scripts/pre-commit-code-review-check.sh --staged
```

## AI Code Review Tools Integration

### Option 1: Qodo Merge

[Qodo Merge](https://docs.qodo.ai/qodo-documentation/qodo-merge/) is an AI-powered code review tool that can be integrated.

#### Setup:

1. **Install Qodo Merge CLI** (if available):
   ```bash
   # Check if Qodo Merge CLI is available
   # Follow Qodo Merge documentation for installation
   ```

2. **Enable in pre-commit hook**:
   Edit `scripts/code-review-pre-commit.sh` and uncomment the AI review section:
   ```bash
   # Uncomment this section in code-review-pre-commit.sh
   if command -v qodo-merge &> /dev/null; then
       echo -e "${CYAN}🤖 Running AI code review...${NC}"
       qodo-merge review --files "$STAGED_FILES" || {
           echo -e "${YELLOW}⚠️  AI code review found suggestions (non-blocking)${NC}"
       }
   fi
   ```

3. **GitHub/GitLab Integration**:
   - Install Qodo Merge GitHub App: https://github.com/apps/qodo-merge
   - Or GitLab App: https://gitlab.com/qodo-merge
   - Configure it to review pull requests automatically

### Option 2: CodeRabbit

[CodeRabbit](https://coderabbit.ai/) is another AI code review tool.

#### Setup:

1. **Install CodeRabbit CLI** (if available):
   ```bash
   npm install -g @coderabbitai/cli
   ```

2. **Enable in pre-commit hook**:
   Add to `scripts/code-review-pre-commit.sh`:
   ```bash
   if command -v code-rabbit &> /dev/null; then
       echo -e "${CYAN}🤖 Running CodeRabbit review...${NC}"
       code-rabbit review --files "$STAGED_FILES" || {
           echo -e "${YELLOW}⚠️  CodeRabbit found suggestions (non-blocking)${NC}"
       }
   fi
   ```

### Option 3: Custom AI Review Tool

You can integrate any AI code review tool by:

1. **Adding to the hook script**:
   Edit `scripts/code-review-pre-commit.sh` and add your tool:
   ```bash
   # Your custom AI review tool
   if command -v your-ai-review-tool &> /dev/null; then
       echo -e "${CYAN}🤖 Running AI code review...${NC}"
       your-ai-review-tool review "$STAGED_FILES"
   fi
   ```

2. **Environment Variables**:
   You can configure API keys or settings via environment variables:
   ```bash
   export AI_REVIEW_API_KEY="your-key"
   export AI_REVIEW_ENABLED="true"
   ```

## Pattern-Based Code Review

The hook checks for common patterns from `docs/code-reviews/review-comments-repository.md`:

### Patterns Checked:

1. **Hardcoded Heuristics**
   - Detects simple if/else conditions that should use CrewAI agents
   - Suggests using agents instead of hardcoded rules

2. **Multi-Tenant Filters**
   - Checks database queries for missing `client_account_id` and `engagement_id`
   - Ensures proper data scoping

3. **Direct LLM Calls**
   - Detects direct OpenAI/Anthropic API calls
   - Suggests using `multi_model_service` for cost tracking

4. **Error Handling**
   - Checks for proper try-except blocks
   - Validates error message sanitization

5. **Security Patterns**
   - Checks for sensitive data in logs
   - Validates audit logging for critical operations

## Configuration

### Disable Code Review Hook

To temporarily disable the code review hook:

```bash
# Skip pre-commit hooks for one commit
git commit --no-verify -m "Your message"

# Or disable specific hook
SKIP=code-review-check git commit -m "Your message"
```

### Make Reviews Blocking

By default, code review issues are warnings and don't block commits. To make them blocking:

Edit `scripts/code-review-pre-commit.sh` and change:
```bash
# Change from:
exit 0  # Warnings only

# To:
exit 1  # Block commits with issues
```

## Workflow

### Standard Workflow:

1. **Make changes** to your code
2. **Stage files**: `git add .`
3. **Commit**: `git commit -m "Your message"`
   - Pre-commit hook runs automatically
   - Code review checks execute
   - AI review runs (if configured)
4. **Review suggestions** and fix if needed
5. **Push**: `git push`

### Before PR:

1. **Run full review**: `./scripts/pre-commit-code-review-check.sh`
2. **Fix any issues** found
3. **Create PR** - Qodo Merge/CodeRabbit will review automatically (if configured)

## Troubleshooting

### Hook Not Running

```bash
# Reinstall pre-commit hooks
pre-commit install

# Run manually to test
pre-commit run code-review-check --all-files
```

### AI Tool Not Found

If AI review tools are not installed, the hook will skip that step and continue with pattern-based checks.

### Performance Issues

If the hook is too slow:
- It only runs on staged files (not all files)
- AI reviews are optional and can be disabled
- Pattern checks are lightweight

## Best Practices

1. **Review Warnings**: Even if they don't block commits, review warnings before pushing
2. **Update Patterns**: Add new patterns to `docs/code-reviews/review-comments-repository.md` as they're discovered
3. **AI Review**: Use AI reviews as a supplement, not replacement for manual review
4. **Team Alignment**: Ensure team understands which patterns are checked

## Related Documentation

- [Code Review Repository](./code-reviews/review-comments-repository.md) - Common patterns and issues
- [Pre-Commit Configuration](../.pre-commit-config.yaml) - Full hook configuration
- [PR Workflow](../scripts/CURSOR_AI_AGENT_PR_WORKFLOW.md) - Complete PR workflow

