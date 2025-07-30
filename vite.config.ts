import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8081,  // Fixed port for frontend
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Local backend
        changeOrigin: true,
        secure: false,
        rewrite: (path) => {
          console.log(`Proxying ${path} to backend:8000`);
          return path;
        }
      }
    }
  },
  plugins: [
    react()
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    'process.env': {},
    'process.env.NODE_ENV': JSON.stringify(mode),
  },
  build: {
    rollupOptions: {
      output: {
        // Advanced code splitting configuration for lazy loading
        manualChunks: {
          // CRITICAL - Core vendor chunks
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-query': ['@tanstack/react-query'],

          // HIGH PRIORITY - UI components
          'vendor-ui': [
            '@radix-ui/react-accordion',
            '@radix-ui/react-alert-dialog',
            '@radix-ui/react-avatar',
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-tabs'
          ],

          // NORMAL PRIORITY - Feature chunks
          'discovery': ['./src/pages/Discovery.tsx'],
          'assessment': ['./src/pages/Assess.tsx'],
          'planning': ['./src/pages/Plan.tsx'],
          'execution': ['./src/pages/Execute.tsx'],
          'modernization': ['./src/pages/Modernize.tsx'],
          'finops': ['./src/pages/FinOps.tsx'],
          'decommission': ['./src/pages/Decommission.tsx'],

          // LOW PRIORITY - utilities
          'utils': [],
          'icons': ['lucide-react'],
          'charts': ['recharts']
        },
        chunkFileNames: (chunkInfo) => {
          const name = chunkInfo.name;
          // Use descriptive names for better cache management
          // Avoid double vendor prefix by checking if name already starts with vendor
          if (name?.startsWith('vendor-')) return `assets/${name}-[hash].js`;
          if (name?.includes('vendor')) return 'assets/vendor-[name]-[hash].js';
          if (name?.includes('admin')) return 'assets/admin-[name]-[hash].js';
          return 'assets/[name]-[hash].js';
        }
      }
    },
    chunkSizeWarningLimit: 1000, // 1MB warning limit
    sourcemap: mode === 'development'
  },
  optimizeDeps: {
    include: [
      // Pre-bundle critical dependencies for faster dev startup
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'lucide-react'
    ]
  }
}));
