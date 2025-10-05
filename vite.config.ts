import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// Root Vite config used by Vercel and local dev. Mirrors the advanced config
// previously under config/tools, with paths resolved relative to project root.
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8081,
    proxy: {
      "/api": {
        target:
          process.env.DOCKER_ENV === "true"
            ? "http://backend:8000"
            : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        rewrite: (p) => p,
        proxyTimeout: 200000, // 200 seconds - support tier_2 AI analysis (180s timeout)
      },
      "/docs": {
        target:
          process.env.DOCKER_ENV === "true"
            ? "http://backend:8000"
            : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/redoc": {
        target:
          process.env.DOCKER_ENV === "true"
            ? "http://backend:8000"
            : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
      "/openapi.json": {
        target:
          process.env.DOCKER_ENV === "true"
            ? "http://backend:8000"
            : "http://localhost:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    "process.env": {},
    "process.env.NODE_ENV": JSON.stringify(mode),
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-query": ["@tanstack/react-query"],
          "vendor-ui": [
            "@radix-ui/react-accordion",
            "@radix-ui/react-alert-dialog",
            "@radix-ui/react-avatar",
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-tabs",
          ],
          discovery: ["./src/pages/Discovery.tsx"],
          assessment: ["./src/pages/Assess.tsx"],
          planning: ["./src/pages/Plan.tsx"],
          execution: ["./src/pages/Execute.tsx"],
          modernization: ["./src/pages/Modernize.tsx"],
          finops: ["./src/pages/FinOps.tsx"],
          decommission: ["./src/pages/Decommission.tsx"],
          utils: [],
          icons: ["lucide-react"],
          charts: ["recharts"],
        },
        chunkFileNames: (chunkInfo) => {
          const name = chunkInfo.name;
          if (name?.startsWith("vendor-")) return `assets/${name}-[hash].js`;
          if (name?.includes("vendor")) return "assets/vendor-[name]-[hash].js";
          if (name?.includes("admin")) return "assets/admin-[name]-[hash].js";
          return "assets/[name]-[hash].js";
        },
      },
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: mode === "development",
  },
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-router-dom",
      "@tanstack/react-query",
      "lucide-react",
    ],
  },
}));
