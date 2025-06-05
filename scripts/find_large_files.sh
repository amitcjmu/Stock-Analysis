#!/bin/zsh

# Find Python and Node.js files, excluding specified directories, and create a table for files with >400 lines
find . -type f \( -name "*.py" -o -name "*.js" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/venv/*" \
  -not -path "*/docs/*" \
  -not -path "*/tests/*" \
  -exec sh -c 'wc -l "$1" | awk "\$1 > 800 {print \$2 \"|\" \$1}"' sh {} \; | \
  awk -F'|' '{printf "| %-50s | %10s |\n", $1, $2}' | \
  (echo "| Filename                                           | Lines     |"; echo "|----------------------------------------------------|-----------|"; cat)

