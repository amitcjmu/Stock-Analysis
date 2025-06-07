import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8081,  // Fixed port for frontend
    proxy: {
      '/api': {
        target: 'http://backend:8000',  // Docker service name
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
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
