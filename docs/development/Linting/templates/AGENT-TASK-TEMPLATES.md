# AI Agent Task Templates

## Overview
This document provides standardized task templates for AI agents working on ESLint compliance. Each template includes specific instructions, validation requirements, and success criteria.

## Template A: Forward Declaration Agent

### Agent Profile
- **Agent ID**: Agent A
- **Wave**: 1 (High-Impact)
- **Duration**: 6 hours
- **Target Errors**: 111 (Forward declaration placeholders)

### Task Description
Replace forward declaration placeholders with proper TypeScript interface definitions in core type files.

### Specific Instructions
```
OBJECTIVE: Replace `{ [key: string]: any; }` patterns with proper interface definitions

TARGET FILES:
- src/types/api/planning/timeline/core-types.ts (42 errors)
- src/types/api/planning/strategy/core-types.ts (37 errors)
- src/types/api/finops/flow-management.ts (32 errors)

REPLACEMENT STRATEGY:
1. Identify forward declaration pattern: `{ [key: string]: any; }`
2. Analyze context and usage patterns
3. Replace with proper interface using shared types from /src/types/shared/
4. Use AnalysisResult, CostAnalysis, BaseMetadata interfaces where applicable
5. Ensure all properties have specific types

TEMPLATE REPLACEMENT:
// BEFORE:
interface SomeAnalysis { [key: string]: any; }

// AFTER:
interface SomeAnalysis {
  analysisType: string;
  results: AnalysisResult[];
  confidence: number;
  recommendations: string[];
  metadata: BaseMetadata;
  [additionalProps: string]: unknown; // Only if truly dynamic
}

VALIDATION REQUIREMENTS:
- TypeScript compilation must pass
- No new ESLint errors introduced
- All usages of modified interfaces must remain functional
- Import shared types correctly
```

### Success Criteria
- [ ] All 111 targeted any-type errors eliminated
- [ ] TypeScript builds successfully
- [ ] No breaking changes to existing code
- [ ] Proper use of shared type definitions

---

## Template B: Metadata Standardization Agent

### Agent Profile
- **Agent ID**: Agent B  
- **Wave**: 1 (High-Impact)
- **Duration**: 6 hours
- **Target Errors**: 80 (Metadata containers)

### Task Description
Standardize metadata containers across API type definitions using shared metadata interfaces.

### Specific Instructions
```
OBJECTIVE: Replace `metadata: Record<string, any>` with typed metadata interfaces

TARGET PATTERN: metadata: Record<string, any>

REPLACEMENT STRATEGY:
1. Identify all metadata property definitions
2. Determine appropriate metadata type based on context:
   - BaseMetadata: Basic tags, labels, annotations
   - AuditableMetadata: Includes audit trails (createdBy, updatedBy, etc.)
   - DomainMetadata: Domain-specific extensions
3. Replace with typed interface
4. Import shared metadata types

TEMPLATE REPLACEMENT:
// BEFORE:
interface SomeEntity {
  id: string;
  name: string;
  metadata: Record<string, any>;
}

// AFTER:
import { AuditableMetadata } from '../shared/metadata-types';

interface SomeEntity {
  id: string;
  name: string;
  metadata: AuditableMetadata;
}

VALIDATION REQUIREMENTS:
- All metadata usages compile correctly
- Existing metadata properties remain accessible
- Import paths are correct
- No circular dependencies
```

### Success Criteria
- [ ] All 80 metadata any-type errors eliminated
- [ ] Consistent metadata typing across domains
- [ ] Proper import of shared metadata types
- [ ] No functional regressions

---

## Template C: Configuration Value Agent

### Agent Profile
- **Agent ID**: Agent C
- **Wave**: 1 (High-Impact)  
- **Duration**: 6 hours
- **Target Errors**: 60 (Configuration values)

### Task Description
Replace generic configuration values with proper union types in constraint and criteria systems.

