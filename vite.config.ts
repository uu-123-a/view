import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/react") || id.includes("node_modules\\react")) return "vendor-react";
          if (id.includes("node_modules/recharts") || id.includes("node_modules\\recharts")) return "vendor-charts";
          if (id.includes("node_modules/lucide-react") || id.includes("node_modules\\lucide-react")) return "vendor-icons";
          return undefined;
        },
      },
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true,
      },
    },
  },
});
