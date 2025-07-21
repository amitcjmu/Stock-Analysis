# API Hook Types - Modular Structure

This directory contains the modularized API hook types, previously consolidated in a single 520-line file with 131 functions. The types are now organized by domain for better maintainability and tree-shaking.

## Structure

```
api/
├── index.ts           # Barrel export for all modules
├── core.ts           # Core API hooks (UseApi, UseRequest, UseApiClient, UseApiState)
├── query.ts          # Query hooks (UseQuery, UseInfiniteQuery)
├── mutation.ts       # Mutation hooks (UseMutation)
├── subscription.ts   # Real-time hooks (UseSubscription)
├── batch.ts          # Batch operations (UseBatchRequest)
├── file-operations.ts # File operations (UseFileUpload)
├── cache.ts          # Cache management (UseCache)
├── shared.ts         # Shared types used across modules
└── README.md         # This file
```

## Migration Guide

### Old Import (Deprecated)
```typescript
import { UseQueryParams, UseQueryReturn } from '@/types/hooks/api';
```

### New Import (Recommended)
```typescript
// Import from specific modules for better tree-shaking
import { UseQueryParams, UseQueryReturn } from '@/types/hooks/api/query';
import { UseMutationParams } from '@/types/hooks/api/mutation';
import { UseFileUploadParams } from '@/types/hooks/api/file-operations';
```

### Backward Compatibility
The original `api.ts` file still exists and re-exports all types for backward compatibility. However, it's marked as deprecated and new code should use the modular imports.

## Module Overview

### Core (`core.ts`)
- **UseApi**: Base API hook for general HTTP operations
- **UseRequest**: Request execution with progress tracking
- **UseApiClient**: API client management with interceptors
- **UseApiState**: API state management utilities

### Query (`query.ts`)
- **UseQuery**: Standard data fetching with caching
- **UseInfiniteQuery**: Paginated/infinite scrolling queries

### Mutation (`mutation.ts`)
- **UseMutation**: Data modification with optimistic updates

### Subscription (`subscription.ts`)
- **UseSubscription**: WebSocket, SSE, and polling subscriptions

### Batch (`batch.ts`)
- **UseBatchRequest**: Execute multiple requests in batch

### File Operations (`file-operations.ts`)
- **UseFileUpload**: File upload with chunking and progress

### Cache (`cache.ts`)
- **UseCache**: Client-side caching with TTL management

### Shared (`shared.ts`)
Common types used across modules:
- API response interfaces
- Configuration types (RetryConfig, CacheConfig, AuthConfig)
- Interceptor interfaces
- Progress tracking types
- HTTP method and response type enums

## Benefits of Modularization

1. **Better Organization**: Related types are grouped together
2. **Improved Maintainability**: Easier to locate and modify specific hook types
3. **Tree-shaking**: Import only what you need for smaller bundle sizes
4. **Type Safety**: Clear separation of concerns with focused interfaces
5. **Scalability**: Easy to add new hook types without cluttering existing files

## Type Count Summary

- **Total Interfaces**: 46 main interfaces
- **Hook Pairs**: 11 (Params + Return interfaces)
- **Supporting Types**: 24 additional types and interfaces
- **Type Aliases**: 5 type definitions