import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/frontend/setup.js'],
    globals: true,
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './tests/coverage/frontend',
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.config.js',
        '**/*.config.ts',
        'public/',
        'dist/',
        'build/',
        // Exclude lazy loading infrastructure from coverage (tested separately)
        'src/components/lazy/index.ts',
        'src/utils/lazy/loadingManager.ts'
      ],
      thresholds: {
        lines: 75,  // Increased for modular architecture
        functions: 75,
        branches: 65,
        statements: 75
      },
      // Include modular component coverage
      include: [
        'src/**/*.{ts,tsx}',
        'src/components/lazy/**/*.{ts,tsx}',
        'src/hooks/lazy/**/*.{ts,tsx}',
        'src/utils/lazy/**/*.{ts,tsx}'
      ]
    },
    // Test timeout
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // Environment variables for testing
    env: {
      NODE_ENV: 'test',
      VITE_API_BASE_URL: 'http://localhost:8000',
      DOCKER_API_BASE: 'http://localhost:8000',
      DOCKER_FRONTEND_BASE: 'http://localhost:8081'
    },
    
    // Test patterns - Updated for modular architecture
    include: [
      'tests/frontend/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      // Include modular component tests
      'tests/frontend/components/**/*.test.{ts,tsx}',
      'tests/frontend/hooks/**/*.test.{ts,tsx}',
      'tests/frontend/utils/**/*.test.{ts,tsx}'
    ],
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache'
    ],
    
    // Mock configuration - Enhanced for modular architecture
    deps: {
      inline: ['vitest-canvas-mock']
    },
    
    // Setup for lazy loading and module boundary testing
    transformMode: {
      web: [/\.[jt]sx?$/],
      ssr: [/\.([cm]?[jt]s|[jt]sx)$/]
    },
    
    // Browser-like environment for React components
    threads: false,
    isolate: false
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../../src'),
      '@components': path.resolve(__dirname, '../../src/components'),
      '@pages': path.resolve(__dirname, '../../src/pages'),
      '@config': path.resolve(__dirname, '../../src/config'),
      '@hooks': path.resolve(__dirname, '../../src/hooks'),
      '@lib': path.resolve(__dirname, '../../src/lib')
    }
  },
  // Define environment variables for tests
  define: {
    'process.env': {
      NODE_ENV: '"test"',
      DOCKER_API_BASE: '"http://localhost:8000"',
      DOCKER_FRONTEND_BASE: '"http://localhost:8081"'
    }
  }
}); 