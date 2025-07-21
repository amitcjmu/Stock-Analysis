# Admin Component Architecture

## Overview

The admin component system has been modularized to promote code reuse, maintainability, and consistency across admin dashboard interfaces. This document outlines the architecture and usage patterns for admin components in the AI Modernize Migration Platform.

## Architecture Overview

```
src/components/admin/
├── shared/                           # Shared admin utilities and components
│   ├── components/                   # Reusable UI components
│   │   ├── StatCard.tsx             # Metric display cards
│   │   ├── ProgressCard.tsx         # Progress visualization cards
│   │   ├── ActionCard.tsx           # Quick action cards with buttons
│   │   ├── AdminHeader.tsx          # Consistent page headers
│   │   ├── AdminLoadingState.tsx    # Loading and error states
│   │   └── index.ts                 # Component exports
│   ├── hooks/                       # Shared admin hooks
│   │   ├── useAdminToasts.ts       # Toast notifications
│   │   ├── useAdminData.ts         # Data fetching patterns
│   │   └── index.ts                # Hook exports
│   ├── utils/                       # Shared utilities
│   │   └── adminFormatters.ts      # Formatting functions
│   └── index.ts                     # Main module exports
├── platform-admin/                  # Platform administration
│   ├── components/                  # Platform-specific components
│   └── PlatformAdminDashboard.tsx  # Main platform admin page
├── user-approvals/                  # User approval management
│   ├── [existing components]       # Already modularized
│   └── UserApprovalsMain.tsx       # Main user approval page
└── pages/admin/                     # Admin dashboard pages
    ├── components/                  # Dashboard-specific components
    └── AdminDashboard.tsx          # Main admin dashboard
```

## Core Components

### Shared Components

#### StatCard
Displays key metrics with optional icons and trend indicators.

```tsx
import { StatCard } from '@/components/admin/shared/components/StatCard';

<StatCard
  title="Total Users"
  value={42}
  description="active users"
  icon={Users}
  change={{
    value: 12,
    label: "from last month",
    type: "increase"
  }}
/>
```

#### ProgressCard
Shows data distribution with progress bars.

```tsx
import { ProgressCard } from '@/components/admin/shared/components/ProgressCard';

<ProgressCard
  title="Clients by Industry"
  description="Distribution across sectors"
  items={[
    { label: "Technology", value: 15, total: 50 },
    { label: "Healthcare", value: 20, total: 50 }
  ]}
/>
```

#### ActionCard
Provides quick action buttons for common tasks.

```tsx
import { ActionCard } from '@/components/admin/shared/components/ActionCard';

<ActionCard
  title="Quick Actions"
  description="Common tasks"
  actions={[
    {
      label: "Create User",
      href: "/admin/users/new",
      icon: Plus,
      variant: "default"
    }
  ]}
/>
```

#### AdminHeader
Consistent page headers with actions and refresh capability.

```tsx
import { AdminHeader } from '@/components/admin/shared/components/AdminHeader';

<AdminHeader
  title="Admin Dashboard"
  description="Manage platform resources"
  onRefresh={() => refetch()}
  actions={[
    {
      label: "New Client",
      href: "/admin/clients/new",
      icon: Plus
    }
  ]}
/>
```

### Shared Hooks

#### useAdminToasts
Consistent toast messaging across admin components.

```tsx
import { useAdminToasts } from '@/components/admin/shared';

const { 
  showUserApprovedToast, 
  showGenericErrorToast 
} = useAdminToasts();

// Usage
showUserApprovedToast("John Doe");
showGenericErrorToast("approve user");
```

#### useAdminData
Common data fetching pattern with demo fallbacks.

```tsx
import { useAdminData } from '@/components/admin/shared';

const { data, loading, error, refetch, isUsingDemoData } = useAdminData(
  '/admin/stats',
  demoData,
  { showDemoWarning: true }
);
```

### Shared Utilities

#### Admin Formatters
Common formatting functions used across admin components.

```tsx
import { 
  formatDate, 
  formatCurrency,
  getAccessLevelColor,
  safePercentage 
} from '@/components/admin/shared';

// Usage
const formattedDate = formatDate('2025-01-15T10:30:00Z');
const price = formatCurrency(1500);
const colorClass = getAccessLevelColor('admin');
const percentage = safePercentage(25, 100); // 25.0
```

## Component Patterns

### Dashboard Structure

Each admin dashboard follows a consistent structure:

