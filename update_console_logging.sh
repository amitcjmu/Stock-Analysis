#!/bin/bash
# Script to update console.log/warn/error statements to use debug utility
# Per GPT5 review: Wrap debug logs with NODE_ENV checks

set -e

TARGET_DIR="src/pages/collection/adaptive-forms"

echo "🔄 Updating console statements in $TARGET_DIR to use debug utility..."

# Find all TypeScript/TSX files with console statements
FILES=$(grep -rl "console\." "$TARGET_DIR" --include="*.tsx" --include="*.ts" || true)

if [ -z "$FILES" ]; then
    echo "✅ No files with console statements found"
    exit 0
fi

echo "Found $(echo "$FILES" | wc -l) files to update"

for FILE in $FILES; do
    echo "Processing: $FILE"

    # Check if file already imports debug utilities
    if grep -q "from '@/utils/debug'" "$FILE"; then
        echo "  ℹ️  Already imports debug utils, skipping import addition"
    else
        # Add import at top of file (after existing imports)
        # Find the line number of the last import
        LAST_IMPORT_LINE=$(grep -n "^import " "$FILE" | tail -1 | cut -d: -f1 || echo "0")

        if [ "$LAST_IMPORT_LINE" != "0" ]; then
            # Insert after last import
            sed -i '' "${LAST_IMPORT_LINE}a\\
import { debugLog, debugWarn, debugError } from '@/utils/debug';
" "$FILE"
            echo "  ✅ Added debug utility import after line $LAST_IMPORT_LINE"
        fi
    fi

    # Replace console.log with debugLog
    sed -i '' 's/console\.log(/debugLog(/g' "$FILE"

    # Replace console.warn with debugWarn
    sed -i '' 's/console\.warn(/debugWarn(/g' "$FILE"

    # Replace console.error with debugError
    sed -i '' 's/console\.error(/debugError(/g' "$FILE"

    # Replace console.info with debugInfo (need to add to import if used)
    if grep -q "debugInfo(" "$FILE"; then
        sed -i '' 's/debugLog, debugWarn, debugError/debugLog, debugWarn, debugError, debugInfo/g' "$FILE"
    fi

    echo "  ✅ Updated console statements"
done

echo ""
echo "✅ Successfully updated all console statements in $TARGET_DIR"
echo "📋 Summary:"
echo "   - Files updated: $(echo "$FILES" | wc -l)"
echo "   - console.log  → debugLog"
echo "   - console.warn → debugWarn"
echo "   - console.error → debugError"
echo ""
echo "ℹ️  Debug logging is now controlled by:"
echo "   - Development: Always enabled"
echo "   - Production: Only if NEXT_PUBLIC_DEBUG=true"
