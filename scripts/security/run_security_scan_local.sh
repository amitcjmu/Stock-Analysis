#!/bin/bash
# Local Security Scan Runner
# Runs the same security scans as GitHub Actions but locally

set -e

echo "🔐 AI Force Migration Platform - Local Security Scanner"
echo "======================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create reports directory
REPORT_DIR="security-reports-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "📁 Reports will be saved to: $REPORT_DIR"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python tools if needed
install_if_missing() {
    local tool=$1
    if ! command_exists "$tool"; then
        echo "Installing $tool..."
        pip install "$tool"
    fi
}

# Check Python version
echo "🐍 Checking Python environment..."
python --version

# Install security tools if not present
echo ""
echo "📦 Installing/checking security tools..."
pip install --quiet bandit safety pip-audit semgrep gitleaks

# 1. Run Bandit (SAST for Python)
echo ""
echo "🔍 Running Bandit security linter..."
bandit -r backend/ -f json -o "$REPORT_DIR/bandit-report.json" --severity-level low 2>/dev/null || true
bandit -r backend/ -f txt -o "$REPORT_DIR/bandit-report.txt" --severity-level low 2>/dev/null || true

# Count Bandit issues
BANDIT_ISSUES=$(python -c "import json; data=json.load(open('$REPORT_DIR/bandit-report.json')); print(len(data.get('results', [])))" 2>/dev/null || echo "0")
echo "  Found $BANDIT_ISSUES potential security issues"

# 2. Run Safety (Dependency vulnerabilities)
echo ""
echo "🔍 Running Safety dependency check..."
safety check --json --output "$REPORT_DIR/safety-report.json" -r backend/requirements.txt 2>/dev/null || true

# Count Safety vulnerabilities
SAFETY_VULNS=$(python -c "import json; data=json.load(open('$REPORT_DIR/safety-report.json')); print(len(data.get('vulnerabilities', [])))" 2>/dev/null || echo "0")
echo "  Found $SAFETY_VULNS vulnerable dependencies"

# 3. Run pip-audit
echo ""
echo "🔍 Running pip-audit..."
pip-audit -r backend/requirements.txt --format json --output "$REPORT_DIR/pip-audit-report.json" 2>/dev/null || true

# 4. Check for hardcoded secrets
echo ""
echo "🔍 Checking for hardcoded secrets..."
python scripts/security/check_credentials.py backend/**/*.py > "$REPORT_DIR/credentials-check.txt" 2>&1 || true

# 5. Run Semgrep (if available)
if command_exists semgrep; then
    echo ""
    echo "🔍 Running Semgrep security patterns..."
    semgrep --config=auto --json --output="$REPORT_DIR/semgrep-report.json" backend/ 2>/dev/null || true
fi

# 6. Quick secret scan with grep
echo ""
echo "🔍 Quick scan for common secret patterns..."
{
    echo "=== Potential Secrets Found ==="
    echo ""
    
    # API Keys
    grep -r "api_key\|apikey\|api-key" backend/ --include="*.py" | grep -v "Field(\|Column(\|# EXAMPLE" | grep "=" || echo "No hardcoded API keys found"
    
    echo ""
    # Passwords
    grep -r "password\s*=" backend/ --include="*.py" | grep -v "Field(\|Column(\|# EXAMPLE\|bcrypt" | grep '"' || echo "No hardcoded passwords found"
    
    echo ""
    # Secret Keys
    grep -r "SECRET_KEY\|secret_key" backend/ --include="*.py" | grep -v "Field(default=None\|getenv\|environ" | grep "=" || echo "No hardcoded secret keys found"
    
    echo ""
    # JWT Secrets
    grep -r "JWT_SECRET\|jwt_secret" backend/ --include="*.py" | grep -v "Field(\|getenv\|environ" | grep "=" || echo "No hardcoded JWT secrets found"
} > "$REPORT_DIR/secret-patterns.txt"

# 7. Generate consolidated report
echo ""
echo "📊 Generating consolidated security report..."

# Create a simple summary
cat > "$REPORT_DIR/summary.txt" << EOF
Security Scan Summary
====================
Scan Date: $(date)
Directory: $(pwd)

Quick Results:
- Bandit Issues: $BANDIT_ISSUES
- Vulnerable Dependencies: $SAFETY_VULNS
- Hardcoded Secrets: Check credentials-check.txt and secret-patterns.txt

Detailed reports available in: $REPORT_DIR/
EOF

# Generate full markdown report if script exists
if [ -f "scripts/security/generate_security_report.py" ]; then
    python scripts/security/generate_security_report.py "$REPORT_DIR" > "$REPORT_DIR/SECURITY_ASSESSMENT.md" 2>/dev/null || true
fi

# 8. Display summary
echo ""
echo "✅ Security scan complete!"
echo ""
echo "📋 Summary:"
echo "  - Bandit security issues: $BANDIT_ISSUES"
echo "  - Vulnerable dependencies: $SAFETY_VULNS"
echo ""

# Check for critical issues
if [ "$SAFETY_VULNS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Vulnerable dependencies detected${NC}"
fi

# Show specific file we know has issues
echo ""
echo "🔍 Checking known problem file (config.py)..."
grep "SECRET_KEY.*=" backend/app/core/config.py | grep -v "Field(default=None" || echo "No issues found"

echo ""
echo "📁 Full reports saved to: $REPORT_DIR/"
echo ""
echo "Key files to review:"
echo "  - $REPORT_DIR/SECURITY_ASSESSMENT.md (main report)"
echo "  - $REPORT_DIR/bandit-report.txt (code security issues)"
echo "  - $REPORT_DIR/safety-report.json (dependency vulnerabilities)"
echo "  - $REPORT_DIR/credentials-check.txt (hardcoded secrets)"
echo "  - $REPORT_DIR/secret-patterns.txt (secret patterns found)"

# Open the report if on macOS
if [[ "$OSTYPE" == "darwin"* ]] && [ -f "$REPORT_DIR/SECURITY_ASSESSMENT.md" ]; then
    echo ""
    read -p "Would you like to open the security report? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$REPORT_DIR/SECURITY_ASSESSMENT.md"
    fi
fi