1. **Header** - Page title, description, and primary actions
2. **Stats Overview** - Key metrics using StatCard components
3. **Tabbed Content** - Detailed analytics and management views
4. **Action Areas** - Quick actions and common tasks

### Data Loading Pattern

```tsx
// Standard pattern for admin components
const { data, loading, error, refetch } = useQuery({
  queryKey: ['adminData'],
  queryFn: fetchAdminData,
  retry: 1,
  staleTime: 5 * 60 * 1000
});

if (loading) return <AdminLoadingState />;
if (error) return <AdminErrorState onRetry={refetch} />;
```

### Error Handling

All admin components use consistent error handling:

```tsx
const { showGenericErrorToast, showDemoDataWarningToast } = useAdminToasts();

try {
  // API call
} catch (error) {
  console.error('Operation failed:', error);
  showGenericErrorToast('operation name');
}
```

## Component Organization

### Modularized Components

Each major admin section is broken into focused components:

**AdminDashboard Components:**
- `DashboardStats` - Overview metrics
- `ClientAnalytics` - Client distribution charts  
- `EngagementAnalytics` - Engagement progress and metrics
- `UserManagement` - User statistics and actions
- `RecentActivity` - Platform activity feed

**PlatformAdminDashboard Components:**
- `PlatformStats` - Purge request statistics
- `PendingItemsList` - List of deletion requests
- `PurgeActionDialog` - Approval/rejection dialog
- `ItemDetailsDialog` - Detailed request information

### Component Responsibilities

Each component has a single, focused responsibility:

- **Container Components** - Data fetching, state management
- **Presentation Components** - Pure UI rendering
- **Utility Components** - Shared functionality (headers, stats, etc.)

## Best Practices

### 1. Component Composition
Use shared components to build complex interfaces:

```tsx
<AdminHeader title="Dashboard" onRefresh={refetch} />
<div className="grid grid-cols-4 gap-6">
  <StatCard title="Users" value={users.length} />
  <StatCard title="Active" value={activeUsers.length} />
</div>
```

### 2. Consistent Styling
All components use Tailwind CSS with consistent patterns:
- Grid layouts: `grid grid-cols-X gap-6`
- Spacing: `space-y-6` for vertical, `gap-X` for grid
- Colors: Semantic color classes for status indicators

### 3. Accessibility
- Proper heading hierarchy (h1, h2, h3)
- Descriptive button labels
- Loading states with screen reader text
- Keyboard navigation support

### 4. Performance
- Use React.memo for pure components
- Implement proper loading states
- Debounce user inputs
- Lazy load heavy components

## Migration Notes

### Breaking Changes
- Removed individual utility functions from components
- Consolidated toast messaging patterns
- Standardized loading states

### Backward Compatibility
- All existing component interfaces maintained
- Gradual migration path available
- Demo data fallbacks preserved

## Usage Examples

### Creating a New Admin Page

```tsx
import React from 'react';
import { 
  AdminHeader, 
  StatCard, 
  AdminLoadingState 
} from '@/components/admin/shared';

export const NewAdminPage: React.FC = () => {
  const { data, loading, refetch } = useAdminData('/admin/new-data', demoData);
  
  if (loading) return <AdminLoadingState />;
  
  return (
    <div className="space-y-6">
      <AdminHeader 
        title="New Admin Page" 
        onRefresh={refetch}
      />
      
      <div className="grid grid-cols-3 gap-6">
        <StatCard title="Metric 1" value={data.metric1} />
        <StatCard title="Metric 2" value={data.metric2} />
        <StatCard title="Metric 3" value={data.metric3} />
      </div>
    </div>
  );
};
```

### Extending Existing Components

```tsx
// Custom stat card with additional functionality
const CustomStatCard: React.FC<CustomStatProps> = (props) => {
  return (
    <StatCard
      {...props}
      onClick={() => handleCustomAction()}
      className="cursor-pointer hover:shadow-lg"
    />
  );
};
```

## Future Enhancements

### Planned Additions
- [ ] AdminContext for global state management
- [ ] Real-time data updates with WebSocket integration
- [ ] Advanced filtering and search components
- [ ] Export functionality for reports
- [ ] Bulk action components

### Performance Improvements
- [ ] Virtual scrolling for large lists
- [ ] Component lazy loading
- [ ] Data caching strategies
- [ ] Bundle size optimization

## Support

For questions or issues with admin components:
1. Check this documentation for patterns and examples
2. Review existing component implementations
3. Follow the established conventions for new components
4. Ensure backward compatibility when making changes

---

*This documentation is maintained alongside the admin component codebase. Please update it when making architectural changes.*