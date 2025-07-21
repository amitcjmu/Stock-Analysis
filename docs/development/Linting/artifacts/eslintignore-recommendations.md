# ESLint Ignore Recommendations for Phase 0.5

## Overview
This document provides recommendations for updating `.eslintignore` to exclude non-actionable files before starting the AI agent swarm deployment.

## Recommended .eslintignore Additions

```bash
# Third-party and auto-generated code - Phase 0.5 exclusions

# Node modules (should already be excluded)
node_modules/
**/node_modules/

# Build outputs
dist/
build/
.next/
out/

# Auto-generated files
**/*.d.ts
**/*.generated.ts
**/*.auto.ts
**/generated/
**/auto-generated/

# Third-party library wrappers
**/vendor/
**/lib/
**/libs/
**/third-party/

# Package manager files
package-lock.json
yarn.lock
pnpm-lock.yaml

# IDE and editor generated files
.vscode/
.idea/
*.swp
*.swo
*~

# Test coverage reports
coverage/
.nyc_output/
**/coverage/

# Temporary and cache files
.cache/
*.tmp
*.temp
.temp/
.tmp/

# Documentation build outputs
docs/build/
**/docs/build/

# Storybook build outputs
storybook-static/

# Environment and config files (if containing third-party schemas)
# Note: Only add these if they contain auto-generated content
# .env.example
# *.config.js (evaluate case by case)

# Database migrations (if auto-generated)
# **/migrations/*.auto.ts
# **/migrations/*.generated.ts

# API client code (if auto-generated)
**/api-client/generated/
**/openapi/generated/
**/swagger/generated/

# Localization files (if auto-generated)
**/i18n/generated/
**/locales/generated/

# Asset and media files
**/*.png
**/*.jpg
**/*.jpeg
**/*.gif
**/*.svg
**/*.ico
**/*.webp
**/*.mp4
**/*.mp3
**/*.pdf
**/*.zip
**/*.tar.gz
```

## Files to Investigate Before Excluding

### Potentially Auto-Generated (Verify Before Adding to .eslintignore)
1. **Config files ending in .config.js/.config.ts**
   - Check if they're manually maintained or auto-generated
   - Examples: `webpack.config.js`, `vite.config.ts`, `tailwind.config.js`

2. **Type definition files (.d.ts)**
   - Some may be manually maintained for custom types
   - Only exclude if they're definitely auto-generated

3. **API/Schema files**
   - Files containing OpenAPI, GraphQL, or database schemas
   - May be auto-generated from external sources

4. **Test files**
   - Generally should NOT be excluded unless auto-generated
   - Focus on `.spec.ts`, `.test.ts` files

5. **Component library files**
   - UI component libraries may have generated index files
   - Check for auto-generated barrel exports

## Validation Script

Create a script to identify potential non-actionable files:

```bash
#!/bin/bash
# scan-generated-files.sh

echo "🔍 Scanning for potentially auto-generated files..."

echo "📁 Files with 'generated' in path:"
find . -type f -name "*.ts" -o -name "*.tsx" | grep -i generated | head -20

echo "📁 Files with auto-generation comments:"
grep -r "This file was automatically generated" --include="*.ts" --include="*.tsx" . | head -10

echo "📁 Files with very high any-type density (>50% of lines):"
npm run lint 2>&1 | awk -F: '/no-explicit-any/ {file=$1} END {for(f in files) if(files[f]>50) print f, files[f]}' | head -10

echo "📁 Large files that might be generated (>1000 lines):"
find . -name "*.ts" -o -name "*.tsx" | xargs wc -l | sort -nr | head -10 | awk '$1 > 1000 {print $2, $1 " lines"}'

echo "✅ Scan complete. Review results before updating .eslintignore"
```

## Implementation Steps for Phase 0.5

### Step 1: Create Backup
```bash
# Backup current .eslintignore
cp .eslintignore .eslintignore.backup.$(date +%Y%m%d)
```

### Step 2: Run Investigation Script
```bash
# Make script executable and run
chmod +x scan-generated-files.sh
./scan-generated-files.sh > generated-files-report.txt
```

### Step 3: Update .eslintignore
```bash
# Add recommended exclusions to .eslintignore
cat eslintignore-recommendations.txt >> .eslintignore
```

### Step 4: Validate Impact
```bash
# Run ESLint to get new baseline count
npm run lint 2>&1 | grep -c "error"

# Compare with original count (2,173)
# Expected: Reduction of 50-200 errors from excluded files

# Update progress tracker with new baseline
node docs/development/Linting/artifacts/progress-tracker.js --update-markdown
```

## Expected Impact

### Error Reduction Estimate
- **Third-party files**: 50-100 errors
- **Auto-generated files**: 20-50 errors
- **Build outputs**: 10-30 errors
- **Total estimated reduction**: 80-180 errors

### New Baseline Target
- **Original count**: 2,173 errors
- **After exclusions**: ~2,000-2,093 actionable errors
- **Agent targets will adjust**: Proportional reduction across all agents

## Quality Assurance

### Validation Checklist
- [ ] No manually maintained files excluded
- [ ] All excluded files are truly non-actionable
- [ ] Build and test suite still pass
- [ ] TypeScript compilation unaffected
- [ ] New error count documented and communicated to agents

### Rollback Plan
```bash
# If exclusions cause issues, rollback
cp .eslintignore.backup.$(date +%Y%m%d) .eslintignore

# Verify rollback
npm run lint 2>&1 | grep -c "error"  # Should return to ~2,173
```

---

**Document Version**: 1.0  
**Implementation**: Phase 0.5 - Task 0.1  
**Owner**: Preparation Agent  
**Review Required**: Technical Lead approval before implementation