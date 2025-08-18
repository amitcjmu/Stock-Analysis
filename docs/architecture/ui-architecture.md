# UI Architecture Documentation

## Overview

This document describes the UI/UX architecture of the AI Modernize Migration Platform, focusing on component design patterns, user experience flows, accessibility, and design system implementation.

## Design System Foundation

### Component Library Stack
- **Base**: Radix UI primitives for accessibility
- **Styling**: Tailwind CSS with custom design tokens
- **Components**: shadcn/ui component library
- **Icons**: Lucide React icon library
- **Theming**: CSS variables with light/dark mode support

### Design Tokens

```css
/* Core design tokens defined in globals.css */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96%;
  --accent: 210 40% 96%;
  --destructive: 0 84.2% 60.2%;
  --muted: 210 40% 96%;
  --border: 214.3 31.8% 91.4%;
  --radius: 0.5rem;
}
```

### Typography Hierarchy

```tsx
// Typography scale following design system
const typography = {
  h1: "scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl",
  h2: "scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight",
  h3: "scroll-m-20 text-2xl font-semibold tracking-tight",
  h4: "scroll-m-20 text-xl font-semibold tracking-tight",
  p: "leading-7 [&:not(:first-child)]:mt-6",
  lead: "text-xl text-muted-foreground",
  large: "text-lg font-semibold",
  small: "text-sm font-medium leading-none",
  muted: "text-sm text-muted-foreground",
}
```

## Component Architecture Patterns

### 1. Atomic Design Structure

```
Components Hierarchy:
├── Atoms (ui/)
│   ├── Button
│   ├── Input
│   ├── Card
│   └── Badge
├── Molecules (shared/)
│   ├── SearchField
│   ├── StatusIndicator
│   └── ProgressBar
├── Organisms (feature-specific/)
│   ├── DataTable
│   ├── UploadZone
│   └── AgentMonitor
└── Templates (pages/)
    ├── DiscoveryPage
    ├── AssessmentPage
    └── DashboardLayout
```

### 2. Composition Patterns

#### Compound Components
```tsx
// Example: Card compound component
<Card>
  <CardHeader>
    <CardTitle>Asset Analysis</CardTitle>
    <CardDescription>Review discovered assets</CardDescription>
  </CardHeader>
  <CardContent>
    <AssetTable data={assets} />
  </CardContent>
  <CardFooter>
    <Button>Export Report</Button>
  </CardFooter>
</Card>
```

#### Render Props Pattern
```tsx
// Example: Data fetching with render props
<DataProvider endpoint="/api/assets">
  {({ data, loading, error }) => (
    <>
      {loading && <LoadingSpinner />}
      {error && <ErrorAlert message={error.message} />}
      {data && <AssetGrid assets={data} />}
    </>
  )}
</DataProvider>
```

### 3. Layout Patterns

#### Responsive Grid System
```tsx
// Responsive layout using CSS Grid
const ResponsiveGrid = ({ children }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    {children}
  </div>
);
```

#### Sidebar Layout
```tsx
// Main application layout
const AppLayout = ({ children }) => (
  <div className="flex h-screen bg-background">
    <Sidebar />
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header />
      <main className="flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  </div>
);
```

## User Experience Flows

### 1. Migration Workflow Flow

```
Discovery → Collection → Assessment → Planning → Execution → Modernization → FinOps
    ↓         ↓            ↓           ↓          ↓            ↓             ↓
Data Import   Adaptive     6R Analysis  Wave      Cutover     Refactoring   Cost
Field Map     Forms        Tech Debt    Planning  Execution   Architecture  Analysis
Cleansing     Bulk Upload  Risk         Timeline  Rollback    Patterns      Savings
Inventory     Integration  Assessment   Resources Monitoring  Deployment    Tracking
Dependencies  Validation   Treatment    Targets   Reports     Progress      Budgets
```

### 2. User Journey Mapping

#### New User Onboarding
1. **Welcome Screen**: Platform overview and capabilities
2. **Client Setup**: Create client account and engagement
3. **Data Upload**: CMDB import with guided field mapping
4. **First Discovery**: Automated analysis with AI insights
5. **Results Review**: Interactive dashboard with recommendations

