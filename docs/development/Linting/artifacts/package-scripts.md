# Recommended Package.json Script Additions

## Overview
These scripts should be added to `package.json` to support the ESLint compliance AI agent swarm project.

## Scripts to Add

```json
{
  "scripts": {
    // Existing scripts...
    
    // AI Agent Swarm Support Scripts
    "lint:progress": "node docs/development/Linting/artifacts/progress-tracker.js",
    "lint:progress:update": "node docs/development/Linting/artifacts/progress-tracker.js --update-markdown",
    "lint:agent:validate": "npm run typecheck && npm run lint:progress:update",
    "lint:scan:generated": "bash docs/development/Linting/artifacts/scan-generated-files.sh",
    
    // Enhanced linting for different tolerance levels
    "lint:strict": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:tolerant": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 200",
    "lint:agent-ready": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 50",
    
    // Agent-specific validation scripts
    "lint:agent:a": "eslint 'src/types/api/planning/**/*.ts' --ext ts --max-warnings 0",
    "lint:agent:b": "eslint 'src/types/api/**/*.ts' --ext ts --max-warnings 0",
    "lint:agent:c": "eslint 'src/types/api/planning/**/*.ts' 'src/types/api/finops/**/*.ts' --ext ts --max-warnings 0",
    "lint:agent:d": "eslint 'src/types/hooks/shared/form-hooks.ts' 'src/hooks/useUnifiedDiscoveryFlow.ts' --ext ts --max-warnings 0",
    "lint:agent:e": "eslint 'src/utils/api/**/*.ts' --ext ts --max-warnings 0",
    "lint:agent:f": "eslint 'src/components/discovery/**/*.ts' 'src/types/components/**/*.ts' --ext ts --max-warnings 0",
    "lint:agent:g": "eslint 'src/types/hooks/shared/ui-state.ts' 'src/types/hooks/shared/base-patterns.ts' --ext ts --max-warnings 0",
    "lint:agent:h": "eslint . --ext ts,tsx --max-warnings 0",
    
    // Checkpoint and rollback scripts
    "agent:checkpoint": "git add . && git commit -m 'checkpoint: agent progress' && git tag agent-checkpoint-$(date +%Y%m%d-%H%M%S)",
    "agent:rollback": "git reset --hard $(git tag -l 'agent-checkpoint-*' | tail -1)",
    
    // Type validation scripts  
    "types:validate": "tsc --noEmit --skipLibCheck",
    "types:shared": "tsc --noEmit src/types/shared/*.ts",
    
    // Performance monitoring
    "build:time": "time npm run build",
    "typecheck:time": "time npm run typecheck"
  }
}
```

## Script Usage Guide

### Progress Tracking Scripts

#### `npm run lint:progress`
- Analyzes current ESLint error state
- Shows agent-specific progress
- Displays top issue files
- **Usage**: Regular monitoring, no file updates

#### `npm run lint:progress:update`  
- Same as above but updates PROGRESS-TRACKER.md
- **Usage**: After agent milestones, end of work sessions

#### `npm run lint:agent:validate`
- Full validation: TypeScript + progress update
- **Usage**: Before committing agent work

### Tolerance Level Scripts

#### `npm run lint:strict`
- Zero tolerance for warnings/errors
- **Usage**: Final validation, production readiness

#### `npm run lint:tolerant`  
- Allows up to 200 warnings (current CI setting)
- **Usage**: Development work, iterative progress

#### `npm run lint:agent-ready`
- Target state: 50 warnings maximum
- **Usage**: Pre-deployment validation

### Agent-Specific Scripts

Each agent has a dedicated script to validate only their domain:
- `npm run lint:agent:a` - Forward declarations
- `npm run lint:agent:b` - Metadata standardization  
- `npm run lint:agent:c` - Configuration values
- etc.

**Usage**: Agent self-validation before marking complete

### Checkpoint Scripts

#### `npm run agent:checkpoint`
- Creates git commit and tag with timestamp
- **Usage**: After successful agent milestones

#### `npm run agent:rollback`
- Rolls back to latest agent checkpoint
- **Usage**: Recovery from failed agent work

## Implementation

### Add to package.json
```bash
# Backup current package.json
cp package.json package.json.backup

# Manually add scripts from above to package.json scripts section
# Or use jq to merge (if jq available):
# jq '.scripts += $new_scripts' package.json --argjson new_scripts '{"lint:progress": "node docs/development/Linting/artifacts/progress-tracker.js", ...}'
```

### Create Supporting Files
```bash
# Make scripts executable
chmod +x docs/development/Linting/artifacts/progress-tracker.js
chmod +x docs/development/Linting/artifacts/scan-generated-files.sh

# Test scripts work
npm run lint:progress
npm run lint:strict
```

### Verify Installation
```bash
# Test all new scripts
npm run lint:progress
npm run lint:agent:a
npm run types:validate

# Verify output and functionality
echo "✅ All scripts operational"
```

## Integration with CI/CD

### GitHub Actions Integration
Add to `.github/workflows/ci.yml`:

```yaml
- name: Agent Progress Tracking
  run: npm run lint:progress:update
  
- name: Upload Progress Report  
  uses: actions/upload-artifact@v4
  with:
    name: lint-progress-report
    path: docs/development/Linting/tracking/
```

### Pre-commit Hooks
Add to `.husky/pre-commit` (if using Husky):

```bash
#!/bin/sh
npm run lint:agent:validate
npm run types:validate
```

## Benefits

### For Agents
- **Self-validation**: Each agent can verify their work independently
- **Progress tracking**: Real-time feedback on error reduction
- **Domain focus**: Agent-specific linting for targeted work

### For Coordinators  
- **Monitoring**: Real-time progress across all agents
- **Quality gates**: Automated validation before integration
- **Recovery**: Easy rollback capabilities

### For CI/CD
- **Automated tracking**: Progress updates without manual intervention
- **Flexible tolerance**: Different lint levels for different stages
- **Performance monitoring**: Track impact on build times

---

**Document Version**: 1.0  
**Implementation**: Phase 0.5 - Task 0.2  
**Owner**: Foundation Agent  
**Dependencies**: progress-tracker.js, scan-generated-files.sh