---
allowed-tools: Bash(find:*), Bash(wc:*), Bash(git:*), Bash(rm:*), Task, Grep, Glob, LS, Read, Edit, MultiEdit, Write, TodoWrite
description: Modularize large files with complete cleanup and verification
argument-hint: [target-lines] [min-lines]
---

# Multi-Agent Modularization Orchestrator v3

I'll orchestrate multiple specialized agents to modularize large files with PROPER CLEANUP - no orphaned files!

## Configuration
- Target lines per module: ${1:-400}
- Minimum lines to trigger: ${2:-1000}
- Branch: fix/modularization-cleanup-$(date +%Y%m%d)

## Phase 1: Detect Incomplete Modularizations

First, let me check for orphaned files from previous modularization attempts...

### Checking for Known Issues
1. **Azure Adapter** - checking for orphaned azure_adapter.py and duplicates
2. **Collection CRUD** - checking for improperly split files
3. **Other modules** - scanning for pattern *_auth.py, *_compute.py alongside directories

```bash
# Find potential orphaned files
echo "=== Checking for orphaned modularization files ==="
for dir in backend/app/services/*/; do
  if [ -d "$dir" ]; then
    base=$(basename "$dir")
    parent_dir=$(dirname "$dir")
    if [ -f "$parent_dir/${base}.py" ]; then
      echo "ORPHAN FOUND: ${base}.py exists alongside ${dir}"
      wc -l "$parent_dir/${base}.py"
    fi
    # Check for split files
    for pattern in auth compute storage network crud utils validators serializers; do
      if [ -f "$parent_dir/${base}_${pattern}.py" ]; then
        echo "DUPLICATE FOUND: ${base}_${pattern}.py in parent directory"
        wc -l "$parent_dir/${base}_${pattern}.py"
      fi
    done
  fi
done
```

## Phase 2: Cleanup Before New Modularization

I'll clean up any orphaned files found before proceeding:

1. **Delete orphaned monolithic files**
2. **Remove duplicate split files**
3. **Fix broken imports**
4. **Verify cleanup successful**

## Phase 3: Analyze Files Needing Modularization

Now searching for Python files exceeding ${2:-1000} lines...

After analysis, I'll provide:
- Files needing modularization
- Current line counts
- Complexity metrics
- Priority order

## Phase 4: Multi-Agent Execution with Verification

### 4.1: Product Owner Agent
Analyzes and prioritizes based on:
- Files with existing orphans (highest priority)
- Business impact
- Technical debt

### 4.2: SRE Modularization Agents (4 parallel)
Each agent MUST:
```
Task: sre-precommit-enforcer
Prompt: "
  Modularize ${FILE} with COMPLETE CLEANUP:

  CRITICAL REQUIREMENTS:
  1. Create module directory with proper structure
  2. Split into modules (target: ${1:-400} lines each)
  3. **DELETE THE ORIGINAL FILE** - Do not leave it as backup
  4. **DELETE ANY SPLIT FILES** in parent directory (*_auth.py, etc.)
  5. Update ALL imports in codebase
  6. Create proper __init__.py with exports

  VERIFICATION STEPS:
  - Confirm original file deleted: rm ${FILE}
  - Check no duplicates remain: ls ${FILE}_*.py should be empty
  - Test imports work: python -c 'from module import *'
  - Compare line counts: new total MUST be less than original

  Return:
  - Files created
  - Files deleted (MUST include original)
  - Import updates made
  - Line count before/after
"
```

### 4.3: Cleanup Verification Agent
```
Task: sre-precommit-enforcer
Prompt: "
  CRITICAL: Verify cleanup for ${MODULE}:

  CHECK 1 - Orphaned Files:
  [ ] Original monolithic file deleted
  [ ] No *_auth.py, *_compute.py in parent directory
  [ ] No duplicate implementations

  CHECK 2 - Structure Validation:
  [ ] Module directory exists with __init__.py
  [ ] All submodules < ${1:-400} lines
  [ ] Total lines less than original

  CHECK 3 - Import Validation:
  [ ] All imports updated to use module path
  [ ] No imports from old file location
  [ ] Import test passes

  If ANY check fails:
  1. Fix the issue immediately
  2. Delete orphaned files
  3. Update incorrect imports

  Return cleanup report with all actions taken.
"
```

### 4.4: DevSecOps Linting Agent
- Fix all pre-commit issues
- **VERIFY no untracked orphan files**
- Commit only if cleanup verified

### 4.5: QA Validation Agent
- Test all functionality works
- Verify no import errors
- Check no duplicate code
- Confirm line count reduced

## Phase 5: Final Verification & Report

### Critical Checks Before Commit
```bash
# No orphaned files should exist
echo "=== Final Orphan Check ==="
ORPHANS_FOUND=0
for module in ${MODULES_PROCESSED}; do
  if [ -f "${module}.py" ]; then
    echo "ERROR: Orphan still exists: ${module}.py"
    ORPHANS_FOUND=1
  fi
done

if [ $ORPHANS_FOUND -eq 1 ]; then
  echo "FAIL: Orphaned files still exist - cleanup incomplete!"
  exit 1
fi

# Verify line count reduction
echo "=== Line Count Verification ==="
echo "Before: ${TOTAL_LINES_BEFORE}"
echo "After: ${TOTAL_LINES_AFTER}"
if [ ${TOTAL_LINES_AFTER} -ge ${TOTAL_LINES_BEFORE} ]; then
  echo "FAIL: Line count increased or unchanged!"
  exit 1
fi
```

### Success Report
```
Modularization with Cleanup Complete
════════════════════════════════════

Files Processed: X
├── Modularized: Y
├── Orphans Deleted: Z
└── Imports Fixed: W

Cleanup Summary:
🗑️ Deleted azure_adapter.py (1362 lines)
🗑️ Deleted azure_adapter_auth.py (245 lines)
🗑️ Deleted collection_crud.py (1129 lines)
...

Line Count Impact:
Before: X,XXX lines total
After: Y,YYY lines total
Reduction: Z% achieved

✅ All orphaned files removed
✅ All imports updated
✅ Total lines reduced
✅ All tests passing
```

## Critical Success Criteria

The modularization is ONLY successful when:
1. ✅ Original file is DELETED (not kept as backup)
2. ✅ No split files (*_auth.py) in parent directory
3. ✅ All imports updated to module structure
4. ✅ Total line count DECREASED
5. ✅ No untracked files in git status
6. ✅ All tests pass

Let me begin by checking for orphaned files from previous modularizations...
