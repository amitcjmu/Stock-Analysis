# Git Workflow Scripts

These scripts ensure your branch is always synced with the latest `main` branch before pushing code, preventing merge conflicts in PRs.

## Scripts

### `pre-commit-code-review-check.sh`

Reviews changed code against common patterns in the code review repository.

**Usage:**
```bash
# Check all modified files
./scripts/pre-commit-code-review-check.sh

# Check only staged files
./scripts/pre-commit-code-review-check.sh --staged
```

**Features:**
- ✅ Checks for common code review patterns (local imports, error handling, etc.)
- ✅ References `docs/code-reviews/review-comments-repository.md`
- ✅ Provides actionable warnings before PR review
- ✅ Non-blocking (warns but doesn't fail commit)

**What it checks:**
- Local imports inside functions
- `str(exc)` exposed to users (error sanitization)
- SimpleNamespace usage (prefer dataclasses)
- Missing error handling for external calls
- Magic numbers (should use named constants)
- Missing audit logging for critical operations
- Logging sensitive data

**When to use:**
- Before committing code
- Before pushing to remote
- As part of standard workflow

See `docs/code-reviews/review-comments-repository.md` for full pattern list.

---

### `sync-with-main.sh`

Ensures your current branch is synced with the latest `main` branch.

**Usage:**
```bash
# Check if branch needs syncing (non-destructive)
./scripts/sync-with-main.sh --check

# Sync with main (rebase)
./scripts/sync-with-main.sh

# Sync with main and push
./scripts/sync-with-main.sh --push
```

**Features:**
- ✅ Automatically stashes uncommitted changes before syncing
- ✅ Restores stashed changes after successful sync
- ✅ Handles rebase conflicts gracefully
- ✅ Provides clear status messages
- ✅ Prevents syncing if you're on `main` branch

**What it does:**
1. Fetches latest changes from `origin/main`
2. Checks how many commits behind/ahead your branch is
3. If behind, rebases your branch onto `main`
4. Restores any stashed changes
5. Verifies sync was successful

---

### `git-safe-push.sh`

Wrapper around `git push` that ensures branch is synced with main first.

**Usage:**
```bash
# Push current branch (synced with main first)
./scripts/git-safe-push.sh

# Push specific branch
./scripts/git-safe-push.sh origin feature-branch

# Force push (after syncing)
./scripts/git-safe-push.sh --force
```

**Features:**
- ✅ Automatically syncs with main before pushing
- ✅ Supports all standard `git push` arguments
- ✅ Prevents pushing outdated code

---

### `update-repository-docs.sh`

Updates code review and testing repository documents with new patterns from PR comments. This ensures repositories stay current and continuously improve.

**Usage:**
```bash
# Check for updates needed
./scripts/update-repository-docs.sh

# Fetch PR comments for review
./scripts/update-repository-docs.sh --pr <number>

# Manual entry mode
./scripts/update-repository-docs.sh --review
```

**Features:**
- ✅ Checks repository document status
- ✅ Fetches PR comments for review (with `gh` CLI)
- ✅ Prompts for manual pattern entry
- ✅ References both code review and testing repositories
- ✅ Helps maintain continuous improvement

**What it does:**
1. Checks if repository documents exist
2. Shows last updated dates
3. Provides update reminders
4. Helps identify patterns from PR comments
5. Guides pattern documentation format

**When to use:**
- ✅ After addressing PR review comments
- ✅ When identifying new patterns
- ✅ Before pushing code (verify updates)
- ✅ When reviewing PR comments for patterns

**This ensures repository documents stay current and improve continuously.**

---

### `run-pr-tests.sh`

Runs PR-ready tests before manual code review. This is typically run toward the end of PR when code is complete.

**Usage:**
```bash
# Run PR-ready tests (smoke + unit)
./scripts/run-pr-tests.sh

# Run specific test suite
./scripts/run-pr-tests.sh --unit          # Unit tests only
./scripts/run-pr-tests.sh --integration   # Integration tests only
./scripts/run-pr-tests.sh --smoke         # Smoke tests only
./scripts/run-pr-tests.sh --coverage      # All tests with coverage report
```

**Features:**
- ✅ Verifies Docker services are running
- ✅ Auto-detects test directory in container
- ✅ References testing repository guidelines
- ✅ Provides clear test results and next steps
- ✅ Generates coverage reports (with `--coverage`)

**What it does:**
1. Checks Docker services are healthy
2. Detects test directory inside container
3. Runs appropriate test suite (smoke + unit by default)
4. Reports pass/fail status
5. References testing repository documentation

**When to use:**
- ✅ Before requesting manual PR review
- ✅ Toward the end of PR when code is complete
- ✅ After all code changes are committed
- ✅ Before updating PR description

**Testing Repository References:**
- `docs/testing/testing-strategy.md` - Testing strategy and patterns
- `docs/testing/QA_GUIDE.md` - QA guide and test execution
- `docs/testing/README.md` - Comprehensive test documentation
- `docs/testing/Discovery-Flow-UnitTest-Coverage.md` - Discovery flow tests
- `docs/testing/CrewAIAgents-UnitTest-Coverage.md` - CrewAI agent tests

---

## Setup (Optional)

### Add Shell Aliases

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# Sync with main
alias gsync='./scripts/sync-with-main.sh'

# Safe push (syncs first)
alias gpush='./scripts/git-safe-push.sh'

# Run PR-ready tests
alias gtest='./scripts/run-pr-tests.sh'

# Update repository documents
alias gdocs='./scripts/update-repository-docs.sh'
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

Now you can use:
```bash
gsync          # Sync with main
gpush          # Push (synced first)
gsync --push   # Sync and push
gtest          # Run PR-ready tests
gdocs          # Update repository docs
gdocs --pr 123 # Update docs from PR #123
```

---

## Integration with Cursor AI Agent

**IMPORTANT:** The Cursor AI agent is configured to:
1. ✅ Review code against common patterns before pushing (`pre-commit-code-review-check.sh`)
2. ✅ Reference `docs/code-reviews/review-comments-repository.md` for patterns
3. ✅ Always run `sync-with-main.sh` before pushing code
4. ✅ **Update repository documents** when addressing PR review comments
5. ✅ **Keep documents current** with continuous improvements
6. ✅ Keep memory updated about this workflow requirement
7. ✅ Use these scripts as the standard process

This ensures both automated checks (scripts) and AI awareness (memory) work together to make check-ins more efficient and keep repository documents continuously updated.

## Complete Workflow

### Before Pushing Code (Initial Commit):

1. **Code review check** (catch issues early):
   ```bash
   ./scripts/pre-commit-code-review-check.sh
   ```

2. **Sync with main** (prevent merge conflicts):
   ```bash
   ./scripts/sync-with-main.sh --push
   ```

3. **Push code** (already done if using `--push` flag)

### Before PR Review (Toward End of PR):

4. **Run PR-ready tests** (before manual review):
   ```bash
   ./scripts/run-pr-tests.sh
   ```

5. **Review test results** and fix any failures

6. **Update PR description** with test results

7. **Request manual code review**

### After Addressing PR Review Comments (Continuous Updates):

8. **Update repository documents** (keep them current):
   ```bash
   ./scripts/update-repository-docs.sh --pr <number>
   ```

9. **Add new patterns** to appropriate repository:
   - Code review patterns → `docs/code-reviews/review-comments-repository.md`
   - Testing patterns → `docs/testing/testing-strategy.md` or `docs/testing/QA_GUIDE.md`

10. **Include PR reference** in pattern documentation

11. **Verify updates** before next push:
    ```bash
    ./scripts/update-repository-docs.sh
    ```

This workflow ensures:
- Common review patterns are caught early
- Code is always based on latest main
- Tests are run before PR review (explicit prompt)
- **Repository documents stay current** (continuous updates)
- **Patterns are documented** as they're discovered
- PRs are cleaner and faster to review
- Less back-and-forth in PR reviews
- **Knowledge base improves** with each PR

---

## When to Use

**Always run `sync-with-main.sh` before:**
- Pushing code to remote branch
- Creating/updating PRs
- Starting new feature work (to ensure you start from latest main)
- After pulling/merging main into your branch manually

**When you don't need it:**
- First commit on a new branch (unless main has moved)
- If you just synced and haven't made new commits
- Working on local-only changes (until you're ready to push)

---

## Troubleshooting

### Rebase Conflicts

If rebase has conflicts:
1. Resolve conflicts in the affected files
2. Stage resolved files: `git add <file>`
3. Continue rebase: `git rebase --continue`
4. Re-run sync script: `./scripts/sync-with-main.sh`

### Stashed Changes Conflicts

If stashed changes have conflicts after sync:
1. Resolve conflicts in the affected files
2. Stage resolved files: `git add <file>`
3. Apply stash: `git stash pop`
4. Or manually apply: `git stash show -p | git apply`

### Script Not Executable

If you get "Permission denied":
```bash
chmod +x scripts/sync-with-main.sh
chmod +x scripts/git-safe-push.sh
```

---

## Why This Matters

- **Prevents merge conflicts**: Code is always based on latest main
- **Cleaner PRs**: No "merge main into feature" commits
- **Faster reviews**: Reviewers see only your changes
- **Consistent workflow**: Same process for everyone
- **AI agent compliance**: Ensures Cursor AI follows the process
