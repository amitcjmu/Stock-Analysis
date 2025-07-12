/**
 * Frontend test setup for enhanced Asset Inventory functionality.
 * Configures testing environment and mocks for React components.
 */

import { afterEach, beforeAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Clean up after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Global test setup
beforeAll(() => {
  // Mock window.matchMedia for responsive design tests
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // Deprecated
      removeListener: vi.fn(), // Deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // Mock ResizeObserver
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));

  // Mock IntersectionObserver for viewport-based lazy loading
  global.IntersectionObserver = vi.fn().mockImplementation((callback) => ({
    observe: vi.fn(),
    unobserve: vi.fn(), 
    disconnect: vi.fn(),
    root: null,
    rootMargin: '',
    thresholds: [],
    // Add callback mock for testing
    _callback: callback,
    _triggerIntersection: (entries) => callback(entries)
  }));

  // Mock scrollTo
  Object.defineProperty(window, 'scrollTo', {
    writable: true,
    value: vi.fn(),
  });

  // Mock localStorage
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    },
    writable: true,
  });

  // Mock fetch for API calls
  global.fetch = vi.fn();

  // Mock performance API for lazy loading performance tests
  if (!global.performance) {
    global.performance = {};
  }
  global.performance.mark = vi.fn();
  global.performance.measure = vi.fn();
  global.performance.getEntriesByName = vi.fn(() => []);
  global.performance.now = vi.fn(() => Date.now());

  // Console error suppression for expected React warnings during tests
  const originalError = console.error;
  beforeEach(() => {
    console.error = vi.fn().mockImplementation((message) => {
      // Allow certain expected warnings through
      if (
        message.includes('Warning: ReactDOM.render is deprecated') ||
        message.includes('Warning: findDOMNode is deprecated')
      ) {
        return;
      }
      originalError(message);
    });
  });

  afterEach(() => {
    console.error = originalError;
  });

  // Mock environment variables for Docker testing
  process.env.DOCKER_API_BASE = 'http://localhost:8000';
  process.env.DOCKER_FRONTEND_BASE = 'http://localhost:8081';
  process.env.NODE_ENV = 'test';
});

// Custom matchers for enhanced asset inventory testing
expect.extend({
  toBeValidAssetType(received) {
    const validTypes = [
      'Application',
      'Server', 
      'Database',
      'Network Device',
      'Storage Device',
      'Security Device',
      'Infrastructure Device',
      'Virtualization Platform',
      'Unknown'
    ];
    
    const pass = validTypes.includes(received);
    
    return {
      pass,
      message: () => pass 
        ? `Expected ${received} not to be a valid asset type`
        : `Expected ${received} to be a valid asset type. Valid types: ${validTypes.join(', ')}`
    };
  },

  toBeValid6RReadiness(received) {
    const validStatuses = [
      'Ready',
      'Not Applicable',
      'Needs Owner Info',
      'Needs Infrastructure Data', 
      'Needs Version Info',
      'Insufficient Data',
      'Type Classification Needed',
      'Complex Analysis Required'
    ];
    
    const pass = validStatuses.includes(received);
    
    return {
      pass,
      message: () => pass
        ? `Expected ${received} not to be a valid 6R readiness status`
        : `Expected ${received} to be a valid 6R readiness status. Valid statuses: ${validStatuses.join(', ')}`
    };
  },

  toBeValidMigrationComplexity(received) {
    const validComplexities = ['Low', 'Medium', 'High'];
    
    const pass = validComplexities.includes(received);
    
    return {
      pass,
      message: () => pass
        ? `Expected ${received} not to be a valid migration complexity`
        : `Expected ${received} to be a valid migration complexity. Valid complexities: ${validComplexities.join(', ')}`
    };
  },

  toHaveValidSummaryStructure(received) {
    const requiredFields = ['total', 'applications', 'servers', 'databases', 'devices', 'unknown'];
    const hasAllFields = requiredFields.every(field => 
      received.hasOwnProperty(field) && typeof received[field] === 'number'
    );
    
    return {
      pass: hasAllFields,
      message: () => hasAllFields
        ? `Expected summary not to have valid structure`
        : `Expected summary to have all required numeric fields: ${requiredFields.join(', ')}`
    };
  }
});

// Mock data for testing
export const mockAssetData = {
  assets: [
    {
      id: 'TEST001',
      type: 'Server',
      name: 'test-server',
      environment: 'Production',
      criticality: 'High',
      sixr_ready: 'Ready',
      migration_complexity: 'Medium'
    }
  ],
  summary: {
    total: 1,
    applications: 0,
    servers: 1,
    databases: 0,
    devices: 0,
    unknown: 0,
    device_breakdown: {
      network: 0,
      storage: 0,
      security: 0,
      infrastructure: 0,
      virtualization: 0
    }
  }
};

// Test utilities
export const createMockApiResponse = (data, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data))
  });
};

export const waitFor = (callback, options = {}) => {
  const { timeout = 1000, interval = 50 } = options;
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      try {
        const result = callback();
        if (result) {
          resolve(result);
          return;
        }
      } catch (error) {
        // Continue checking
      }
      
      if (Date.now() - startTime >= timeout) {
        reject(new Error('Timeout waiting for condition'));
        return;
      }
      
      setTimeout(check, interval);
    };
    
    check();
  });
};

// Modular architecture testing utilities
export const mockLazyComponent = (componentName, implementation) => {
  return vi.fn().mockImplementation(() => implementation);
};

export const mockDynamicImport = (modulePath, mockImplementation) => {
  return vi.doMock(modulePath, () => ({
    default: mockImplementation,
    __esModule: true
  }));
};

export const createLazyComponentMock = (testId, content = 'Mocked Component') => {
  return () => React.createElement('div', { 'data-testid': testId }, content);
};

export const triggerViewportIntersection = (entries) => {
  const observer = global.IntersectionObserver.mock.results[0]?.value;
  if (observer && observer._triggerIntersection) {
    observer._triggerIntersection(entries);
  }
};

// Bundle loading test utilities
export const mockBundleLoad = (bundleName, delay = 0) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ default: createLazyComponentMock(`${bundleName}-component`) });
    }, delay);
  });
};

// Performance measurement utilities for lazy loading
export const measureLazyLoadPerformance = (componentName) => {
  const startMark = `lazy-${componentName}-start`;
  const endMark = `lazy-${componentName}-end`;
  const measureName = `lazy-${componentName}-duration`;
  
  return {
    start: () => global.performance.mark(startMark),
    end: () => global.performance.mark(endMark),
    measure: () => global.performance.measure(measureName, startMark, endMark),
    getDuration: () => {
      const entries = global.performance.getEntriesByName(measureName);
      return entries.length > 0 ? entries[0].duration : 0;
    }
  };
}; 