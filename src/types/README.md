# TypeScript Module Boundaries and Namespace Organization

This directory contains a comprehensive TypeScript module boundary system that provides structured type organization, namespace declarations, and enhanced developer experience for the Migration Platform application.

## 🏗️ Architecture Overview

The type system is organized into five main categories:

1. **Module Namespaces** (`/modules/`) - Core business logic type declarations
2. **Component Types** (`/components/`) - React component prop and state types
3. **Hook Types** (`/hooks/`) - Custom hook parameter and return types
4. **API Types** (`/api/`) - Request/response and client interface types
5. **Utilities** (`/guards.ts`, `/global.ts`) - Type guards, validation, and global declarations

## 📁 Directory Structure

```
src/types/
├── index.ts                 # Main barrel export with module boundaries
├── guards.ts               # Type guards and validation utilities
├── global.ts               # Global type declarations
├── modules/
│   ├── index.ts            # Module namespace barrel exports
│   ├── discovery.ts        # DiscoveryFlow namespace
│   ├── flow-orchestration.ts  # FlowOrchestration namespace
│   └── shared-utilities.ts # SharedUtilities namespace
├── components/
│   ├── index.ts            # Component type barrel exports
│   ├── navigation.ts       # Navigation component types
│   ├── discovery.ts        # Discovery component types
│   ├── shared.ts           # Shared component types
│   ├── forms.ts            # Form component types
│   ├── layout.ts           # Layout component types
│   ├── data-display.ts     # Data display component types
│   ├── feedback.ts         # Feedback component types
│   └── admin.ts            # Admin component types
├── hooks/
│   ├── index.ts            # Hook type barrel exports
│   ├── discovery.ts        # Discovery-specific hooks
│   ├── shared.ts           # Common hook patterns
│   ├── api.ts              # API-related hooks
│   ├── state-management.ts # State management hooks
│   ├── flow-orchestration.ts # Flow orchestration hooks
│   └── admin.ts            # Admin hooks
└── api/
    ├── index.ts            # API type barrel exports
    ├── shared.ts           # Common API types
    ├── discovery.ts        # Discovery API types
    ├── assessment.ts       # Assessment API types
    ├── planning.ts         # Planning API types
    ├── execution.ts        # Execution API types
    ├── modernize.ts        # Modernization API types
    ├── finops.ts           # FinOps API types
    ├── observability.ts    # Observability API types
    ├── decommission.ts     # Decommission API types
    ├── admin.ts            # Admin API types
    └── auth.ts             # Authentication API types
```

## 🚀 Usage Examples

### Basic Imports

```typescript
// Import specific module namespaces
import { DiscoveryFlow, FlowOrchestration, SharedUtilities } from '@/types';

// Import component types
import { NavigationComponents, DiscoveryComponents } from '@/types';

// Import hook types
import { DiscoveryHooks, SharedHooks, APIHooks } from '@/types';

// Import API types
import { DiscoveryAPI, AssessmentAPI, SharedAPI } from '@/types';
```

### Using Module Namespaces

```typescript
// DiscoveryFlow namespace usage
type FlowData = DiscoveryFlow.Models.FlowData;
type FlowState = DiscoveryFlow.Models.FlowState;
type FlowPhase = DiscoveryFlow.Models.FlowPhase;

// FlowOrchestration namespace usage
type AgentConfig = FlowOrchestration.Models.AgentConfiguration;
type CrewConfig = FlowOrchestration.Models.CrewConfiguration;
type TaskDef = FlowOrchestration.Models.TaskDefinition;

// SharedUtilities namespace usage
type AuthService = SharedUtilities.Auth.AuthenticationService;
type APIClient = SharedUtilities.API.APIClientService;
```

### Component Type Usage

```typescript
import { FieldMappingsTabProps, NavigationSidebarProps } from '@/types';

// Using component props
const FieldMappingsTab: React.FC<FieldMappingsTabProps> = ({
  flowId,
  mappings,
  onMappingUpdate,
  // ... other props with full type safety
}) => {
  // Component implementation
};
```

### Hook Type Usage

```typescript
import { UseAttributeMappingParams, UseAttributeMappingReturn } from '@/types';

// Custom hook with proper typing
const useAttributeMapping = (
  params: UseAttributeMappingParams
): UseAttributeMappingReturn => {
  // Hook implementation with full type safety
};
```

### API Type Usage

```typescript
import { 
  InitializeDiscoveryFlowRequest, 
  InitializeDiscoveryFlowResponse 
} from '@/types';

// API function with proper typing
const initializeFlow = async (
  request: InitializeDiscoveryFlowRequest
): Promise<InitializeDiscoveryFlowResponse> => {
  // API call implementation
};
```

## 🛡️ Type Safety Features

### Module Boundary Enforcement

```typescript
import { validateModuleBoundary, MODULE_BOUNDARIES } from '@/types';

// Validate module boundaries at runtime
const isValidModule = validateModuleBoundary('COMPONENTS', 'discovery'); // true
const isInvalid = validateModuleBoundary('COMPONENTS', 'invalid'); // false

// Get available modules
const availableComponents = getAvailableModules('COMPONENTS');
// ['navigation', 'discovery', 'shared', 'forms', 'layout', 'data-display', 'feedback', 'admin']
```

### Type Guards

