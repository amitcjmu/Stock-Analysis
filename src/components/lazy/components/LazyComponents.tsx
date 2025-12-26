/**
 * Lazy Components - Component-level code splitting for heavy components
 */

import React from 'react'
import { lazy, Suspense } from 'react'
import { LoadingFallback, ErrorFallback, SkeletonFallback } from '../LoadingFallback';
import { LoadingPriority } from '@/types/lazy';
import { ErrorBoundary } from 'react-error-boundary';

const createLazyComponent = <P extends Record<string, unknown> = Record<string, unknown>>(
  importFn: () => Promise<{ default: React.ComponentType<P> }>,
  componentName: string,
  fallbackType: 'loading' | 'skeleton' | 'minimal' = 'loading',
  priority: LoadingPriority = LoadingPriority.NORMAL
) => {
  const LazyComponent = lazy(importFn);

  const getFallback = (): JSX.Element => {
    switch (fallbackType) {
      case 'skeleton':
        return <SkeletonFallback type="card" />;
      case 'minimal':
        return <LoadingFallback compact />;
      case 'loading':
      default:
        return (
          <LoadingFallback
            message={`Loading ${componentName}...`}
            priority={priority}
          />
        );
    }
  };

  return React.forwardRef<HTMLElement, P>((props, ref) => (
    <ErrorBoundary
      FallbackComponent={({ error, resetErrorBoundary }) => (
        <ErrorFallback
          error={error}
          retry={resetErrorBoundary}
          componentName={componentName}
        />
      )}
      onError={(error) => {
        console.error(`Error loading ${componentName}:`, error);
      }}
    >
      <Suspense fallback={getFallback()}>
        <LazyComponent {...props} ref={ref} />
      </Suspense>
    </ErrorBoundary>
  ));
};

// Discovery Components (HIGH priority - frequently used)
export const LazyFileUploadArea = createLazyComponent(
  () => import('@/components/discovery/FileUploadArea'),
  'File Upload Area',
  'skeleton',
  LoadingPriority.HIGH
);

export const LazyProjectDialog = createLazyComponent(
  () => import('@/components/discovery/ProjectDialog'),
  'Project Dialog',
  'minimal',
  LoadingPriority.HIGH
);

export const LazyFileList = createLazyComponent(
  () => import('@/components/discovery/FileList'),
  'File List',
  'skeleton',
  LoadingPriority.HIGH
);

export const LazyRawDataTable = createLazyComponent(
  () => import('@/components/discovery/RawDataTable'),
  'Raw Data Table',
  'skeleton',
  LoadingPriority.HIGH
);

// REMOVED: Attribute Mapping Components (NORMAL priority)
// export const LazyNavigationTabs = createLazyComponent(
//   () => import('@/components/discovery/attribute-mapping/NavigationTabs'),
//   'Navigation Tabs',
//   'minimal',
//   LoadingPriority.NORMAL
// );

// REMOVED: Data Cleansing Components (NORMAL priority)
// export const LazyQualityDashboard = createLazyComponent(
//   () => import('@/components/discovery/data-cleansing/QualityDashboard'),
//   'Quality Dashboard',
//   'skeleton',
//   LoadingPriority.NORMAL
// );

// export const LazyAgentQualityAnalysis = createLazyComponent(
//   () => import('@/components/discovery/data-cleansing/AgentQualityAnalysis'),
//   'Agent Quality Analysis',
//   'skeleton',
//   LoadingPriority.NORMAL
// );

// export const LazyRecommendationsSummary = createLazyComponent(
//   () => import('@/components/discovery/data-cleansing/RecommendationsSummary'),
//   'Recommendations Summary',
//   'skeleton',
//   LoadingPriority.NORMAL
// );

// export const LazyActionFeedback = createLazyComponent(
//   () => import('@/components/discovery/data-cleansing/ActionFeedback'),
//   'Action Feedback',
//   'minimal',
//   LoadingPriority.NORMAL
// );

// export const LazyQualityIssuesSummary = createLazyComponent(
//   () => import('@/components/discovery/data-cleansing/QualityIssuesSummary'),
//   'Quality Issues Summary',
//   'skeleton',
//   LoadingPriority.NORMAL
// );

