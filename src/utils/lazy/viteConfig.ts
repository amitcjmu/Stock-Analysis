/**
 * Vite Configuration Helper for Lazy Loading Optimization
 * Provides optimized build configuration for code splitting
 */

import { defineConfig } from 'vite';

export const createLazyLoadingConfig = (baseConfig: unknown = {}) => {
  return defineConfig({
    ...baseConfig,
    build: {
      ...baseConfig.build,
      rollupOptions: {
        ...baseConfig.build?.rollupOptions,
        output: {
          ...baseConfig.build?.rollupOptions?.output,
          // Manual chunking strategy for optimal lazy loading
          manualChunks: {
            // Core vendor chunks (CRITICAL priority)
            'vendor-react': ['react', 'react-dom', 'react-router-dom'],
            'vendor-query': ['@tanstack/react-query'],
            
            // UI library chunks (HIGH priority)
            'vendor-ui-core': [
              '@radix-ui/react-accordion',
              '@radix-ui/react-alert-dialog',
              '@radix-ui/react-avatar',
              '@radix-ui/react-button',
              '@radix-ui/react-card',
              '@radix-ui/react-dialog',
              '@radix-ui/react-dropdown-menu'
            ],
            'vendor-ui-extended': [
              '@radix-ui/react-popover',
              '@radix-ui/react-select',
              '@radix-ui/react-tabs',
              '@radix-ui/react-toast',
              '@radix-ui/react-tooltip'
            ],
            
            // Icons and styling (NORMAL priority)
            'vendor-icons': ['lucide-react'],
            'vendor-styling': ['clsx', 'tailwind-merge', 'class-variance-authority'],
            
            // Form handling (NORMAL priority)
            'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],
            
            // Data processing (NORMAL priority)
            'vendor-data': ['papaparse', 'date-fns'],
            
            // Visualization (LOW priority)
            'vendor-charts': ['recharts'],
            'vendor-3d': ['@react-three/fiber', '@react-three/drei', 'three'],
            
            // Feature-based chunks (organized by priority)
            'discovery-core': [
              './src/pages/Discovery.tsx',
              './src/pages/discovery/Index.tsx'
            ],
            'discovery-features': [
              './src/pages/discovery/CMDBImport.tsx',
              './src/pages/discovery/Inventory.tsx',
              './src/pages/discovery/Dependencies.tsx'
            ],
            'discovery-advanced': [
              './src/pages/discovery/DataCleansing.tsx',
              './src/pages/discovery/AttributeMapping.tsx',
              './src/pages/discovery/TechDebtAnalysis.tsx'
            ],
            
            'assessment-core': [
              './src/pages/Assess.tsx',
              './src/pages/assessment/AssessmentFlowOverview.tsx'
            ],
            'assessment-features': [
              './src/pages/assess/Treatment.tsx',
              './src/pages/assess/WavePlanning.tsx',
              './src/pages/assess/Roadmap.tsx'
            ],
            'assessment-flows': [
              './src/pages/assessment/InitializeFlow.tsx',
              './src/pages/assessment/InitializeFlowWithInventory.tsx'
            ],
            
            'planning': [
              './src/pages/Plan.tsx',
              './src/pages/plan/Index.tsx',
              './src/pages/plan/Timeline.tsx',
              './src/pages/plan/Resource.tsx'
            ],
            
            'execution': [
              './src/pages/Execute.tsx',
              './src/pages/execute/Index.tsx',
              './src/pages/execute/Rehost.tsx',
              './src/pages/execute/Replatform.tsx'
            ],
            
            'modernization': [
              './src/pages/Modernize.tsx',
              './src/pages/modernize/Index.tsx',
              './src/pages/modernize/Refactor.tsx'
            ],
            
            'finops': [
              './src/pages/FinOps.tsx',
              './src/pages/finops/CloudComparison.tsx',
              './src/pages/finops/CostAnalysis.tsx'
            ],
            
            'decommissioning': [
              './src/pages/Decommission.tsx',
              './src/pages/decommission/Index.tsx',
              './src/pages/decommission/Planning.tsx'
            ],
            
            'observability': [
              './src/pages/Observability.tsx',
              './src/pages/AgentMonitoring.tsx'
            ],
            
            // Admin chunks (LOW priority)
            'admin-core': [
              './src/pages/admin/AdminDashboard.tsx',
              './src/components/admin/AdminLayout.tsx'
            ],
            'admin-management': [
              './src/pages/admin/ClientManagement.tsx',
              './src/pages/admin/EngagementManagement.tsx',
              './src/pages/admin/UserApprovals.tsx'
            ],
            
            // Component chunks
            'components-discovery': [
              './src/components/discovery/FileUploadArea.tsx',
              './src/components/discovery/ProjectDialog.tsx',
              './src/components/discovery/RawDataTable.tsx'
            ],
            'components-sixr': [
              './src/components/sixr/ParameterSliders.tsx',
              './src/components/sixr/QualifyingQuestions.tsx',
              './src/components/sixr/AnalysisProgress.tsx'
            ],
            'components-admin': [
              './src/components/admin/user-approvals/UserStats.tsx',
              './src/components/admin/engagement-management/EngagementFilters.tsx'
            ],
            
            // Utility chunks
            'utils-data': [
              './src/utils/dataCleansingUtils.ts',
              './src/utils/migration/sessionToFlow.ts'
            ],
            'utils-lazy': [
              './src/utils/lazy/loadingManager.ts',
              './src/utils/lazy/routePreloader.ts',
              './src/utils/lazy/performanceMonitor.ts'
            ]
          },
          
          // Chunk naming strategy
          chunkFileNames: (chunkInfo) => {
            const name = chunkInfo.name;
            
            // Critical chunks get short names for faster loading
            if (name?.includes('vendor-react') || name?.includes('vendor-query')) {
              return 'assets/critical-[name]-[hash].js';
            }
            
            // Feature chunks get descriptive names
            if (name?.includes('discovery') || name?.includes('assessment')) {
              return 'assets/features-[name]-[hash].js';
            }
            
            // Admin chunks get grouped
            if (name?.includes('admin')) {
              return 'assets/admin-[name]-[hash].js';
            }
            
            // Default naming
            return 'assets/[name]-[hash].js';
          },
          
          // Asset naming
          assetFileNames: 'assets/[name]-[hash].[ext]',
          entryFileNames: 'assets/[name]-[hash].js'
        }
      },
      
      // Optimize chunk sizes
      chunkSizeWarningLimit: 1000, // 1MB warning limit
      
      // Enable source maps in development
      sourcemap: process.env.NODE_ENV === 'development',
      
      // Minification options
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: process.env.NODE_ENV === 'production',
          drop_debugger: process.env.NODE_ENV === 'production'
        }
      }
    },
    
    // Optimization for development
    optimizeDeps: {
      ...baseConfig.optimizeDeps,
      include: [
        // Pre-bundle frequently used dependencies
        'react',
        'react-dom',
        'react-router-dom',
        '@tanstack/react-query',
        'lucide-react'
      ],
      exclude: [
        // Exclude large dependencies from pre-bundling
        '@react-three/fiber',
        '@react-three/drei',
        'three'
      ]
    },
    
    // Split vendor chunks in development too
    esbuild: {
      ...baseConfig.esbuild,
      // Keep class names in development for better debugging
      keepNames: process.env.NODE_ENV === 'development'
    }
  });
};

export const getLazyLoadingAnalysis = () => {
  return {
    chunkStrategy: {
      critical: ['vendor-react', 'vendor-query'],
      high: ['discovery-core', 'assessment-core', 'vendor-ui-core'],
      normal: ['discovery-features', 'assessment-features', 'planning', 'execution'],
      low: ['admin-core', 'admin-management', 'vendor-charts', 'vendor-3d']
    },
    targetSizes: {
      initial: '< 200KB',
      critical: '< 100KB per chunk',
      features: '< 500KB per chunk',
      admin: '< 300KB per chunk'
    },
    loadingStrategy: {
      immediate: ['critical chunks'],
      preload: ['high priority chunks on route hover'],
      onDemand: ['normal priority chunks on navigation'],
      lazy: ['low priority chunks when needed']
    }
  };
};

export default createLazyLoadingConfig;