#### Power User Workflow
1. **Quick Navigation**: Keyboard shortcuts and breadcrumbs
2. **Bulk Operations**: Multi-select actions across data tables
3. **Advanced Filters**: Complex queries and saved searches
4. **Real-time Updates**: Live status monitoring and notifications
5. **Export/Reporting**: Customizable report generation

### 3. Error Recovery Flows

#### Validation Errors
```tsx
// Progressive error disclosure
<FormField>
  <Input 
    error={fieldError}
    onBlur={validateField}
  />
  {fieldError && (
    <ErrorMessage>
      {fieldError.message}
      <HelpLink to={fieldError.helpUrl} />
    </ErrorMessage>
  )}
</FormField>
```

#### Network Failures
```tsx
// Graceful degradation with retry options
const NetworkErrorBoundary = ({ children, fallback }) => (
  <ErrorBoundary
    fallback={({ error, retry }) => (
      <div className="text-center p-6">
        <AlertTriangle className="h-12 w-12 text-orange-500 mx-auto mb-4" />
        <h3>Connection Lost</h3>
        <p>Unable to connect to the server.</p>
        <Button onClick={retry} className="mt-4">
          Try Again
        </Button>
      </div>
    )}
  >
    {children}
  </ErrorBoundary>
);
```

## Accessibility Implementation

### 1. WCAG 2.1 Compliance

#### Keyboard Navigation
```tsx
// Focus management for modals
const Modal = ({ isOpen, onClose, children }) => {
  const [focusedElement, setFocusedElement] = useState(null);
  
  useEffect(() => {
    if (isOpen) {
      setFocusedElement(document.activeElement);
      // Focus first interactive element
      const firstFocusable = modalRef.current?.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();
    } else {
      // Restore focus
      focusedElement?.focus();
    }
  }, [isOpen]);
};
```

#### Screen Reader Support
```tsx
// ARIA labels and descriptions
<Button
  aria-label="Delete asset item"
  aria-describedby="delete-warning"
  onClick={handleDelete}
>
  <Trash2 aria-hidden="true" />
</Button>
<div id="delete-warning" className="sr-only">
  This action cannot be undone
</div>
```

### 2. Color and Contrast

```css
/* High contrast mode support */
@media (prefers-contrast: high) {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 0%;
    --border: 0 0% 0%;
    --primary: 240 100% 50%;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 3. Focus Management

```tsx
// Focus trap for dialogs
const FocusTrap = ({ children, active }) => {
  const trapRef = useRef(null);
  
  useEffect(() => {
    if (!active) return;
    
    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        const focusableElements = trapRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [active]);
  
  return <div ref={trapRef}>{children}</div>;
};
```

## Responsive Design Strategy

### 1. Mobile-First Approach

```css
/* Base styles for mobile */
.container {
  padding: 1rem;
  max-width: 100%;
}

/* Tablet styles */
@media (min-width: 768px) {
  .container {
    padding: 2rem;
    max-width: 768px;
  }
}

/* Desktop styles */
@media (min-width: 1024px) {
  .container {
    padding: 3rem;
    max-width: 1200px;
  }
}
```

### 2. Flexible Components

```tsx
// Responsive navigation
const Navigation = () => {
  const [isMobile, setIsMobile] = useState(false);
  
  return isMobile ? (
    <MobileNavigation />
  ) : (
    <DesktopNavigation />
  );
};

// Responsive data tables
const DataTable = ({ data, columns }) => {
  const { width } = useWindowSize();
  
  return width < 768 ? (
    <CardList data={data} />
  ) : (
    <Table data={data} columns={columns} />
  );
};
```

### 3. Touch-Friendly Interactions

```css
/* Minimum touch target size */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  padding: 12px;
}

/* Touch feedback */
.touch-target:active {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}
```

## Performance Optimization

### 1. Lazy Loading Strategy

```tsx
// Component-level lazy loading
const LazyChart = lazy(() => import('@/components/visualization/Chart'));

