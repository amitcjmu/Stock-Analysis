# Enhanced ESLint Rule Recommendations

## Overview
Additional ESLint rules to enforce during and after the AI agent swarm project, including the critical type-only import enforcement.

## Priority 1: Type-Only Import Enforcement

### Add to eslint.config.js

```javascript
// Add to existing rules in eslint.config.js
rules: {
  // Existing rules...
  "@typescript-eslint/no-unused-vars": "off",
  
  // NEW: Enforce type-only imports (CRITICAL)
  "@typescript-eslint/consistent-type-imports": [
    "error",
    {
      "prefer": "type-imports",
      "disallowTypeAnnotations": false,
      "fixStyle": "separate-type-imports"
    }
  ],
  
  // NEW: Enforce type-only exports where applicable
  "@typescript-eslint/consistent-type-exports": [
    "error",
    {
      "fixMixedExportsWithInlineTypeSpecifier": true
    }
  ],
  
  // NEW: Prevent unnecessary type assertions
  "@typescript-eslint/no-unnecessary-type-assertion": "error",
  
  // NEW: Enforce consistent type definitions
  "@typescript-eslint/consistent-type-definitions": ["error", "interface"],
  
  // Enhanced after cleanup: Stricter any-type enforcement
  // NOTE: Change this to "error" in Phase 4 after cleanup
  "@typescript-eslint/no-explicit-any": "warn", // Current: warn, Target: error
}
```

### Rule Explanations

#### `@typescript-eslint/consistent-type-imports`
- **Purpose**: Enforces `import type` for type-only imports
- **Benefit**: Prevents runtime circular dependencies and reduces bundle size
- **Auto-fix**: Can automatically fix existing incorrect imports

#### `@typescript-eslint/consistent-type-exports`  
- **Purpose**: Enforces `export type` for type-only exports
- **Benefit**: Complements type-import enforcement
- **Auto-fix**: Automatically fixes mixed export statements

#### `@typescript-eslint/no-unnecessary-type-assertion`
- **Purpose**: Prevents `as Type` when TypeScript can infer correctly
- **Benefit**: Cleaner code, fewer runtime assumptions
- **Impact**: Medium - improves type safety

#### `@typescript-eslint/consistent-type-definitions`
- **Purpose**: Enforces `interface` over `type` for object definitions
- **Benefit**: Consistency with shared type definitions
- **Impact**: Low - stylistic but important for large codebases

## Priority 2: Additional Quality Rules

### Performance & Bundle Optimization
```javascript
rules: {
  // Prevent import of entire modules when only parts needed
  "import/no-namespace": "error",
  
  // Ensure imports are at top of file
  "import/first": "error",
  
  // Prevent duplicate imports
  "import/no-duplicates": "error",
  
  // Sort imports consistently
  "import/order": ["error", {
    "groups": [
      "builtin",
      "external", 
      "internal",
      "parent",
      "sibling",
      "index",
      "type"
    ],
    "newlines-between": "always",
    "alphabetize": {
      "order": "asc",
      "caseInsensitive": true
    }
  }]
}
```

### Type Safety Enhancements
```javascript
rules: {
  // Prevent any[] arrays after cleanup
  "@typescript-eslint/array-type": ["error", {
    "default": "array-simple"
  }],
  
  // Require explicit return types on exported functions
  "@typescript-eslint/explicit-module-boundary-types": "error",
  
  // Prevent empty interfaces (use type aliases instead)
  "@typescript-eslint/no-empty-interface": "error",
  
  // Require consistent member delimiter style
  "@typescript-eslint/member-delimiter-style": ["error", {
    "multiline": {
      "delimiter": "semi",
      "requireLast": true
    }
  }]
}
```

## Implementation Timeline

### Phase 0.5: Preparation
```javascript
// Add these rules as "warn" during setup
"@typescript-eslint/consistent-type-imports": "warn",
"@typescript-eslint/consistent-type-exports": "warn",
```

### Phase 2: During Agent Work
```javascript
// Keep as warnings to not block agent progress
"@typescript-eslint/consistent-type-imports": "warn",
"@typescript-eslint/no-unnecessary-type-assertion": "warn",
```

### Phase 4: Post-Cleanup Enforcement  
```javascript
// Upgrade to errors for strict enforcement
"@typescript-eslint/consistent-type-imports": "error",
"@typescript-eslint/consistent-type-exports": "error", 
"@typescript-eslint/no-explicit-any": "error", // Zero tolerance
"@typescript-eslint/no-unnecessary-type-assertion": "error",
```

## Auto-Fix Capability

Many of these rules support automatic fixing:

```bash
# Fix type imports automatically
npx eslint . --ext ts,tsx --fix --rule "@typescript-eslint/consistent-type-imports: error"

# Fix type exports automatically  
npx eslint . --ext ts,tsx --fix --rule "@typescript-eslint/consistent-type-exports: error"

# Fix import ordering
npx eslint . --ext ts,tsx --fix --rule "import/order: error"
```

## Package.json Script Additions

```json
{
  "scripts": {
    // Add to existing scripts
    "lint:type-imports": "eslint . --ext ts,tsx --rule '@typescript-eslint/consistent-type-imports: error'",
    "lint:fix-imports": "eslint . --ext ts,tsx --fix --rule '@typescript-eslint/consistent-type-imports: error' --rule '@typescript-eslint/consistent-type-exports: error'",
    "lint:imports-only": "eslint . --ext ts,tsx --rule 'import/order: error' --rule 'import/no-duplicates: error'"
  }
}
```

## Benefits

### Bundle Size Reduction
- **Type-only imports**: Prevent unnecessary runtime code inclusion
- **Import optimization**: Remove duplicate and unused imports
- **Tree shaking**: Enable better dead code elimination

### Runtime Performance  
- **Circular dependency prevention**: Avoid runtime resolution cycles
- **Module loading**: Faster initial bundle parsing
- **Memory usage**: Reduced runtime type checking overhead

### Developer Experience
- **Auto-fix**: Most issues can be automatically resolved
- **Consistency**: Standardized import/export patterns
- **IDE support**: Better IntelliSense and refactoring

## Validation

### Before Implementation
```bash
# Check current type import violations
npx eslint . --ext ts,tsx --rule "@typescript-eslint/consistent-type-imports: error" | grep -c "error"

# Estimate impact of auto-fixes
npx eslint . --ext ts,tsx --fix --dry-run --rule "@typescript-eslint/consistent-type-imports: error"
```

### After Implementation  
```bash
# Verify all type imports are correct
npm run lint:type-imports

# Check bundle size impact
npm run build && ls -la dist/
```

---

**Document Version**: 1.0  
**Implementation Phase**: 0.5 (Preparation) + 4 (Enforcement)  
**Auto-fix Capable**: Yes (majority of rules)  
**Bundle Impact**: Significant size reduction expected