# Agent Observability Components - Phase 4A

This directory contains the core frontend components for the Agent Observability Enhancement project, implementing Phase 4A requirements.

## Overview

The Agent Observability Components provide a comprehensive dashboard for monitoring individual agent performance, status, and metrics in real-time. These components integrate with the backend APIs from Phase 3 to deliver a complete observability solution.

## Components

### Core Components

#### `AgentListOverview`
Main dashboard component displaying a grid/list of agent performance cards.

```tsx
import { AgentListOverview } from '../components/observability';

<AgentListOverview
  refreshInterval={30}
  showFilters={true}
  compactView={false}
  onAgentSelect={(agent) => console.log('Selected:', agent)}
/>
```

#### `AgentPerformanceCard`
Individual agent performance display with metrics and status.

```tsx
import { AgentPerformanceCard } from '../components/observability';

<AgentPerformanceCard
  agent={agentData}
  detailed={true}
  showChart={true}
  onClick={handleAgentClick}
/>
```

#### `AgentStatusIndicator`
Visual status indicators with multiple variants.

```tsx
import { AgentStatusIndicator } from '../components/observability';

<AgentStatusIndicator
  status="active"
  variant="badge"
  size="md"
  showLabel={true}
  pulse={true}
/>
```

#### `AgentMetricsChart`
Performance trend visualization components.

```tsx
import { SparklineChart, SuccessRateGauge } from '../components/observability';

<SparklineChart
  data={sparklineData}
  title="Success Rate Trend"
  height={80}
  animate={true}
/>

<SuccessRateGauge value={0.95} size={120} />
```

### Enhanced Components

#### `ResponsiveAgentListOverview`
Enhanced version with comprehensive responsive design and error handling.

```tsx
import { ResponsiveAgentListOverview } from '../components/observability';

<ResponsiveAgentListOverview
  refreshInterval={30}
  showFilters={true}
  onAgentSelect={handleAgentSelect}
/>
```

### Utility Components

#### `ObservabilityErrorBoundary`
Error boundary for handling component errors gracefully.

```tsx
import { ObservabilityErrorBoundary } from '../components/observability';

<ObservabilityErrorBoundary showDetails={true}>
  <YourObservabilityComponents />
</ObservabilityErrorBoundary>
```

#### Loading States
Various loading state components for different scenarios.

```tsx
import {
  LoadingSpinner,
  AgentListSkeleton,
  ProgressiveLoader
} from '../components/observability';

<LoadingSpinner text="Loading agents..." size="lg" />
<AgentListSkeleton count={6} />
<ProgressiveLoader stages={loadingStages} currentStage={2} />
```

### Hooks

#### `useResponsiveLayout`
Responsive design utilities.

```tsx
import { useResponsiveLayout, useGridLayout } from '../components/observability';

const { isMobile, isTablet, breakpoint } = useResponsiveLayout();
const { columns, gridClass } = useGridLayout(4);
```

## Integration

### 1. Basic Integration

Replace existing agent displays with the new components:

```tsx
// Before
<OldAgentMonitor />

// After
import { AgentListOverview } from '../components/observability';

<AgentListOverview
  refreshInterval={30}
  showFilters={true}
  onAgentSelect={handleAgentSelect}
/>
```

### 2. Enhanced Observability Page

Create a comprehensive observability dashboard:

```tsx
import {
  ResponsiveAgentListOverview,
  ObservabilityErrorBoundary
} from '../components/observability';

const ObservabilityDashboard = () => {
  return (
    <ObservabilityErrorBoundary>
      <div className="space-y-6">
        <h1>Agent Observability Dashboard</h1>
        <ResponsiveAgentListOverview
          refreshInterval={30}
          showFilters={true}
          onAgentSelect={handleAgentSelect}
        />
      </div>
    </ObservabilityErrorBoundary>
  );
};
```

### 3. Custom Integration

Use individual components for custom layouts:

```tsx
import {
  AgentStatusIndicator,
  AgentPerformanceCard,
  SparklineChart
} from '../components/observability';

const CustomDashboard = () => {
  return (
    <div className="grid grid-cols-3 gap-6">
      <div>
        <AgentStatusIndicator status="active" variant="badge" />
        <AgentPerformanceCard agent={agent} detailed={false} />
      </div>
      <div className="col-span-2">
        <SparklineChart data={chartData} title="Performance Trend" />
      </div>
    </div>
  );
};
```

## API Integration

The components use the `agentObservabilityService` for data fetching:

```tsx
import { agentObservabilityService } from '../../services/api/agentObservabilityService';

// Get all agents
const summary = await agentObservabilityService.getAllAgentsSummary();

// Get specific agent performance
const performance = await agentObservabilityService.getAgentPerformance('AgentName');

// Get real-time activity
const activity = await agentObservabilityService.getAgentActivityFeed();
```

## Styling and Theming

Components use Tailwind CSS with the existing design system:

- Consistent with existing UI components (`Card`, `Button`, `Badge`)
- Responsive design breakpoints
- Dark mode support (via CSS variables)
- Customizable via className props

## Performance Considerations

1. **Auto-refresh**: Components include intelligent refresh intervals
2. **Loading States**: Progressive loading for better UX
3. **Error Handling**: Comprehensive error boundaries and retry logic
4. **Responsive**: Optimized layouts for all screen sizes
5. **Caching**: Service layer includes response caching

## Browser Support

- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Mobile browsers (iOS Safari 14+, Chrome Mobile 90+)
- Responsive design for screen sizes 320px - 2560px

## Dependencies

- React 18+
- Lucide React (icons)
- Tailwind CSS (styling)
- clsx & tailwind-merge (utility functions)

## Future Enhancements (Phase 4B)

- Advanced analytics and reporting
- Real-time WebSocket updates
- Agent performance comparison
- Historical trend analysis
- Custom dashboards and widgets
- Export and sharing capabilities

## Troubleshooting

### Common Issues

1. **Components not loading**: Check API endpoints are accessible
2. **Styling issues**: Ensure Tailwind CSS is properly configured
3. **Type errors**: Verify all required types are imported
4. **Performance issues**: Check refresh intervals and data volume

### Debug Mode

Enable debug logging:

```tsx
// In development, components log additional debug information
console.log('Agent data:', agentData);
```

## Support

For issues related to these components:
1. Check the browser console for errors
2. Verify API connectivity
3. Review component props and usage
4. Check responsive design breakpoints

---

**Implementation Status**: ✅ Phase 4A Complete

**Next Phase**: Phase 4B - Advanced Features and Analytics
