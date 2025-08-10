#!/bin/bash
# Installation script for local policy enforcement
# Replaces GitHub CI Actions with pre-commit hooks

set -e

echo "🔧 Installing Local Policy Enforcement Hooks"
echo "============================================"

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Check if ripgrep is installed
if ! command -v rg &> /dev/null; then
    echo "📦 Installing ripgrep..."
    if command -v brew &> /dev/null; then
        brew install ripgrep
    else
        echo "❌ Please install ripgrep manually: https://github.com/BurntSushi/ripgrep#installation"
        exit 1
    fi
fi

# Install pre-commit hooks
echo "⚙️  Installing pre-commit hooks..."
pre-commit install

# Test policy checks
echo "🧪 Testing policy enforcement..."
if ./scripts/policy-checks.sh; then
    echo ""
    echo "✅ Local Policy Enforcement Setup Complete!"
    echo ""
    echo "📋 What's Configured:"
    echo "   • Legacy endpoint detection (/api/v1/discovery → blocked)"
    echo "   • Deprecated import prevention (old repository bases)"
    echo "   • Sync/async database pattern validation"
    echo "   • Environment flag consistency checks"
    echo ""
    echo "🚀 Policy checks will now run automatically on each commit."
    echo "   To run manually: ./scripts/policy-checks.sh"
    echo "   To bypass temporarily: git commit --no-verify"
else
    echo "❌ Policy check test failed. Please review and fix issues."
    exit 1
fi
