/**
 * E2E Tests for Modular Component Loading
 * 
 * Tests the end-to-end functionality of lazy-loaded modular components including:
 * - Component loading behavior in real browser environment
 * - Error boundary functionality
 * - Loading states and performance
 * - User interaction with lazy-loaded components
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Modular Component Loading E2E', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/discovery');
    
    // Wait for the main app to load
    await page.waitForSelector('[data-testid="app-loaded"]', { timeout: 10000 });
  });

  test('should load lazy components on navigation', async ({ page }) => {
    // Navigate to different sections to trigger lazy loading
    await page.click('[data-testid="navigation-discovery"]');
    
    // Should see loading state first
    await expect(page.locator('[data-testid="loading-fallback"]')).toBeVisible();
    
    // Then the component should load
    await page.waitForSelector('[data-testid="discovery-page"]', { timeout: 5000 });
    await expect(page.locator('[data-testid="discovery-page"]')).toBeVisible();
    
    // Loading state should disappear
    await expect(page.locator('[data-testid="loading-fallback"]')).not.toBeVisible();
  });

  test('should handle lazy component errors gracefully', async ({ page }) => {
    // Mock a network error for component loading
    await page.route('**/lazy-*.js', route => route.abort('failed'));
    
    // Navigate to trigger component loading
    await page.click('[data-testid="navigation-admin"]');
    
    // Should show error boundary
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();
    await expect(page.locator('text=Error loading')).toBeVisible();
    
    // Should have retry button
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should retry failed component loads', async ({ page }) => {
    let attemptCount = 0;
    
    // Mock first attempt to fail, second to succeed
    await page.route('**/lazy-admin*.js', route => {
      attemptCount++;
      if (attemptCount === 1) {
        route.abort('failed');
      } else {
        route.continue();
      }
    });
    
    // Navigate to trigger component loading
    await page.click('[data-testid="navigation-admin"]');
    
    // Should show error initially
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();
    
    // Click retry
    await page.click('[data-testid="retry-button"]');
    
    // Should eventually load successfully
    await page.waitForSelector('[data-testid="admin-page"]', { timeout: 5000 });
    await expect(page.locator('[data-testid="admin-page"]')).toBeVisible();
  });

  test('should load components on viewport intersection', async ({ page }) => {
    // Navigate to a page with viewport-lazy components
    await page.goto('/discovery/inventory');
    
    // Scroll down to trigger viewport-based loading
    const heavyComponent = page.locator('[data-testid="heavy-asset-table"]');
    
    // Component should not be loaded initially
    await expect(heavyComponent).not.toBeVisible();
    
    // Scroll to bring component into view
    await page.evaluate(() => {
      window.scrollTo(0, 1000);
    });
    
    // Component should start loading
    await expect(page.locator('[data-testid="viewport-loading"]')).toBeVisible();
    
    // Then load successfully
    await page.waitForSelector('[data-testid="heavy-asset-table"]', { timeout: 5000 });
    await expect(heavyComponent).toBeVisible();
  });

  test('should support conditional component loading based on permissions', async ({ page }) => {
    // Test with admin user (should load admin components)
    await page.goto('/admin');
    
    // Should load admin-only components
    await page.waitForSelector('[data-testid="admin-user-management"]', { timeout: 5000 });
    await expect(page.locator('[data-testid="admin-user-management"]')).toBeVisible();
    
    // Switch to regular user context (mock lower permissions)
    await page.evaluate(() => {
      window.localStorage.setItem('userRole', 'user');
    });
    
    await page.reload();
    
    // Admin components should not load
    await expect(page.locator('[data-testid="admin-user-management"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="insufficient-permissions"]')).toBeVisible();
  });

  test('should measure and report component loading performance', async ({ page }) => {
    // Enable performance monitoring
    await page.addInitScript(() => {
      window.performance.mark = window.performance.mark || (() => {});
      window.performance.measure = window.performance.measure || (() => {});
    });
    
    const startTime = Date.now();
    
    // Navigate to trigger component loading
    await page.click('[data-testid="navigation-discovery"]');
    
    // Wait for component to load
    await page.waitForSelector('[data-testid="discovery-page"]', { timeout: 5000 });
    
    const loadTime = Date.now() - startTime;
    
    // Loading should be reasonably fast (under 3 seconds)
    expect(loadTime).toBeLessThan(3000);
    
    // Check if performance metrics are available
    const performanceEntries = await page.evaluate(() => {
      return performance.getEntriesByType('measure').map(entry => ({
        name: entry.name,
        duration: entry.duration
      }));
    });
    
    // Should have lazy loading performance entries
    const lazyLoadEntries = performanceEntries.filter(entry => 
      entry.name.includes('lazy') || entry.name.includes('component-load')
    );
    
    expect(lazyLoadEntries.length).toBeGreaterThan(0);
  });

  test('should handle multiple concurrent lazy loads', async ({ page }) => {
    // Navigate to a complex page with multiple lazy components
    await page.goto('/discovery/field-mapping');
    
    // Multiple components should start loading
    const loadingIndicators = page.locator('[data-testid*="loading"]');
    await expect(loadingIndicators.first()).toBeVisible();
    
    // All components should eventually load
    await Promise.all([
      page.waitForSelector('[data-testid="field-mapping-table"]', { timeout: 5000 }),
      page.waitForSelector('[data-testid="mapping-suggestions"]', { timeout: 5000 }),
      page.waitForSelector('[data-testid="mapping-validation"]', { timeout: 5000 })
    ]);
    
    // All components should be visible
    await expect(page.locator('[data-testid="field-mapping-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="mapping-suggestions"]')).toBeVisible();
    await expect(page.locator('[data-testid="mapping-validation"]')).toBeVisible();
    
    // No loading indicators should remain
    await expect(loadingIndicators).not.toBeVisible();
  });

  test('should maintain accessibility during lazy loading', async ({ page }) => {
    // Navigate to trigger lazy loading
    await page.click('[data-testid="navigation-discovery"]');
    
    // Check accessibility of loading state
    const loadingElement = page.locator('[data-testid="loading-fallback"]');
    await expect(loadingElement).toBeVisible();
    
    // Should have proper ARIA labels
    await expect(loadingElement).toHaveAttribute('aria-label');
    await expect(loadingElement).toHaveAttribute('role', 'status');
    
    // Wait for component to load
    await page.waitForSelector('[data-testid="discovery-page"]', { timeout: 5000 });
    
    // Loaded component should be accessible
    const loadedComponent = page.locator('[data-testid="discovery-page"]');
    await expect(loadedComponent).toBeVisible();
    
    // Should maintain focus management
    const focusableElements = loadedComponent.locator('button, input, select, textarea, a[href]');
    const firstFocusable = focusableElements.first();
    
    if (await firstFocusable.count() > 0) {
      await firstFocusable.focus();
      await expect(firstFocusable).toBeFocused();
    }
  });

  test('should cache loaded components for performance', async ({ page }) => {
    // Navigate to a page
    await page.click('[data-testid="navigation-discovery"]');
    await page.waitForSelector('[data-testid="discovery-page"]', { timeout: 5000 });
    
    const firstLoadTime = Date.now();
    
    // Navigate away
    await page.click('[data-testid="navigation-home"]');
    await page.waitForSelector('[data-testid="home-page"]', { timeout: 5000 });
    
    // Navigate back (should be cached)
    const cacheStartTime = Date.now();
    await page.click('[data-testid="navigation-discovery"]');
    await page.waitForSelector('[data-testid="discovery-page"]', { timeout: 5000 });
    const cacheLoadTime = Date.now() - cacheStartTime;
    
    // Cached load should be much faster
    expect(cacheLoadTime).toBeLessThan(1000);
  });

  test('should handle progressive enhancement correctly', async ({ page }) => {
    // Mock slow network conditions
    await page.route('**/enhanced-*.js', route => {
      setTimeout(() => route.continue(), 2000); // 2 second delay
    });
    
    // Navigate to page with progressive enhancement
    await page.goto('/discovery/advanced-analysis');
    
    // Should show basic component first
    await expect(page.locator('[data-testid="basic-analysis"]')).toBeVisible();
    
    // Enhanced features should load after delay
    await page.waitForSelector('[data-testid="enhanced-analysis"]', { timeout: 4000 });
    await expect(page.locator('[data-testid="enhanced-analysis"]')).toBeVisible();
    
    // Basic component should be replaced/enhanced
    const enhancementIndicator = page.locator('[data-testid="enhancement-active"]');
    await expect(enhancementIndicator).toBeVisible();
  });

  test('should support keyboard navigation with lazy components', async ({ page }) => {
    // Navigate using keyboard
    await page.keyboard.press('Tab'); // Focus first navigation item
    await page.keyboard.press('Tab'); // Focus discovery navigation
    await page.keyboard.press('Enter'); // Activate discovery
    
    // Should trigger lazy loading
    await page.waitForSelector('[data-testid="discovery-page"]', { timeout: 5000 });
    
    // Should be able to continue keyboard navigation
    await page.keyboard.press('Tab'); // Focus first element in loaded component
    
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // Should be within the loaded component
    const discoveryPage = page.locator('[data-testid="discovery-page"]');
    await expect(focusedElement).toBeVisible();
    
    // Verify focus is within discovery component
    const isWithinDiscovery = await discoveryPage.evaluate((discovery, focused) => {
      return discovery.contains(focused);
    }, await focusedElement.elementHandle());
    
    expect(isWithinDiscovery).toBe(true);
  });
});

