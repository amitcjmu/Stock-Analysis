import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

// Root Vite config for Vercel build. Ensures '@' alias resolves to project src/.
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  define: {
    'process.env': {},
    'process.env.NODE_ENV': JSON.stringify(mode)
  },
  build: {
    chunkSizeWarningLimit: 1000,
    sourcemap: mode === 'development'
  }
}));
