# Admin Type System Documentation

## Overview

The admin type system has been modularized for better maintainability, type safety, and developer experience. This document describes the new structure and migration guide.

## Directory Structure

```
admin/
├── common/                 # Shared types used across admin modules
│   ├── device-info.ts     # Device-related types
│   ├── enums.ts          # Common enumerations
│   ├── filters.ts        # Filtering and query types
│   ├── geo-location.ts   # Geographic location types
│   ├── metadata.ts       # Metadata patterns
│   ├── time-ranges.ts    # Time-related types
│   └── index.ts          # Common types export
│
├── notifications/         # Notification management types
│   ├── api-types.ts      # API request/response types
│   ├── delivery.ts       # Delivery and channel types
│   ├── enums.ts         # Notification-specific enums
│   ├── notification.ts   # Core notification types
│   ├── templates.ts      # Template management types
│   ├── tracking.ts       # Tracking and analytics types
│   └── index.ts         # Notification types export
│
├── analytics/            # Analytics and reporting types
│   ├── api-types.ts     # API request/response types
│   ├── enums.ts        # Analytics-specific enums
│   ├── insights.ts      # Insights and alerts types
│   ├── performance.ts   # Performance metrics types
│   ├── platform.ts      # Platform analytics types
│   ├── reports.ts       # Report generation types
│   ├── usage.ts         # Usage analytics types
│   └── index.ts        # Analytics types export
│
├── audit/               # Audit and security types
│   ├── activity.ts      # User activity types
│   ├── api-types.ts     # API request/response types
│   ├── audit-log.ts     # Audit log types
│   ├── enums.ts        # Audit-specific enums
│   ├── security-events.ts # Security event types
│   └── index.ts        # Audit types export
│
├── notification-types.ts  # Deprecated - maintained for backward compatibility
├── analytics-reporting-types.ts # Deprecated - maintained for backward compatibility
└── audit-logging-types.ts # Deprecated - maintained for backward compatibility
```

## Migration Guide

### Old Import Pattern (Still Works)
```typescript
// Importing from monolithic files
import { 
  Notification, 
  GeoLocation, 
  DeviceInfo 
} from '@/types/api/admin/notification-types';

import { 
  PlatformAnalytics, 
  ReportType 
} from '@/types/api/admin/analytics-reporting-types';

import { 
  AuditLog, 
  SecurityEvent 
} from '@/types/api/admin/audit-logging-types';
```

### New Import Pattern (Recommended)
```typescript
// Import from specific modules for better tree-shaking
import { Notification } from '@/types/api/admin/notifications/notification';
import { GeoLocation, DeviceInfo } from '@/types/api/admin/common';

import { PlatformAnalytics } from '@/types/api/admin/analytics/platform';
import { ReportType } from '@/types/api/admin/analytics/enums';

import { AuditLog } from '@/types/api/admin/audit/audit-log';
import { SecurityEvent } from '@/types/api/admin/audit/security-events';

// Or import everything from a module
import * as NotificationTypes from '@/types/api/admin/notifications';
import * as AnalyticsTypes from '@/types/api/admin/analytics';
import * as AuditTypes from '@/types/api/admin/audit';
```

## Benefits of Modularization

### 1. **Reduced Duplication**
- Common types like `GeoLocation` and `DeviceInfo` are now defined once in the `common` module
- Shared enums and metadata patterns are centralized

### 2. **Better Organization**
- Related types are grouped together in focused modules
- Easier to find and understand type relationships
- Clear separation of concerns

### 3. **Improved Maintainability**
- Smaller files are easier to review and modify
- Changes are localized to specific modules
- Reduced merge conflicts in team development

### 4. **Enhanced Developer Experience**
- Better IDE support with focused imports
- Improved type inference and autocomplete
- Clearer import paths indicate type purpose

### 5. **Type Safety**
- Consistent type definitions across modules
- Strong typing for all admin operations
- Compile-time validation of type usage

## Common Types Reference

### Geographic and Location Types
- `GeoLocation` - Geographic location with coordinates
- `Address` - Physical address information
- `LocationRestriction` - Location-based access restrictions
- `ActivityLocation` - Location activity tracking

### Device Information Types
- `DeviceInfo` - Device details and fingerprinting
- `DeviceType` - Device type enumeration
- `TrustedDevice` - Trusted device management
- `ActivityDevice` - Device activity tracking

### Metadata Types
- `BaseMetadata` - Common metadata pattern
- `AuditMetadata` - Audit-specific metadata
- `NotificationMetadata` - Notification metadata
- `AnalyticsMetadata` - Analytics metadata
- `ReportMetadata` - Report metadata
- `SecurityEventMetadata` - Security event metadata

### Time and Scheduling Types
- `TimeRange` - Basic time range
- `AnalyticsTimeRange` - Analytics time range with granularity
- `RecurringSchedule` - Recurring schedule configuration
- `QuietHours` - Quiet hours configuration

### Common Enumerations
- `Priority` - Priority levels (low, medium, high, critical)
- `Severity` - Severity levels
- `ConfidenceLevel` - Confidence levels for predictions
- `ImpactLevel` - Impact assessment levels
- `Environment` - Environment types (production, staging, etc.)

### Filtering and Query Types
- `BaseFilter` - Base filter interface
- `Condition` - Condition-based filtering
- `RateLimit` - Rate limiting configuration
- `RetryPolicy` - Retry policy configuration

## Best Practices

1. **Import Specific Types**: Import only what you need for better tree-shaking
2. **Use Type Guards**: Leverage TypeScript's type narrowing capabilities
3. **Avoid Circular Dependencies**: Import from specific modules, not index files when possible
4. **Document Complex Types**: Add JSDoc comments for complex type structures
5. **Maintain Backward Compatibility**: Use the re-export files during migration periods

## Future Improvements

1. **Type Validation**: Runtime validation utilities for API responses
2. **Type Generators**: Generate types from OpenAPI specifications
3. **Mock Data Factories**: Type-safe mock data generation for testing
4. **Type Documentation**: Auto-generated documentation from TypeScript definitions

Generated with CC for modular admin type organization.