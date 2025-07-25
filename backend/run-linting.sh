#!/bin/bash
# Run backend linting locally

echo "=== Running Backend Linting ==="
echo "Using ruff to check Python code..."

# Check if ruff is available
if ! command -v ruff &> /dev/null && ! python3 -m ruff --version &> /dev/null; then
    echo "Error: ruff is not installed. Install with: pip install ruff"
    exit 1
fi

# Run ruff
echo "Running ruff check..."
python3 -m ruff check . --config pyproject.toml 2>&1 | tee ruff-report.txt

# Count errors
TOTAL_ERRORS=$(python3 -m ruff check . --config pyproject.toml 2>&1 | grep -E "\.py:" | wc -l)
echo ""
echo "Total linting errors: $TOTAL_ERRORS"

# Show summary by error type
echo ""
echo "=== Error Summary by Type ==="
python3 -m ruff check . --config pyproject.toml 2>&1 | grep -E "\.py:" | awk -F': ' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -nr | head -20

# Show files with most errors
echo ""
echo "=== Files with Most Errors ==="
python3 -m ruff check . --config pyproject.toml 2>&1 | grep -E "\.py:" | awk -F':' '{print $1}' | sort | uniq -c | sort -nr | head -20