test.describe('Bundle Loading and Code Splitting', () => {
  
  test('should load appropriate bundle chunks', async ({ page, context }) => {
    // Monitor network requests for bundle chunks
    const bundleRequests: string[] = [];
    
    page.on('request', request => {
      if (request.url().includes('.js') && request.url().includes('chunk')) {
        bundleRequests.push(request.url());
      }
    });
    
    await page.goto('/');
    
    // Navigate to different sections
    await page.click('[data-testid="navigation-discovery"]');
    await page.waitForLoadState('networkidle');
    
    await page.click('[data-testid="navigation-assess"]');
    await page.waitForLoadState('networkidle');
    
    // Should load different chunk files
    expect(bundleRequests.length).toBeGreaterThan(1);
    
    // Should have distinct chunks for different routes
    const discoveryChunks = bundleRequests.filter(url => url.includes('discovery'));
    const assessChunks = bundleRequests.filter(url => url.includes('assess'));
    
    expect(discoveryChunks.length).toBeGreaterThan(0);
    expect(assessChunks.length).toBeGreaterThan(0);
  });

  test('should handle bundle loading failures gracefully', async ({ page }) => {
    // Block all chunk loading
    await page.route('**/chunk-*.js', route => route.abort('failed'));
    
    await page.goto('/');
    
    // Try to navigate
    await page.click('[data-testid="navigation-discovery"]');
    
    // Should show error boundary
    await expect(page.locator('[data-testid="chunk-load-error"]')).toBeVisible();
    await expect(page.locator('text=Failed to load application')).toBeVisible();
    
    // Should provide fallback options
    await expect(page.locator('[data-testid="fallback-options"]')).toBeVisible();
  });
});