### Specific Instructions
```
OBJECTIVE: Replace `value: any` with typed configuration values

TARGET PATTERN: value: any (in constraint/criteria contexts)

REPLACEMENT STRATEGY:
1. Identify configuration value patterns
2. Analyze actual value types used in codebase
3. Create union types for common configuration patterns
4. Use ConfigurationValue type for generic configs
5. Create specific types for domain constraints

TEMPLATE REPLACEMENT:
// BEFORE:
interface Constraint {
  type: string;
  value: any;
  description: string;
}

// AFTER:  
import { ConfigurationValue } from '../shared/config-types';

interface Constraint {
  type: string;
  value: ConfigurationValue;
  description: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
}

CONFIGURATION VALUE TYPES:
type ConfigurationValue = 
  | string 
  | number 
  | boolean 
  | string[] 
  | number[]
  | Record<string, unknown>;

VALIDATION REQUIREMENTS:
- All constraint values must be assignable to ConfigurationValue
- Existing configurations remain valid
- Type safety improved without breaking changes
```

### Success Criteria
- [ ] All 60 configuration any-type errors eliminated
- [ ] Type-safe configuration handling
- [ ] Backward compatibility maintained
- [ ] Union types properly implemented

---

## Template D: Form Hook Agent

### Agent Profile
- **Agent ID**: Agent D
- **Wave**: 2 (Medium-Impact)
- **Duration**: 6 hours
- **Target Errors**: 50 (Form handling)

### Task Description
Implement proper TypeScript integration for React Hook Form and event handling systems.

### Specific Instructions
```
OBJECTIVE: Replace generic form types with proper React Hook Form TypeScript integration

TARGET FILES:
- src/types/hooks/shared/form-hooks.ts (37 errors)
- src/hooks/useUnifiedDiscoveryFlow.ts (25 errors)

REPLACEMENT STRATEGY:
1. Replace TFieldValues = any with specific form data types
2. Type event handlers properly
3. Use React Hook Form's FieldValues where appropriate
4. Create domain-specific form interfaces

TEMPLATE REPLACEMENT:
// BEFORE:
interface FormHookConfig<TFieldValues = any> {
  control: any;
  resolver: any;
  defaultValues?: TFieldValues;
}

// AFTER:
import { Control, FieldValues, Resolver } from 'react-hook-form';

interface FormHookConfig<TFieldValues extends FieldValues = FieldValues> {
  control: Control<TFieldValues>;
  resolver: Resolver<TFieldValues>;
  defaultValues?: Partial<TFieldValues>;
}

VALIDATION REQUIREMENTS:
- React Hook Form types imported correctly
- Form submissions remain functional
- Validation logic preserved
- Event handlers properly typed
```

### Success Criteria
- [ ] All 50 form any-type errors eliminated
- [ ] Proper React Hook Form integration
- [ ] Type-safe form handling
- [ ] No form functionality regressions

---

## Template E: API Response Agent

### Agent Profile
- **Agent ID**: Agent E
- **Wave**: 2 (Medium-Impact)
- **Duration**: 6 hours
- **Target Errors**: 40 (API responses)

### Task Description
Create proper TypeScript definitions for API response types and utility functions.

### Specific Instructions
```
OBJECTIVE: Replace any types in API response handling with proper interfaces

TARGET FILES:
- src/utils/api/apiTypes.ts (30 errors)
- Related API utility files

REPLACEMENT STRATEGY:
1. Identify API response patterns
2. Create proper response interfaces
3. Use generic types for common API patterns
4. Implement proper error handling types

TEMPLATE REPLACEMENT:
// BEFORE:
interface ApiResponse {
  data: any;
  error?: any;
  meta?: any;
}

// AFTER:
interface ApiResponse<TData = unknown, TError = ApiError> {
  data: TData;
  error?: TError;
  meta?: ResponseMetadata;
}

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

VALIDATION REQUIREMENTS:
- API calls compile correctly
- Response handling remains functional
- Error types properly defined
- Generic types work with all API endpoints
```

### Success Criteria
- [ ] All 40 API any-type errors eliminated
- [ ] Type-safe API response handling
- [ ] Generic API interfaces implemented
- [ ] Error handling properly typed

---

## Template F: Component Props Agent

### Agent Profile
- **Agent ID**: Agent F
- **Wave**: 2 (Medium-Impact)
- **Duration**: 6 hours
- **Target Errors**: 35 (Component interfaces)

### Task Description
Define proper TypeScript interfaces for React component props and UI state management.

