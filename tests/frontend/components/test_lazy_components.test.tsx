/**
 * Tests for Lazy Loading Components
 * 
 * Tests the modular lazy loading component infrastructure including:
 * - Dynamic component loading
 * - Error boundary behavior
 * - Loading state management
 * - Viewport-based loading
 * - Conditional loading patterns
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ErrorBoundary } from 'react-error-boundary';

// Import lazy components to test
import {
  LazyFileUploadArea,
  LazyProjectDialog,
  LazyNavigationTabs,
  LazyQualityDashboard,
  ConditionalLazyComponent,
  ViewportLazyComponent,
  ProgressiveLazyComponent
} from '@/components/lazy/components/LazyComponents';

import { LoadingFallback, ErrorFallback, SkeletonFallback } from '@/components/lazy/LoadingFallback';

// Mock the dynamic imports
const mockFileUploadComponent = () => React.createElement('div', { 'data-testid': 'file-upload-component' }, 'File Upload Component');
const mockProjectDialogComponent = () => React.createElement('div', { 'data-testid': 'project-dialog-component' }, 'Project Dialog Component');
const mockNavigationTabsComponent = () => React.createElement('div', { 'data-testid': 'navigation-tabs-component' }, 'Navigation Tabs Component');
const mockQualityDashboardComponent = () => React.createElement('div', { 'data-testid': 'quality-dashboard-component' }, 'Quality Dashboard Component');

// Mock React.lazy
const originalLazy = React.lazy;
const mockLazy = vi.fn();

beforeEach(() => {
  // Mock React.lazy to return our mock components
  React.lazy = mockLazy;
  
  // Setup default mock implementations
  mockLazy.mockImplementation((importFn) => {
    const componentName = importFn.toString();
    
    if (componentName.includes('FileUploadArea')) {
      return React.forwardRef(() => mockFileUploadComponent());
    }
    if (componentName.includes('ProjectDialog')) {
      return React.forwardRef(() => mockProjectDialogComponent());
    }
    if (componentName.includes('NavigationTabs')) {
      return React.forwardRef(() => mockNavigationTabsComponent());
    }
    if (componentName.includes('QualityDashboard')) {
      return React.forwardRef(() => mockQualityDashboardComponent());
    }
    
    // Default mock component
    return React.forwardRef(() => React.createElement('div', { 'data-testid': 'mock-lazy-component' }, 'Mock Lazy Component'));
  });
});

afterEach(() => {
  React.lazy = originalLazy;
  vi.clearAllMocks();
});

describe('Lazy Component Loading', () => {
  it('should render LazyFileUploadArea with loading state then component', async () => {
    // Act
    render(<LazyFileUploadArea />);
    
    // Assert - Initially shows loading
    expect(screen.getByText(/loading file upload area/i)).toBeInTheDocument();
    
    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByTestId('file-upload-component')).toBeInTheDocument();
    });
    
    // Loading state should be gone
    expect(screen.queryByText(/loading file upload area/i)).not.toBeInTheDocument();
  });

  it('should render LazyProjectDialog with minimal fallback', async () => {
    // Act
    render(<LazyProjectDialog />);
    
    // Assert - Shows loading fallback initially
    expect(screen.getByRole('progressbar') || screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByTestId('project-dialog-component')).toBeInTheDocument();
    });
  });

  it('should render LazyNavigationTabs with correct priority', async () => {
    // Act
    render(<LazyNavigationTabs />);
    
    // Assert - Component loads normally (NORMAL priority)
    await waitFor(() => {
      expect(screen.getByTestId('navigation-tabs-component')).toBeInTheDocument();
    });
  });

  it('should render LazyQualityDashboard with skeleton fallback', async () => {
    // Act
    render(<LazyQualityDashboard />);
    
    // Assert - Shows skeleton fallback initially
    expect(screen.getByTestId('skeleton-fallback') || screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByTestId('quality-dashboard-component')).toBeInTheDocument();
    });
  });
});

describe('Error Boundary Behavior', () => {
  it('should catch and display error when component fails to load', async () => {
    // Arrange - Mock a failing component
    const FailingComponent = React.lazy(() => Promise.reject(new Error('Component load failed')));
    
    const mockError = vi.fn();
    const originalError = console.error;
    console.error = mockError;
    
    // Act
    render(
      <ErrorBoundary
        FallbackComponent={({ error, resetErrorBoundary }) => (
          <ErrorFallback
            error={error}
            retry={resetErrorBoundary}
            componentName="Test Component"
          />
        )}
      >
        <React.Suspense fallback={<LoadingFallback />}>
          <FailingComponent />
        </React.Suspense>
      </ErrorBoundary>
    );
    
    // Assert - Error boundary should catch the error
    await waitFor(() => {
      expect(screen.getByText(/error loading test component/i)).toBeInTheDocument();
      expect(screen.getByText(/retry/i)).toBeInTheDocument();
    });
    
    console.error = originalError;
  });

  it('should allow retry after error', async () => {
    // Arrange
    let attemptCount = 0;
    const FlakyComponent = React.lazy(() => {
      attemptCount++;
      if (attemptCount === 1) {
        return Promise.reject(new Error('First attempt failed'));
      }
      return Promise.resolve({ default: () => React.createElement('div', { 'data-testid': 'success-component' }, 'Success!') });
    });

    // Act
    render(
      <ErrorBoundary
        FallbackComponent={({ error, resetErrorBoundary }) => (
          <ErrorFallback
            error={error}
            retry={resetErrorBoundary}
            componentName="Flaky Component"
          />
        )}
      >
        <React.Suspense fallback={<LoadingFallback />}>
          <FlakyComponent />
        </React.Suspense>
      </ErrorBoundary>
    );

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/error loading flaky component/i)).toBeInTheDocument();
    });

    // Click retry button
    const retryButton = screen.getByText(/retry/i);
    fireEvent.click(retryButton);

    // Assert - Component should load successfully on retry
    await waitFor(() => {
      expect(screen.getByTestId('success-component')).toBeInTheDocument();
    });
  });
});

describe('ConditionalLazyComponent', () => {
  it('should render children when condition is true', () => {
    // Act
    render(
      <ConditionalLazyComponent condition={true}>
        <div data-testid="conditional-content">Conditional Content</div>
      </ConditionalLazyComponent>
    );
    
    // Assert
    expect(screen.getByTestId('conditional-content')).toBeInTheDocument();
  });

  it('should render fallback when condition is false', () => {
    // Act
    render(
      <ConditionalLazyComponent 
        condition={false}
        fallback={<div data-testid="fallback-content">Fallback Content</div>}
      >
        <div data-testid="conditional-content">Conditional Content</div>
      </ConditionalLazyComponent>
    );
    
    // Assert
    expect(screen.getByTestId('fallback-content')).toBeInTheDocument();
    expect(screen.queryByTestId('conditional-content')).not.toBeInTheDocument();
  });

  it('should render null when condition is false and no fallback provided', () => {
    // Act
    const { container } = render(
      <ConditionalLazyComponent condition={false}>
        <div data-testid="conditional-content">Conditional Content</div>
      </ConditionalLazyComponent>
    );
    
    // Assert
    expect(container.firstChild).toBeNull();
  });
});

describe('ViewportLazyComponent', () => {
  // Mock IntersectionObserver
  const mockIntersectionObserver = vi.fn();
  
  beforeEach(() => {
    global.IntersectionObserver = vi.fn().mockImplementation((callback) => {
      mockIntersectionObserver.mockImplementation(callback);
      return {
        observe: vi.fn(),
        disconnect: vi.fn(),
        unobserve: vi.fn(),
      };
    });
  });

  it('should initially render placeholder', () => {
    // Act
    render(
      <ViewportLazyComponent placeholder={<div data-testid="placeholder">Placeholder</div>}>
        <div data-testid="viewport-content">Viewport Content</div>
      </ViewportLazyComponent>
    );
    
    // Assert
    expect(screen.getByTestId('placeholder')).toBeInTheDocument();
    expect(screen.queryByTestId('viewport-content')).not.toBeInTheDocument();
  });

  it('should render content when component enters viewport', async () => {
    // Act
    render(
      <ViewportLazyComponent>
        <div data-testid="viewport-content">Viewport Content</div>
      </ViewportLazyComponent>
    );
    
    // Simulate intersection observer triggering
    act(() => {
      mockIntersectionObserver([{ isIntersecting: true }]);
    });
    
    // Assert
    await waitFor(() => {
      expect(screen.getByTestId('viewport-content')).toBeInTheDocument();
    });
  });

  it('should use custom threshold and rootMargin', () => {
    // Act
    render(
      <ViewportLazyComponent threshold={0.5} rootMargin="100px">
        <div data-testid="viewport-content">Viewport Content</div>
      </ViewportLazyComponent>
    );
    
    // Assert - IntersectionObserver should be called with custom options
    expect(global.IntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      { threshold: 0.5, rootMargin: '100px' }
    );
  });

  it('should render default min-height placeholder when no placeholder provided', () => {
    // Act
    const { container } = render(
      <ViewportLazyComponent>
        <div data-testid="viewport-content">Viewport Content</div>
      </ViewportLazyComponent>
    );
    
    // Assert
    const placeholderDiv = container.querySelector('div[style*="min-height"]');
    expect(placeholderDiv).toBeInTheDocument();
    expect(placeholderDiv).toHaveStyle({ minHeight: '200px' });
  });
});

describe('ProgressiveLazyComponent', () => {
  const BaseComponent = () => <div data-testid="base-component">Base Component</div>;
  const EnhancedComponent = () => <div data-testid="enhanced-component">Enhanced Component</div>;

  it('should render base component when enhancement condition is false', async () => {
    // Act
    render(
      <ProgressiveLazyComponent
        baseComponent={BaseComponent}
        enhancedImport={() => Promise.resolve({ default: EnhancedComponent })}
        enhancementCondition={false}
        props={{}}
      />
    );
    
    // Assert
    await waitFor(() => {
      expect(screen.getByTestId('base-component')).toBeInTheDocument();
      expect(screen.queryByTestId('enhanced-component')).not.toBeInTheDocument();
    });
  });

  it('should load enhanced component when enhancement condition is true', async () => {
    // Act
    render(
      <ProgressiveLazyComponent
        baseComponent={BaseComponent}
        enhancedImport={() => Promise.resolve({ default: EnhancedComponent })}
        enhancementCondition={true}
        props={{}}
      />
    );
    
    // Assert - Should initially show base component
    expect(screen.getByTestId('base-component')).toBeInTheDocument();
    
    // Wait for enhanced component to load
    await waitFor(() => {
      expect(screen.getByTestId('enhanced-component')).toBeInTheDocument();
    });
  });

  it('should fallback to base component if enhanced import fails', async () => {
    // Arrange
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    // Act
    render(
      <ProgressiveLazyComponent
        baseComponent={BaseComponent}
        enhancedImport={() => Promise.reject(new Error('Enhanced import failed'))}
        enhancementCondition={true}
        props={{}}
      />
    );
    
    // Assert - Should fallback to base component
    await waitFor(() => {
      expect(screen.getByTestId('base-component')).toBeInTheDocument();
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load enhanced component')
      );
    });
    
    consoleSpy.mockRestore();
  });
});

describe('Loading Fallback Components', () => {
  it('should render LoadingFallback with message', () => {
    // Act
    render(<LoadingFallback message="Loading test component..." />);
    
    // Assert
    expect(screen.getByText(/loading test component/i)).toBeInTheDocument();
  });

  it('should render compact LoadingFallback', () => {
    // Act
    render(<LoadingFallback compact />);
    
    // Assert
    const loadingElement = screen.getByRole('progressbar') || screen.getByText(/loading/i);
    expect(loadingElement).toBeInTheDocument();
    expect(loadingElement.className).toContain('compact');
  });

  it('should render SkeletonFallback with specified type', () => {
    // Act
    render(<SkeletonFallback type="card" />);
    
    // Assert
    expect(screen.getByTestId('skeleton-fallback')).toBeInTheDocument();
    expect(screen.getByTestId('skeleton-fallback')).toHaveClass('skeleton-card');
  });

  it('should render ErrorFallback with retry button', () => {
    // Arrange
    const error = new Error('Test error');
    const retryFn = vi.fn();
    
    // Act
    render(
      <ErrorFallback
        error={error}
        retry={retryFn}
        componentName="Test Component"
      />
    );
    
    // Assert
    expect(screen.getByText(/error loading test component/i)).toBeInTheDocument();
    expect(screen.getByText(/test error/i)).toBeInTheDocument();
    
    const retryButton = screen.getByText(/retry/i);
    expect(retryButton).toBeInTheDocument();
    
    // Test retry functionality
    fireEvent.click(retryButton);
    expect(retryFn).toHaveBeenCalledOnce();
  });
});

describe('Performance and Bundle Loading', () => {
  it('should not load component immediately if lazy', () => {
    // Act
    render(<LazyFileUploadArea />);
    
    // Assert - Component should not be loaded immediately
    expect(screen.queryByTestId('file-upload-component')).not.toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should load component only once', async () => {
    // Arrange
    const importSpy = vi.fn(() => Promise.resolve({ default: mockFileUploadComponent }));
    mockLazy.mockImplementation(() => React.forwardRef(() => {
      importSpy();
      return mockFileUploadComponent();
    }));
    
    // Act - Render component multiple times
    const { rerender } = render(<LazyFileUploadArea />);
    rerender(<LazyFileUploadArea />);
    rerender(<LazyFileUploadArea />);
    
    // Wait for loading
    await waitFor(() => {
      expect(screen.getByTestId('file-upload-component')).toBeInTheDocument();
    });
    
    // Assert - Import should only be called once due to caching
    expect(importSpy).toHaveBeenCalledTimes(1);
  });

  it('should handle multiple concurrent lazy loads', async () => {
    // Act - Render multiple lazy components simultaneously
    render(
      <div>
        <LazyFileUploadArea />
        <LazyProjectDialog />
        <LazyNavigationTabs />
      </div>
    );
    
    // Assert - All components should eventually load
    await waitFor(() => {
      expect(screen.getByTestId('file-upload-component')).toBeInTheDocument();
      expect(screen.getByTestId('project-dialog-component')).toBeInTheDocument();
      expect(screen.getByTestId('navigation-tabs-component')).toBeInTheDocument();
    });
  });
});

describe('Accessibility', () => {
  it('should maintain accessibility during loading states', () => {
    // Act
    render(<LazyFileUploadArea />);
    
    // Assert - Loading state should be accessible
    const loadingElement = screen.getByRole('progressbar') || screen.getByText(/loading/i);
    expect(loadingElement).toBeInTheDocument();
    expect(loadingElement).toHaveAttribute('aria-label', expect.stringContaining('Loading'));
  });

  it('should maintain focus management after component loads', async () => {
    // Act
    render(<LazyFileUploadArea />);
    
    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByTestId('file-upload-component')).toBeInTheDocument();
    });
    
    // Assert - Component should be properly accessible
    const loadedComponent = screen.getByTestId('file-upload-component');
    expect(loadedComponent).toBeInTheDocument();
    expect(loadedComponent).toBeVisible();
  });

  it('should provide meaningful error messages for screen readers', async () => {
    // Arrange
    const error = new Error('Component failed to load');
    
    // Act
    render(
      <ErrorFallback
        error={error}
        retry={() => {}}
        componentName="Test Component"
      />
    );
    
    // Assert
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/error loading test component/i)).toBeInTheDocument();
  });
});