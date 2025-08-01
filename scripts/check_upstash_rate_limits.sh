#!/bin/bash
# Check for Upstash references and ensure rate limiting is implemented

files=$(git diff --staged --name-only | grep -E "\.(py)$")
if [ -n "$files" ]; then
    echo "$files" | xargs grep -l "upstash\|UPSTASH" 2>/dev/null | while read file; do
        echo "Warning: $file contains Upstash references - ensure rate limiting is implemented"
    done
fi
exit 0