```typescript
import { 
  isDiscoveryFlow, 
  isFieldMapping, 
  TypeRegistry,
  BaseApiRequestGuard 
} from '@/types';

// Runtime type checking
if (isDiscoveryFlow(data)) {
  // data is now typed as DiscoveryFlow.Models.FlowData
  console.log(data.flowName);
}

// Schema-based validation
const apiRequestValidation = BaseApiRequestGuard.validate(requestData);
if (!apiRequestValidation.isValid) {
  console.error('Validation errors:', apiRequestValidation.errors);
}

// Type registry usage
if (TypeRegistry.check('FieldMapping', data)) {
  // data is properly typed
}
```

### Branded Types

```typescript
import { FlowId, UserId, createFlowId, assertIsFlowId } from '@/types';

// Create branded types for type safety
const flowId: FlowId = createFlowId('flow-123');
const userId: UserId = createUserId('user-456');

// Type assertions
try {
  assertIsFlowId(someString);
  // someString is now guaranteed to be a FlowId
} catch (error) {
  console.error('Invalid FlowId');
}
```

## 🔧 Development Tools

### Browser Console Helpers (Development Mode)

```javascript
// Access type system utilities in browser console
window.__MIGRATION_PLATFORM_DEV__.typeGuards.listRegisteredTypes();
window.__MIGRATION_PLATFORM_DEV__.typeGuards.validateType('FieldMapping', data);
window.__MIGRATION_PLATFORM_DEV__.moduleHelpers.listAllTypes();
```

### Module Importers

```typescript
import { ComponentImporter, HookImporter, APIImporter } from '@/types';

// Type-safe dynamic imports
const isValidComponent = ComponentImporter.validate('discovery'); // true
const discoveryTypes = await ComponentImporter.importModule('discovery');

// Get available modules
const availableHooks = HookImporter.getAvailable();
// ['discovery', 'shared', 'api', 'state-management', 'flow-orchestration', 'admin']
```

### Custom Type Guards

```typescript
import { createTypeGuard, createValidatingTypeGuard } from '@/types';

// Simple type guard
const isCustomType = createTypeGuard<CustomType>(
  (obj): obj is CustomType => {
    return obj && typeof obj.id === 'string' && typeof obj.name === 'string';
  },
  'CustomType'
);

// Validating type guard with detailed errors
const customValidator = createValidatingTypeGuard<CustomType>(
  (obj) => {
    const errors: string[] = [];
    if (!obj?.id) errors.push('Missing id');
    if (!obj?.name) errors.push('Missing name');
    return { isValid: errors.length === 0, errors };
  },
  'CustomType'
);
```

## 📋 Best Practices

### 1. Import Organization

```typescript
// ✅ Good: Import from main entry point
import { DiscoveryFlow, UseAttributeMappingReturn } from '@/types';

// ❌ Avoid: Direct imports from nested files
import { DiscoveryFlow } from '@/types/modules/discovery';
```

### 2. Namespace Usage

```typescript
// ✅ Good: Use namespace organization
type FlowData = DiscoveryFlow.Models.FlowData;
type FlowService = DiscoveryFlow.Services.FlowManagementService;

// ❌ Avoid: Importing individual types without namespace context
import { FlowData, FlowManagementService } from '@/types';
```

### 3. Type Safety

```typescript
// ✅ Good: Use type guards for runtime validation
if (isDiscoveryFlow(data)) {
  processFlowData(data); // data is properly typed
}

// ❌ Avoid: Type assertions without validation
const flowData = data as DiscoveryFlow.Models.FlowData;
```

### 4. API Types

```typescript
// ✅ Good: Use specific request/response types
const handleRequest = async (
  request: InitializeDiscoveryFlowRequest
): Promise<InitializeDiscoveryFlowResponse> => {
  // Implementation
};

// ❌ Avoid: Generic any types
const handleRequest = async (request: any): Promise<any> => {
  // Implementation
};
```

## 🔍 Type System Metadata

```typescript
import { TYPE_SYSTEM_METADATA } from '@/types';

console.log(TYPE_SYSTEM_METADATA);
// {
//   version: '1.0.0',
//   build: '2024-01-15T10:30:00.000Z',
//   boundaries: { MODULES: [...], COMPONENTS: [...], ... },
//   description: 'TypeScript module boundaries and namespace organization system',
//   features: ['Module namespace declarations', 'Component type libraries', ...]
// }
```

## 🧪 Testing Type Definitions

```typescript
// Type-only tests for compile-time validation
type Tests = [
  // Test that FlowData has required properties
  Expect<Equal<keyof DiscoveryFlow.Models.FlowData, 'id' | 'flowName' | 'status' | 'phases'>>,
  
  // Test that API response extends base response
  Expect<Extends<InitializeDiscoveryFlowResponse, BaseApiResponse>>,
  
  // Test that hook return type has required methods
  Expect<HasProperty<UseAttributeMappingReturn, 'mappings'>>,
];
```

## 📈 Performance Considerations

- **Tree Shaking**: Barrel exports are optimized for tree shaking
- **Type-Only Imports**: Use `import type` for type-only imports when possible
- **Lazy Loading**: Module importers support dynamic imports for code splitting
- **Development Mode**: Type guards and validation are optimized for development builds

## 🔄 Migration Guide

When migrating existing code to use the new type system:

1. **Replace direct imports** with namespace imports
2. **Add type guards** for runtime validation
3. **Use branded types** for IDs and critical values
4. **Leverage component type libraries** for React components
5. **Adopt API type boundaries** for consistent request/response handling

## 📚 Related Documentation

- [Component Architecture Guide](../components/README.md)
- [Hook Patterns Guide](../hooks/README.md)
- [API Integration Guide](../api/README.md)
- [State Management Guide](../state/README.md)
- [Flow Orchestration Guide](../flows/README.md)

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintainers**: Development Team