### Specific Instructions
```
OBJECTIVE: Replace any types in component prop definitions with proper interfaces

TARGET FILES:
- src/components/discovery/attribute-mapping/.../bulkOperations.ts (28 errors)
- src/types/components/discovery/data-import-types.ts (24 errors)

REPLACEMENT STRATEGY:
1. Analyze component prop usage patterns
2. Create proper prop interfaces
3. Use React's built-in types where appropriate
4. Define event handler signatures

TEMPLATE REPLACEMENT:
// BEFORE:
interface ComponentProps {
  data: any;
  onSelect: (item: any) => void;
  config?: any;
}

// AFTER:
interface ComponentProps<TData = unknown> {
  data: TData;
  onSelect: (item: TData) => void;
  config?: ComponentConfig;
}

interface ComponentConfig {
  theme?: 'light' | 'dark';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
}

VALIDATION REQUIREMENTS:
- Component props properly typed
- Event handlers have correct signatures
- React component usage remains functional
- Props are properly constrained
```

### Success Criteria
- [ ] All 35 component any-type errors eliminated
- [ ] Type-safe component interfaces
- [ ] Proper React TypeScript integration
- [ ] Component functionality preserved

---

## Template G: Hook & State Agent

### Agent Profile
- **Agent ID**: Agent G
- **Wave**: 3 (Cleanup)
- **Duration**: 4 hours
- **Target Errors**: 30 (Hook patterns)

### Task Description
Implement proper typing for custom hooks and state management patterns.

### Specific Instructions
```
OBJECTIVE: Replace any types in custom hooks and state management with proper types

TARGET FILES:
- src/types/hooks/shared/ui-state.ts (23 errors)
- src/types/hooks/shared/base-patterns.ts (23 errors)

REPLACEMENT STRATEGY:
1. Analyze hook return types and parameters
2. Use proper React hook typing patterns
3. Define state shape interfaces
4. Type reducer actions and state updates

TEMPLATE REPLACEMENT:
// BEFORE:
function useCustomHook(): {
  data: any;
  actions: any;
} {
  // hook implementation
}

// AFTER:
interface HookState<TData = unknown> {
  data: TData;
  loading: boolean;
  error: string | null;
}

interface HookActions<TData = unknown> {
  update: (data: Partial<TData>) => void;
  reset: () => void;
  refresh: () => Promise<void>;
}

function useCustomHook<TData = unknown>(): {
  state: HookState<TData>;
  actions: HookActions<TData>;
} {
  // hook implementation
}

VALIDATION REQUIREMENTS:
- Hook types properly defined
- State management remains functional
- Actions properly typed
- Generic patterns work across use cases
```

### Success Criteria
- [ ] All 30 hook any-type errors eliminated
- [ ] Type-safe custom hooks
- [ ] Proper state management typing
- [ ] Hook patterns standardized

---

## Template H: Edge Cases Agent

### Agent Profile
- **Agent ID**: Agent H
- **Wave**: 3 (Cleanup)
- **Duration**: 4 hours  
- **Target Errors**: 25 (Remaining issues)

### Task Description
Address remaining edge cases and miscellaneous any-type usage across the codebase.

### Specific Instructions
```
OBJECTIVE: Address remaining any-type errors and edge cases

APPROACH:
1. Analyze each remaining any-type error individually
2. Determine appropriate typing strategy
3. Apply context-specific solutions
4. Handle complex/unusual patterns

EDGE CASE PATTERNS:
- Dynamic object creation
- Third-party library integration
- Complex generic constraints
- Legacy code compatibility

VALIDATION REQUIREMENTS:
- Each error addressed individually
- Solutions don't break existing functionality
- Types are as specific as possible
- Documentation added for complex cases
```

### Success Criteria
- [ ] All remaining any-type errors eliminated
- [ ] Edge cases properly handled
- [ ] Complex patterns documented
- [ ] Final ESLint compliance achieved

---

## Validation Framework

### Pre-Task Checklist
- [ ] Agent has access to shared type definitions
- [ ] Target files identified and analyzed
- [ ] Branch created for agent work
- [ ] Dependencies installed and up-to-date

### During-Task Validation
- [ ] TypeScript compilation passes after each change
- [ ] ESLint errors reducing as expected
- [ ] No new errors introduced
- [ ] Functionality verified through spot testing

### Post-Task Validation  
- [ ] All targeted errors eliminated
- [ ] Build and test suite passing
- [ ] Code review checklist completed
- [ ] Progress tracker updated

### Escalation Criteria
- TypeScript compilation failures
- Breaking changes to existing functionality
- Unable to determine proper type for complex cases
- Cross-agent conflicts or dependencies

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-21  
**Next Review**: After Phase 1 completion