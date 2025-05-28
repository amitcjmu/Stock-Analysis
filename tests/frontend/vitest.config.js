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
        'build/'
      ],
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 50,
        statements: 60
      }
    },
    // Test timeout
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // Environment variables for testing
    env: {
      NODE_ENV: 'test',
      VITE_API_BASE_URL: 'http://localhost:8000',
      DOCKER_API_BASE: 'http://localhost:8000',
      DOCKER_FRONTEND_BASE: 'http://localhost:3000'
    },
    
    // Test patterns
    include: [
      'tests/frontend/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache'
    ],
    
    // Mock configuration
    deps: {
      inline: ['vitest-canvas-mock']
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
  }
}); 