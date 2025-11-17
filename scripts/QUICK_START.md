# Quick Start - Git Workflow Scripts

## 🚀 What to Say / Type

### To Push Code (I'll automatically sync with main)

Just say:
```
push the code
```
or
```
push changes
```
or
```
commit and push
```

**I'll automatically:**
- ✅ Run code review check
- ✅ Sync with main (if needed)
- ✅ Handle conflicts (if any)
- ✅ Push your code

---

### To Sync with Main Manually (Optional)

Say:
```
sync with main
```

Or run directly:
```bash
./scripts/sync-with-main.sh
```

---

### To Check for Code Review Issues

Say:
```
check code review patterns
```

Or run directly:
```bash
./scripts/pre-commit-code-review-check.sh
```

---

### When Code is Ready for Review

Say:
```
ready for review
```
or
```
pr ready
```

**I'll explicitly prompt you:**
```
🧪 PR Testing Required

Before requesting manual code review, tests should be run.

Should I run the PR-ready tests now?
Run: ./scripts/run-pr-tests.sh
```

Then you can say:
```
yes, run tests
```

Or run directly:
```bash
./scripts/run-pr-tests.sh
```

---

### After Addressing PR Review Comments

Say:
```
update repository docs from PR #123
```

Or run directly:
```bash
./scripts/update-repository-docs.sh --pr 123
```

---

## 📋 Common Commands

### Manual Script Execution

```bash
# Sync with main
./scripts/sync-with-main.sh

# Sync and push in one command
./scripts/sync-with-main.sh --push

# Safe push (syncs first)
./scripts/git-safe-push.sh

# Check code review patterns
./scripts/pre-commit-code-review-check.sh

# Run PR-ready tests
./scripts/run-pr-tests.sh

# Update repository docs from PR
./scripts/update-repository-docs.sh --pr <number>
```

---

## 🎯 Typical Workflow Prompts

### Complete Workflow Example

**You say:** `"I've finished the feature, push the code"`

**I'll do:**
1. ✅ Code review check
2. ✅ Sync with main
3. ✅ Push code

---

**Later, you say:** `"ready for review"`

**I'll say:** `"Should I run tests?"`

**You say:** `"yes"`

**I'll do:**
1. ✅ Run tests
2. ✅ Show results
3. ✅ Update PR description

---

**After PR comments, you say:** `"address the review comments"`

**I'll do:**
1. ✅ Fix the issues
2. ✅ Update repository docs (if pattern found)
3. ✅ Ask if you want to push

**You say:** `"push"`

**I'll do:**
1. ✅ Sync with main
2. ✅ Push code

---

## 💡 Pro Tips

- **No special keywords needed** - Just say "push the code" naturally
- **I'll automatically sync** - You don't need to remember
- **Tests are explicitly prompted** - I'll ask before running them
- **Repository docs updated automatically** - When patterns are identified

---

## 🆘 Quick Help

**"What scripts are available?"**
```bash
ls -la scripts/*.sh
cat scripts/README.md
```

**"Show me the workflow guide"**
```bash
cat scripts/CURSOR_AI_AGENT_PR_WORKFLOW.md
```

**"Check if branch is synced"**
```bash
./scripts/sync-with-main.sh --check
```

---

**Remember:** Just talk naturally! Say "push the code" and I'll handle the rest automatically. 🎉
