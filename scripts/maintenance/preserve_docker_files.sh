#!/bin/bash
# Preserve valuable Docker and build files before git reset

echo "Preserving Docker and build files..."

# Create backup directory
mkdir -p .preserved_files

# Preserve Docker files
cp Dockerfile.backend .preserved_files/
cp Dockerfile.backend.lint .preserved_files/
cp Dockerfile.backend.dev .preserved_files/ 2>/dev/null || true
cp Dockerfile.frontend.optimized .preserved_files/ 2>/dev/null || true
cp backend/Dockerfile.optimized .preserved_files/ 2>/dev/null || true

# Preserve requirements files
cp backend/requirements-lint.txt .preserved_files/ 2>/dev/null || true

# Preserve useful fix scripts
cp backend/fix_list_comprehension_syntax.py .preserved_files/ 2>/dev/null || true
cp backend/fix_syntax_errors.py .preserved_files/ 2>/dev/null || true
cp backend/fix_all_migrations.py .preserved_files/ 2>/dev/null || true

# Save current git status for reference
git status > .preserved_files/git_status_before_reset.txt
git diff --stat > .preserved_files/git_diff_stat.txt

echo "Files preserved in .preserved_files/"
echo ""
echo "After git reset, restore with:"
echo "  cp .preserved_files/Dockerfile.backend ."
echo "  cp .preserved_files/Dockerfile.backend.lint ."
echo "  cp .preserved_files/requirements-lint.txt backend/"
