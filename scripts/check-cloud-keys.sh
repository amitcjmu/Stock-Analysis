#!/bin/bash
# Check for cloud service keys in staged files
# Patterns are stored here to avoid self-detection in .pre-commit-config.yaml

# AWS Access Key pattern: AKIA followed by 16 alphanumeric characters
# AWS Secret pattern: ASCP followed by base64 characters
PATTERN='(AKIA[0-9A-Z]{16}|aws_access_key_id|aws_secret_access_key|ASCP[A-Za-z0-9/+=]{8,})'

# Get staged files
STAGED_FILES=$(git diff --staged --name-only | grep -E '\.(py|yml|yaml|json|env)$' || true)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Check each file
for file in $STAGED_FILES; do
    if [ -f "$file" ] && grep -qE "$PATTERN" "$file" 2>/dev/null; then
        echo "Found cloud service keys in: $file"
        exit 1
    fi
done

exit 0
