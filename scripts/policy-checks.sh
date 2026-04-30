#!/bin/bash
# Policy Enforcement Script - Local Alternative to GitHub CI
# Replace GitHub Actions limits by running policy checks during pre-commit
#
# Uses git grep (no ripgrep required) and runs from repository root.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🛡️  Running Code Policy Enforcement Checks..."

# Function to get staged files (for pre-commit) or all files (for manual run)
get_target_files() {
    local file_pattern="$1"

    # If running in git pre-commit context, only check staged files
    if git rev-parse --verify HEAD >/dev/null 2>&1; then
        staged_files=$(git diff --cached --name-only --diff-filter=AM | grep -E "$file_pattern" || true)
        if [ -n "$staged_files" ]; then
            echo "$staged_files"
        fi
    else
        # Fallback to all files if not in git context
        find "$PROJECT_ROOT" -type f -name "*.py" | grep -E "$file_pattern" || true
    fi
}

# Check 1: Block legacy discovery endpoint usage in app code
check_legacy_endpoints() {
    echo "🔍 Checking for legacy discovery endpoint usage..."

    # Target backend app code, exclude tests, README, and scripts
    local app_files
    app_files=$(get_target_files "backend/app/.*\.py$")
    # Exclude files that document removal or block legacy endpoints
    app_files=$(echo "$app_files" | grep -v "backend/app/middleware/legacy_endpoint_guard.py" || true)
    app_files=$(echo "$app_files" | grep -v "backend/app/utils/endpoint_migration_logger.py" || true)
    app_files=$(echo "$app_files" | grep -v "_DEPRECATED" || true)

    if [ -n "$app_files" ]; then
        # Check for legacy endpoint patterns (git grep — no ripgrep dependency)
        if echo "$app_files" | xargs git grep -nF '/api/v1/discovery' -- 2>/dev/null; then
            echo "❌ Legacy discovery endpoints found in application code!"
            echo "   Use /api/v1/flows or unified endpoints instead."
            echo "   Found in staged files:"
            echo "$app_files" | xargs git grep -lF '/api/v1/discovery' -- 2>/dev/null || true
            return 1
        fi
    fi

    echo "✅ No legacy discovery endpoints in app code"
    return 0
}

# Check 2: Block deprecated repository base imports
check_deprecated_imports() {
    echo "🔍 Checking for deprecated repository imports..."

    local backend_files
    backend_files=$(get_target_files "backend/.*\.py$")

    if [ -n "$backend_files" ]; then
        # Check for deprecated ContextAwareRepository imports
        if echo "$backend_files" | xargs git grep -nE 'from app\.repositories\.base import ContextAwareRepository' -- 2>/dev/null; then
            echo "❌ Deprecated ContextAwareRepository import detected!"
            echo "   Use: from app.repositories.context_aware_repository import ContextAwareRepository"
            echo "   Found in staged files:"
            echo "$backend_files" | xargs git grep -lE 'from app\.repositories\.base import ContextAwareRepository' -- 2>/dev/null || true
            return 1
        fi

        # Check for other deprecated context-aware imports
        if echo "$backend_files" | xargs git grep -nE 'from app\.core\.context_aware import ContextAwareRepository' -- 2>/dev/null; then
            echo "❌ Deprecated context_aware.py import detected!"
            echo "   Use: from app.repositories.context_aware_repository import ContextAwareRepository"
            return 1
        fi
    fi

    echo "✅ No deprecated repository imports found"
    return 0
}

# Check 3: Block sync database patterns in async code
check_sync_db_patterns() {
    echo "🔍 Checking for sync database patterns in async code..."

    local app_files
    app_files=$(get_target_files "backend/app/.*\.py$")

    if [ -n "$app_files" ]; then
        # Check for sync SessionLocal usage
        if echo "$app_files" | xargs git grep -nF 'SessionLocal(' -- 2>/dev/null | grep -v "AsyncSessionLocal"; then
            echo "❌ Sync SessionLocal usage found in async app code!"
            echo "   Use AsyncSessionLocal instead for consistency."
            return 1
        fi

        # Check for sync query patterns
        if echo "$app_files" | xargs git grep -nF '.query(' -- 2>/dev/null | head -5; then
            echo "⚠️  Found potential sync .query() patterns. Verify these are using async session.execute(select(...))"
            echo "   Manual review needed for above matches."
        fi
    fi

    echo "✅ No sync database patterns in async code"
    return 0
}

# Check 4: Validate environment flag usage
check_env_flags() {
    echo "🔍 Checking environment flag consistency..."

    local python_files
    python_files=$(get_target_files "backend/.*\.py$")

    if [ -n "$python_files" ]; then
        # Check for proper env flag imports
        local flag_usage
        flag_usage=$(echo "$python_files" | xargs git grep -nE 'CREWAI_ENABLE_MEMORY|LEGACY_ENDPOINTS_ALLOW' -- 2>/dev/null || true)

        if [ -n "$flag_usage" ]; then
            echo "📋 Environment flag usage found:"
            echo "$flag_usage" | head -3

            # Ensure proper import pattern
            local files_with_flags
            files_with_flags=$(echo "$flag_usage" | cut -d: -f1 | sort -u)
            for file in $files_with_flags; do
                if ! grep -q "from app.core.env_flags import is_truthy_env" "$file" 2>/dev/null; then
                    echo "⚠️  File $file uses environment flags but missing proper import"
                    echo "   Add: from app.core.env_flags import is_truthy_env"
                fi
            done
        fi
    fi

    echo "✅ Environment flag usage consistent"
    return 0
}

# Check 5: Validate unified endpoint usage
check_unified_endpoints() {
    echo "🔍 Validating unified endpoint consistency..."

    local api_files
    api_files=$(get_target_files "(backend/app/api/.*|src/.*)\.(py|ts|tsx)$")

    if [ -n "$api_files" ]; then
        # Count unified vs legacy endpoint references
        local unified_count legacy_count
        unified_count=$(echo "$api_files" | xargs git grep -cF '/api/v1/flows' -- 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
        legacy_count=$(echo "$api_files" | xargs git grep -cF '/api/v1/discovery' -- 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')

        echo "📊 Endpoint usage: Unified(/api/v1/flows): $unified_count, Legacy(/api/v1/discovery): $legacy_count"

        if [ "${legacy_count:-0}" -gt 0 ] && [ "${unified_count:-0}" -eq 0 ]; then
            echo "⚠️  High legacy endpoint usage with no unified endpoints. Consider migration."
        fi
    fi

    return 0
}

# Main execution
main() {
    cd "$PROJECT_ROOT"

    local exit_code=0

    # Run all checks
    check_legacy_endpoints || exit_code=1
    echo ""

    check_deprecated_imports || exit_code=1
    echo ""

    check_sync_db_patterns || exit_code=1
    echo ""

    check_env_flags || exit_code=1
    echo ""

    check_unified_endpoints || exit_code=1
    echo ""

    if [ $exit_code -eq 0 ]; then
        echo "✅ All policy checks passed!"
    else
        echo "❌ Policy violations found. Please fix before committing."
    fi

    exit $exit_code
}

# Run main function
main "$@"
