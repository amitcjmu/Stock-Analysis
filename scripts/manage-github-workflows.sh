#!/bin/bash

# Script to disable/enable GitHub workflows to conserve Actions minutes

set -e

WORKFLOWS_DIR=".github/workflows"

# Function to disable workflows
disable_heavy_workflows() {
    echo "🔄 Disabling resource-heavy workflows..."

    # List of workflows to disable
    heavy_workflows=(
        "ci.yml"
        "deployment-check.yml"
        "phase1-tests.yml"
        "pull-request.yml"
        "redis-infrastructure-ci.yml"
        "redis-security.yml"
        "security.yml"
        "merge-guardian.yml"
        "enforce-pr-workflow.yml"
        "dependency-update.yml"
        "seed-implementation-tasks.yml"
        "security-scan-on-demand.yml"
    )

    for workflow in "${heavy_workflows[@]}"; do
        if [ -f "$WORKFLOWS_DIR/$workflow" ]; then
            mv "$WORKFLOWS_DIR/$workflow" "$WORKFLOWS_DIR/$workflow.disabled"
            echo "  ❌ Disabled: $workflow"
        elif [ -f "$WORKFLOWS_DIR/$workflow.disabled" ]; then
            echo "  ⏭️  Already disabled: $workflow"
        else
            echo "  ⚠️  Not found: $workflow"
        fi
    done

    echo ""
    echo "✅ Heavy workflows disabled. Only essential checks will run."
    echo ""
    echo "Keeping active:"
    echo "  ✓ essential-pr-checks.yml (lightweight checks)"
    echo "  ✓ enforce-policies.yml (simple policy checks)"
    echo ""
}

# Function to enable all workflows
enable_all_workflows() {
    echo "🔄 Re-enabling all workflows..."

    for file in $WORKFLOWS_DIR/*.yml.disabled; do
        if [ -f "$file" ]; then
            original_name="${file%.disabled}"
            mv "$file" "$original_name"
            echo "  ✅ Enabled: $(basename $original_name)"
        fi
    done

    echo ""
    echo "✅ All workflows re-enabled."
}

# Function to show status
show_status() {
    echo "📊 GitHub Workflows Status"
    echo ""
    echo "Active workflows:"
    for file in $WORKFLOWS_DIR/*.yml; do
        if [ -f "$file" ] && [[ ! "$file" == *.disabled ]]; then
            size=$(du -h "$file" | cut -f1)
            echo "  ✅ $(basename $file) ($size)"
        fi
    done

    echo ""
    echo "Disabled workflows:"
    for file in $WORKFLOWS_DIR/*.yml.disabled; do
        if [ -f "$file" ]; then
            size=$(du -h "$file" | cut -f1)
            echo "  ❌ $(basename ${file%.disabled}) ($size)"
        fi
    done
}

# Main menu
case "${1:-}" in
    disable)
        disable_heavy_workflows
        ;;
    enable)
        enable_all_workflows
        ;;
    status)
        show_status
        ;;
    *)
        echo "GitHub Workflows Manager"
        echo ""
        echo "Usage: $0 [disable|enable|status]"
        echo ""
        echo "Commands:"
        echo "  disable - Disable resource-heavy workflows to save Actions minutes"
        echo "  enable  - Re-enable all disabled workflows"
        echo "  status  - Show current status of all workflows"
        echo ""
        echo "Current status:"
        show_status
        ;;
esac