// Image lazy loading with intersection observer
const LazyImage = ({ src, alt, ...props }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef();
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    
    if (imgRef.current) {
      observer.observe(imgRef.current);
    }
    
    return () => observer.disconnect();
  }, []);
  
  return (
    <div ref={imgRef} {...props}>
      {isInView && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          className={cn(
            "transition-opacity duration-300",
            isLoaded ? "opacity-100" : "opacity-0"
          )}
        />
      )}
    </div>
  );
};
```

### 2. Virtual Scrolling

```tsx
// Virtual scrolling for large datasets
const VirtualList = ({ items, itemHeight, containerHeight }) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight),
    items.length - 1
  );
  
  const visibleItems = items.slice(startIndex, endIndex + 1);
  
  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={(e) => setScrollTop(e.target.scrollTop)}
    >
      <div style={{ height: items.length * itemHeight, position: 'relative' }}>
        {visibleItems.map((item, index) => (
          <div
            key={startIndex + index}
            style={{
              position: 'absolute',
              top: (startIndex + index) * itemHeight,
              height: itemHeight,
              width: '100%',
            }}
          >
            <ListItem item={item} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 3. Memoization Strategy

```tsx
// Memoized expensive calculations
const AssetAnalysis = memo(({ assets, filters }) => {
  const analysisResults = useMemo(() => {
    return assets
      .filter(asset => matchesFilters(asset, filters))
      .reduce((acc, asset) => {
        // Expensive analysis calculations
        return {
          ...acc,
          totalValue: acc.totalValue + asset.value,
          riskScore: calculateRiskScore(acc.riskScore, asset),
          recommendations: [...acc.recommendations, ...getRecommendations(asset)]
        };
      }, { totalValue: 0, riskScore: 0, recommendations: [] });
  }, [assets, filters]);
  
  return <AnalysisChart data={analysisResults} />;
});
```

## State Management Patterns

### 1. Component State
```tsx
// Local state for simple UI interactions
const [isExpanded, setIsExpanded] = useState(false);
const [searchQuery, setSearchQuery] = useState('');
```

### 2. Context for Global State
```tsx
// Authentication context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### 3. External State Management
```tsx
// TanStack Query for server state
const { data: assets, isLoading, error } = useQuery({
  queryKey: ['assets', clientId, engagementId],
  queryFn: () => fetchAssets(clientId, engagementId),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

## Theme and Customization

### 1. Theme Provider
```tsx
const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('system');
  
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

### 2. Custom CSS Properties
```css
/* Dynamic theme switching */
.light {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}

/* Component-specific theming */
.data-table {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  border-color: hsl(var(--border));
}
```

## Testing Strategy

### 1. Component Testing
```tsx
// Unit tests for components
test('Button renders correctly', () => {
  render(<Button variant="primary">Click me</Button>);
  expect(screen.getByRole('button')).toHaveClass('bg-primary');
});

// Accessibility testing
test('Button is accessible', () => {
  render(<Button aria-label="Save document">Save</Button>);
  expect(screen.getByLabelText('Save document')).toBeInTheDocument();
});
```

### 2. Visual Regression Testing
```tsx
// Storybook stories for visual testing
export default {
  title: 'Components/Button',
  component: Button,
};

export const AllVariants = () => (
  <div className="space-x-4">
    <Button variant="default">Default</Button>
    <Button variant="destructive">Destructive</Button>
    <Button variant="outline">Outline</Button>
    <Button variant="ghost">Ghost</Button>
  </div>
);
```

### 3. User Interaction Testing
```tsx
// E2E tests for user flows
test('User can complete discovery workflow', async () => {
  await page.goto('/discovery');
  await page.click('[data-testid="upload-button"]');
  await page.setInputFiles('input[type="file"]', 'test-data.csv');
  await page.click('[data-testid="analyze-button"]');
  await expect(page.locator('[data-testid="analysis-results"]')).toBeVisible();
});
```

## Best Practices

### 1. Component Guidelines
- Use TypeScript for all components
- Follow single responsibility principle
- Implement proper error boundaries
- Use semantic HTML elements
- Include proper ARIA attributes

### 2. Performance Guidelines
- Implement lazy loading for routes
- Use React.memo for expensive components
- Optimize bundle size with code splitting
- Minimize re-renders with proper dependencies
- Use virtual scrolling for large lists

### 3. Accessibility Guidelines
- Maintain proper heading hierarchy
- Provide keyboard navigation
- Include focus indicators
- Support screen readers
- Test with accessibility tools

### 4. Maintenance Guidelines
- Document component APIs
- Use consistent naming conventions
- Implement comprehensive testing
- Regular accessibility audits
- Performance monitoring

Last Updated: 2025-01-18