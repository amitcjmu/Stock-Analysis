# Qodo Merge / PR-Agent Setup Guide

This guide explains how to set up Qodo Merge (PR-Agent) for AI-powered code review in your pre-commit workflow.

## What is Qodo Merge?

Qodo Merge (also known as PR-Agent) is an AI-powered code review tool that:
- Analyzes code changes automatically
- Provides intelligent suggestions and improvements
- Detects potential bugs and security issues
- Enforces coding standards

## Installation Options

### Option 1: PR-Agent CLI (Recommended for Pre-Commit)

Install PR-Agent as a Python package:

```bash
# Install PR-Agent
pip install pr-agent

# Verify installation
pr-agent --version
```

**Configuration:**
```bash
# Set environment variable to enable
export QODO_ENABLED=true

# Or add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export QODO_ENABLED=true' >> ~/.zshrc
```

### Option 2: Qodo Merge API

If you have a Qodo Merge API key:

```bash
# Set API key
export QODO_API_KEY="your-api-key-here"

# Optional: Set custom endpoint
export QODO_ENDPOINT="https://api.qodo.ai/v1/review"

# Enable Qodo
export QODO_ENABLED=true
```

### Option 3: GitHub App Integration (For PR Reviews)

For automatic PR reviews (not pre-commit):

1. **Install GitHub App:**
   - Visit: https://github.com/apps/qodo-merge
   - Click "Install" and select your repositories
   - Configure permissions as needed

2. **Features:**
   - Automatic PR reviews
   - PR summarization
   - Code suggestions
   - Compliance checks

## Pre-Commit Integration

The code review hook automatically detects and uses Qodo Merge if:

1. **PR-Agent CLI is installed**, OR
2. **QODO_API_KEY is set**, OR
3. **QODO_ENABLED=true** is set

### Enable in Pre-Commit

The hook is already integrated. Just configure your environment:

```bash
# Enable Qodo Merge
export QODO_ENABLED=true

# Or use API key
export QODO_API_KEY="your-key"

# Test the hook
pre-commit run code-review-check --all-files
```

### Environment Variables

Add to your `.env` file (backend/.env):

```bash
# Qodo Merge / PR-Agent Configuration
QODO_ENABLED=true
QODO_API_KEY=your-api-key-here
QODO_ENDPOINT=https://api.qodo.ai/v1/review  # Optional
```

Or set in your shell:

```bash
# For current session
export QODO_ENABLED=true
export QODO_API_KEY="your-key"

# For permanent setup (add to ~/.zshrc or ~/.bashrc)
echo 'export QODO_ENABLED=true' >> ~/.zshrc
echo 'export QODO_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

## Docker Environment

If running in Docker, add to your `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - QODO_ENABLED=${QODO_ENABLED:-false}
      - QODO_API_KEY=${QODO_API_KEY:-}
      - QODO_ENDPOINT=${QODO_ENDPOINT:-https://api.qodo.ai/v1/review}
```

Or add to `.env.docker`:

```bash
QODO_ENABLED=true
QODO_API_KEY=your-api-key-here
```

## Usage

### Automatic (Pre-Commit)

The hook runs automatically on commit:

```bash
git add .
git commit -m "Your changes"
# Qodo Merge review runs automatically
```

### Manual Review

Run the code review check manually:

```bash
# Check staged files
./scripts/code-review-pre-commit.sh

# Or via pre-commit
pre-commit run code-review-check
```

### PR Reviews

If using GitHub App, Qodo Merge automatically reviews pull requests:
- Visit your PR on GitHub
- Qodo Merge comments appear automatically
- Use commands like `/review`, `/improve`, `/describe`

## Configuration

### Disable Qodo Merge

Temporarily disable:

```bash
# Unset environment variable
unset QODO_ENABLED
unset QODO_API_KEY

# Or set to false
export QODO_ENABLED=false
```

### Make Reviews Blocking

By default, AI review suggestions are non-blocking. To make them block commits:

Edit `scripts/code-review-pre-commit.sh` and change the exit code in the AI review section from `exit 0` to `exit 1`.

## Troubleshooting

### PR-Agent Not Found

```bash
# Check if installed
which pr-agent

# Reinstall if needed
pip install --upgrade pr-agent
```

### API Key Issues

```bash
# Verify API key is set
echo $QODO_API_KEY

# Test API connection (adjust endpoint)
curl -H "Authorization: Bearer $QODO_API_KEY" \
     https://api.qodo.ai/v1/health
```

### Hook Not Running

```bash
# Reinstall pre-commit hooks
pre-commit install

# Test manually
pre-commit run code-review-check --all-files
```

### Performance

If reviews are too slow:
- The hook only reviews staged files (not all files)
- Reviews run in parallel when possible
- You can disable for specific commits: `git commit --no-verify`

## Alternative: CodeRabbit

If you prefer CodeRabbit instead:

```bash
# Install CodeRabbit CLI
npm install -g @coderabbitai/cli

# Configure
export CODERABBIT_ENABLED=true
export CODERABBIT_API_KEY="your-key"
```

Then update `scripts/code-review-pre-commit.sh` to add CodeRabbit support.

## Best Practices

1. **Start with Warnings**: Keep reviews non-blocking initially
2. **Review Suggestions**: Always review AI suggestions before accepting
3. **Team Alignment**: Ensure team understands AI review process
4. **Combine with Manual Review**: AI review supplements, doesn't replace human review
5. **Update Patterns**: Add project-specific patterns to review repository

## Related Documentation

- [Code Review Integration](./CODE_REVIEW_INTEGRATION.md) - General code review setup
- [Code Review Repository](./code-reviews/review-comments-repository.md) - Pattern repository
- [PR-Agent GitHub](https://github.com/Writesonic/qodo-pr-agent) - Official repository
- [Qodo Merge Docs](https://docs.qodo.ai/qodo-documentation/qodo-merge/) - Official documentation