// Note: 6R Analysis Components removed as part of Assessment Flow Migration Phase 5
// These components have been deleted:
// - LazyParameterSliders
// - LazyQualifyingQuestions
// - LazyAnalysisProgress
// - LazyApplicationSelector
// - LazySixRErrorBoundary
// Use Assessment Flow components instead

// Admin Components (LOW priority)
export const LazyUserStats = createLazyComponent(
  () => import('@/components/admin/user-approvals/UserStats'),
  'User Statistics',
  'skeleton',
  LoadingPriority.LOW
);

export const LazyApprovalActions = createLazyComponent(
  () => import('@/components/admin/user-approvals/ApprovalActions'),
  'Approval Actions',
  'minimal',
  LoadingPriority.LOW
);

export const LazyUserDetailsModal = createLazyComponent(
  () => import('@/components/admin/user-approvals/UserDetailsModal'),
  'User Details Modal',
  'loading',
  LoadingPriority.LOW
);

export const LazyEngagementFilters = createLazyComponent(
  () => import('@/components/admin/engagement-management/EngagementFilters'),
  'Engagement Filters',
  'skeleton',
  LoadingPriority.LOW
);

export const LazySessionComparison = createLazyComponent(
  () => import('@/components/admin/SessionComparison'),
  'Session Comparison',
  'skeleton',
  LoadingPriority.LOW
);

// Context Providers (CRITICAL priority - needed for app functionality)
export const LazyChatFeedbackContext = createLazyComponent(
  () => import('@/contexts/ChatFeedbackContext'),
  'Chat Feedback Context',
  'minimal',
  LoadingPriority.CRITICAL
);

// Specialized lazy component for conditional loading based on user permissions
interface ConditionalLazyComponentProps {
  condition: boolean;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loadingMessage?: string;
}

export const ConditionalLazyComponent: React.FC<ConditionalLazyComponentProps> = ({
  condition,
  children,
  fallback,
  loadingMessage = 'Loading...'
}) => {
  if (!condition) {
    return <>{fallback || null}</>;
  }

  return (
    <Suspense fallback={<LoadingFallback message={loadingMessage} compact />}>
      {children}
    </Suspense>
  );
};

// Viewport-based lazy component wrapper
interface ViewportLazyComponentProps {
  children: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
  fallback?: React.ReactNode;
  placeholder?: React.ReactNode;
}

export const ViewportLazyComponent: React.FC<ViewportLazyComponentProps> = ({
  children,
  threshold = 0.1,
  rootMargin = '50px',
  fallback,
  placeholder
}) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold, rootMargin }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [threshold, rootMargin]);

  return (
    <div ref={ref}>
      {isVisible ? (
        <Suspense fallback={fallback || <LoadingFallback compact />}>
          {children}
        </Suspense>
      ) : (
        placeholder || <div style={{ minHeight: '200px' }} />
      )}
    </div>
  );
};

// Progressive enhancement wrapper
interface ProgressiveLazyComponentProps<P = Record<string, unknown>> {
  baseComponent: React.ComponentType<P>;
  enhancedImport: () => Promise<{ default: React.ComponentType<P> }>;
  enhancementCondition: boolean;
  props: P;
}

export const ProgressiveLazyComponent = <P extends Record<string, unknown> = Record<string, unknown>>({
  baseComponent: BaseComponent,
  enhancedImport,
  enhancementCondition,
  props
}: ProgressiveLazyComponentProps<P>): JSX.Element => {
  const [EnhancedComponent, setEnhancedComponent] = React.useState<React.ComponentType<P> | null>(null);

  React.useEffect(() => {
    if (enhancementCondition && !EnhancedComponent) {
      enhancedImport().then(module => {
        setEnhancedComponent(() => module.default);
      }).catch(error => {
        console.warn('Failed to load enhanced component, falling back to base:', error);
      });
    }
  }, [enhancementCondition, EnhancedComponent, enhancedImport]);

  const ComponentToRender = EnhancedComponent || BaseComponent;

  return (
    <Suspense fallback={<LoadingFallback compact />}>
      <ComponentToRender {...props} />
    </Suspense>
  );
};
