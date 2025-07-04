# Archived Frontend Code

This directory contains archived legacy frontend code that has been replaced or is no longer in use.

## Archived Components

### Discovery V2 Components
- **DiscoveryFlowV2.tsx** - Legacy Discovery Flow V2 page
- **DiscoveryFlowV2Dashboard.tsx** - Legacy dashboard component
- **useDiscoveryFlowV2.ts** - Legacy hook for V2 flow
- **discoveryFlowV2Service.ts** - Legacy V2 service
- **UploadBlockerV2.tsx** - Legacy upload blocker V2
- **useIncompleteFlowDetectionV2.ts** - Legacy incomplete flow detection

### Duplicate Components
- **RealTimeProcessingMonitor.tsx** - Duplicate of UniversalProcessingStatus
- **AssetInventory.tsx** - Duplicate inventory page (using Inventory.tsx instead)
- **AssetInventoryRedesigned.tsx** - Another duplicate inventory page

### Demo/Test Components
- **DataImportDemo.tsx** - Demo data import page
- **DemoInitializeFlow.tsx** - Demo assessment flow initialization

## Why Archived

These components were archived as part of the platform cleanup effort to:
1. Remove duplicate implementations
2. Eliminate legacy V2 API references
3. Consolidate to single implementations
4. Reduce code complexity and maintenance burden

## Migration Notes

- For Discovery Flow: Use the unified discovery flow at `/api/v1/unified-discovery/`
- For Real-time Monitoring: Use `UniversalProcessingStatus` component
- For Inventory: Use the main `Inventory.tsx` page component
- All V2 APIs have been removed from the backend

Last updated: July 2025